"""
Voucher Budget Service — Kiểm soát ngân sách và tỷ lệ trúng thưởng
====================================================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
Module 1 — Lớp 4: Hạn mức Voucher

MỤC ĐÍCH:
  Kiểm soát số lượng voucher phát ra mỗi ngày và tỷ lệ trúng thưởng.
  Chỉ áp dụng sau khi feedback đã qua ĐỦ Lớp 1–3 (validity_status = "valid").
  Chủ quán cấu hình qua Dashboard; thay đổi có hiệu lực ngay không cần deploy.

CẤU HÌNH FIRESTORE:
  Collection: `voucher_budget_config/{tenant_id}`
  Fields:
    daily_voucher_limit:  int   — số voucher tối đa/ngày (0 = tắt hoàn toàn)
    win_rate_percent:     float — % lượt valid được trúng (0.0–100.0)
    vouchers_issued_today: int  — bộ đếm tự động reset mỗi ngày
    last_reset_date:      string — "YYYY-MM-DD" theo UTC+7 (VN timezone)

LUỒNG PHÁT VOUCHER:
  1. Đọc config của tenant từ Firestore.
  2. Kiểm tra last_reset_date != today → tự reset counter về 0.
  3. Kiểm tra vouchers_issued_today < daily_voucher_limit.
  4. Random win_rate_percent → trúng hay không.
  5. Nếu trúng → atomic increment vouchers_issued_today + sinh voucher code.
  6. Trả VoucherResult.

RACE CONDITION:
  Dùng Firestore Transaction để atomic increment vouchers_issued_today.
  Không thể xảy ra tình trạng phát vượt daily_voucher_limit dù nhiều request đồng thời.

TÍCH HỢP VỚI /spin:
  Route /spin sẽ gọi issue_voucher() thay vì random trực tiếp.
  /spin chỉ được gọi với feedback_id có validity_status = "valid" (kiểm tra trong route).
"""

import logging
import os
import random
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional

from backend.db.firestore_client import get_firestore_client

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Múi giờ Việt Nam (UTC+7) — dùng để xác định "ngày hôm nay" đúng với VN
# ---------------------------------------------------------------------------
_VN_TZ = timezone(timedelta(hours=7))

# ---------------------------------------------------------------------------
# Giá trị mặc định khi chưa có config trong Firestore
# ---------------------------------------------------------------------------
_DEFAULT_CONFIG = {
    "daily_voucher_limit": 50,    # 50 voucher/ngày cho tenant mới
    "win_rate_percent": 30.0,     # 30% lượt valid được trúng
    "vouchers_issued_today": 0,
    "last_reset_date": "",        # sẽ được set khi có request đầu tiên
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class VoucherResult:
    """Kết quả kiểm tra và phát voucher."""
    voucher_issued: bool           # True nếu phát được voucher
    voucher_code: Optional[str]    # Mã voucher (None nếu không phát)
    reason: str                    # Lý do (để log)
    daily_remaining: Optional[int] # Số voucher còn lại trong ngày


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_voucher_config(tenant_id: str) -> dict:
    """
    Đọc cấu hình voucher budget của tenant.
    Trả về config mặc định nếu chưa có document trong Firestore.
    """
    try:
        db = get_firestore_client()
        snap = db.collection("voucher_budget_config").document(tenant_id).get()
        if snap.exists:
            return {**_DEFAULT_CONFIG, **snap.to_dict()}
    except Exception as e:
        logger.warning(f"[VoucherBudget] Không đọc được config: {e} — dùng default")
    return {**_DEFAULT_CONFIG}


def set_voucher_config(tenant_id: str, config_updates: dict) -> None:
    """
    Cập nhật cấu hình voucher budget của tenant.
    Chỉ update các field được truyền vào (merge=True).

    Args:
        tenant_id:      ID của tenant.
        config_updates: Dict chứa các field cần update.
                        Hợp lệ: daily_voucher_limit, win_rate_percent.
    """
    allowed_fields = {"daily_voucher_limit", "win_rate_percent"}
    filtered = {k: v for k, v in config_updates.items() if k in allowed_fields}

    if not filtered:
        raise ValueError(f"Không có field hợp lệ. Hợp lệ: {allowed_fields}")

    # Validate
    if "daily_voucher_limit" in filtered:
        v = int(filtered["daily_voucher_limit"])
        if v < 0:
            raise ValueError("daily_voucher_limit phải >= 0")
        filtered["daily_voucher_limit"] = v

    if "win_rate_percent" in filtered:
        v = float(filtered["win_rate_percent"])
        if not (0.0 <= v <= 100.0):
            raise ValueError("win_rate_percent phải trong khoảng [0, 100]")
        filtered["win_rate_percent"] = v

    try:
        db = get_firestore_client()
        db.collection("voucher_budget_config").document(tenant_id).set(filtered, merge=True)
        logger.info(f"[VoucherBudget] Cập nhật config: {tenant_id} → {filtered}")
    except Exception as e:
        logger.error(f"[VoucherBudget] Không lưu được config: {e}")
        raise


def issue_voucher(
    tenant_id: str,
    customer_phone: str,
    feedback_id: str,
) -> VoucherResult:
    """
    Kiểm tra ngân sách và phát voucher cho 1 lượt phản hồi hợp lệ.

    Chỉ gọi hàm này khi feedback đã có validity_status = "valid".

    Luồng:
      1. Đọc config.
      2. Auto-reset counter nếu sang ngày mới (theo VN timezone).
      3. Kiểm tra đã đạt daily_voucher_limit chưa.
      4. Random theo win_rate_percent.
      5. Nếu trúng → atomic increment + sinh voucher code.

    Returns:
        VoucherResult.
    """
    try:
        db = get_firestore_client()
        config_ref = db.collection("voucher_budget_config").document(tenant_id)

        @_firestore_transactional
        def _do_transaction(transaction, ref):
            snap = ref.get(transaction=transaction)

            if snap.exists:
                config = {**_DEFAULT_CONFIG, **snap.to_dict()}
            else:
                config = {**_DEFAULT_CONFIG}
                # Tạo document mặc định
                transaction.set(ref, config)

            # Auto-reset counter theo VN timezone
            today_vn = _today_vn()
            if config.get("last_reset_date") != today_vn:
                config["vouchers_issued_today"] = 0
                config["last_reset_date"] = today_vn
                transaction.update(ref, {
                    "vouchers_issued_today": 0,
                    "last_reset_date": today_vn,
                })
                logger.info(f"[VoucherBudget] Reset counter ngày mới: {tenant_id} → {today_vn}")

            daily_limit = int(config.get("daily_voucher_limit", 50))
            issued_today = int(config.get("vouchers_issued_today", 0))
            win_rate = float(config.get("win_rate_percent", 30.0))

            remaining = max(0, daily_limit - issued_today)

            # Kiểm tra đã hết hạn mức chưa
            if daily_limit == 0 or issued_today >= daily_limit:
                return VoucherResult(
                    voucher_issued=False,
                    voucher_code=None,
                    reason=f"Đã đạt hạn mức {daily_limit} voucher/ngày",
                    daily_remaining=0,
                )

            # Random theo win_rate
            rand_val = random.random() * 100.0
            if rand_val > win_rate:
                return VoucherResult(
                    voucher_issued=False,
                    voucher_code=None,
                    reason=f"Không trúng thưởng (win_rate={win_rate:.0f}%, roll={rand_val:.1f}%)",
                    daily_remaining=remaining,
                )

            # Trúng thưởng → atomic increment
            new_issued = issued_today + 1
            transaction.update(ref, {"vouchers_issued_today": new_issued})

            # Sinh voucher code
            voucher_code = _generate_voucher_code(tenant_id, feedback_id)
            logger.info(
                f"[VoucherBudget] PHÁT VOUCHER: {voucher_code} | "
                f"tenant={tenant_id} | issued={new_issued}/{daily_limit}"
            )
            return VoucherResult(
                voucher_issued=True,
                voucher_code=voucher_code,
                reason=f"Trúng thưởng (win_rate={win_rate:.0f}%)",
                daily_remaining=max(0, daily_limit - new_issued),
            )

        transaction = db.transaction()
        return _do_transaction(transaction, config_ref)

    except Exception as e:
        logger.error(f"[VoucherBudget] Lỗi transaction: {type(e).__name__}: {e}")
        # Fail safe: không phát voucher nếu lỗi, nhưng không crash pipeline
        return VoucherResult(
            voucher_issued=False,
            voucher_code=None,
            reason=f"Lỗi hệ thống: {type(e).__name__}",
            daily_remaining=None,
        )


def mark_feedback_spin_used(tenant_id: str, feedback_id: str) -> bool:
    """
    Đánh dấu feedback_id đã được dùng để spin 1 lần.
    Gọi khi /spin đã xử lý xong.

    Returns:
        True nếu đây là lần đầu tiên spin (chưa dùng trước).
        False nếu feedback_id đã spin rồi (chặn replay).
    """
    try:
        db = get_firestore_client()
        fb_ref = (
            db.collection("tenants").document(tenant_id)
            .collection("feedbacks").document(feedback_id)
        )

        @_firestore_transactional
        def _check_and_mark(transaction, ref):
            snap = ref.get(transaction=transaction)
            if not snap.exists:
                return False  # feedback không tồn tại
            data = snap.to_dict() or {}
            if data.get("spin_used"):
                return False  # đã spin rồi → chặn
            transaction.update(ref, {"spin_used": True, "spin_used_at": datetime.now(timezone.utc)})
            return True

        transaction = db.transaction()
        return _check_and_mark(transaction, fb_ref)

    except Exception as e:
        logger.error(f"[VoucherBudget] Lỗi mark_spin_used: {e}")
        return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _today_vn() -> str:
    """Trả về ngày hôm nay theo VN timezone (UTC+7) dạng 'YYYY-MM-DD'."""
    return datetime.now(_VN_TZ).strftime("%Y-%m-%d")


def _generate_voucher_code(tenant_id: str, feedback_id: str) -> str:
    """
    Sinh voucher code ngắn gọn, unique đủ cho demo.
    Format: SX-{4 char tenant slug}-{8 char random hex từ feedback_id}
    """
    import hashlib
    tenant_slug = (tenant_id[:4]).upper().replace("-", "").replace("_", "")
    fb_hash = hashlib.md5(feedback_id.encode()).hexdigest()[:8].upper()
    return f"SX-{tenant_slug}-{fb_hash}"


def _firestore_transactional(func):
    """Decorator wrapper tương thích với firebase_admin @firestore.transactional."""
    from firebase_admin import firestore as _fs
    return _fs.transactional(func)
