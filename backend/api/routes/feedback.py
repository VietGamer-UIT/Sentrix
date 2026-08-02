"""
Feedback Endpoint — POST /api/v1/feedback
==========================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
Giai đoạn: 3 (nhận + validate + fraud filter + lưu tạm)
           Giai đoạn 4-6 sẽ thêm Whisper/Librosa/ABSA vào đây

LUỒNG XỬ LÝ HIỆN TẠI (Giai đoạn 3):
  Nhận request → validate input → fraud filter → lưu audio tạm → trả response

LUỒNG XỬ LÝ ĐẦY ĐỦ (sau khi hoàn thành giai đoạn 4-8):
  Nhận request → validate → fraud filter → Whisper STT → Librosa features
  → ABSA (Gemini) → Dynamic Weighted Fusion → tính RFMS → lưu Firestore
  → [nếu P_churn > threshold] trigger Zalo ZNS
"""

import uuid
import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.api.middleware.fraud_filter import basic_fraud_filter

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Cấu hình
# ---------------------------------------------------------------------------
# Định dạng audio được chấp nhận (MIME type)
ALLOWED_AUDIO_MIME_TYPES = {
    "audio/webm",           # WebM (Chrome/Firefox ghi âm trực tiếp)
    "audio/mpeg",           # MP3
    "audio/wav",            # WAV
    "audio/ogg",            # OGG
    "audio/mp4",            # MP4 audio (Safari)
    "audio/x-m4a",          # M4A
    "application/octet-stream",  # Fallback khi browser không set đúng MIME
}

# Kích thước tối đa file audio (bytes) — 5MB
AUDIO_MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5MB

# Thư mục lưu audio tạm (Giai đoạn 3 — chưa upload lên Firebase Storage)
# Giai đoạn 8 sẽ thay bằng Firebase Storage upload
TEMP_AUDIO_DIR = Path(tempfile.gettempdir()) / "sentrix_audio_temp"


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------
class FeedbackAcceptedResponse(BaseModel):
    """Response khi phản hồi được nhận thành công."""
    request_id: str           # UUID để tracking qua các giai đoạn xử lý
    status: str               # "accepted" | "accepted_with_warning"
    message: str
    tenant_id: str
    location: str
    input_type: str           # "audio" | "text" | "audio_and_text"
    is_suspicious: bool       # Kết quả từ fraud filter
    suspicious_reason: str | None  # Lý do nếu bị đánh dấu


class FeedbackErrorResponse(BaseModel):
    """Response khi có lỗi validation."""
    error: str
    detail: str


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _ensure_temp_dir() -> None:
    """Tạo thư mục temp nếu chưa tồn tại."""
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
    # Kiểm tra MIME type
    content_type = audio_file.content_type or ""
    if content_type not in ALLOWED_AUDIO_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Định dạng audio không được hỗ trợ: '{content_type}'. "
                f"Chấp nhận: webm, mp3, wav, ogg, mp4, m4a."
            ),
        )

    # Đọc nội dung file
    content = await audio_file.read()
    file_size = len(content)

    # Kiểm tra kích thước
    if file_size > AUDIO_MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File audio quá lớn: {file_size / 1024 / 1024:.1f}MB. "
                f"Giới hạn tối đa: {AUDIO_MAX_SIZE_BYTES // 1024 // 1024}MB (~15 giây ghi âm)."
            ),
        )

    # Lưu tạm vào disk (Giai đoạn 4 sẽ đọc file này để gửi Whisper)
    _ensure_temp_dir()
    ext = Path(audio_file.filename or "audio.webm").suffix or ".webm"
    temp_path = TEMP_AUDIO_DIR / f"{request_id}{ext}"
    temp_path.write_bytes(content)

    logger.info(
        f"[Feedback] Audio lưu tạm: {temp_path} "
        f"({file_size} bytes, MIME: {content_type})"
    )

    return content, str(temp_path)


# ---------------------------------------------------------------------------
# Endpoint chính
# ---------------------------------------------------------------------------
@router.post(
    "/feedback",
    response_model=FeedbackAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Nhận phản hồi khách hàng (audio hoặc text)",
    description=(
        "Endpoint trung tâm nhận phản hồi từ Web Client của khách hàng sau khi quét QR. "
        "Chấp nhận audio (WebM/MP3/WAV, tối đa 5MB) HOẶC văn bản gõ tay, hoặc cả hai. "
        "Trả về request_id để theo dõi quá trình xử lý bất đồng bộ sau này."
    ),
    responses={
        202: {"description": "Phản hồi được nhận, đang xử lý"},
        400: {"description": "Thiếu input hoặc input không hợp lệ"},
        413: {"description": "File audio quá lớn"},
        422: {"description": "Lỗi validation form fields"},
    },
)
async def submit_feedback(
    tenant_id: str = Form(
        ...,
        description="ID của doanh nghiệp (tenant). Lấy từ QR code.",
        examples=["pho-ba-lan_1722500000000"],
    ),
    location: str = Form(
        ...,
        description="Bàn hoặc khu vực quét QR.",
        examples=["Ban 5"],
        min_length=1,
        max_length=100,
    ),
    audio_file: UploadFile | None = File(
        default=None,
        description="File ghi âm phản hồi (WebM/MP3/WAV). Tối đa 5MB (~15 giây).",
    ),
    text_content: str | None = Form(
        default=None,
        description="Phản hồi bằng văn bản gõ tay (nếu không ghi âm).",
        max_length=2000,
    ),
) -> JSONResponse:
    """
    Nhận phản hồi từ khách hàng — audio, text, hoặc cả hai.

    Luồng xử lý Giai đoạn 3:
    1. Validate: phải có ít nhất audio hoặc text.
    2. Validate audio: đúng định dạng, không quá 5MB.
    3. Fraud filter sơ bộ: audio quá ngắn? text toàn rác?
    4. Lưu audio tạm vào disk (giai đoạn 4 sẽ gửi lên Whisper).
    5. Trả response 202 Accepted kèm request_id.
    """
    # --- Bước 1: Bắt buộc phải có ít nhất 1 trong 2 ---
    has_audio = audio_file is not None and audio_file.filename
    has_text = text_content is not None and text_content.strip()

    if not has_audio and not has_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Thiếu nội dung phản hồi: phải có ít nhất 1 trong 2 — "
                "file audio (audio_file) HOẶC văn bản (text_content)."
            ),
        )

    # --- Tạo request_id duy nhất cho lần xử lý này ---
    request_id = str(uuid.uuid4())
    logger.info(
        f"[Feedback] Nhận request mới | request_id={request_id} "
        f"| tenant={tenant_id} | location={location} "
        f"| has_audio={has_audio} | has_text={has_text}"
    )

    # --- Bước 2: Validate và lưu tạm audio ---
    audio_bytes_count: int | None = None
    temp_audio_path: str | None = None

    if has_audio:
        audio_content, temp_audio_path = await _read_and_validate_audio(
            audio_file, request_id
        )
        audio_bytes_count = len(audio_content)

    # --- Bước 3: Fraud filter ---
    text_to_check = text_content.strip() if has_text else None
    fraud_result = basic_fraud_filter(
        audio_bytes=audio_bytes_count,
        text_content=text_to_check,
    )

    if fraud_result.should_reject:
        # Xóa file tạm nếu đã lưu
        if temp_audio_path and Path(temp_audio_path).exists():
            Path(temp_audio_path).unlink()
        logger.warning(
            f"[Feedback] Từ chối request {request_id}: {fraud_result.reason}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phản hồi không hợp lệ: {fraud_result.reason}",
        )

    # --- Bước 4: Log kết quả (Giai đoạn 4-6 sẽ thay bằng xử lý AI thật) ---
    if fraud_result.is_suspicious:
        logger.warning(
            f"[Feedback] Request {request_id} bị đánh dấu nghi ngờ: "
            f"{fraud_result.reason} — vẫn xử lý tiếp"
        )

    # Xác định input_type để ghi vào response
    if has_audio and has_text:
        input_type = "audio_and_text"
    elif has_audio:
        input_type = "audio"
    else:
        input_type = "text"

    # TODO (Giai đoạn 4): Gọi Whisper API để chuyển audio → text
    # TODO (Giai đoạn 5): Gọi Librosa để trích xuất MFCC/F0/Jitter/Shimmer
    # TODO (Giai đoạn 6): Gọi Gemini ABSA + Dynamic Weighted Fusion
    # TODO (Giai đoạn 7): Tính RFMS + P_churn
    # TODO (Giai đoạn 8): Lưu vào Firestore

    logger.info(
        f"[Feedback] Chấp nhận request {request_id} "
        f"| input_type={input_type} "
        f"| audio_temp={temp_audio_path or 'N/A'} "
        f"| text_preview={repr((text_to_check or '')[:50])}"
    )

    # --- Bước 5: Trả response 202 Accepted ---
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content=FeedbackAcceptedResponse(
            request_id=request_id,
            status="accepted_with_warning" if fraud_result.is_suspicious else "accepted",
            message=(
                "Phản hồi đã được nhận và đang được xử lý."
                + (f" Lưu ý: {fraud_result.reason}" if fraud_result.is_suspicious else "")
            ),
            tenant_id=tenant_id,
            location=location,
            input_type=input_type,
            is_suspicious=fraud_result.is_suspicious,
            suspicious_reason=fraud_result.reason if fraud_result.is_suspicious else None,
        ).model_dump(),
    )
