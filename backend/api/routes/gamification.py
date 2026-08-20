import logging
import random
from fastapi import APIRouter, Form, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from backend.db.firestore_client import get_firestore_client
from backend.db.firestore_ops import update_feedback_gamification, get_or_create_customer, update_customer_rfms, update_customer_voucher

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
            # Kiểm tra xem feedback đã được link với customer chưa
            db = get_firestore_client()
            feedback_ref = db.collection("tenants").document(tenant_id).collection("feedbacks").document(feedback_id)
            feedback_snap = feedback_ref.get()
            
            already_linked = False
            if feedback_snap.exists:
                fb_data = feedback_snap.to_dict()
                already_linked = bool(fb_data.get("customer_id"))
                
                # Nếu chưa link, đồng bộ RFMS từ feedback sang customer mới tạo
                if not already_linked:
                    # Lấy sentiment_score, đổi sang thang [0,1] để làm sentiment_score_raw
                    sent_score = fb_data.get("sentiment_score", 0.0)
                    sent_score_raw = (sent_score + 1.0) / 2.0
                    
                    update_customer_rfms(
                        tenant_id=tenant_id,
                        customer_id=customer_id,
                        R=fb_data.get("rfms_r", 0.5),
                        F=fb_data.get("rfms_f", 0.0),
                        M=fb_data.get("rfms_m", 0.0),
                        S=fb_data.get("rfms_s", 0.5),
                        p_churn=fb_data.get("p_churn", 0.5),
                        sentiment_score_raw=sent_score_raw,
                        voucher_code=voucher_code
                    )
                elif voucher_code:
                    # Nếu đã link từ trước, chỉ cập nhật thêm mã voucher
                    update_customer_voucher(
                        tenant_id=tenant_id,
                        customer_id=customer_id,
                        voucher_code=voucher_code
                    )

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
