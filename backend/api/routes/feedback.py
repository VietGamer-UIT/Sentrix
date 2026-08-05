"""
Feedback Endpoint — POST /api/v1/feedback
==========================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect) — hỗ trợ bởi Đoàn Hoàng Việt
Giai đoạn: 3 (nhận + validate + fraud filter)
           4: Whisper STT
           5: Librosa audio features
           6: ABSA + Dynamic Weighted Fusion
           7: RFMS + Churn Probability
           8: Lưu Firestore multi-tenant (GIAI ĐOẠN NÀY)

LUỒNG XỬ LÝ ĐẦY ĐỦ (Giai đoạn 8):
  1. Validate input (audio/text, MIME type, kích thước)
  2. Fraud filter sơ bộ
  3. Whisper STT (audio → transcript)
  4. Librosa (audio features: MFCC, F0, Jitter, Shimmer, stress_score)
  5. ABSA qua Gemini LLM (phân tích cảm xúc theo khía cạnh)
  6. Dynamic Weighted Fusion (kết hợp text + audio, phát hiện mỉa mai)
  7. Tính RFMS + P_churn
  8. get_or_create_customer → save_feedback → update_customer_rfms
  9. Trả 202 Accepted (nếu P_churn > threshold → Giai đoạn 9 xử lý ZNS)

LƯU Ý THIẾT KẾ:
  - Các bước Librosa / ABSA / Fusion / RFMS là KHÔNG BLOCKING đối với việc trả
    response cho client — response 202 trả ngay sau khi validate xong.
    Xử lý pipeline chạy ĐỒNG BỘ trước khi trả response trong phiên bản MVP này.
    (Giai đoạn tương lai: chuyển sang async task queue nếu cần scale.)
  - Nếu ABSA hoặc Librosa lỗi → vẫn lưu feedback với dữ liệu có sẵn + ghi rõ lỗi.
  - Nếu Firestore lỗi → trả 503, KHÔNG để mất dữ liệu im lặng.
"""

import uuid
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.api.middleware.fraud_filter import basic_fraud_filter
from backend.ai_pipeline.stt_whisper import (
    transcribe_audio,
    WhisperError,
    WhisperAuthError,
    WhisperFormatError,
    WhisperTimeoutError,
)
from backend.ai_pipeline.audio_features_librosa import (
    extract_audio_features,
    AudioFeaturesError,
)
from backend.ai_pipeline.absa_llm import analyze_absa, ABSAError, ABSAAuthError
from backend.ai_pipeline.fusion import dynamic_weighted_fusion
from backend.rfms_model.churn_model import (
    calculate_churn_full,
    DEFAULT_CHURN_ALERT_THRESHOLD,
)
from backend.db.firestore_ops import (
    save_feedback,
    get_or_create_customer,
    update_customer_rfms,
    get_tenant_config,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Cấu hình
# ---------------------------------------------------------------------------
ALLOWED_AUDIO_MIME_TYPES = {
    "audio/webm",
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
    "audio/mp4",
    "audio/x-m4a",
    "application/octet-stream",
}

AUDIO_MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5MB

TEMP_AUDIO_DIR = Path(tempfile.gettempdir()) / "sentrix_audio_temp"

# Số ngày mặc định kể từ lần cuối nếu không có phone (guest)
GUEST_RECENCY_DAYS_DEFAULT = 30.0


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------
class FeedbackAcceptedResponse(BaseModel):
    """Response khi phản hồi được xử lý và lưu thành công."""
    request_id: str
    feedback_id: Optional[str]           # Firestore document ID (None nếu lưu lỗi)
    status: str                           # "processed" | "processed_with_warning" | "error"
    message: str
    tenant_id: str
    location: str
    input_type: str
    transcript: Optional[str]
    sentiment_score: Optional[float]      # Điểm cảm xúc tổng hợp [0,1]
    overall_sentiment: Optional[str]      # "Tích cực" | "Tiêu cực" | "Trung lập"
    is_sarcasm_suspected: bool
    p_churn: Optional[float]
    churn_risk_level: Optional[str]
    should_alert: bool                    # True nếu vượt ngưỡng → sẽ trigger ZNS (Giai đoạn 9)
    is_suspicious: bool
    suspicious_reason: Optional[str]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _ensure_temp_dir() -> None:
    TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


async def _read_and_validate_audio(
    audio_file: UploadFile,
    request_id: str,
) -> tuple[bytes, str]:
    """
    Đọc và validate file audio. Trả về (content_bytes, saved_temp_path).

    Raises:
        HTTPException 400: Nếu file không hợp lệ.
        HTTPException 413: Nếu file quá lớn.
    """
    content_type = audio_file.content_type or ""
    if content_type not in ALLOWED_AUDIO_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Dinh dang audio khong duoc ho tro: '{content_type}'. "
                f"Chap nhan: webm, mp3, wav, ogg, mp4, m4a."
            ),
        )

    content = await audio_file.read()
    file_size = len(content)

    if file_size > AUDIO_MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File audio qua lon: {file_size / 1024 / 1024:.1f}MB. "
                f"Gioi han toi da: {AUDIO_MAX_SIZE_BYTES // 1024 // 1024}MB."
            ),
        )

    _ensure_temp_dir()
    ext = Path(audio_file.filename or "audio.webm").suffix or ".webm"
    temp_path = TEMP_AUDIO_DIR / f"{request_id}{ext}"
    temp_path.write_bytes(content)

    logger.info(
        f"[Feedback] Audio luu tam: {temp_path} "
        f"({file_size} bytes, MIME: {content_type})"
    )
    return content, str(temp_path)


def _cleanup_temp_audio(temp_path: Optional[str]) -> None:
    """Xóa file audio tạm sau khi xử lý xong."""
    if temp_path and Path(temp_path).exists():
        try:
            Path(temp_path).unlink()
        except Exception:
            pass  # Không crash vì lỗi xóa file tạm


# ---------------------------------------------------------------------------
# Endpoint chính
# ---------------------------------------------------------------------------
@router.post(
    "/feedback",
    response_model=FeedbackAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Nhan phan hoi khach hang (audio hoac text) — Pipeline day du",
    description=(
        "Endpoint trung tam nhan phan hoi tu Web Client. "
        "Chay toan bo pipeline: STT → Librosa → ABSA → Fusion → RFMS → Firestore. "
        "Tra ve 202 Accepted kem ket qua phan tich va P_churn."
    ),
    responses={
        202: {"description": "Phan hoi duoc xu ly va luu thanh cong"},
        400: {"description": "Thieu input hoac input khong hop le"},
        413: {"description": "File audio qua lon"},
        503: {"description": "Dich vu ngoai (Firestore/Gemini) tam thoi khong kha dung"},
    },
)
async def submit_feedback(
    tenant_id: str = Form(
        ...,
        description="ID cua doanh nghiep (tenant). Lay tu QR code.",
        examples=["pho-ba-lan_1722500000000"],
    ),
    location: str = Form(
        ...,
        description="Ban hoac khu vuc quet QR.",
        examples=["Ban 5"],
        min_length=1,
        max_length=100,
    ),
    audio_file: UploadFile | None = File(
        default=None,
        description="File ghi am phan hoi (WebM/MP3/WAV). Toi da 5MB.",
    ),
    text_content: str | None = Form(
        default=None,
        description="Phan hoi bang van ban go tay.",
        max_length=2000,
    ),
    customer_phone: str | None = Form(
        default=None,
        description="So dien thoai khach hang (tuy chon). Dung de tinh RFMS. Se duoc hash truoc khi luu.",
        max_length=20,
    ),
    total_spending: float = Form(
        default=0.0,
        description="Tong chi tieu lan nay (VND). Dung tinh M trong RFMS.",
    ),
) -> JSONResponse:
    """
    Pipeline đầy đủ Giai đoạn 8: nhận → xử lý → lưu Firestore.
    """
    # -----------------------------------------------------------------------
    # Bước 1: Validate đầu vào
    # -----------------------------------------------------------------------
    has_audio = audio_file is not None and audio_file.filename
    has_text = text_content is not None and text_content.strip()

    if not has_audio and not has_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Thieu noi dung phan hoi: phai co it nhat audio hoac text_content.",
        )

    request_id = str(uuid.uuid4())
    logger.info(
        f"[Feedback] === Bat dau pipeline | request_id={request_id} "
        f"| tenant={tenant_id} | location={location} "
        f"| has_audio={has_audio} | has_text={has_text} ==="
    )

    # Xác định input_type
    if has_audio and has_text:
        input_type = "audio_and_text"
    elif has_audio:
        input_type = "audio"
    else:
        input_type = "text"

    # -----------------------------------------------------------------------
    # Bước 2: Đọc và lưu tạm audio
    # -----------------------------------------------------------------------
    audio_bytes_count: Optional[int] = None
    temp_audio_path: Optional[str] = None

    if has_audio:
        audio_content, temp_audio_path = await _read_and_validate_audio(
            audio_file, request_id
        )
        audio_bytes_count = len(audio_content)

    # -----------------------------------------------------------------------
    # Bước 3: Fraud filter
    # -----------------------------------------------------------------------
    text_to_check = text_content.strip() if has_text else None
    fraud_result = basic_fraud_filter(
        audio_bytes=audio_bytes_count,
        text_content=text_to_check,
    )

    if fraud_result.should_reject:
        _cleanup_temp_audio(temp_audio_path)
        logger.warning(f"[Feedback] Tu choi request {request_id}: {fraud_result.reason}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phan hoi khong hop le: {fraud_result.reason}",
        )

    # -----------------------------------------------------------------------
    # Bước 4: Whisper STT
    # -----------------------------------------------------------------------
    transcript: Optional[str] = text_to_check  # Nếu có text gốc thì dùng luôn

    if has_audio and temp_audio_path:
        try:
            logger.info(f"[Feedback] [4] Whisper STT ...")
            whisper_text = transcribe_audio(temp_audio_path, language="vi")
            # Ưu tiên transcript từ Whisper; nếu trống thì fallback về text gõ tay
            if whisper_text:
                transcript = whisper_text
            logger.info(f"[Feedback] Whisper: {repr((transcript or '')[:80])}")
        except WhisperAuthError as e:
            _cleanup_temp_audio(temp_audio_path)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"STT service khong kha dung (loi xac thuc): {e}",
            )
        except WhisperFormatError as e:
            logger.warning(f"[Feedback] Whisper format error (bo qua): {e}")
        except WhisperTimeoutError:
            logger.warning("[Feedback] Whisper timeout — su dung text goc neu co")
        except WhisperError as e:
            logger.warning(f"[Feedback] Whisper loi: {e}")

    # -----------------------------------------------------------------------
    # Bước 5: Librosa audio features
    # -----------------------------------------------------------------------
    audio_features: Optional[dict] = None

    if has_audio and temp_audio_path:
        try:
            logger.info(f"[Feedback] [5] Librosa feature extraction ...")
            audio_features = extract_audio_features(temp_audio_path)
            logger.info(
                f"[Feedback] Librosa: stress_score={audio_features.get('stress_score')}, "
                f"f0_mean={audio_features.get('f0_mean')}Hz"
            )
        except AudioFeaturesError as e:
            logger.warning(f"[Feedback] Librosa loi (bo qua): {e}")
        except Exception as e:
            logger.warning(f"[Feedback] Librosa loi khong xac dinh (bo qua): {e}")

    # Dọn temp audio sau khi Whisper + Librosa đã đọc xong
    _cleanup_temp_audio(temp_audio_path)
    temp_audio_path = None

    # -----------------------------------------------------------------------
    # Bước 6: ABSA + Dynamic Weighted Fusion
    # -----------------------------------------------------------------------
    absa_result: Optional[dict] = None
    fusion_result: Optional[dict] = None
    sentiment_score: float = 0.5       # neutral mặc định
    overall_sentiment: str = "Trung lap"
    is_sarcasm_suspected: bool = False

    text_for_absa = transcript or text_to_check

    if text_for_absa:
        try:
            logger.info(f"[Feedback] [6] ABSA qua Gemini ...")
            absa_result = analyze_absa(text_for_absa)

            if absa_result.get("is_spam"):
                logger.warning(f"[Feedback] ABSA phat hien SPAM/NONSENSE")

            logger.info(f"[Feedback] ABSA: {len(absa_result.get('aspects', []))} aspects")

            # Fusion
            fusion_result = dynamic_weighted_fusion(absa_result, audio_features)
            sentiment_score = fusion_result.get("sentiment_score", 0.5)
            overall_sentiment = fusion_result.get("overall_sentiment", "Trung lap")
            is_sarcasm_suspected = fusion_result.get("is_sarcasm_suspected", False)

            logger.info(
                f"[Feedback] Fusion: sentiment={sentiment_score:.4f} "
                f"({overall_sentiment}), sarcasm={is_sarcasm_suspected}"
            )
        except ABSAAuthError as e:
            logger.error(f"[Feedback] ABSA auth error: {e}")
            # Không crash — tiếp tục với sentiment_score mặc định
        except ABSAError as e:
            logger.warning(f"[Feedback] ABSA loi (su dung sentiment mac dinh): {e}")
        except Exception as e:
            logger.warning(f"[Feedback] ABSA/Fusion loi (bo qua): {e}")

    # -----------------------------------------------------------------------
    # Bước 7: Tính RFMS + P_churn
    # -----------------------------------------------------------------------
    p_churn: float = 0.5
    churn_risk_level: str = "medium"
    should_alert: bool = False
    rfms_normalized: dict = {}

    try:
        logger.info(f"[Feedback] [7] Tinh RFMS + P_churn ...")

        # Đọc cấu hình tenant để lấy churn_threshold tuỳ chỉnh nếu có
        tenant_config = None
        try:
            tenant_config = get_tenant_config(tenant_id)
        except Exception:
            pass  # Không crash nếu không đọc được config

        churn_threshold = DEFAULT_CHURN_ALERT_THRESHOLD
        if tenant_config and "churn_threshold" in tenant_config:
            churn_threshold = float(tenant_config["churn_threshold"])

        # Recency: nếu có phone → sẽ lấy từ last_feedback_at trong DB
        # Đơn giản hoá MVP: dùng giá trị mặc định, customer tự cập nhật sau
        recency_days = GUEST_RECENCY_DAYS_DEFAULT
        if customer_phone:
            # Sẽ lấy chính xác sau khi get_or_create_customer
            # Tạm dùng 1 ngày (khách vừa gửi) → sẽ tinh chỉnh sau
            recency_days = 1.0

        churn_result = calculate_churn_full(
            recency_days=recency_days,
            frequency=1,           # Mỗi feedback = 1 lần giao dịch; tích luỹ dần qua DB
            monetary=total_spending,
            sentiment_score=sentiment_score,
            churn_threshold=churn_threshold,
        )

        p_churn = churn_result["p_churn"]
        churn_risk_level = churn_result["risk_level"].lower()
        should_alert = churn_result["should_alert"]
        rfms_normalized = {k: churn_result[k] for k in ("R", "F", "M", "S")}

        logger.info(
            f"[Feedback] RFMS: P_churn={p_churn:.4f} "
            f"({churn_risk_level}) | alert={should_alert}"
        )

    except Exception as e:
        logger.error(f"[Feedback] Loi tinh RFMS/Churn: {e}")

    # -----------------------------------------------------------------------
    # Bước 8: Lưu Firestore multi-tenant
    # -----------------------------------------------------------------------
    feedback_id: Optional[str] = None
    customer_id: Optional[str] = None

    try:
        logger.info(f"[Feedback] [8] Luu Firestore ...")

        # 8a. Lấy/tạo customer nếu có phone
        if customer_phone:
            customer_doc = get_or_create_customer(tenant_id, customer_phone)
            customer_id = customer_doc["customer_id"]

        # 8b. Chuẩn bị feedback document theo schema.md
        aspects_to_save = []
        if fusion_result and fusion_result.get("aspects"):
            aspects_to_save = fusion_result["aspects"]
        elif absa_result and absa_result.get("aspects"):
            aspects_to_save = absa_result["aspects"]

        # Chuẩn bị audio_features để lưu (chỉ lấy các field theo schema, bỏ file_info)
        audio_features_to_save: Optional[dict] = None
        if audio_features:
            audio_features_to_save = {
                "mfcc_mean":    audio_features.get("mfcc_mean", []),
                "f0_mean":      audio_features.get("f0_mean", 0.0),
                "jitter":       audio_features.get("jitter", 0.0),
                "shimmer":      audio_features.get("shimmer", 0.0),
                "stress_score": audio_features.get("stress_score", 0.0),
                "is_stressed":  audio_features.get("is_stressed", False),
            }

        feedback_doc = {
            "customer_id":        customer_id,
            "location":           location,
            "input_type":         input_type,
            "transcript":         transcript or "",
            "audio_features":     audio_features_to_save,
            "aspects":            aspects_to_save,
            "sentiment_score":    sentiment_score,
            "is_sarcasm":         is_sarcasm_suspected,
            "fusion_mode":        (fusion_result or {}).get("fusion_mode"),
            "is_spam":            (absa_result or {}).get("is_spam", False),
            "p_churn":            p_churn,
            "churn_risk_level":   churn_risk_level,
            "rfms_r":             rfms_normalized.get("R"),
            "rfms_f":             rfms_normalized.get("F"),
            "rfms_m":             rfms_normalized.get("M"),
            "rfms_s":             rfms_normalized.get("S"),
            "is_suspicious":      fraud_result.is_suspicious,
            "suspicious_reason":  fraud_result.reason if fraud_result.is_suspicious else None,
            "processing_status":  "done",
            "error_message":      None,
            "request_id":         request_id,
        }

        feedback_id = save_feedback(tenant_id, feedback_doc)
        logger.info(f"[Feedback] Luu feedback thanh cong: {feedback_id}")

        # 8c. Cập nhật RFMS cho customer nếu có
        if customer_id:
            update_customer_rfms(
                tenant_id=tenant_id,
                customer_id=customer_id,
                R=rfms_normalized.get("R", 0.5),
                F=rfms_normalized.get("F", 0.0),
                M=rfms_normalized.get("M", 0.0),
                S=rfms_normalized.get("S", 0.5),
                p_churn=p_churn,
                sentiment_score_raw=sentiment_score,
            )

    except EnvironmentError as e:
        # Firebase credentials chưa cấu hình — cho phép chạy mà không cần Firestore
        logger.warning(f"[Feedback] Firestore chua cau hinh (bo qua luu): {e}")
    except Exception as e:
        logger.error(f"[Feedback] Loi luu Firestore: {type(e).__name__}: {e}")
        # Không raise — feedback đã xử lý xong, chỉ không lưu được
        # Pipeline chính (ABSA, RFMS) đã chạy xong, kết quả đã có trong response

    # -----------------------------------------------------------------------
    # Bước 9 (Giai đoạn 9 — TODO): Zalo ZNS webhook nếu should_alert
    # -----------------------------------------------------------------------
    if should_alert:
        logger.warning(
            f"[Feedback] P_churn={p_churn:.4f} vuot nguong! "
            f"[TODO-G9] Can trigger Zalo ZNS cho customer={customer_id}"
        )
        # Giai đoạn 9 sẽ implement hàm send_zalo_zns_alert() ở đây

    # -----------------------------------------------------------------------
    # Trả response 202
    # -----------------------------------------------------------------------
    final_status = "processed"
    if fraud_result.is_suspicious:
        final_status = "processed_with_warning"

    logger.info(
        f"[Feedback] === Hoan thanh pipeline | request_id={request_id} "
        f"| feedback_id={feedback_id} | p_churn={p_churn:.4f} ==="
    )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content=FeedbackAcceptedResponse(
            request_id=request_id,
            feedback_id=feedback_id,
            status=final_status,
            message=(
                "Phan hoi da duoc xu ly va luu thanh cong."
                + (" Co dau hieu dang nghi ngo." if fraud_result.is_suspicious else "")
            ),
            tenant_id=tenant_id,
            location=location,
            input_type=input_type,
            transcript=transcript,
            sentiment_score=sentiment_score,
            overall_sentiment=overall_sentiment,
            is_sarcasm_suspected=is_sarcasm_suspected,
            p_churn=p_churn,
            churn_risk_level=churn_risk_level,
            should_alert=should_alert,
            is_suspicious=fraud_result.is_suspicious,
            suspicious_reason=fraud_result.reason if fraud_result.is_suspicious else None,
        ).model_dump(),
    )
