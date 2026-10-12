"""
OTP Service — Xác thực số điện thoại hoặc email qua mã OTP
==================================================
Author: Đoàn Hoàng Việt
Module 1 — Lớp 1: Rate Limiting + Xác thực OTP

MỤC ĐÍCH:
  Cung cấp interface `OtpProvider` và các implementation cụ thể để gửi/xác thực OTP.
  Thiết kế theo mô hình Strategy Pattern — dễ hoán đổi provider mà không sửa business logic.

PROVIDERS:
  - MockOtpProvider:     Giả lập để demo (không gửi SMS/Zalo thật).
                         Code tĩnh = OTP_MOCK_CODE (default "123456").
                         Log code ra stdout để giám khảo dễ xem trong demo.
  - EmailOtpProvider:    Gửi OTP qua Gmail SMTP (miễn phí). Cấu hình:
                         SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD (Gmail App Password).
  - ZaloZnsOtpProvider:  Stub — TODO: cắm API Zalo OTP thật khi có template_id + credentials.
                         Xem: https://developers.zalo.me/docs/zns/gui-tin-zns

CHỌN PROVIDER:
  Đọc biến môi trường OTP_PROVIDER:
    - "mock"  (default) → MockOtpProvider
    - "email"           → EmailOtpProvider (Gmail SMTP)
    - "zalo"            → ZaloZnsOtpProvider

LƯU TRỮ SESSION OTP:
  OTP được lưu vào Firestore collection `otp_sessions/{contact_hash}` với:
    - otp_code_hash: SHA-256 của code (không lưu plaintext)
    - expires_at:    thời điểm hết hạn (5 phút)
    - verified:      True sau khi xác thực thành công
    - attempts:      số lần nhập sai (giới hạn 3 lần)
  Fallback in-memory nếu Firestore chưa setup (dev/test).
"""

import hashlib
import logging
import os
import secrets
import re
import smtplib
import string
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from backend.services.email_validation_service import mask_email

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hằng số cấu hình
# ---------------------------------------------------------------------------
OTP_CODE_LENGTH = 6
OTP_EXPIRE_MINUTES = 5        # OTP hết hạn sau 5 phút
OTP_MAX_ATTEMPTS = 3          # Tối đa 3 lần nhập sai trước khi hủy session
OTP_RESEND_COOLDOWN_SECONDS = 60   # Khoảng cách tối thiểu giữa 2 lần gửi OTP (60s)
OTP_VERIFIED_SESSION_TTL_MINUTES = 30  # Session đã verified hết hạn sau 30 phút
OTP_HOURLY_SEND_LIMIT = 5     # Tối đa 5 lần gửi OTP/giờ/contact


def is_dev_env() -> bool:
    """Kiểm tra môi trường có thuộc development/dev/test không."""
    env = os.getenv("ENVIRONMENT", "").strip().lower()
    return env in {"development", "dev", "test"}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
class OtpSendResult:
    """Kết quả gửi OTP."""
    def __init__(self, success: bool, message: str, error: Optional[str] = None):
        self.success = success
        self.message = message
        self.error = error


class OtpVerifyResult:
    """Kết quả xác thực OTP."""
    def __init__(self, success: bool, message: str, attempts_remaining: int = 0):
        self.success = success
        self.message = message
        self.attempts_remaining = attempts_remaining


# ---------------------------------------------------------------------------
# Rate limit & Cooldown Exceptions
# ---------------------------------------------------------------------------
class OtpRateLimitError(ValueError):
    """Base exception cho rate limit OTP."""
    pass


class OtpCooldownError(OtpRateLimitError):
    """Bị chặn do cooldown giữa hai lần gửi OTP (tối thiểu 60s)."""
    def __init__(self, remaining_seconds: int):
        self.remaining_seconds = max(1, remaining_seconds)
        super().__init__(f"Vui lòng đợi {self.remaining_seconds} giây trước khi yêu cầu mã OTP mới.")


class OtpHourlyLimitError(OtpRateLimitError):
    """Bị chặn do chạm giới hạn gửi OTP trong một giờ."""
    def __init__(self, limit: int = OTP_HOURLY_SEND_LIMIT):
        self.limit = limit
        super().__init__(f"Đã vượt giới hạn {limit} lần gửi OTP trong giờ này.")


# ---------------------------------------------------------------------------
# Abstract Interface
# ---------------------------------------------------------------------------
class OtpProvider(ABC):
    """Interface cơ sở cho các OTP provider. Mọi provider phải implement 2 method này."""

    @abstractmethod
    def send_otp(self, contact: str, otp_code: str) -> OtpSendResult:
        """
        Gửi OTP đến số điện thoại hoặc địa chỉ email.

        Args:
            contact:  SĐT chuẩn hoá ("+84901234567") hoặc email ("user@gmail.com")
            otp_code: Mã OTP 6 chữ số đã được tạo ngẫu nhiên.

        Returns:
            OtpSendResult với success=True nếu gửi thành công.
        """
        ...

    @abstractmethod
    def provider_name(self) -> str:
        """Tên provider để log."""
        ...


# ---------------------------------------------------------------------------
# Mock Provider — Dùng cho demo và unit test
# ---------------------------------------------------------------------------
class MockOtpProvider(OtpProvider):
    """
    OTP provider giả lập — KHÔNG gửi SMS/Zalo thật.

    Hoạt động:
      - Chấp nhận bất kỳ số điện thoại hoặc email nào.
      - Log mã OTP ra console (để giám khảo xem trong demo live).
      - Để bật "always accept" trong demo: đặt OTP_MOCK_ACCEPT_ALL=true
        thì verify sẽ chấp nhận bất kỳ code nào (tiện cho demo nhanh).

    TODO (production): Thay bằng ZaloZnsOtpProvider hoặc EmailOtpProvider.
    """

    def send_otp(self, contact: str, otp_code: str) -> OtpSendResult:
        is_dev = is_dev_env()
        if is_dev:
            logger.info(
                f"[MockOTP] ═══════════════════════════════════════\n"
                f"[MockOTP] Liên hệ: {mask_email(contact) if _is_email(contact) else '***'}\n"
                f"[MockOTP] Mã OTP: {otp_code}  ← (giả lập, không gửi thật)\n"
                f"[MockOTP] Hết hạn: {OTP_EXPIRE_MINUTES} phút\n"
                f"[MockOTP] ═══════════════════════════════════════"
            )
        return OtpSendResult(
            success=True,
            message=f"[DEMO] OTP đã được gửi (giả lập). Mã: {otp_code}" if is_dev else "Mã OTP đã được gửi.",
        )

    def provider_name(self) -> str:
        return "MockOtpProvider"


# ---------------------------------------------------------------------------
# Email OTP Provider — Gửi OTP qua Gmail SMTP hoặc HTTP API (tránh block port 25/465/587)
# ---------------------------------------------------------------------------
class EmailOtpProvider(OtpProvider):
    """
    OTP provider qua Gmail SMTP hoặc HTTP API.

    CẤU HÌNH (trong .env):
      EMAIL_TRANSPORT = "smtp" (mặc định) hoặc "http_api"

      # Cho SMTP:
      SMTP_HOST     = smtp.gmail.com
      SMTP_PORT     = 587
      SMTP_USER     = your-gmail@gmail.com
      SMTP_PASSWORD = xxxx xxxx xxxx xxxx
      SMTP_FROM_NAME = Sentrix OTP

      # Cho HTTP API (Render free tier safe):
      EMAIL_API_URL = https://api.resend.com/emails (hoặc provider khác)
      EMAIL_API_KEY = ...
      EMAIL_FROM    = onboarding@resend.dev
    """

    def __init__(self):
        self.transport = os.getenv("EMAIL_TRANSPORT", "smtp").lower()
        
        # Cấu hình SMTP
        self.host      = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.port      = int(os.getenv("SMTP_PORT", "587"))
        self.user      = os.getenv("SMTP_USER", "")
        self.password  = os.getenv("SMTP_PASSWORD", "")
        
        # Cấu hình HTTP API
        self.api_url   = os.getenv("EMAIL_API_URL", "")
        self.api_key   = os.getenv("EMAIL_API_KEY", "")
        self.api_from  = os.getenv("EMAIL_FROM", "")
        
        self.from_name = os.getenv("SMTP_FROM_NAME", "Sentrix")
        
        logger.info(f"[EmailOTP] INITIALIZED. Transport={self.transport}, HAS_API_KEY={bool(self.api_key)}")

    def send_otp(self, contact: str, otp_code: str) -> OtpSendResult:
        logger.info(f"[EmailOTP] send_otp called. Effective transport={self.transport}")
        if self.transport == "smtp" and (not self.user or not self.password):
            logger.error("[EmailOTP] SMTP_USER hoặc SMTP_PASSWORD chưa được cấu hình.")
            return OtpSendResult(
                success=False,
                error="Email OTP chưa được cấu hình. Kiểm tra SMTP_USER và SMTP_PASSWORD trong .env.",
                message="Không thể gửi OTP qua email.",
            )
            
        if self.transport == "http_api" and (not self.api_url or not self.api_key or not self.api_from):
            logger.error("[EmailOTP] HTTP API chưa được cấu hình đủ EMAIL_API_URL, EMAIL_API_KEY, EMAIL_FROM.")
            return OtpSendResult(
                success=False,
                error="Email OTP chưa được cấu hình cho HTTP API.",
                message="Không thể gửi OTP qua email.",
            )

        subject = f"Mã xác thực Sentrix: {otp_code}"
        html_body = f"""\
<html><body style="font-family: Arial, sans-serif; max-width: 480px; margin: auto; padding: 24px;">
  <div style="text-align:center; margin-bottom:20px;">
    <span style="font-size:32px;">&#128274;</span>
  </div>
  <h2 style="color:#0688A6; text-align:center;">Mã xác thực Sentrix</h2>
  <p style="color:#404040; text-align:center;">
    Nhập mã dưới đây để xác nhận và nhận voucher ưu đãi:
  </p>
  <div style="background:#F5F6FA; border-radius:12px; padding:24px; text-align:center; margin:20px 0;">
    <span style="font-size:40px; font-weight:800; letter-spacing:12px; color:#0688A6;">{otp_code}</span>
  </div>
  <p style="color:#808080; font-size:13px; text-align:center;">
    Mã có hiệu lực trong <strong>5 phút</strong>.<br/>
    Nếu bạn không yêu cầu mã này, vui lòng bỏ qua email này.
  </p>
  <hr style="border:none;border-top:1px solid #E0E0E0;margin:20px 0;"/>
  <p style="color:#BCBCBC; font-size:11px; text-align:center;">
    Powered by <strong>Sentrix</strong> · AI Customer Experience
  </p>
</body></html>"""

        if self.transport == "http_api":
            try:
                import httpx
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "from": f"{self.from_name} <{self.api_from}>",
                    "to": [contact],
                    "subject": subject,
                    "html": html_body
                }
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(self.api_url, headers=headers, json=payload)
                    if resp.status_code >= 400:
                        is_dev = os.getenv("ENVIRONMENT", "production") != "production"
                        if is_dev:
                            logger.error(f"[EmailOTP] HTTP API trả về lỗi: {resp.status_code} - {resp.text}")
                        else:
                            logger.error(f"[EmailOTP] HTTP API trả về lỗi: {resp.status_code}")
                        
                        return OtpSendResult(
                            success=False,
                            error=f"Email API error: {resp.status_code}",
                            message="Gửi email thất bại. Vui lòng thử lại sau.",
                        )
                logger.info(f"[EmailOTP] Đã gửi OTP qua HTTP API tới: {mask_email(contact)}")
                return OtpSendResult(
                    success=True,
                    message=f"Mã OTP đã được gửi tới {mask_email(contact)}. Kiểm tra hộp thư (và spam).",
                )
            except Exception as e:
                logger.error(f"[EmailOTP] Lỗi gửi email HTTP API: {type(e).__name__}")
                return OtpSendResult(
                    success=False,
                    error=str(e),
                    message="Gửi email thất bại. Vui lòng thử lại sau.",
                )
        else:
            # SMTP Transport
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"]    = f"{self.from_name} <{self.user}>"
            msg["To"]      = contact
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            try:
                with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                    server.ehlo()
                    server.starttls()
                    server.login(self.user, self.password)
                    server.sendmail(self.user, [contact], msg.as_string())
                logger.info(f"[EmailOTP] Đã gửi OTP qua SMTP tới: {mask_email(contact)}")
                return OtpSendResult(
                    success=True,
                    message=f"Mã OTP đã được gửi tới {mask_email(contact)}. Kiểm tra hộp thư (và spam).",
                )
            except smtplib.SMTPAuthenticationError:
                logger.error("[EmailOTP] Xác thực SMTP thất bại. Kiểm tra SMTP_USER/PASSWORD.")
                return OtpSendResult(
                    success=False,
                    error="Xác thực email thất bại. Kiểm tra cấu hình SMTP.",
                    message="Không thể gửi OTP qua email.",
                )
            except Exception as e:
                logger.error(f"[EmailOTP] Lỗi gửi email SMTP: {type(e).__name__}")
                return OtpSendResult(
                    success=False,
                    error=str(e),
                    message="Gửi email thất bại. Vui lòng thử lại sau.",
                )

    def provider_name(self) -> str:
        return "EmailOtpProvider"


# ---------------------------------------------------------------------------
# Zalo ZNS OTP Provider — TODO: cắm API thật
# ---------------------------------------------------------------------------
class ZaloZnsOtpProvider(OtpProvider):
    """
    OTP provider qua Zalo ZNS OTP template.

    TODO: Implement khi có:
      1. ZALO_APP_ID — App ID từ Zalo Developer Console
      2. ZALO_ACCESS_TOKEN — Token OAuth2 của OA (Official Account)
      3. ZALO_OTP_TEMPLATE_ID — ID template OTP đã được Zalo duyệt

    Tham khảo: https://developers.zalo.me/docs/zns/gui-tin-zns
    Lưu ý: Zalo ZNS OTP yêu cầu số điện thoại đã follow OA — cần hướng dẫn user follow OA trước.
    """

    def __init__(self):
        self.app_id = os.getenv("ZALO_APP_ID", "")
        self.access_token = os.getenv("ZALO_ACCESS_TOKEN", "")
        self.template_id = os.getenv("ZALO_OTP_TEMPLATE_ID", "")

    def send_otp(self, phone_number: str, otp_code: str) -> OtpSendResult:
        # TODO: Gọi Zalo ZNS API để gửi template OTP
        # Endpoint: POST https://business.openapi.zalo.me/message/template
        # Body: { "phone": phone_number, "template_id": self.template_id,
        #         "template_data": { "otp": otp_code, "expire_time": "5 phút" } }
        logger.warning(
            "[ZaloOTP] ZaloZnsOtpProvider chưa được implement. "
            "Cần cấu hình ZALO_APP_ID + ZALO_ACCESS_TOKEN + ZALO_OTP_TEMPLATE_ID. "
            "Hiện đang dùng MockOtpProvider làm fallback."
        )
        return OtpSendResult(
            success=False,
            error="ZaloZnsOtpProvider chưa được cấu hình. Xem TODO trong otp_service.py.",
            message="OTP provider chưa sẵn sàng.",
        )

    def provider_name(self) -> str:
        return "ZaloZnsOtpProvider"


class DisabledPhoneOtpProvider(OtpProvider):
    """
    Provider mặc định trên production khi SĐT được gửi lên nhưng Zalo/SMS chưa tích hợp.
    Luôn trả về lỗi, chặn số điện thoại đi vào Email API.
    """
    def send_otp(self, contact: str, otp_code: str) -> OtpSendResult:
        logger.warning("[OTP] Từ chối gửi OTP qua SĐT vì chưa cấu hình SMS/Zalo.")
        return OtpSendResult(
            success=False,
            error="Xác thực OTP qua số điện thoại hiện chưa khả dụng. Vui lòng sử dụng địa chỉ email để nhận mã.",
            message="Không thể gửi OTP."
        )

    def provider_name(self) -> str:
        return "DisabledPhoneOtpProvider"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
def get_otp_provider(contact: str = "") -> OtpProvider:
    """
    Trả về OTP provider phù hợp dựa trên contact và biến môi trường.
    Nếu là email -> EmailOtpProvider.
    Nếu là SĐT -> Kiểm tra môi trường và cấu hình (chặn mock trên production).
    """
    if contact and _is_email(contact):
        return EmailOtpProvider()
        
    provider_name = os.getenv("OTP_PROVIDER", "mock").lower().strip()
    if provider_name == "zalo":
        return ZaloZnsOtpProvider()

    # Số điện thoại, nhưng không phải Zalo.
    # Chỉ cho phép Mock trên môi trường dev/test.
    env = os.getenv("ENVIRONMENT", "").strip().lower()
    is_dev = env in {"development", "dev", "test"}

    if is_dev and provider_name == "mock":
        return MockOtpProvider()
        
    return DisabledPhoneOtpProvider()


# ---------------------------------------------------------------------------
# Contact Helpers (SĐT hoặc Email)
# ---------------------------------------------------------------------------

def _is_email(contact: str) -> bool:
    """Kiểm tra contact có phải email không."""
    return bool(re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', contact.strip()))


def _normalize_contact(contact: str) -> str:
    """
    Chuẩn hoá contact để hash nhất quán.
    - Email: strip + lowercase
    - SĐT: chuyển về +84...
    """
    contact = contact.strip()
    if _is_email(contact):
        return contact.lower()
    # SĐT: normalize về +84
    phone = contact.replace(" ", "").replace("-", "")
    if phone.startswith("0"):
        phone = "+84" + phone[1:]
    elif not phone.startswith("+"):
        phone = "+84" + phone
    return phone


def _normalize_phone(phone: str) -> str:
    """Chuẩn hoá SĐT về dạng +84... để hash nhất quán. (Backward compat)"""
    return _normalize_contact(phone)


def _hash_contact_for_otp(contact: str) -> str:
    """
    Tạo document ID cho otp_sessions từ contact (SĐT hoặc email).
    Dùng SHA-256 để bảo vệ thông tin cá nhân — không lưu contact gốc vào Firestore.
    """
    normalized = _normalize_contact(contact)
    return "otp_" + hashlib.sha256(normalized.encode()).hexdigest()[:20]


def _hash_phone_for_otp(phone: str) -> str:
    """Backward compat alias cho _hash_contact_for_otp."""
    return _hash_contact_for_otp(phone)


def _generate_otp_code() -> str:
    """Tạo mã OTP ngẫu nhiên 6 chữ số (sử dụng secrets cho bảo mật)."""
    return "".join(secrets.choice(string.digits) for _ in range(OTP_CODE_LENGTH))


def _hash_otp_code(code: str) -> str:
    """Hash OTP code trước khi lưu vào Firestore (không lưu plaintext)."""
    return hashlib.sha256(code.encode()).hexdigest()


# ---------------------------------------------------------------------------
# OTP Session Management (Firestore-backed với in-memory fallback)
# ---------------------------------------------------------------------------

# In-memory fallback (dùng khi Firestore chưa setup)
_memory_sessions: dict = {}


def check_otp_cooldown(contact: str) -> tuple[bool, int]:
    """
    Kiểm tra xem contact này có đang trong thời gian chờ (cooldown 60s) giữa 2 lần gửi OTP không.
    Returns:
        (allowed, remaining_seconds)
    Raises:
        RuntimeError: nếu ở production và Firestore không thể truy xuất.
    """
    session_key = _hash_contact_for_otp(contact)
    now = datetime.now(timezone.utc)
    is_dev = is_dev_env()

    session_data = None
    try:
        from backend.db.firestore_client import get_firestore_client
        db = get_firestore_client()
        snap = db.collection("otp_sessions").document(session_key).get()
        if snap.exists:
            session_data = snap.to_dict()
    except Exception as e:
        if not is_dev:
            logger.error(f"[OTP] Production không thể kiểm tra cooldown do lỗi Firestore: {type(e).__name__}")
            raise RuntimeError(f"Lỗi cơ sở dữ liệu khi kiểm tra cooldown OTP: {type(e).__name__}") from e
        session_data = _memory_sessions.get(session_key)

    if not session_data and is_dev:
        session_data = _memory_sessions.get(session_key)

    if session_data:
        created_at = session_data.get("created_at")
        if created_at:
            if hasattr(created_at, "timestamp"):
                created_at = datetime.fromtimestamp(created_at.timestamp(), tz=timezone.utc)
            elif isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)

            elapsed = (now - created_at).total_seconds()
            if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
                remaining = int(OTP_RESEND_COOLDOWN_SECONDS - elapsed)
                return False, max(1, remaining)

    return True, 0


def check_otp_hourly_rate_limit(contact: str) -> tuple[bool, int]:
    """
    Kiểm tra giới hạn 5 lần gửi OTP/giờ/contact (bền vững qua restart).

    Ghi send_count và send_hour vào otp_sessions document.
    Nếu send_count >= OTP_HOURLY_SEND_LIMIT trong cùng giờ UTC → từ chối.

    Returns:
        (allowed, sends_this_hour)
    Raises:
        RuntimeError: nếu ở production và Firestore không thể truy xuất.
    """
    session_key = _hash_contact_for_otp(contact)
    now = datetime.now(timezone.utc)
    current_hour = now.strftime("%Y-%m-%dT%H")
    is_dev = is_dev_env()

    session_data = None
    try:
        from backend.db.firestore_client import get_firestore_client
        db = get_firestore_client()
        snap = db.collection("otp_sessions").document(session_key).get()
        if snap.exists:
            session_data = snap.to_dict()
    except Exception as e:
        if not is_dev:
            logger.error(f"[OTP] Production không thể kiểm tra hourly rate limit do lỗi Firestore: {type(e).__name__}")
            raise RuntimeError(f"Lỗi cơ sở dữ liệu khi kiểm tra giới hạn gửi OTP: {type(e).__name__}") from e
        session_data = _memory_sessions.get(session_key)

    if not session_data and is_dev:
        session_data = _memory_sessions.get(session_key)

    if session_data:
        stored_hour = session_data.get("send_hour", "")
        send_count = session_data.get("send_count", 0)
        if stored_hour == current_hour and send_count >= OTP_HOURLY_SEND_LIMIT:
            return False, send_count

    return True, 0


def delete_otp_session_on_send_failure(contact: str) -> None:
    """
    Xóa/rollback OTP session khi provider gửi thất bại hoặc gặp exception.
    Đảm bảo provider failure không tạo trạng thái giả là đã gửi thành công —
    client có thể thử lại mà không bị chặn bởi cooldown của session lỗi.

    Bảo toàn send_count và send_hour để hourly rate limit vẫn enforce (chống lạm dụng).
    Chỉ xóa created_at và otp_code_hash để reset cooldown và vô hiệu hoá mã OTP.
    """
    session_key = _hash_contact_for_otp(contact)
    is_dev = is_dev_env()
    reset_data = {
        "created_at": None,          # Reset cooldown — cho phép gửi lại ngay
        "otp_code_hash": None,       # Vô hiệu hoá code cũ (không thể verify session lỗi)
        "verified": False,
        "send_failed": True,         # Đánh dấu để debug
    }

    # Thử update Firestore
    try:
        from backend.db.firestore_client import get_firestore_client
        db = get_firestore_client()
        ref = db.collection("otp_sessions").document(session_key)
        snap = ref.get()
        if snap.exists:
            ref.update(reset_data)
            logger.debug(f"[OTP] Rolled back failed send session in Firestore: {session_key}")
            if is_dev and session_key in _memory_sessions:
                _memory_sessions[session_key].update(reset_data)
            return
        elif not is_dev:
            logger.error(f"[OTP] Rollback Firestore thất bại: session không tồn tại: {session_key}")
            raise RuntimeError("Session không tồn tại trên Firestore để rollback")
    except Exception as e:
        logger.error(f"[OTP] Không rollback được Firestore session sau provider fail: {type(e).__name__}")
        if not is_dev:
            raise RuntimeError(f"Lỗi rollback OTP session trên Firestore: {type(e).__name__}") from e

    # Fallback in-memory (dev/test)
    if is_dev and session_key in _memory_sessions:
        _memory_sessions[session_key].update(reset_data)


def create_otp_session(contact: str) -> str:
    """
    Tạo session OTP mới, lưu vào Firestore (hoặc in-memory fallback trong dev/test).

    Args:
        contact: SĐT hoặc địa chỉ email của khách hàng.

    Returns:
        otp_code: Mã OTP plaintext (chỉ dùng để gửi cho user, KHÔNG lưu lại).
    Raises:
        RuntimeError: nếu ở production và không thể lưu session vào Firestore.
    """
    is_dev = is_dev_env()
    is_mock = os.getenv("OTP_PROVIDER", "mock").strip().lower() == "mock"

    # Cho phép override code tĩnh trong môi trường mock (tiện demo)
    mock_code = os.getenv("OTP_MOCK_CODE", "").strip()
    if is_dev and is_mock and mock_code:
        otp_code = mock_code
    else:
        otp_code = _generate_otp_code()

    session_key = _hash_contact_for_otp(contact)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=OTP_EXPIRE_MINUTES)
    current_hour = now.strftime("%Y-%m-%dT%H")

    # Tự động verified=True cho Phone Demo (chỉ dev)
    accept_all = os.getenv("OTP_MOCK_ACCEPT_ALL", "").strip().lower() == "true"
    is_phone_demo = is_dev and not _is_email(contact) and is_mock and accept_all

    # Đọc send_count hiện tại để ghi tăng dần (hourly rate limit)
    prev_send_count = 0
    prev_send_hour = ""

    try:
        from backend.db.firestore_client import get_firestore_client
        db = get_firestore_client()
        session_ref = db.collection("otp_sessions").document(session_key)

        from firebase_admin import firestore

        @firestore.transactional
        def _atomic_create_txn(transaction, ref):
            snap = ref.get(transaction=transaction)
            prev_send_count = 0
            prev_send_hour = ""
            if snap.exists:
                _prev = snap.to_dict() or {}

                # 1. Atomic check: Cooldown 60 giây trong cùng transaction!
                prev_created_at = _prev.get("created_at")
                if prev_created_at is not None:
                    if hasattr(prev_created_at, "timestamp"):
                        prev_created_at_dt = datetime.fromtimestamp(prev_created_at.timestamp(), tz=timezone.utc)
                    elif isinstance(prev_created_at, str):
                        try:
                            prev_created_at_dt = datetime.fromisoformat(prev_created_at)
                        except ValueError:
                            prev_created_at_dt = None
                    else:
                        prev_created_at_dt = None

                    if prev_created_at_dt:
                        if prev_created_at_dt.tzinfo is None:
                            prev_created_at_dt = prev_created_at_dt.replace(tzinfo=timezone.utc)
                        elapsed = (now - prev_created_at_dt).total_seconds()
                        if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
                            remaining = max(1, int(OTP_RESEND_COOLDOWN_SECONDS - elapsed))
                            logger.info(f"[OTP] Cooldown còn hiệu lực trong transaction: {remaining}s | {session_key}")
                            raise OtpCooldownError(remaining_seconds=remaining)

                # 2. Atomic check: Hourly limit 5 lần/giờ trong cùng transaction!
                prev_send_hour = _prev.get("send_hour", "")
                if prev_send_hour == current_hour:
                    prev_send_count = _prev.get("send_count", 0)

            if prev_send_hour == current_hour and prev_send_count >= OTP_HOURLY_SEND_LIMIT:
                logger.warning(f"[OTP] Hourly rate limit chạm ngưỡng khi tạo session: {session_key}")
                raise OtpHourlyLimitError(limit=OTP_HOURLY_SEND_LIMIT)

            new_session_data = {
                "otp_code_hash": _hash_otp_code(otp_code),
                "expires_at": expires_at,
                "verified": is_phone_demo,
                "attempts": 0,
                "created_at": now,
                "send_hour": current_hour,
                "send_count": prev_send_count + 1,
                "send_failed": False,
            }
            transaction.set(ref, new_session_data)
            return new_session_data

        txn = db.transaction()
        session_data = _atomic_create_txn(txn, session_ref)
        logger.debug(f"[OTP] Session created in Firestore atomically: {session_key}")
        if is_dev:
            _memory_sessions[session_key] = session_data
        return otp_code

    except (OtpCooldownError, OtpHourlyLimitError, ValueError):
        # Re-raise rate limit / cooldown errors so caller returns 429
        raise
    except Exception as e:
        if not is_dev:
            # Production: KHÔNG cho phép in-memory fallback!
            logger.error(f"[OTP] Production không thể lưu OTP session vào Firestore: {type(e).__name__}")
            raise RuntimeError(f"Không thể lưu OTP session vào cơ sở dữ liệu: {type(e).__name__}") from e

        # Fallback in-memory cho dev/test không có Firestore
        logger.warning(f"[OTP] Dùng in-memory fallback (Firestore lỗi): {type(e).__name__}")
        _prev_mem = _memory_sessions.get(session_key, {})

        mem_created_at = _prev_mem.get("created_at")
        if mem_created_at is not None:
            if hasattr(mem_created_at, "timestamp"):
                mem_created_at_dt = datetime.fromtimestamp(mem_created_at.timestamp(), tz=timezone.utc)
            elif isinstance(mem_created_at, str):
                try:
                    mem_created_at_dt = datetime.fromisoformat(mem_created_at)
                except ValueError:
                    mem_created_at_dt = None
            else:
                mem_created_at_dt = None

            if mem_created_at_dt:
                if mem_created_at_dt.tzinfo is None:
                    mem_created_at_dt = mem_created_at_dt.replace(tzinfo=timezone.utc)
                elapsed = (now - mem_created_at_dt).total_seconds()
                if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
                    remaining = max(1, int(OTP_RESEND_COOLDOWN_SECONDS - elapsed))
                    logger.info(f"[OTP] Cooldown còn hiệu lực trong RAM: {remaining}s | {session_key}")
                    raise OtpCooldownError(remaining_seconds=remaining)

        prev_send_hour = _prev_mem.get("send_hour", "")
        prev_send_count = _prev_mem.get("send_count", 0) if prev_send_hour == current_hour else 0

        if prev_send_hour == current_hour and prev_send_count >= OTP_HOURLY_SEND_LIMIT:
            logger.warning(f"[OTP] Hourly rate limit chạm ngưỡng khi tạo session (RAM): {session_key}")
            raise OtpHourlyLimitError(limit=OTP_HOURLY_SEND_LIMIT)

        session_data = {
            "otp_code_hash": _hash_otp_code(otp_code),
            "expires_at": expires_at,
            "verified": is_phone_demo,
            "attempts": 0,
            "created_at": now,
            "send_hour": current_hour,
            "send_count": prev_send_count + 1,
            "send_failed": False,
        }
        _memory_sessions[session_key] = session_data
        return otp_code


def verify_otp_session(contact: str, code_input: str) -> OtpVerifyResult:
    """
    Xác thực OTP do user nhập.

    Kiểm tra:
      1. Session tồn tại (Firestore trên prod, RAM fallback trên dev).
      2. Chưa hết hạn (OTP_EXPIRE_MINUTES).
      3. Chưa verified (tránh reuse — mỗi OTP chỉ dùng được 1 lần).
      4. Session không bị đánh dấu send_failed.
      5. Số lần thử chưa vượt OTP_MAX_ATTEMPTS.
      6. Code đúng (so sánh hash).
      7. Cập nhật verified=True và verified_at vào persistent storage.

    Returns:
        OtpVerifyResult với success=True nếu hợp lệ.
    """
    is_dev = is_dev_env()
    is_mock = os.getenv("OTP_PROVIDER", "mock").strip().lower() == "mock"
    accept_all = os.getenv("OTP_MOCK_ACCEPT_ALL", "").strip().lower() == "true"
    if is_dev and not _is_email(contact) and is_mock and accept_all:
        logger.info("[OTP] MockOTP accept-all mode — bỏ qua xác thực code cho SĐT")
        return OtpVerifyResult(success=True, message="OTP hợp lệ (mock accept-all mode).")

    session_key = _hash_contact_for_otp(contact)
    now = datetime.now(timezone.utc)

    session_data = None
    use_firestore = False
    session_ref = None

    try:
        from backend.db.firestore_client import get_firestore_client
        db = get_firestore_client()
        session_ref = db.collection("otp_sessions").document(session_key)

        from firebase_admin import firestore

        @firestore.transactional
        def _atomic_verify_txn(txn, ref):
            snap = ref.get(transaction=txn)
            if not snap.exists:
                return None  # Không có trong Firestore

            data = snap.to_dict() or {}

            # Kiểm tra session bị đánh dấu send_failed
            if data.get("send_failed"):
                return OtpVerifyResult(
                    success=False,
                    message="Mã OTP trước đó gửi thất bại. Vui lòng yêu cầu mã mới.",
                )

            # Kiểm tra hết hạn
            expires_at = data.get("expires_at")
            if expires_at is None:
                return OtpVerifyResult(
                    success=False,
                    message="Mã OTP không hợp lệ. Vui lòng yêu cầu mã mới.",
                )
            if hasattr(expires_at, "timestamp"):
                expires_at = datetime.fromtimestamp(expires_at.timestamp(), tz=timezone.utc)
            if now > expires_at:
                return OtpVerifyResult(
                    success=False,
                    message=f"Mã OTP đã hết hạn ({OTP_EXPIRE_MINUTES} phút). Vui lòng yêu cầu mã mới.",
                )

            # Kiểm tra đã verified rồi (ngăn chặn race condition xác thực đồng thời 2 lần)
            if data.get("verified"):
                return OtpVerifyResult(
                    success=False,
                    message="Mã OTP này đã được sử dụng. Vui lòng yêu cầu mã mới.",
                )

            # Kiểm tra số lần thử
            attempts = data.get("attempts", 0)
            if attempts >= OTP_MAX_ATTEMPTS:
                return OtpVerifyResult(
                    success=False,
                    message=f"Đã nhập sai quá {OTP_MAX_ATTEMPTS} lần. Vui lòng yêu cầu mã mới.",
                    attempts_remaining=0,
                )

            stored_hash = data.get("otp_code_hash")
            if not stored_hash:
                return OtpVerifyResult(
                    success=False,
                    message="Mã OTP không hợp lệ. Vui lòng yêu cầu mã mới.",
                )

            input_hash = _hash_otp_code(code_input.strip())
            if input_hash != stored_hash:
                new_attempts = attempts + 1
                remaining = max(0, OTP_MAX_ATTEMPTS - new_attempts)
                txn.update(ref, {"attempts": new_attempts})
                return OtpVerifyResult(
                    success=False,
                    message=f"Mã OTP không đúng. Còn {remaining} lần thử.",
                    attempts_remaining=remaining,
                )

            # Mã đúng -> Cập nhật verified=True và verified_at ngay trong transaction
            txn.update(ref, {"verified": True, "verified_at": now})
            return OtpVerifyResult(success=True, message="Xác thực thông tin liên hệ thành công.")

        txn = db.transaction()
        result = _atomic_verify_txn(txn, session_ref)
        if result is not None:
            if result.success:
                logger.info(f"[OTP] Xác thực thành công: {session_key}")
                if is_dev and session_key in _memory_sessions:
                    _memory_sessions[session_key]["verified"] = True
                    _memory_sessions[session_key]["verified_at"] = now
            return result

        # result is None nghĩa là doc không tồn tại trong Firestore
        if not is_dev:
            # Production: doc không có trên Firestore -> từ chối an toàn, KHÔNG đọc RAM
            return OtpVerifyResult(
                success=False,
                message="Mã OTP không tồn tại hoặc đã hết hạn. Vui lòng yêu cầu mã mới.",
            )

    except Exception as e:
        if not is_dev:
            logger.error(f"[OTP] Production lỗi Firestore khi verify: {type(e).__name__}")
            return OtpVerifyResult(
                success=False,
                message="Dịch vụ xác thực tạm thời không khả dụng. Vui lòng thử lại sau.",
            )
        logger.warning(f"[OTP] Dùng in-memory fallback (Firestore lỗi): {type(e).__name__}")

    # Fallback in-memory cho dev/test
    if is_dev:
        session_data = _memory_sessions.get(session_key)
        if not session_data:
            return OtpVerifyResult(
                success=False,
                message="Mã OTP không tồn tại hoặc đã hết hạn. Vui lòng yêu cầu mã mới.",
            )

        # Kiểm tra session bị đánh dấu send_failed
        if session_data.get("send_failed"):
            return OtpVerifyResult(
                success=False,
                message="Mã OTP trước đó gửi thất bại. Vui lòng yêu cầu mã mới.",
            )

        # Kiểm tra hết hạn
        expires_at = session_data.get("expires_at")
        if expires_at is None:
            return OtpVerifyResult(
                success=False,
                message="Mã OTP không hợp lệ. Vui lòng yêu cầu mã mới.",
            )
        if hasattr(expires_at, "timestamp"):
            expires_at = datetime.fromtimestamp(expires_at.timestamp(), tz=timezone.utc)
        if now > expires_at:
            return OtpVerifyResult(
                success=False,
                message=f"Mã OTP đã hết hạn ({OTP_EXPIRE_MINUTES} phút). Vui lòng yêu cầu mã mới.",
            )

        # Kiểm tra đã verified rồi
        if session_data.get("verified"):
            return OtpVerifyResult(
                success=False,
                message="Mã OTP này đã được sử dụng. Vui lòng yêu cầu mã mới.",
            )

        # Kiểm tra số lần thử
        attempts = session_data.get("attempts", 0)
        if attempts >= OTP_MAX_ATTEMPTS:
            return OtpVerifyResult(
                success=False,
                message=f"Đã nhập sai quá {OTP_MAX_ATTEMPTS} lần. Vui lòng yêu cầu mã mới.",
                attempts_remaining=0,
            )

        stored_hash = session_data.get("otp_code_hash")
        if not stored_hash:
            return OtpVerifyResult(
                success=False,
                message="Mã OTP không hợp lệ. Vui lòng yêu cầu mã mới.",
            )

        input_hash = _hash_otp_code(code_input.strip())
        if input_hash != stored_hash:
            new_attempts = attempts + 1
            session_data["attempts"] = new_attempts
            remaining = max(0, OTP_MAX_ATTEMPTS - new_attempts)
            return OtpVerifyResult(
                success=False,
                message=f"Mã OTP không đúng. Còn {remaining} lần thử.",
                attempts_remaining=remaining,
            )

        # Đánh dấu đã verified
        session_data["verified"] = True
        session_data["verified_at"] = now
        logger.info(f"[OTP] Xác thực thành công (RAM): {session_key}")
        return OtpVerifyResult(success=True, message="Xác thực thông tin liên hệ thành công.")

    return OtpVerifyResult(
        success=False,
        message="Mã OTP không tồn tại hoặc đã hết hạn. Vui lòng yêu cầu mã mới.",
    )


def check_verified_session_valid(contact: str) -> tuple[bool, str]:
    """
    Kiểm tra session OTP đã verified còn hiệu lực không (dùng trong /feedback).

    Phân biệt với verify_otp_session (nhận code input) —
    hàm này chỉ đọc trạng thái session đã được verify trước đó.

    TTL riêng sau xác thực: OTP_VERIFIED_SESSION_TTL_MINUTES (30 phút).
    Session cũ thiếu verified_at → từ chối an toàn (không mặc định hợp lệ).

    Returns:
        (is_valid, reason): reason là "" nếu hợp lệ, hoặc mã lỗi nếu không.
    Raises:
        RuntimeError: nếu Firestore không thể đọc được (caller phải bắt và trả 503).
    """
    session_key = _hash_contact_for_otp(contact)
    now = datetime.now(timezone.utc)
    is_dev = is_dev_env()

    # Đọc session — KHÔNG fallback im lặng khi Firestore lỗi
    session_data = None
    try:
        from backend.db.firestore_client import get_firestore_client
        db = get_firestore_client()
        snap = db.collection("otp_sessions").document(session_key).get()
        if snap.exists:
            session_data = snap.to_dict()
        else:
            session_data = None
    except Exception as e:
        # Firestore lỗi → raise để caller trả 503, không coi là verified
        logger.error(f"[OTP] Firestore lỗi khi đọc verified session: {type(e).__name__}")
        raise RuntimeError(f"Firestore không khả dụng khi kiểm tra OTP session: {type(e).__name__}") from e

    # Session không tồn tại trong Firestore
    if not session_data:
        if is_dev:
            # Thử in-memory (chỉ cho dev/test fallback)
            session_data = _memory_sessions.get(session_key)
        if not session_data:
            return False, "session_not_found"

    # Chưa verified
    if not session_data.get("verified", False):
        return False, "not_verified"

    # Kiểm tra verified_at + TTL riêng
    verified_at = session_data.get("verified_at")
    if verified_at is None:
        logger.warning(f"[OTP] Session {session_key} thiếu verified_at — từ chối (backward safe)")
        return False, "missing_verified_at"
    if hasattr(verified_at, "timestamp"):
        verified_at = datetime.fromtimestamp(verified_at.timestamp(), tz=timezone.utc)
    elif isinstance(verified_at, str):
        try:
            verified_at = datetime.fromisoformat(verified_at)
        except ValueError:
            return False, "invalid_verified_at"

    session_age_seconds = (now - verified_at).total_seconds()
    ttl_seconds = OTP_VERIFIED_SESSION_TTL_MINUTES * 60
    if session_age_seconds > ttl_seconds:
        logger.info(f"[OTP] Session {session_key} đã hết hạn ({session_age_seconds:.0f}s > {ttl_seconds}s)")
        return False, "session_expired"

    return True, ""


def _update_session(session_key: str, update_data: dict, session_ref, use_firestore: bool) -> None:
    """Helper cập nhật session (Firestore hoặc in-memory)."""
    is_dev = is_dev_env()
    if use_firestore and session_ref:
        try:
            session_ref.update(update_data)
            if is_dev and session_key in _memory_sessions:
                _memory_sessions[session_key].update(update_data)
            return
        except Exception as e:
            logger.warning(f"[OTP] Không update được Firestore session: {type(e).__name__}")
            if not is_dev:
                raise RuntimeError(f"Không thể cập nhật Firestore session: {type(e).__name__}") from e
    if is_dev and session_key in _memory_sessions:
        _memory_sessions[session_key].update(update_data)

