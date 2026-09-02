"""
Feedback Endpoint — POST /api/v1/feedback
==========================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect) — hỗ trợ bởi Đoàn Hoàng Việt
Giai đoạn: 3 (nhận + validate + fraud filter)
           4: Whisper STT
           5: Librosa audio features
           6: ABSA + Dynamic Weighted Fusion
           7: RFMS + Churn Probability
           8: Lưu Firestore multi-tenant
           9: Webhook Zalo ZNS khi P_churn vượt ngưỡng (GIAI ĐOẠN NÀY)

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

import asyncio
import concurrent.futures
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
    WhisperRateLimitError,
)
from backend.ai_pipeline.audio_features_librosa import (
    extract_audio_features,
    AudioFeaturesError,
)
from backend.ai_pipeline.absa_llm import analyze_absa, ABSAError, ABSAAuthError
from backend.ai_pipeline.fusion import dynamic_weighted_fusion, normalize_aspects_for_db
from backend.rfms_model.churn_model import (
    calculate_churn_full,
    DEFAULT_CHURN_ALERT_THRESHOLD,
)
from backend.webhooks.zalo_zns import (
    send_zalo_zns_alert,
    get_primary_complained_aspect,
)
from backend.db.firestore_ops import (
    save_feedback,
    get_or_create_customer,
    update_customer_rfms,
    get_tenant_config,
    _mask_phone,
)
# ── Module 1: Anti-Fraud Services ──────────────────────────────────────────
from backend.services.audio_quality_service import analyze_audio_quality
from backend.services.semantic_validity_service import check_semantic_validity
from backend.services.rate_limit_service import check_rate_limit, record_submission
from backend.services.otp_service import verify_otp_session

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

# Timeout cho Gemini ABSA (giây).
# BUG-07 FIX: tăng từ 10 → 25s.
# Gemini Flash-Lite free tier có thể mất 5-15s; 10s quá ngắn khiến nhiều request
# rơi vào fallback sentiment=0.5/aspects=[] → làm sai toàn bộ pipeline RFMS phía sau.
# Bằng chứng: dashboard thực tế cho thấy câu "đồ ăn bẩn có ruồi" bị chấm +0.50
# (chữ ký timeout điển hình — không phải model kém).
GEMINI_ABSA_TIMEOUT_SECONDS = 25


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
    # ── Module 1: Anti-Fraud fields ────────────────────────────────────────
    validity_status: str                  # "valid" | "invalid_short_audio" | "invalid_low_snr" | "invalid_semantic" | "rate_limited"
    fraud_layer_rejected_at: Optional[int]  # Lớp nào reject (1|2|3|4|None)
    voucher_eligible: bool                # False nếu phản hồi ẩn danh
    snr_score: Optional[float]            # SNR đo được (dB)
    audio_duration_sec: Optional[float]   # Thời lượng audio (giây)
    voucher_issued: bool                  # True nếu đã phát voucher


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
    base_content_type = content_type.split(";")[0].strip().lower()
    
    if base_content_type not in ALLOWED_AUDIO_MIME_TYPES:
        logger.warning(f"[Feedback] Tu choi do dinh dang audio khong duoc ho tro: '{content_type}' (base: '{base_content_type}')")
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
        logger.warning(f"[Feedback] Tu choi do file audio qua lon: {file_size} bytes")
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
    """
    Xóa file audio tạm sau khi Whisper API đã xử lý xong.

    Căn cứ: Nguyên tắc Data Minimization theo Luật Bảo vệ dữ liệu cá nhân
    số 91/2025/QH15 — không lưu giữ dữ liệu cá nhân lâu hơn mục đích cần thiết.
    Giọng nói là dữ liệu sinh trắc học (nhạy cảm — Điều 4.1.đ NĐ 356/2025/NĐ-CP),
    phải xóa ngay sau khi Whisper chuyển thành text thành công.

    Log [Audit-PDPA] phục vụ kiểm toán nội bộ nếu bị cơ quan chức năng hỏi.
    """
    if temp_path and Path(temp_path).exists():
        try:
            Path(temp_path).unlink()
            # [Audit-PDPA] Log bắt buộc — bằng chứng xóa file audio tạm đúng hạn
            logger.info(
                f"[Audit-PDPA] Đã xóa file audio tạm sau xử lý: {Path(temp_path).name} "
                f"| Tuân thủ nguyên tắc Data Minimization — Luật 91/2025/QH15"
            )
        except Exception as _del_err:
            logger.warning(
                f"[Audit-PDPA] CẢNH BÁO: Không xóa được file audio tạm: "
                f"{Path(temp_path).name} — {_del_err}"
            )
    elif temp_path:
        # File đã bị xóa trước đó (normal case cho early-reject paths)
        logger.debug(f"[Audit-PDPA] File audio tạm đã không còn tồn tại: {temp_path}")



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
    voucher_eligible: bool = Form(
        default=False,
        description="True nếu khách hàng đồng ý nhập SĐT và muốn nhận voucher. False = ẩn danh, không cần OTP.",
    ),
    total_spending: float = Form(
        default=0.0,
        description="Tong chi tieu lan nay (VND). Dung tinh M trong RFMS.",
    ),
    feedback_id: str | None = Form(
        default=None,
        description="UUID tự sinh từ frontend phục vụ Fire-and-Forget",
    ),
) -> JSONResponse:
    """
    Pipeline đầy đủ Giai đoạn 8 + Module 1 Anti-Fraud:
      LỚP 1: Rate limit + OTP (chỉ khi voucher_eligible=True)
      LỚP 2: Audio quality gate (duration + SNR) → reject trước Whisper
      LỚP 3: Semantic validity (LLM) → reject sau Whisper, trước ABSA
      LỚP 4: Voucher budget → tích hợp trong /spin
    """""
    # -----------------------------------------------------------------------
    # Bước 1: Validate đầu vào
    # -----------------------------------------------------------------------
    has_audio = audio_file is not None and audio_file.filename
    has_text = text_content is not None and text_content.strip()

    request_id = str(uuid.uuid4())

    if not has_audio and not has_text:
        logger.warning(f"[Feedback] Tu choi do thieu noi dung (request_id={request_id}): khong co audio cung khong co text_content")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Thieu noi dung phan hoi: phai co it nhat audio hoac text_content.",
        )

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
    # ANTI-FRAUD LỚP 1 — Rate Limiting + OTP (chỉ áp dụng khi voucher_eligible)
    # -----------------------------------------------------------------------
    # Phản hồi ẩn danh (voucher_eligible=False): bỏ qua OTP và rate limit.
    # Lý do: ưu tiên thu thập dữ liệu; ẩn danh → không nhận voucher → ít động cơ gian lận.
    validity_status: str = "valid"          # Track qua toàn bộ pipeline
    fraud_layer_rejected_at: Optional[int] = None
    effective_voucher_eligible: bool = voucher_eligible and bool(customer_phone)

    if effective_voucher_eligible:
        # 1a. Kiểm tra OTP đã verified chưa
        otp_check = verify_otp_session(customer_phone, "__check_only__")
        # verify_otp_session với code giả → sẽ fail, nhưng nếu session đã verified thì pass
        # Cách đúng: đọc session từ Firestore để check verified flag
        try:
            from backend.db.firestore_client import get_firestore_client as _get_fs
            from backend.services.otp_service import _hash_phone_for_otp as _hpo
            _db = _get_fs()
            _session_key = _hpo(customer_phone)
            _otp_snap = _db.collection("otp_sessions").document(_session_key).get()
            _otp_verified = _otp_snap.exists and (_otp_snap.to_dict() or {}).get("verified", False)
        except Exception:
            _otp_verified = True  # Firestore lỗi → cho qua (không chặn do lỗi hạ tầng)

        if not _otp_verified:
            _cleanup_temp_audio(temp_audio_path)
            logger.warning(f"[Feedback] Chặn Lớp 1: OTP chưa verified | phone=****{customer_phone[-4:]}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vui lòng xác thực số điện thoại qua OTP trước khi nhận voucher.",
            )

        # 1b. Kiểm tra rate limit (1 lượt hợp lệ / 24h / SĐT)
        _ip = None  # FastAPI không expose IP trực tiếp ở đây; thêm Request nếu cần
        rate_result = check_rate_limit(
            phone_number=customer_phone,
            tenant_id=tenant_id,
        )
        if not rate_result.allowed:
            # Rate limit KHÔNG phải gian lận — chỉ giới hạn hợp lệ
            # Vẫn cho lưu feedback nhưng không nhận voucher
            validity_status = "rate_limited"
            fraud_layer_rejected_at = 1
            effective_voucher_eligible = False
            logger.info(
                f"[Feedback] Rate limited (Lớp 1): phone=****{customer_phone[-4:]} "
                f"— vẫn lưu feedback, không phát voucher"
            )

    # -----------------------------------------------------------------------
    # Bước 3: Fraud filter sơ bộ (rule-based, giữ nguyên từ phiên bản cũ)
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
    # Bước 4 + 5: Whisper STT và Librosa audio features — CHẠY SONG SONG
    # Dùng asyncio.gather + ThreadPoolExecutor để không block event loop.
    # -----------------------------------------------------------------------
    transcript: Optional[str] = text_to_check  # Nếu có text gốc thì dùng luôn
    audio_features: Optional[dict] = None
    # Khởi tạo các biến audio quality (sẽ được gán trong block audio nếu có audio)
    if not has_audio:
        _audio_duration_sec = None
        _snr_score = None

    if has_audio and temp_audio_path:
        # ── ANTI-FRAUD LỚP 2: Audio Quality Gate ──────────────────────────────
        # Chạy TRƯỚC Whisper để tiết kiệm chi phí API khi audio rác.
        # Đọc lại bytes từ file tạm (đã lưu ở bước 2).
        if validity_status == "valid" and fraud_layer_rejected_at is None:
            try:
                _audio_bytes_for_qc = Path(temp_audio_path).read_bytes()
                _quality_result = analyze_audio_quality(_audio_bytes_for_qc)
                _audio_duration_sec = _quality_result.duration_sec
                _snr_score = _quality_result.snr_db

                if not _quality_result.passed:
                    # Reject ngay — KHÔNG gọi Whisper
                    _cleanup_temp_audio(temp_audio_path)
                    logger.warning(
                        f"[Feedback] Reject Lớp 2 ({_quality_result.reject_reason}): "
                        f"{_quality_result.reject_message}"
                    )
                    validity_status = _quality_result.reject_reason or "invalid_short_audio"
                    fraud_layer_rejected_at = 2
                    effective_voucher_eligible = False
                    # Lưu partial feedback để audit và hiển thị % bị lọc trên dashboard
                    _partial_doc = {
                        "customer_id":          None,
                        "phone_masked":          _mask_phone(customer_phone) if customer_phone else None,
                        "location":             location,
                        "input_type":           input_type,
                        "transcript":           "",
                        "aspects":              [],
                        "sentiment_score":      None,
                        "validity_status":      validity_status,
                        "fraud_layer_rejected_at": fraud_layer_rejected_at,
                        "voucher_eligible":     False,
                        "voucher_issued":        False,
                        "snr_score":             _snr_score,
                        "audio_duration_sec":    _audio_duration_sec,
                        "is_spam":              False,
                        "is_suspicious":        False,
                        "suspicious_reason":    None,
                        "p_churn":              None,
                        "processing_status":    "rejected_layer2",
                        "request_id":           request_id,
                    }
                    _fid = save_feedback(tenant_id, _partial_doc, feedback_id_override=feedback_id)
                    return JSONResponse(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        content={
                            "request_id": request_id,
                            "feedback_id": _fid,
                            "status": "rejected",
                            "validity_status": validity_status,
                            "fraud_layer_rejected_at": fraud_layer_rejected_at,
                            "message": _quality_result.reject_message,
                            "voucher_eligible": False,
                            "voucher_issued": False,
                        },
                    )
            except Exception as _qe:
                logger.warning(f"[Feedback] Audio quality check lỗi (bỏ qua): {_qe}")
                _audio_duration_sec = None
                _snr_score = None
        else:
            _audio_duration_sec = None
            _snr_score = None

        loop = asyncio.get_event_loop()
        _executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

        # --- Wrapper chạy Whisper trong thread ---
        def _run_whisper() -> Optional[str]:
            try:
                logger.info("[Feedback] [4] Groq Whisper STT (thread) ...")
                result = transcribe_audio(temp_audio_path, language="vi")
                logger.info(f"[Feedback] Groq Whisper xong: {repr((result or '')[:80])}")
                return result
            except (WhisperAuthError, WhisperRateLimitError):
                raise  # Sẽ được xử lý ở bên ngoài
            except (WhisperFormatError, WhisperTimeoutError, WhisperError) as e:
                logger.warning(f"[Feedback] Whisper loi (bo qua): {type(e).__name__}: {e}")
                return None

        # --- Wrapper chạy Librosa trong thread ---
        def _run_librosa() -> Optional[dict]:
            try:
                logger.info("[Feedback] [5] Librosa feature extraction (thread) ...")
                feats = extract_audio_features(temp_audio_path)
                logger.info(
                    f"[Feedback] Librosa xong: stress_score={feats.get('stress_score')}, "
                    f"f0_mean={feats.get('f0_mean')}Hz"
                )
                return feats
            except (AudioFeaturesError, Exception) as e:
                logger.warning(f"[Feedback] Librosa loi (bo qua): {type(e).__name__}: {e}")
                return None

        try:
            # Gửi cả 2 tác vụ vào ThreadPoolExecutor, chạy song song
            whisper_future = loop.run_in_executor(_executor, _run_whisper)
            librosa_future = loop.run_in_executor(_executor, _run_librosa)
            whisper_result, librosa_result = await asyncio.gather(
                whisper_future, librosa_future, return_exceptions=True
            )

            # Xử lý kết quả Whisper
            if isinstance(whisper_result, WhisperRateLimitError):
                _cleanup_temp_audio(temp_audio_path)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Hệ thống đang bận, vui lòng thử lại sau vài giây.",
                )
            elif isinstance(whisper_result, WhisperAuthError):
                _cleanup_temp_audio(temp_audio_path)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"STT service khong kha dung (loi xac thuc): {whisper_result}",
                )
            elif isinstance(whisper_result, BaseException):
                logger.warning(f"[Feedback] Whisper exception trong gather: {whisper_result}")
            elif whisper_result:
                transcript = whisper_result

            # Xử lý kết quả Librosa
            if isinstance(librosa_result, BaseException):
                logger.warning(f"[Feedback] Librosa exception trong gather: {librosa_result}")
            elif librosa_result:
                audio_features = librosa_result

        finally:
            _executor.shutdown(wait=False)

    # Dọn temp audio sau khi Whisper + Librosa đã đọc xong
    _cleanup_temp_audio(temp_audio_path)
    temp_audio_path = None

    # -----------------------------------------------------------------------
    # Bước 6: ABSA + Dynamic Weighted Fusion
    # -----------------------------------------------------------------------
    absa_result: Optional[dict] = None
    fusion_result: Optional[dict] = None
    # 0.D FIX: Fallback là None thay vì 0.0.
    # Lý do: 0.0 bị lưu vào Firestore và dashboard hiển thị "0.00" khi ABSA fail/timeout.
    # None rõ ràng hơn: "chưa có kết quả ABSA" khác với "trung tính thật sự" (= 0.0).
    # churn_model.py nhận S [0,1] → dùng _internal_sentiment_for_rfms (không ảnh hưởng).
    sentiment_score: Optional[float] = None   # external [-1, +1] — None khi ABSA chưa chạy
    _internal_sentiment_for_rfms: float = 0.5  # internal [0,1] — dùng tính RFMS S
    overall_sentiment: str = "Trung lap"
    is_sarcasm_suspected: bool = False

    text_for_absa = transcript or text_to_check

    # ── ANTI-FRAUD LỚP 3: Semantic Validity (LLM Classifier) ────────────────────
    # Chạy SAU Whisper (cần có transcript), TRƯỚC ABSA
    # để không tốn LLM call ABSA cho các phản hồi vô nghĩa.
    _semantic_validity_reason: str = ""
    if text_for_absa and validity_status == "valid" and fraud_layer_rejected_at is None:
        try:
            # Lấy transcript lần trước của customer để phát hiện copy-paste
            _last_transcript: Optional[str] = None
            if customer_phone:
                try:
                    _cust_for_check = get_or_create_customer(tenant_id, customer_phone)
                    _last_transcript = (_cust_for_check or {}).get("last_transcript")
                except Exception:
                    pass

            logger.info("[Feedback] [LỚP 3] Semantic validity check ...")
            _sem_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            _sem_loop = asyncio.get_event_loop()
            try:
                _sem_result = await asyncio.wait_for(
                    _sem_loop.run_in_executor(
                        _sem_executor,
                        check_semantic_validity,
                        text_for_absa,
                        _last_transcript,
                    ),
                    timeout=20,  # Timeout dài hơn 1 chút so với SEMANTIC_CHECK_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                _sem_result = None  # Fallback: tiếp tục xử lý
            finally:
                _sem_executor.shutdown(wait=False)

            if _sem_result is not None and not _sem_result.is_valid:
                validity_status = "invalid_semantic"
                fraud_layer_rejected_at = 3
                effective_voucher_eligible = False
                _semantic_validity_reason = _sem_result.reason
                logger.warning(
                    f"[Feedback] Reject LỚp 3 (invalid_semantic): {_sem_result.reason}"
                )
                # Lưu vào Firestore (ẩn khỏi dashboard nhưng có thể audit)
                # Tiếp tục xử lý (không early-exit) — vẫn luưu record ẩn
        except Exception as _se:
            logger.warning(f"[Feedback] Semantic validity lỗi (bỏ qua): {_se}")

    # Bỏ qua ABSA nếu đã bị reject ở Lớp 3 — tiết kiệm 1 lần gọi Gemini
    if text_for_absa and validity_status not in ("invalid_semantic",):
        try:
            logger.info(
                f"[Feedback] [6] ABSA qua Gemini (timeout={GEMINI_ABSA_TIMEOUT_SECONDS}s) ..."
            )
            # Chạy ABSA trong ThreadPoolExecutor với timeout để tránh block > 10s
            _absa_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            _absa_loop = asyncio.get_event_loop()
            try:
                absa_result = await asyncio.wait_for(
                    _absa_loop.run_in_executor(_absa_executor, analyze_absa, text_for_absa),
                    timeout=GEMINI_ABSA_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    f"[Feedback] Gemini ABSA timeout sau {GEMINI_ABSA_TIMEOUT_SECONDS}s "
                    "— su dung sentiment mac dinh (fallback)."
                )
                absa_result = None
            finally:
                _absa_executor.shutdown(wait=False)

            if absa_result is not None:
                if absa_result.get("is_spam"):
                    logger.warning(f"[Feedback] ABSA phat hien SPAM/NONSENSE")

                logger.info(f"[Feedback] ABSA: {len(absa_result.get('aspects', []))} aspects")

                # D2 FIX: fusion_result trả ra 2 giá trị:
                #   sentiment_score         = external [-1, +1] → lưu Firestore
                #   _internal_sentiment_score = internal [0, 1] → dùng RFMS S
                fusion_result = dynamic_weighted_fusion(absa_result, audio_features)
                sentiment_score = fusion_result.get("sentiment_score", 0.0)  # external
                _internal_sentiment_for_rfms = fusion_result.get("_internal_sentiment_score", 0.5)
                overall_sentiment = fusion_result.get("overall_sentiment", "Trung lap")
                is_sarcasm_suspected = fusion_result.get("is_sarcasm_suspected", False)

                logger.info(
                    f"[Feedback] Fusion: sentiment_ext={sentiment_score} "
                    f"({overall_sentiment}), internal={_internal_sentiment_for_rfms:.4f}, "
                    f"sarcasm={is_sarcasm_suspected}"
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

    is_spam = (absa_result or {}).get("is_spam", False)
    is_suspicious_flag = fraud_result.is_suspicious or is_spam

    if is_suspicious_flag:
        logger.warning(f"[Feedback] Phat hien SPAM/NONSENSE -> Bo qua RFMS va Churn")
        sentiment_score = (fusion_result or {}).get("sentiment_score", 0.1)
        overall_sentiment = "Spam"
        p_churn = 0.0
        churn_risk_level = "none"
        should_alert = False
    else:
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

            # ALG-01 FIX: Lấy frequency + recency_days THẬT từ Firestore customer document.
            # Trước đây hardcode frequency=1, recency_days=1 → khiến RFMS vô nghĩa
            # (khách đến 50 lần vẫn bị tính như khách mới đến lần đầu).
            recency_days = GUEST_RECENCY_DAYS_DEFAULT  # fallback: guest không có SĐT
            frequency_actual = 1                        # fallback: ít nhất 1 lần (feedback này)

            if customer_phone:
                try:
                    # get_or_create_customer đã được gọi ở bước 8a (bên dưới),
                    # nhưng để lấy dữ liệu hiện tại TRƯỚC khi tăng feedback_count,
                    # ta gọi get_or_create_customer ở đây sớm hơn.
                    # Hàm này idempotent — gọi 2 lần an toàn, lần 2 chỉ đọc, không tạo mới.
                    customer_doc_pre = get_or_create_customer(tenant_id, customer_phone)
                    old_count = customer_doc_pre.get("feedback_count", 0)
                    # frequency = số lần đã gửi trước + 1 (lần này)
                    frequency_actual = old_count + 1

                    last_at = customer_doc_pre.get("last_feedback_at")
                    if last_at is not None:
                        from datetime import datetime, timezone
                        if hasattr(last_at, "timestamp"):
                            # Firestore Timestamp object
                            last_dt = datetime.fromtimestamp(last_at.timestamp(), tz=timezone.utc)
                        else:
                            last_dt = last_at
                        delta = datetime.now(timezone.utc) - last_dt
                        recency_days = max(0.0, delta.total_seconds() / 86400)
                    else:
                        recency_days = 1.0   # khách mới (lần đầu) → gần đây

                    logger.info(
                        f"[Feedback] RFMS input thực: frequency={frequency_actual}, "
                        f"recency_days={recency_days:.2f}d"
                    )
                except Exception as e_rfms_pre:
                    logger.warning(
                        f"[Feedback] Không lấy được customer data cho RFMS — dùng fallback: {e_rfms_pre}"
                    )
                    recency_days = 1.0
                    frequency_actual = 1

            churn_result = calculate_churn_full(
                recency_days=recency_days,
                frequency=frequency_actual,   # FIX D1: dùng giá trị thật, không hardcode 1
                monetary=total_spending,
                # FIX D2: RFMS cần thang [0,1] — dùng biến internal, KHÔNG dùng sentiment_score [-1,+1]
                sentiment_score=_internal_sentiment_for_rfms,
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
    feedback_id_created: Optional[str] = None
    customer_id: Optional[str] = None

    try:
        logger.info(f"[Feedback] [8] Luu Firestore ...")

        # 8a. Lấy/tạo customer nếu có phone và KHÔNG phải rác
        if customer_phone and not is_suspicious_flag:
            customer_doc = get_or_create_customer(tenant_id, customer_phone)
            customer_id = customer_doc["customer_id"]

        # 8b. Chuẩn bị feedback document theo schema.md
        aspects_to_save = []
        if fusion_result and fusion_result.get("aspects"):
            # fusion_result đã chứa normalized aspects (từ normalize_aspects_for_db trong fusion.py)
            aspects_to_save = fusion_result["aspects"]
        elif absa_result and absa_result.get("aspects"):
            # Fallback: normalize ở đây nếu không có fusion_result
            aspects_to_save = normalize_aspects_for_db(absa_result["aspects"])

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

        # Lấy phone_masked nếu có SĐT (để hiển thị trên Dashboard mà không lộ SĐT gốc)
        phone_masked: Optional[str] = None
        if customer_phone:
            phone_masked = _mask_phone(customer_phone)

        feedback_doc = {
            "customer_id":        customer_id,
            "phone_masked":        phone_masked,          # SĐT ẩn danh hóa, ví dụ "090****567"
            "location":           location,
            "input_type":         input_type,
            "transcript":         transcript or "",
            "audio_features":     audio_features_to_save,
            "aspects":            aspects_to_save,
            "sentiment_score":    sentiment_score,
            # V2: overall_sentiment float [-1,+1] từ ABSA LLM (không phải string)
            # Khác với sentiment_score (fusion text+audio). Dùng cho dashboard biểu đồ aspect.
            "overall_sentiment_float": (absa_result or {}).get("overall_sentiment"),
            # key_phrase: preview ~15 từ cho dashboard, không dùng transcript đầy đủ
            "key_phrase":         (fusion_result or {}).get("key_phrase") or (absa_result or {}).get("key_phrase", ""),
            "is_sarcasm":         is_sarcasm_suspected,
            "sarcasm_from_audio": is_sarcasm_suspected and not (absa_result or {}).get("sarcasm_detected", False),
            "fusion_mode":        (fusion_result or {}).get("fusion_mode"),
            "is_spam":            (absa_result or {}).get("is_spam", False),
            "p_churn":            p_churn,
            "churn_risk_level":   churn_risk_level,
            "rfms_r":             rfms_normalized.get("R"),
            "rfms_f":             rfms_normalized.get("F"),
            "rfms_m":             rfms_normalized.get("M"),
            "rfms_s":             rfms_normalized.get("S"),
            "is_suspicious":      is_suspicious_flag,
            "suspicious_reason":  fraud_result.reason if fraud_result.is_suspicious else None,
            "processing_status":  "done",
            "error_message":      None,
            "request_id":         request_id,
            # ZNS voucher fields — sẽ được cập nhật ở Bước 9 sau khi gửi ZNS thành công
            "zns_voucher_code":   None,
            "zns_sent_at":        None,
            # ── Module 1: Anti-Fraud log fields ───────────────────────────────
            "validity_status":       validity_status,
            "fraud_layer_rejected_at": fraud_layer_rejected_at,
            "voucher_eligible":      effective_voucher_eligible,
            "voucher_issued":         False,  # sẽ cập nhật sau khi /spin chạy
            "spin_used":             False,
            "snr_score":             _snr_score,
            "audio_duration_sec":    _audio_duration_sec,
        }

        feedback_id_created = save_feedback(tenant_id, feedback_doc, feedback_id_override=feedback_id)
        logger.info(f"[Feedback] Luu feedback thanh cong: {feedback_id_created}")

        # 8c. Cập nhật RFMS cho customer nếu có (bỏ qua nếu spam hoặc invalid_semantic)
        # Chỉ cập nhật RFMS khi feedback VALID để không làm sai model với dữ liệu rác.
        # Feedback invalid vẫn được lưu Firestore (để audit) nhưng không ảnh hưởng RFMS.
        if customer_id and not is_suspicious_flag and validity_status == "valid":
            update_customer_rfms(
                tenant_id=tenant_id,
                customer_id=customer_id,
                R=rfms_normalized.get("R", 0.5),    # 0.5 = unknown (safe default)
                F=rfms_normalized.get("F", 0.0),    # 0.0 = lần đầu
                M=rfms_normalized.get("M", 0.0),    # 0.0 = chưa có spending
                S=rfms_normalized.get("S", 0.5),    # 0.5 = neutral (safe default)
                p_churn=p_churn,
                sentiment_score_raw=(
                    _internal_sentiment_for_rfms  # internal [0,1] cho running avg
                ),
            )
            # Cập nhật last_transcript để Lớp 3 phát hiện duplicate lần sau
            try:
                from backend.db.firestore_client import get_firestore_client as _get_fs2
                _db2 = _get_fs2()
                _cust_ref2 = (
                    _db2.collection("tenants").document(tenant_id)
                    .collection("customers").document(customer_id)
                )
                _cust_ref2.update({"last_transcript": (transcript or "")[:500]})
            except Exception as _lt_err:
                logger.warning(f"[Feedback] Không cập nhật last_transcript: {_lt_err}")

        # 8d. Ghi nhận rate limit sau khi đã lưu thành công (chỉ lượt valid có SĐT)
        if validity_status == "valid" and customer_phone:
            try:
                record_submission(phone_number=customer_phone, tenant_id=tenant_id)
            except Exception as _rl_err:
                logger.warning(f"[Feedback] Không ghi rate limit: {_rl_err}")

    except (EnvironmentError, FileNotFoundError) as e:
        # Firebase credentials chưa cấu hình — cho phép chạy mà không cần Firestore
        # (chỉ xảy ra khi không có .env hoặc serviceAccountKey.json)
        logger.warning(
            f"[Feedback] Firestore chua cau hinh — bo qua luu (KHONG co feedback_id): {e}\n"
            f"  → Kiem tra: FIREBASE_CREDENTIALS_PATH hoac FIREBASE_PROJECT_ID/PRIVATE_KEY/CLIENT_EMAIL "
            f"trong file .env"
        )
        # EnvironmentError: không raise vì đây là lỗi môi trường dev/staging chưa setup
        # feedback_id sẽ là None, Frontend sẽ biết không lưu được
    except Exception as e:
        # LỖI THẬT (network, permissions, ...): PHẢI báo lỗi cho Frontend
        # Không được nuốt lỗi vì sẽ khiến SpinPage mất feedback_id và voucher
        logger.error(
            f"[Feedback] LOI LUU FIRESTORE NGHIEM TRONG: {type(e).__name__}: {e}\n"
            f"  → feedback_id se la None, Frontend biet can retry."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Luu feedback that bai do loi Firestore: {type(e).__name__}. "
                "Vui long thu lai sau hoac lien he ky thuat."
            ),
        )

    # --------------------------------------------------------------------------
    # Bước 9 (Giai đoạn 9): Zalo ZNS webhook khi P_churn vượt ngưỡng
    # ĐIỀU KIỆN TRIGGER V2 (cải tiến so với v1 — if-else đơn giản):
    #   p_churn > churn_threshold (mặc định 0.85)
    #   AND sentiment_score (thực đo từ feedback này) < ZNS_NEG_SENTIMENT_THRESHOLD
    # Lý do thêm điều kiện sentiment:
    #   - Khách có p_churn cao nhưng feedback này tích cực (hài lòng) → KBKZNS
    #     (ngưỡi ta đang quay lại, không nên gửi voucher 'cảm ơn vì đã rời bỏ')
    #   - Trigger đúng thời điểm: khi khách vừa rời + sentiment vừa có dấu hiệu tiêu cực
    # ZNS_NEG_SENTIMENT_THRESHOLD: điểm sentinel lưu trong config hoặc mặc định -0.2
    # --------------------------------------------------------------------------
    ZNS_NEG_SENTIMENT_THRESHOLD = float(os.getenv("ZNS_NEG_SENTIMENT_THRESHOLD", "-0.2"))

    # Kiểm tra điều kiện ZNS trigger v2: p_churn cao và sentiment lần này có dấu hiệu xấu
    _sentiment_for_zns = sentiment_score if sentiment_score is not None else 0.0
    _zns_trigger = (
        should_alert
        and customer_phone
        and _sentiment_for_zns < ZNS_NEG_SENTIMENT_THRESHOLD
    )

    if _zns_trigger:
        logger.warning(
            f"[Feedback] ZNS TRIGGER v2: P_churn={p_churn:.4f} + "
            f"sentiment={_sentiment_for_zns:.3f} < {ZNS_NEG_SENTIMENT_THRESHOLD} "
            f"→ Trigger Zalo ZNS!"
        )
    elif should_alert and customer_phone and not _zns_trigger:
        logger.info(
            f"[Feedback] P_churn cao ({p_churn:.4f}) nhưng sentiment={_sentiment_for_zns:.3f} ≥ {ZNS_NEG_SENTIMENT_THRESHOLD} "
            f"→ Bỏ qua ZNS (khách vừa phản hồi tích cực, không phù hợp gửi voucher giữ chân)"
        )

    zns_result: Optional[dict] = None

    if _zns_trigger:
        logger.warning(
            f"[Feedback] P_churn={p_churn:.4f} VUOT NGUONG — Trigger Zalo ZNS!"
        )
        try:
            # Lấy khía cạnh bị phàn nàn nhiều nhất
            primary_aspect = get_primary_complained_aspect(
                fusion_result.get("aspects", []) if fusion_result else []
            )

            # Sinh voucher code đơn giản (production: lấy từ DB hoặc service riêng)
            voucher_code = f"BACK{abs(hash(customer_phone + tenant_id)) % 90 + 10}"

            # Gọi ZNS — hàm này KHÔNG raise exception, chỉ trả dict
            zns_result = send_zalo_zns_alert(
                customer_phone=customer_phone,
                tenant_id=tenant_id,
                aspect_complained=primary_aspect,
                voucher_code=voucher_code,
                p_churn=p_churn,
            )

            if zns_result["success"]:
                logger.info(
                    f"[Feedback] ZNS gui thanh cong | "
                    f"tracking_id={zns_result['tracking_id']} | "
                    f"zalo_msg_id={zns_result['zalo_message_id']}"
                )
                # Cập nhật zns_sent_at + voucher vào Firestore customer VÀ feedback doc
                from backend.db.firestore_client import get_firestore_client as _get_db
                from datetime import datetime, timezone
                _zns_now = datetime.now(timezone.utc)
                if customer_id:
                    try:
                        db = _get_db()
                        cust_ref = (
                            db.collection("tenants").document(tenant_id)
                            .collection("customers").document(customer_id)
                        )
                        cust_ref.update({
                            "zns_sent_at":      _zns_now,
                            "zns_voucher_code": voucher_code,
                        })
                    except Exception as e_zns_update:
                        logger.warning(f"[Feedback] Khong update zns_sent_at cho customer: {e_zns_update}")
                # Cập nhật feedback doc với voucher info (để audit/dashboard)
                if feedback_id:
                    try:
                        db = _get_db()
                        fb_ref = (
                            db.collection("tenants").document(tenant_id)
                            .collection("feedbacks").document(feedback_id)
                        )
                        fb_ref.update({
                            "zns_voucher_code": voucher_code,
                            "zns_sent_at":      _zns_now,
                        })
                        logger.info(f"[Feedback] Cap nhat voucher vao feedback doc: {feedback_id}")
                    except Exception as e_fb_update:
                        logger.warning(f"[Feedback] Khong update voucher vao feedback doc: {e_fb_update}")
            else:
                logger.warning(
                    f"[Feedback] ZNS gui that bai: "
                    f"{zns_result['error_type']}: {zns_result['error_detail'][:100]}"
                )
        except Exception as e_zns:
            # Safety net — ZNS KHONG duoc crash pipeline chinh
            logger.error(f"[Feedback] ZNS unexpected error (bo qua): {type(e_zns).__name__}: {e_zns}")

    elif should_alert and not customer_phone:
        logger.warning(
            f"[Feedback] P_churn={p_churn:.4f} vuot nguong nhung KHONG co customer_phone "
            "— khong gui ZNS. De gui ZNS, frontend can truyen customer_phone."
        )

    # -----------------------------------------------------------------------
    # Trả response 202
    # -----------------------------------------------------------------------
    final_status = "processed"
    if fraud_result.is_suspicious:
        final_status = "processed_with_warning"

    logger.info(
        f"[Feedback] === Hoan thanh pipeline | request_id={request_id} "
        f"| feedback_id={feedback_id_created or feedback_id} | p_churn={p_churn:.4f} ==="
    )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content=FeedbackAcceptedResponse(
            request_id=request_id,
            feedback_id=feedback_id_created or feedback_id,
            status=final_status,
            message=(
                "Phan hoi da duoc xu ly va luu thanh cong."
                + (" Co dau hieu dang nghi ngo." if fraud_result.is_suspicious else "")
                + (" (Noi dung khong hop le, khong tinh vao thong ke.)" if validity_status == "invalid_semantic" else "")
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
            # ── Module 1: Anti-Fraud fields ─────────────────────────────────
            validity_status=validity_status,
            fraud_layer_rejected_at=fraud_layer_rejected_at,
            voucher_eligible=effective_voucher_eligible,
            snr_score=_snr_score,
            audio_duration_sec=_audio_duration_sec,
            voucher_issued=False,  # Luôn False ở đây — voucher phát qua /spin riêng
        ).model_dump(),
    )
