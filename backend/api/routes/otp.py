"""
OTP Routes — POST /api/v1/otp/send + POST /api/v1/otp/verify
=============================================================
Author: Nguyen Thanh Tuyen (AI & Data Architect)
Module 1 — Lop 1: OTP Endpoints

LUONG SU DUNG (tu web-client):
  1. User nhap SDT hoac Email, nhan "Gui ma OTP"
     -> POST /api/v1/otp/send { contact, tenant_id }
     -> Backend tao session, gui OTP qua provider phu hop
       (Email -> Gmail SMTP mien phi | SDT -> Zalo/Mock).

  2. User nhap ma OTP nhan duoc
     -> POST /api/v1/otp/verify { contact, otp_code, tenant_id }
     -> Backend xac thuc, tra otp_verified=true.

  3. Frontend luu trang thai verified, gui kem contact khi submit feedback.
     Backend trong /feedback se kiem tra session da verified chua.

LUU Y BAO MAT:
  - Contact goc KHONG duoc log ra, chi log phan an danh.
"""

import logging
import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, field_validator

from backend.services.otp_service import (
    create_otp_session,
    get_otp_provider,
    verify_otp_session,
    check_otp_cooldown,
    check_otp_hourly_rate_limit,
    delete_otp_session_on_send_failure,
    _normalize_phone,
    _is_email,
    EmailOtpProvider,
    OtpCooldownError,
    OtpHourlyLimitError,
)
from backend.services.rate_limit_service import check_rate_limit
from backend.services.email_validation_service import (
    is_disposable_email,
    FRIENDLY_DISPOSABLE_ERROR_MESSAGE,
    normalize_email,
    mask_email,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------
class OtpSendRequest(BaseModel):
    contact: str          # SDT hoac email
    tenant_id: str
    # Backward compat: neu FE cu gui phone_number thi van nhan duoc
    phone_number: Optional[str] = None

    @field_validator("contact")
    @classmethod
    def validate_contact(cls, v: str) -> str:
        v = v.strip()
        # Kiem tra email
        if re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', v):
            return v.lower()
        # Kiem tra SDT VN
        phone = v.replace(" ", "").replace("-", "")
        if len(phone) < 9 or len(phone) > 15:
            raise ValueError("SDT hoac email khong hop le.")
        if not any(c.isdigit() for c in phone):
            raise ValueError("SDT phai chua chu so.")
        return v


class OtpVerifyRequest(BaseModel):
    contact: str          # SDT hoac email (phai khop voi luc send)
    otp_code: str
    tenant_id: str
    # Backward compat
    phone_number: Optional[str] = None

    @field_validator("otp_code")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Ma OTP phai gom dung 6 chu so.")
        return v


class OtpSendResponse(BaseModel):
    success: bool
    message: str
    expires_in_seconds: int
    contact_type: str     # "email" hoac "phone"


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
    summary="Gui ma OTP xac thuc SDT hoac Email",
    description=(
        "Tao ma OTP va gui den SDT (qua Zalo/SMS) hoac Email (qua Gmail SMTP). "
        "OTP co hieu luc 5 phut. Chi can khi khach muon nhan voucher."
    ),
)
async def send_otp(request: Request, body: OtpSendRequest):
    """
    Gui OTP den SDT hoac Email. Kiem tra rate limit truoc.
    """
    # Backward compat: neu FE gui phone_number thay vi contact
    contact = (body.contact or body.phone_number or "").strip()

    is_email_contact = _is_email(contact)
    contact_type = "email" if is_email_contact else "phone"

    # Chống disposable email (Lớp chống spam)
    if is_email_contact:
        contact = normalize_email(contact)
        if is_disposable_email(contact):
            logger.warning(f"[OTP/send] Tu choi email disposable: {mask_email(contact)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=FRIENDLY_DISPOSABLE_ERROR_MESSAGE,
            )

    # Ẩn danh hóa cho log (dùng trước khi log rate limit)
    if is_email_contact:
        contact_masked = mask_email(contact)
    else:
        contact_masked = f"****{contact[-4:]}" if len(contact) >= 4 else "***"

    # Cooldown giữa các lần gửi (tối thiểu 60s)
    try:
        cooldown_allowed, remaining_sec = check_otp_cooldown(contact)
    except RuntimeError as e:
        logger.error(f"[OTP/send] Loi kiem tra cooldown: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dịch vụ gửi mã OTP tạm thời không khả dụng. Vui lòng thử lại sau.",
        )

    if not cooldown_allowed:
        logger.info(f"[OTP/send] Rate limit cooldown: con {remaining_sec}s | {contact_masked}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Vui lòng đợi {remaining_sec} giây trước khi yêu cầu mã OTP mới.",
        )

    # Giới hạn 5 lần gửi OTP/giờ/contact (P1 rate limit — bền vững qua restart)
    try:
        hourly_allowed, sends_this_hour = check_otp_hourly_rate_limit(contact)
    except RuntimeError as e:
        logger.error(f"[OTP/send] Loi kiem tra hourly rate limit: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dịch vụ gửi mã OTP tạm thời không khả dụng. Vui lòng thử lại sau.",
        )

    if not hourly_allowed:
        logger.warning(f"[OTP/send] Hourly rate limit: {contact_masked} đã gửi {sends_this_hour} lần trong giờ này")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Đã vượt giới hạn gửi OTP. Vui lòng thử lại sau 1 giờ.",
        )

    logger.info(f"[OTP/send] contact={contact_masked} | type={contact_type} | tenant={body.tenant_id}")

    # Tao OTP session va lay code
    try:
        otp_code = create_otp_session(contact)
    except OtpCooldownError as cd_err:
        logger.info(f"[OTP/send] Rate limit cooldown (transaction): con {cd_err.remaining_seconds}s | {contact_masked}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Vui lòng đợi {cd_err.remaining_seconds} giây trước khi yêu cầu mã OTP mới.",
        )
    except (OtpHourlyLimitError, ValueError):
        logger.warning(f"[OTP/send] Hourly rate limit reached: {contact_masked}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Đã vượt giới hạn gửi OTP. Vui lòng thử lại sau 1 giờ.",
        )
    except Exception as e:
        logger.error(f"[OTP/send] Loi tao session: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Khong the tao ma OTP luc nay. Vui long thu lai sau.",
        )

    # Chon provider: email -> EmailOtpProvider, phone -> provider mac dinh (Mock/Zalo)
    provider = get_otp_provider(contact)

    try:
        result = provider.send_otp(contact, otp_code)
    except Exception as _send_exc:
        # P1: Exception/Timeout khi gọi provider -> xử lý an toàn, không trả thành công giả
        try:
            delete_otp_session_on_send_failure(contact)
        except Exception as _rb_err:
            logger.error(f"[OTP/send] Rollback session thất bại sau exception: {type(_rb_err).__name__}")
        logger.error(f"[OTP/send] Provider ném exception khi gửi OTP: {type(_send_exc).__name__}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể gửi mã OTP lúc này. Vui lòng thử lại sau.",
        )

    if not result.success:
        # P1 FIX: Provider thất bại → rollback session để không block lần gửi lại.
        # send_count vẫn được giữ để hourly rate limit vẫn enforce.
        try:
            delete_otp_session_on_send_failure(contact)
        except Exception as _rb_err:
            logger.error(f"[OTP/send] Rollback session thất bại: {type(_rb_err).__name__}")
        logger.warning("[OTP/send] Provider gửi OTP thất bại")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể gửi mã OTP lúc này. Vui lòng thử lại sau.",
        )

    logger.info(f"[OTP/send] Da gui qua {provider.provider_name()}: {contact_masked}")
    return OtpSendResponse(
        success=True,
        message=str(result.message or "Mã OTP đã được gửi thành công."),
        expires_in_seconds=300,  # 5 phut
        contact_type=contact_type,
    )


@router.post(
    "/otp/verify",
    response_model=OtpVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Xac thuc ma OTP (SDT hoac Email)",
    description=(
        "Kiem tra ma OTP do khach hang nhap. "
        "Neu thanh cong, session se duoc danh dau verified."
    ),
)
async def verify_otp(body: OtpVerifyRequest):
    """
    Xac thuc OTP. Sau khi thanh cong, frontend luu trang thai va gui kem contact vao /feedback.
    """
    # Backward compat
    contact = (body.contact or body.phone_number or "").strip()

    is_email_contact = _is_email(contact)
    if is_email_contact:
        contact_masked = mask_email(contact)
    else:
        contact_masked = f"****{contact[-4:]}" if len(contact) >= 4 else "***"

    logger.info(f"[OTP/verify] contact={contact_masked} | tenant={body.tenant_id}")

    result = verify_otp_session(contact, body.otp_code)

    if not result.success:
        logger.warning(
            f"[OTP/verify] That bai: {contact_masked} - {result.message}"
        )
        status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if "tạm thời không khả dụng" in (result.message or "")
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=status_code,
            detail=result.message,
        )

    logger.info(f"[OTP/verify] Thanh cong: {contact_masked}")
    return OtpVerifyResponse(
        success=True,
        message="Xac thuc thanh cong! Ban co the nhan voucher.",
        otp_verified=True,
    )
