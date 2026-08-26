"""
OTP Service — Xác thực số điện thoại qua mã OTP
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
  - ZaloZnsOtpProvider:  Stub — TODO: cắm API Zalo OTP thật khi có template_id + credentials.
                         Xem: https://developers.zalo.me/docs/zns/gui-tin-zns

CHỌN PROVIDER:
  Đọc biến môi trường OTP_PROVIDER:
    - "mock"  (default) → MockOtpProvider
    - "zalo"            → ZaloZnsOtpProvider

LƯU TRỮ SESSION OTP:
  OTP được lưu vào Firestore collection `otp_sessions/{phone_hash}` với:
    - otp_code_hash: SHA-256 của code (không lưu plaintext)
    - expires_at:    thời điểm hết hạn (5 phút)
    - verified:      True sau khi xác thực thành công
    - attempts:      số lần nhập sai (giới hạn 3 lần)
  Fallback in-memory nếu Firestore chưa setup (dev/test).
"""

import hashlib
import logging
import os
import random
import string
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hằng số cấu hình
# ---------------------------------------------------------------------------
OTP_CODE_LENGTH = 6
OTP_EXPIRE_MINUTES = 5     # OTP hết hạn sau 5 phút
OTP_MAX_ATTEMPTS = 3       # Tối đa 3 lần nhập sai trước khi hủy session

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
# Abstract Interface
# ---------------------------------------------------------------------------
class OtpProvider(ABC):
    """Interface cơ sở cho các OTP provider. Mọi provider phải implement 2 method này."""

    @abstractmethod
    def send_otp(self, phone_number: str, otp_code: str) -> OtpSendResult:
        """
        Gửi OTP đến số điện thoại.

        Args:
            phone_number: SĐT chuẩn hoá (ví dụ: "+84901234567")
            otp_code:     Mã OTP 6 chữ số đã được tạo ngẫu nhiên.

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
      - Chấp nhận bất kỳ số điện thoại nào.
      - Log mã OTP ra console (để giám khảo xem trong demo live).
      - Để bật "always accept" trong demo: đặt OTP_MOCK_ACCEPT_ALL=true
        thì verify sẽ chấp nhận bất kỳ code nào (tiện cho demo nhanh).

    TODO (production): Thay bằng ZaloZnsOtpProvider hoặc VnptSmsProvider.
    """

    def send_otp(self, phone_number: str, otp_code: str) -> OtpSendResult:
        # In ra console cho giám khảo xem trong demo — KHÔNG làm trong production
        logger.info(
            f"[MockOTP] ═══════════════════════════════════\n"
            f"[MockOTP] SĐT: {phone_number}\n"
            f"[MockOTP] Mã OTP: {otp_code}  ← (giả lập, không gửi thật)\n"
            f"[MockOTP] Hết hạn: {OTP_EXPIRE_MINUTES} phút\n"
            f"[MockOTP] ═══════════════════════════════════"
        )
        return OtpSendResult(
            success=True,
            message=f"[DEMO] OTP đã được gửi (giả lập). Mã: {otp_code}",
        )

    def provider_name(self) -> str:
        return "MockOtpProvider"


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


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
def get_otp_provider() -> OtpProvider:
    """
    Trả về OTP provider phù hợp dựa trên biến môi trường OTP_PROVIDER.
    Default: MockOtpProvider (an toàn cho dev/demo).
    """
    provider_name = os.getenv("OTP_PROVIDER", "mock").lower().strip()
    if provider_name == "zalo":
        return ZaloZnsOtpProvider()
    return MockOtpProvider()


# ---------------------------------------------------------------------------
# OTP Session Management (Firestore-backed với in-memory fallback)
# ---------------------------------------------------------------------------
def _normalize_phone(phone: str) -> str:
    """Chuẩn hoá SĐT về dạng +84... để hash nhất quán."""
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("0"):
        phone = "+84" + phone[1:]
    elif not phone.startswith("+"):
        phone = "+84" + phone
    return phone


def _hash_phone_for_otp(phone: str) -> str:
    """
    Tạo document ID cho otp_sessions từ SĐT.
    Dùng SHA-256 để bảo vệ SĐT — không lưu SĐT gốc vào Firestore.
    """
    normalized = _normalize_phone(phone)
    return "otp_" + hashlib.sha256(normalized.encode()).hexdigest()[:20]


def _generate_otp_code() -> str:
    """Tạo mã OTP ngẫu nhiên 6 chữ số."""
    return "".join(random.choices(string.digits, k=OTP_CODE_LENGTH))


def _hash_otp_code(code: str) -> str:
    """Hash OTP code trước khi lưu vào Firestore (không lưu plaintext)."""
    return hashlib.sha256(code.encode()).hexdigest()


# In-memory fallback (dùng khi Firestore chưa setup)
_memory_sessions: dict = {}


def create_otp_session(phone_number: str) -> str:
    """
    Tạo session OTP mới, lưu vào Firestore (hoặc in-memory fallback).

    Returns:
        otp_code: Mã OTP plaintext (chỉ dùng để gửi cho user, KHÔNG lưu lại).
    """
    # Cho phép override code tĩnh trong môi trường mock (tiện demo)
    mock_code = os.getenv("OTP_MOCK_CODE", "")
    otp_code = mock_code if mock_code else _generate_otp_code()

    session_key = _hash_phone_for_otp(phone_number)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)

    session_data = {
        "otp_code_hash": _hash_otp_code(otp_code),
        "expires_at": expires_at,
        "verified": False,
        "attempts": 0,
        "created_at": datetime.now(timezone.utc),
    }

    # Thử lưu vào Firestore
    try:
        from backend.db.firestore_client import get_firestore_client
        db = get_firestore_client()
        db.collection("otp_sessions").document(session_key).set(session_data)
        logger.debug(f"[OTP] Session created in Firestore: {session_key}")
    except Exception as e:
        # Fallback in-memory cho dev/test không có Firestore
        logger.warning(f"[OTP] Firestore unavailable, dùng in-memory fallback: {e}")
        _memory_sessions[session_key] = session_data

    return otp_code


def verify_otp_session(phone_number: str, code_input: str) -> OtpVerifyResult:
    """
    Xác thực OTP do user nhập.

    Kiểm tra:
      1. Session tồn tại.
      2. Chưa hết hạn.
      3. Chưa verified (tránh reuse).
      4. Số lần thử chưa vượt OTP_MAX_ATTEMPTS.
      5. Code đúng (so sánh hash).

    Returns:
        OtpVerifyResult với success=True nếu hợp lệ.
    """
    # Trong mock mode và OTP_MOCK_ACCEPT_ALL=true → chấp nhận mọi code
    if os.getenv("OTP_PROVIDER", "mock") == "mock" and os.getenv("OTP_MOCK_ACCEPT_ALL", "").lower() == "true":
        logger.info("[OTP] MockOTP accept-all mode — bỏ qua xác thực code")
        return OtpVerifyResult(success=True, message="OTP hợp lệ (mock accept-all mode).")

    session_key = _hash_phone_for_otp(phone_number)
    now = datetime.now(timezone.utc)

    # Đọc session từ Firestore hoặc in-memory
    session_data = None
    use_firestore = False
    session_ref = None

    try:
        from backend.db.firestore_client import get_firestore_client
        db = get_firestore_client()
        session_ref = db.collection("otp_sessions").document(session_key)
        snap = session_ref.get()
        if snap.exists:
            session_data = snap.to_dict()
            use_firestore = True
    except Exception as e:
        logger.warning(f"[OTP] Dùng in-memory session (Firestore lỗi): {e}")
        session_data = _memory_sessions.get(session_key)

    if not session_data:
        return OtpVerifyResult(
            success=False,
            message="Mã OTP không tồn tại hoặc đã hết hạn. Vui lòng yêu cầu mã mới.",
        )

    # Kiểm tra hết hạn
    expires_at = session_data["expires_at"]
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

    # So sánh hash code
    input_hash = _hash_otp_code(code_input.strip())
    if input_hash != session_data["otp_code_hash"]:
        new_attempts = attempts + 1
        remaining = OTP_MAX_ATTEMPTS - new_attempts
        # Cập nhật attempts
        _update_session(session_key, {"attempts": new_attempts}, session_ref, use_firestore)
        return OtpVerifyResult(
            success=False,
            message=f"Mã OTP không đúng. Còn {remaining} lần thử.",
            attempts_remaining=remaining,
        )

    # Đánh dấu đã verified
    _update_session(session_key, {"verified": True, "verified_at": now}, session_ref, use_firestore)
    logger.info(f"[OTP] Xác thực thành công: {session_key}")
    return OtpVerifyResult(success=True, message="Xác thực số điện thoại thành công.")


def _update_session(session_key: str, update_data: dict, session_ref, use_firestore: bool) -> None:
    """Helper cập nhật session (Firestore hoặc in-memory)."""
    if use_firestore and session_ref:
        try:
            session_ref.update(update_data)
            return
        except Exception as e:
            logger.warning(f"[OTP] Không update được Firestore session: {e}")
    # Fallback in-memory
    if session_key in _memory_sessions:
        _memory_sessions[session_key].update(update_data)
