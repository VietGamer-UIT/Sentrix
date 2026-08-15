import logging
import random
from fastapi import APIRouter, Form, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from backend.db.firestore_ops import update_feedback_gamification, get_or_create_customer, update_customer_rfms

logger = logging.getLogger(__name__)

router = APIRouter()

SPIN_PRIZES = [
    {
        "id": "giam_10",
        "label": "Giảm 10%",
        "probability": 0.35,
        "template": "SENTRIX-10-{phone_suffix}"
    },
    {
        "id": "giam_20",
        "label": "Giảm 20%",
        "probability": 0.20,
        "template": "SENTRIX-20-{phone_suffix}"
    },
    {
        "id": "tang_banh",
        "label": "Tặng bánh",
        "probability": 0.15,
        "template": "SENTRIX-BANH-{phone_suffix}"
    },
    {
        "id": "giam_5",
        "label": "Giảm 5%",
        "probability": 0.20,
        "template": "SENTRIX-5-{phone_suffix}"
    },
    {
        "id": "uong_mien_phi",
        "label": "Voucher uống miễn phí lần sau",
        "probability": 0.05,
        "template": "SENTRIX-FREE-{phone_suffix}"
    },
    {
        "id": "chuc_may_man",
        "label": "Chúc may mắn",
        "probability": 0.05,
        "template": None
    }
]

@router.post("/spin")
async def spin_gamification(
    tenant_id: str = Form(...),
    customer_phone: str = Form(...),
    feedback_id: Optional[str] = Form(None)
):
    """
    Xử lý Vòng quay may mắn sau khi khách hàng đã gửi feedback.
    1. Random phần thưởng theo tỷ lệ.
    2. Cập nhật Số điện thoại + Phần thưởng vào Feedback Document.
    3. Tạo/Cập nhật Customer Document nếu cần.
    """
    logger.info(f"[Gamification] Spin request: tenant={tenant_id}, phone={customer_phone[-4:]}, feedback={feedback_id}")

    # Random prize
    rand = random.random()
    cumulative = 0.0
    selected_prize = SPIN_PRIZES[-1]

    for prize in SPIN_PRIZES:
        cumulative += prize["probability"]
        if rand < cumulative:
            selected_prize = prize
            break

    phone_suffix = customer_phone[-4:].upper() if len(customer_phone) >= 4 else "0000"
    
    voucher_code = ""
    if selected_prize["template"]:
        voucher_code = selected_prize["template"].format(phone_suffix=phone_suffix)
        
    message = f"Chúc mừng bạn nhận được: {selected_prize['label']}!" if voucher_code else "Cảm ơn bạn đã tham gia! Chúc bạn may mắn lần sau."

    try:
        # Lấy/tạo customer
        customer_doc = get_or_create_customer(tenant_id, customer_phone)
        customer_id = customer_doc["customer_id"]

        # Cập nhật thông tin vào Feedback nếu có feedback_id
        if feedback_id:
            update_feedback_gamification(
                tenant_id=tenant_id,
                feedback_id=feedback_id,
                customer_id=customer_id,
                prize=selected_prize["id"],
                voucher_code=voucher_code
            )
        
    except Exception as e:
        logger.error(f"[Gamification] Lỗi khi xử lý spin: {e}")
        # Không throw HTTP error để client vẫn nhận được voucher UI dù Firestore lỗi
        
    return {
        "prize": selected_prize["id"],
        "prize_label": selected_prize["label"],
        "voucher_code": voucher_code,
        "message": message
    }
