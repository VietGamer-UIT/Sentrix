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
    _normalize_phone,
    _is_email,
    EmailOtpProvider,
)
from backend.services.rate_limit_service import check_rate_limit

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

    # An danh hoa cho log
    if is_email_contact:
        parts = contact.split("@")
        contact_masked = f"{parts[0][:2]}***@{parts[1]}"
    else:
        contact_masked = f"****{contact[-4:]}"

    logger.info(f"[OTP/send] contact={contact_masked} | type={contact_type} | tenant={body.tenant_id}")

    # Tao OTP session va lay code
    try:
        otp_code = create_otp_session(contact)
    except Exception as e:
        logger.error(f"[OTP/send] Loi tao session: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Khong the tao ma OTP luc nay. Vui long thu lai sau.",
        )

    # Chon provider: email -> EmailOtpProvider, phone -> provider mac dinh (Mock/Zalo)
    if is_email_contact:
        provider = EmailOtpProvider()
    else:
        provider = get_otp_provider()

    result = provider.send_otp(contact, otp_code)

    if not result.success:
        logger.warning(f"[OTP/send] Provider loi: {result.error}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Khong the gui OTP: {result.error}",
        )

    logger.info(f"[OTP/send] Da gui qua {provider.provider_name()}: {contact_masked}")
    return OtpSendResponse(
        success=True,
        message=result.message,
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
        parts = contact.split("@")
        contact_masked = f"{parts[0][:2]}***@{parts[1]}"
    else:
        contact_masked = f"****{contact[-4:]}"

    logger.info(f"[OTP/verify] contact={contact_masked} | tenant={body.tenant_id}")

    result = verify_otp_session(contact, body.otp_code)

    if not result.success:
        logger.warning(
            f"[OTP/verify] That bai: {contact_masked} - {result.message}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message,
        )

    logger.info(f"[OTP/verify] Thanh cong: {contact_masked}")
    return OtpVerifyResponse(
        success=True,
        message="Xac thuc thanh cong! Ban co the nhan voucher.",
        otp_verified=True,
    )
