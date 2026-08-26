"""
Gamification Routes — POST /api/v1/gamification/spin
=====================================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
Module 1 — Cập nhật: Tích hợp Budget Control vào /spin

THAY ĐỔI so với phiên bản cũ:
  - /spin CHỈ được gọi với feedback_id có validity_status = "valid"
  - Mỗi feedback_id chỉ được spin ĐÚNG 1 LẦN (atomic check via Firestore transaction)
  - Phát voucher qua voucher_budget_service thay vì random trực tiếp
    → không thể phát vượt daily_voucher_limit dù gọi API đồng thời

LÝ DO:
  User có thể bypass giao diện, gọi thẳng API /spin trộm voucher.
  Fix: feedback_id phải được xác thực có validity_status="valid" VÀ chưa spin.
"""

import logging
from fastapi import APIRouter, Form, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from backend.db.firestore_client import get_firestore_client
from backend.db.firestore_ops import (
    update_feedback_gamification,
    get_or_create_customer,
    update_customer_rfms,
    update_customer_voucher,
)
from backend.services.voucher_budget_service import issue_voucher, mark_feedback_spin_used

logger = logging.getLogger(__name__)

router = APIRouter()


def _validate_feedback_for_spin(tenant_id: str, feedback_id: str) -> dict:
    """
    Xác thực feedback_id hợp lệ để spin:
      1. Document tồn tại trong Firestore.
      2. validity_status == "valid" (đã qua đủ Lớp 1–3).
      3. spin_used != True (chưa spin trước đó).

    Returns:
        dict: feedback document data.

    Raises:
        HTTPException 400: Nếu feedback không hợp lệ để spin.
        HTTPException 409: Nếu feedback_id đã được spin rồi.
    """
    try:
        db = get_firestore_client()
        fb_ref = (
            db.collection("tenants").document(tenant_id)
            .collection("feedbacks").document(feedback_id)
        )
        snap = fb_ref.get()
    except Exception as e:
        logger.error(f"[Gamification] Lỗi đọc Firestore: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không thể xác thực phản hồi lúc này. Vui lòng thử lại.",
        )

    if not snap.exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Không tìm thấy phản hồi. Vui lòng gửi phản hồi trước khi quay thưởng.",
        )

    fb_data = snap.to_dict() or {}

    # Kiểm tra validity_status — chỉ chấp nhận "valid"
    validity_status = fb_data.get("validity_status", "valid")  # backward compat: None → "valid"
    if validity_status not in ("valid", None):
        logger.warning(
            f"[Gamification] Chặn spin do validity_status={validity_status}: "
            f"feedback={feedback_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phản hồi không đủ điều kiện nhận thưởng (không qua kiểm tra chất lượng).",
        )

    # Kiểm tra voucher_eligible — nếu anonymous thì không spin
    if fb_data.get("voucher_eligible") is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phản hồi ẩn danh không tham gia chương trình thưởng.",
        )

    # Kiểm tra đã spin chưa
    if fb_data.get("spin_used"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phản hồi này đã được dùng để quay thưởng. Mỗi phản hồi chỉ quay 1 lần.",
        )

    return fb_data


@router.post(
    "/spin",
    summary="Quay thưởng sau khi gửi phản hồi hợp lệ",
    description=(
        "Kiểm tra feedback_id hợp lệ (validity_status=valid, chưa spin), "
        "áp dụng ngân sách voucher/ngày và tỷ lệ trúng thưởng của tenant, "
        "rồi phát voucher nếu trúng. Mỗi feedback_id chỉ spin được 1 lần."
    ),
)
async def spin_gamification(
    tenant_id: str = Form(...),
    customer_phone: str = Form(...),
    feedback_id: Optional[str] = Form(None),
):
    """
    Xử lý Vòng quay may mắn sau khi khách hàng đã gửi feedback hợp lệ.

    Thứ tự kiểm tra:
    1. Xác thực feedback_id: tồn tại, validity_status=valid, chưa spin.
    2. Đánh dấu spin_used=True ngay (atomic) để tránh replay attack.
    3. Gọi voucher_budget_service để kiểm tra ngân sách + random win_rate.
    4. Cập nhật feedback doc + customer doc nếu có voucher.
    """
    logger.info(
        f"[Gamification] Spin request: tenant={tenant_id}, "
        f"phone=****{customer_phone[-4:]}, feedback={feedback_id}"
    )

    # ── Bước 1: Bắt buộc có feedback_id ────────────────────────────────────
    if not feedback_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cần feedback_id để quay thưởng. Vui lòng gửi phản hồi trước.",
        )

    # ── Bước 2: Xác thực feedback hợp lệ để spin ───────────────────────────
    fb_data = _validate_feedback_for_spin(tenant_id, feedback_id)

    # ── Bước 3: Atomic mark spin_used=True (chặn replay ngay lập tức) ──────
    marked = mark_feedback_spin_used(tenant_id, feedback_id)
    if not marked:
        # Race condition: 2 request đồng thời → 1 cái thắng, 1 cái thua
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phản hồi này đã được dùng để quay thưởng. Mỗi phản hồi chỉ quay 1 lần.",
        )

    # ── Bước 4: Kiểm tra ngân sách + random thưởng ─────────────────────────
    voucher_result = issue_voucher(
        tenant_id=tenant_id,
        customer_phone=customer_phone,
        feedback_id=feedback_id,
    )

    voucher_code = voucher_result.voucher_code or ""
    message = (
        f"Chúc mừng! Bạn nhận được voucher: {voucher_code}"
        if voucher_result.voucher_issued
        else "Cảm ơn bạn đã tham gia! Chúc bạn may mắn lần sau."
    )

    # ── Bước 5: Cập nhật Firestore ──────────────────────────────────────────
    try:
        customer_doc = get_or_create_customer(tenant_id, customer_phone)
        customer_id = customer_doc["customer_id"]

        # Cập nhật feedback doc với kết quả spin
        if feedback_id:
            already_linked = bool(fb_data.get("customer_id"))
            if not already_linked:
                sent_score = fb_data.get("sentiment_score", 0.0) or 0.0
                sent_score_raw = (sent_score + 1.0) / 2.0
                update_customer_rfms(
                    tenant_id=tenant_id,
                    customer_id=customer_id,
                    R=fb_data.get("rfms_r", 0.5) or 0.5,
                    F=fb_data.get("rfms_f", 0.0) or 0.0,
                    M=fb_data.get("rfms_m", 0.0) or 0.0,
                    S=fb_data.get("rfms_s", 0.5) or 0.5,
                    p_churn=fb_data.get("p_churn", 0.5) or 0.5,
                    sentiment_score_raw=sent_score_raw,
                    voucher_code=voucher_code if voucher_code else None,
                )
            elif voucher_code:
                update_customer_voucher(tenant_id, customer_id, voucher_code)

            # Xác định prize label theo voucher_code prefix (compat với gamification cũ)
            prize_id = "voucher" if voucher_result.voucher_issued else "chuc_may_man"
            prize_label = f"Voucher {voucher_code}" if voucher_code else "Chúc may mắn"

            update_feedback_gamification(
                tenant_id=tenant_id,
                feedback_id=feedback_id,
                customer_id=customer_id,
                prize=prize_id,
                voucher_code=voucher_code,
            )

    except Exception as e:
        logger.error(f"[Gamification] Lỗi cập nhật Firestore sau spin: {e}")
        # Không throw HTTP error — client đã spin xong, chỉ không update DB

    return {
        "voucher_issued": voucher_result.voucher_issued,
        "voucher_code": voucher_code,
        "message": message,
        "daily_remaining": voucher_result.daily_remaining,
        "reason": voucher_result.reason,
    }
