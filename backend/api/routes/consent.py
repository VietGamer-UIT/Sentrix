"""
Consent Routes — POST /api/v1/consent/record
=============================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
Module 2 — Tuân thủ Nghị định 356/2025/NĐ-CP

MỤC ĐÍCH:
  Nhận bằng chứng đồng ý từ web-client và lưu vào Firestore.
  Đây là endpoint duy nhất ghi vào collection `consent_records/`.

CĂN CỨ PHÁP LÝ:
  Điều 6.2 Nghị định 356/2025/NĐ-CP — bên kiểm soát dữ liệu (Sentrix)
  phải lưu giữ được bằng chứng đồng ý (thời điểm, nội dung đã đồng ý,
  phiên bản điều khoản) để chứng minh khi có tranh chấp.

FIRESTORE PATH:
  consent_records/{tenant_id}/records/{record_id}

THIẾT KẾ:
  - Không cần auth — frontend gọi sau khi user bấm đồng ý.
  - IP address được lấy từ Request object (X-Forwarded-For nếu qua proxy).
  - Không fail-hard: nếu Firestore lỗi → trả 503 nhưng KHÔNG block UX user.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, field_validator

from backend.db.firestore_ops import save_consent_record

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Version hiện tại của điều khoản — tăng khi nội dung thay đổi
# ---------------------------------------------------------------------------
CURRENT_CONSENT_VERSION = "v1.0-356-2025"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class ConsentRecordRequest(BaseModel):
    """
    Payload từ frontend khi user bấm "Đồng ý và tiếp tục".
    """
    tenant_id: str
    consent_version: str          # phiên bản user đã thấy — phải khớp CURRENT_CONSENT_VERSION
    consent_given_at: str         # ISO 8601 UTC string (từ Date.toISOString() JS)
    phone_hash: Optional[str] = None  # SHA-256 của SĐT nếu user đã nhập (None nếu ẩn danh)
    anonymous: bool = False       # True nếu user chọn ẩn danh tại thời điểm consent

    @field_validator("consent_version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        # Chấp nhận version hiện tại (bảo vệ tránh replay với version cũ đã lỗi thời)
        # Nếu cần hỗ trợ multi-version cho backward compat, thêm logic ở đây.
        allowed_versions = {CURRENT_CONSENT_VERSION}
        if v not in allowed_versions:
            raise ValueError(
                f"Consent version '{v}' không hợp lệ. "
                f"Phiên bản hiện tại: {CURRENT_CONSENT_VERSION}"
            )
        return v

    @field_validator("phone_hash")
    @classmethod
    def validate_phone_hash(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        # Hash SHA-256 = 64 ký tự hex
        if len(v) != 64 or not all(c in "0123456789abcdef" for c in v.lower()):
            raise ValueError("phone_hash phải là chuỗi SHA-256 hex 64 ký tự.")
        return v.lower()


class ConsentRecordResponse(BaseModel):
    success: bool
    record_id: Optional[str]
    message: str


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.post(
    "/consent/record",
    response_model=ConsentRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Lưu bằng chứng đồng ý xử lý dữ liệu cá nhân",
    description=(
        "Lưu consent record vào Firestore theo yêu cầu của Điều 6.2 "
        "Nghị định 356/2025/NĐ-CP. Được gọi từ web-client ngay khi user "
        "bấm 'Đồng ý và tiếp tục' trên màn hình Consent Window."
    ),
)
async def record_consent(
    body: ConsentRecordRequest,
    request: Request,
):
    """
    Lưu bằng chứng đồng ý.

    Frontend gọi endpoint này ngay TRƯỚC khi chuyển vào màn hình ghi âm.
    Dữ liệu lưu là bằng chứng pháp lý để Sentrix chứng minh có sự đồng ý
    hợp lệ theo Nghị định 356/2025/NĐ-CP nếu có tranh chấp sau này.
    """
    # Lấy IP — ưu tiên X-Forwarded-For (qua Render.com / Cloudflare proxy)
    ip_address: str = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or request.client.host
        if request.client else "unknown"
    )

    user_agent: str = request.headers.get("user-agent", "")[:512]

    # Parse consent_given_at từ ISO string
    try:
        consent_given_at = datetime.fromisoformat(
            body.consent_given_at.replace("Z", "+00:00")
        )
    except ValueError:
        consent_given_at = datetime.now(timezone.utc)
        logger.warning(
            f"[PDPA] Không parse được consent_given_at: '{body.consent_given_at}' "
            "— dùng thời điểm server nhận request."
        )

    # Xác định danh mục dữ liệu theo lựa chọn của user
    if body.anonymous:
        # Ẩn danh: không có SĐT → không thu thập dữ liệu cơ bản Điều 3 khoản 7
        data_categories = [
            "voice_biometric",   # Điều 4.1.đ — nhạy cảm
            "behavior_tracking", # Điều 4.1.l — nhạy cảm
        ]
    else:
        data_categories = [
            "voice_biometric",   # Điều 4.1.đ — nhạy cảm
            "behavior_tracking", # Điều 4.1.l — nhạy cảm
            "phone_number",      # Điều 3 khoản 7 — cơ bản
        ]

    logger.info(
        f"[PDPA] Nhận consent từ tenant={body.tenant_id} "
        f"| version={body.consent_version} | anonymous={body.anonymous} "
        f"| ip={ip_address[:20]}"
    )

    try:
        record_id = save_consent_record(
            tenant_id=body.tenant_id,
            consent_version=body.consent_version,
            consent_given_at=consent_given_at,
            phone_hash=body.phone_hash,
            user_agent=user_agent,
            ip_address=ip_address,
            data_categories=data_categories,
        )
        return ConsentRecordResponse(
            success=True,
            record_id=record_id,
            message="Bằng chứng đồng ý đã được lưu thành công.",
        )

    except Exception as e:
        # KHÔNG block UX — log lỗi nhưng vẫn báo thành công cho client
        # vì consent đã được lưu ở localStorage (frontend fallback).
        # Lý do: tránh trường hợp Firestore tạm lỗi khiến user không thể gửi phản hồi.
        logger.error(
            f"[PDPA] Lỗi lưu consent record: {type(e).__name__}: {e} "
            f"| tenant={body.tenant_id} | version={body.consent_version}"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Không thể lưu bằng chứng đồng ý lúc này (Firestore tạm lỗi). "
                "Vui lòng thử lại sau."
            ),
        )
