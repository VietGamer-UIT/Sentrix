"""
Rate Limit Service — Giới hạn tần suất gửi phản hồi
=====================================================
Author: Đoàn Hoàng Việt
Module 1 — Lớp 1: Rate Limiting

MỤC ĐÍCH:
  Giới hạn 1 lượt phản hồi hợp lệ / 24h / (IP + SĐT hash).
  Ngăn chặn cùng 1 khách hàng gửi nhiều lượt trong ngày để trộm voucher.

LƯU Ý THIẾT KẾ:
  - Rate limit chỉ áp dụng cho các lượt ĐÃ ĐƯỢC XÁC NHẬN HỢP LỆ
    (sau khi qua Lớp 1 OTP). Phản hồi anonymous (voucher_eligible=false) KHÔNG bị rate limit
    vì chúng ta muốn thu thập nhiều dữ liệu anonymous nhất có thể.
  - Không phân biệt "gian lận" — chỉ là giới hạn hợp lệ, trả thông báo thân thiện.
  - Nếu vi phạm: validity_status = "rate_limited", KHÔNG phát voucher, vẫn ghi nhận.

FIRESTORE:
  Collection: `rate_limits/{phone_hash}`
  Fields:
    last_submission_at: Timestamp — lần gửi hợp lệ gần nhất
    ip_last:            string    — IP gần nhất
    tenant_id_last:     string    — tenant gần nhất
    submission_count:   number    — tổng số lượt hợp lệ đã ghi nhận (audit)
"""

import hashlib
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cấu hình
# ---------------------------------------------------------------------------
RATE_LIMIT_HOURS = 24  # 1 lượt / 24h / SĐT
# In-memory fallback khi Firestore chưa setup (dev/test)
_memory_rate_limits: dict = {}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class RateLimitResult:
    """Kết quả kiểm tra rate limit."""
    allowed: bool                 # True = được phép gửi
    reason: Optional[str]         # Lý do bị chặn (None nếu allowed)
    next_allowed_at: Optional[datetime]  # Thời điểm được phép gửi tiếp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _hash_phone_for_rate_limit(phone: str) -> str:
    """
    Băm SĐT thành document ID cho collection rate_limits.
    SHA-256 one-way — không thể khôi phục SĐT gốc từ hash.
    """
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("0"):
        phone = "+84" + phone[1:]
    elif not phone.startswith("+"):
        phone = "+84" + phone
    return "rl_" + hashlib.sha256(phone.encode("utf-8")).hexdigest()[:24]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def check_rate_limit(
    phone_number: str,
    ip_address: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> RateLimitResult:
    """
    Kiểm tra xem SĐT này có được phép gửi phản hồi hợp lệ không.

    Args:
        phone_number: SĐT khách hàng (sẽ được hash ngay lập tức).
        ip_address:   IP address của request (để log, không dùng làm key chính).
        tenant_id:    Tenant hiện tại.

    Returns:
        RateLimitResult.allowed = True nếu chưa gửi trong 24h gần nhất.
    """
    doc_key = _hash_phone_for_rate_limit(phone_number)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=RATE_LIMIT_HOURS)

    # Thử đọc từ Firestore
    record = _read_record(doc_key)

    if record:
        last_at = record.get("last_submission_at")
        if last_at:
            # Chuẩn hoá Firestore Timestamp → datetime Python
            if hasattr(last_at, "timestamp"):
                last_at = datetime.fromtimestamp(last_at.timestamp(), tz=timezone.utc)
            elif isinstance(last_at, str):
                last_at = datetime.fromisoformat(last_at)

            if last_at > cutoff:
                next_allowed = last_at + timedelta(hours=RATE_LIMIT_HOURS)
                logger.info(
                    f"[RateLimit] Chặn do đã gửi trong {RATE_LIMIT_HOURS}h: "
                    f"{doc_key} | last={last_at.isoformat()}"
                )
                return RateLimitResult(
                    allowed=False,
                    reason=(
                        f"Bạn đã gửi phản hồi hôm nay, cảm ơn bạn! "
                        f"Vui lòng thử lại sau {next_allowed.strftime('%H:%M')} (UTC+7)."
                    ),
                    next_allowed_at=next_allowed,
                )

    logger.debug(f"[RateLimit] Cho phép: {doc_key}")
    return RateLimitResult(allowed=True, reason=None, next_allowed_at=None)


def record_submission(
    phone_number: str,
    ip_address: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> None:
    """
    Ghi nhận lượt gửi hợp lệ vào Firestore.
    Chỉ gọi hàm này sau khi phản hồi đã qua ĐỦ Lớp 1–3 và được đánh dấu "valid".

    Args:
        phone_number: SĐT (sẽ được hash, không lưu gốc).
        ip_address:   IP để log/audit.
        tenant_id:    Tenant ID để log.
    """
    doc_key = _hash_phone_for_rate_limit(phone_number)
    now = datetime.now(timezone.utc)

    record = _read_record(doc_key) or {}
    old_count = record.get("submission_count", 0)

    new_data = {
        "last_submission_at": now,
        "ip_last": ip_address or "unknown",
        "tenant_id_last": tenant_id or "unknown",
        "submission_count": old_count + 1,
        "updated_at": now,
    }

    _write_record(doc_key, new_data)
    logger.info(
        f"[RateLimit] Ghi nhận lượt gửi hợp lệ: {doc_key} "
        f"| count={new_data['submission_count']} | tenant={tenant_id}"
    )


# ---------------------------------------------------------------------------
# Firestore + in-memory backend
# ---------------------------------------------------------------------------
def _read_record(doc_key: str) -> Optional[dict]:
    """Đọc rate limit record từ Firestore. Fallback in-memory nếu lỗi."""
    try:
        from backend.db.firestore_client import get_firestore_client
        db = get_firestore_client()
        snap = db.collection("rate_limits").document(doc_key).get()
        if snap.exists:
            return snap.to_dict()
        return None
    except Exception as e:
        logger.warning(f"[RateLimit] Dùng in-memory fallback (Firestore lỗi): {e}")
        return _memory_rate_limits.get(doc_key)


def _write_record(doc_key: str, data: dict) -> None:
    """Ghi rate limit record lên Firestore. Fallback in-memory nếu lỗi."""
    try:
        from backend.db.firestore_client import get_firestore_client
        db = get_firestore_client()
        db.collection("rate_limits").document(doc_key).set(data, merge=True)
        return
    except Exception as e:
        logger.warning(f"[RateLimit] Không ghi được Firestore, dùng in-memory: {e}")
        _memory_rate_limits[doc_key] = {**_memory_rate_limits.get(doc_key, {}), **data}
