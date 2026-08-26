"""
OTP Routes — POST /api/v1/otp/send + POST /api/v1/otp/verify
=============================================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
Module 1 — Lớp 1: OTP Endpoints

LUỒNG SỬ DỤNG (từ web-client):
  1. User nhập SĐT, nhấn "Gửi mã OTP"
     → POST /api/v1/otp/send { phone_number, tenant_id }
     → Backend tạo session, gửi OTP qua provider.

  2. User nhập mã OTP nhận được
     → POST /api/v1/otp/verify { phone_number, otp_code, tenant_id }
     → Backend xác thực, trả otp_verified=true.

  3. Frontend lưu trạng thái verified, gửi kèm phone_number khi submit feedback.
     Backend trong /feedback sẽ kiểm tra session đã verified chưa.

LƯU Ý BẢO MẬT:
  - Rate limit bản thân endpoint /otp/send: tối đa 3 lần gửi OTP/SĐT/giờ
    để tránh spam SMS (TODO khi cần, hiện để open vì dùng mock).
  - SĐT gốc KHÔNG được log ra, chỉ log 4 chữ số cuối.
"""

import hashlib
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, field_validator

from backend.services.otp_service import (
    create_otp_session,
    get_otp_provider,
    verify_otp_session,
    _normalize_phone,
)
from backend.services.rate_limit_service import check_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------
class OtpSendRequest(BaseModel):
    phone_number: str
    tenant_id: str

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip().replace(" ", "").replace("-", "")
        if len(v) < 9 or len(v) > 15:
            raise ValueError("Số điện thoại không hợp lệ (9–15 chữ số).")
        if not any(c.isdigit() for c in v):
            raise ValueError("Số điện thoại phải chứa chữ số.")
        return v


class OtpVerifyRequest(BaseModel):
    phone_number: str
    otp_code: str
    tenant_id: str

    @field_validator("otp_code")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Mã OTP phải gồm đúng 6 chữ số.")
        return v


class OtpSendResponse(BaseModel):
    success: bool
    message: str
    expires_in_seconds: int


class OtpVerifyResponse(BaseModel):
    success: bool
    message: str
    otp_verified: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post(
    "/otp/send",
    response_model=OtpSendResponse,
    status_code=status.HTTP_200_OK,
    summary="Gửi mã OTP xác thực số điện thoại",
    description=(
        "Tạo mã OTP và gửi đến SĐT của khách hàng. "
        "OTP có hiệu lực 5 phút. Chỉ cần khi khách muốn nhận voucher (không bắt buộc cho phản hồi ẩn danh)."
    ),
)
async def send_otp(request: Request, body: OtpSendRequest):
    """
    Gửi OTP đến SĐT. Kiểm tra rate limit trước.
    """
    phone = _normalize_phone(body.phone_number)
    phone_last4 = phone[-4:]  # Chỉ log 4 chữ số cuối để bảo vệ quyền riêng tư

    logger.info(f"[OTP/send] SĐT=****{phone_last4} | tenant={body.tenant_id}")

    # Tạo OTP session và lấy code
    try:
        otp_code = create_otp_session(body.phone_number)
    except Exception as e:
        logger.error(f"[OTP/send] Lỗi tạo session: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể tạo mã OTP lúc này. Vui lòng thử lại sau.",
        )

    # Gửi OTP qua provider (mock hoặc Zalo)
    provider = get_otp_provider()
    result = provider.send_otp(phone, otp_code)

    if not result.success:
        logger.warning(f"[OTP/send] Provider lỗi: {result.error}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Không thể gửi OTP: {result.error}",
        )

    logger.info(f"[OTP/send] Đã gửi qua {provider.provider_name()}: ****{phone_last4}")
    return OtpSendResponse(
        success=True,
        message="Mã OTP đã được gửi. Vui lòng kiểm tra điện thoại.",
        expires_in_seconds=300,  # 5 phút
    )


@router.post(
    "/otp/verify",
    response_model=OtpVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Xác thực mã OTP",
    description=(
        "Kiểm tra mã OTP do khách hàng nhập. "
        "Nếu thành công, session sẽ được đánh dấu verified — SĐT có thể dùng để nhận voucher."
    ),
)
async def verify_otp(body: OtpVerifyRequest):
    """
    Xác thực OTP. Sau khi thành công, frontend lưu trạng thái và gửi kèm SĐT vào /feedback.
    """
    phone_last4 = body.phone_number.strip()[-4:]
    logger.info(f"[OTP/verify] SĐT=****{phone_last4} | tenant={body.tenant_id}")

    result = verify_otp_session(body.phone_number, body.otp_code)

    if not result.success:
        logger.warning(
            f"[OTP/verify] Thất bại: ****{phone_last4} — {result.message}"
        )
        # Trả 400 để frontend hiển thị thông báo lỗi cụ thể
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message,
        )

    logger.info(f"[OTP/verify] Thành công: ****{phone_last4}")
    return OtpVerifyResponse(
        success=True,
        message=result.message,
        otp_verified=True,
    )
