"""
Firestore Operations — CRUD Multi-Tenant
==========================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect) — hỗ trợ bởi Đoàn Hoàng Việt
Giai đoạn: 8 — Lưu Firestore multi-tenant thật

Các hàm trong module này thực hiện toàn bộ thao tác đọc/ghi Firestore
theo đúng schema đã thiết kế ở Giai đoạn 2 (backend/db/schema.md).

SCHEMA TÓM TẮT:
  tenants/{tenant_id}                         → thông tin doanh nghiệp
  tenants/{tenant_id}/feedbacks/{feedback_id} → 1 lượt phản hồi
  tenants/{tenant_id}/customers/{customer_id} → hồ sơ khách hàng (RFMS + churn)

CÁCH LY TENANT:
  Mọi hàm trong module này đều nhận tenant_id làm tham số bắt buộc đầu tiên.
  Đường dẫn Firestore luôn bắt đầu bằng tenants/{tenant_id}/...
  → Security Rules kiểm soát ở cấp path, đảm bảo không thể đọc chéo.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Any

from google.cloud.firestore_v1 import DocumentReference, DocumentSnapshot
from firebase_admin import firestore  # cần cho @firestore.transactional

from backend.db.firestore_client import get_firestore_client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers nội bộ
# ---------------------------------------------------------------------------

def _now_utc() -> datetime:
    """Thời điểm hiện tại theo UTC (timezone-aware)."""
    return datetime.now(timezone.utc)


def _hash_phone(phone_number: str) -> str:
    """
    Tạo customer_id từ số điện thoại bằng SHA-256 (16 ký tự đầu).

    Format chuẩn hoá: bỏ khoảng trắng, dấu gạch ngang, xử lý +84/0.
    customer_id = "cust_{sha256_hex[:16]}"

    Ẩn danh hoá một chiều: không thể khôi phục SĐT gốc từ customer_id.
    SĐT gốc KHÔNG được lưu trong Firestore.
    """
    # Chuẩn hoá SĐT về dạng +84...
    phone = phone_number.strip().replace(" ", "").replace("-", "")
    if phone.startswith("0"):
        phone = "+84" + phone[1:]
    elif not phone.startswith("+"):
        phone = "+84" + phone

    digest = hashlib.sha256(phone.encode("utf-8")).hexdigest()
    return f"cust_{digest[:16]}"


def _mask_phone(phone_number: str) -> str:
    """
    Tạo SĐT hiển thị dạng masked: "0901234567" → "090****567"
    Bảo vệ quyền riêng tư khách hàng trên Dashboard.
    """
    phone = phone_number.strip().replace(" ", "")
    if len(phone) < 7:
        return "***"
    return phone[:3] + "****" + phone[-3:]


def _sentiment_to_risk_level(p_churn: float) -> str:
    """Chuyển P_churn sang nhãn risk_level cho field churn_risk_level."""
    if p_churn < 0.50:
        return "low"
    elif p_churn < 0.85:
        return "medium"
    else:
        return "high"


# ---------------------------------------------------------------------------
# Ghi feedback
# ---------------------------------------------------------------------------

def save_feedback(
    tenant_id: str,
    feedback_data: dict[str, Any],
) -> str:
    """
    Lưu 1 lượt phản hồi khách hàng vào Firestore.

    Path: tenants/{tenant_id}/feedbacks/{auto_id}

    Args:
        tenant_id: ID của doanh nghiệp (tenant).
        feedback_data: dict chứa dữ liệu feedback đã xử lý qua toàn bộ pipeline.
                       Xem schema.md để biết các field bắt buộc.
                       Sẽ được merge với timestamp server-side (không tin client).

    Returns:
        str: feedback_id (Firestore auto-generated document ID).

    Raises:
        Exception: Lỗi Firestore (network, permissions, ...).
    """
    db = get_firestore_client()

    # Đảm bảo có timestamp server-side (không tin timestamp từ client)
    doc_data = {
        **feedback_data,
        "timestamp": _now_utc(),
        "processing_status": feedback_data.get("processing_status", "done"),
    }

    # Tạo document với auto-generated ID
    tenant_ref = db.collection("tenants").document(tenant_id)
    feedback_ref = tenant_ref.collection("feedbacks").document()
    feedback_id = feedback_ref.id

    # Lưu lại feedback_id vào chính document đó (tiện truy vấn sau)
    doc_data["feedback_id"] = feedback_id

    feedback_ref.set(doc_data)

    logger.info(
        f"[Firestore] Lưu feedback thành công: "
        f"tenants/{tenant_id}/feedbacks/{feedback_id}"
    )
    return feedback_id


def update_feedback_gamification(
    tenant_id: str,
    feedback_id: str,
    customer_id: str,
    prize: str,
    voucher_code: str,
) -> None:
    """
    Cập nhật dữ liệu gamification (số điện thoại / customer_id, giải thưởng)
    vào document feedback hiện có.
    """
    db = get_firestore_client()
    feedback_ref = db.collection("tenants").document(tenant_id).collection("feedbacks").document(feedback_id)
    
    # Kiểm tra xem feedback có tồn tại không
    if not feedback_ref.get().exists:
        raise ValueError(f"Feedback {feedback_id} không tồn tại")
        
    feedback_ref.update({
        "customer_id": customer_id,
        "gamification_prize": prize,
        "gamification_voucher": voucher_code,
        "gamification_updated_at": _now_utc()
    })
    
    logger.info(
        f"[Firestore] Đã cập nhật voucher {voucher_code} cho feedback {feedback_id}"
    )

# ---------------------------------------------------------------------------
# Quản lý customer (get-or-create pattern)
# ---------------------------------------------------------------------------

def get_or_create_customer(
    tenant_id: str,
    phone_number: str,
) -> dict[str, Any]:
    """
    Lấy hoặc tạo mới hồ sơ khách hàng theo SĐT.

    Path: tenants/{tenant_id}/customers/{customer_id}

    Nếu khách hàng chưa tồn tại (lần đầu gửi feedback) → tạo document mới
    với các giá trị mặc định, rồi trả về.
    Nếu đã tồn tại → trả về document hiện tại (KHÔNG cập nhật RFMS ở đây,
    dùng update_customer_rfms() sau khi tính xong).

    Args:
        tenant_id:    ID của doanh nghiệp (tenant).
        phone_number: Số điện thoại khách hàng. Sẽ được hash thành customer_id.
                      SĐT GỐC KHÔNG được lưu vào Firestore.

    Returns:
        dict: Dữ liệu customer document (bao gồm customer_id).

    Raises:
        ValueError: phone_number rỗng.
        Exception: Lỗi Firestore.
    """
    if not phone_number or not phone_number.strip():
        raise ValueError("phone_number không được rỗng.")

    db = get_firestore_client()
    customer_id = _hash_phone(phone_number)
    phone_masked = _mask_phone(phone_number)

    customer_ref = (
        db.collection("tenants")
        .document(tenant_id)
        .collection("customers")
        .document(customer_id)
    )

    doc: DocumentSnapshot = customer_ref.get()

    if doc.exists:
        logger.debug(
            f"[Firestore] Customer tồn tại: "
            f"tenants/{tenant_id}/customers/{customer_id}"
        )
        return {"customer_id": customer_id, **doc.to_dict()}

    # --- Khách hàng mới: tạo document ---
    now = _now_utc()
    new_customer = {
        "customer_id":          customer_id,
        "phone_masked":         phone_masked,
        "first_seen_at":        now,
        "last_feedback_at":     now,
        "feedback_count":       0,          # sẽ tăng sau khi save_feedback
        "total_spending":       0.0,        # chưa có tích hợp POS
        "avg_sentiment_score":  0.5,        # neutral mặc định
        "rfms_r":               0.5,
        "rfms_f":               0.0,
        "rfms_m":               0.0,
        "rfms_s":               0.5,
        "p_churn":              0.5,        # unknown cho khách mới
        "churn_risk_level":     "medium",
        "zns_sent_at":          None,
        "zns_voucher_code":     None,
        "updated_at":           now,
    }
    customer_ref.set(new_customer)

    logger.info(
        f"[Firestore] Tạo customer mới: "
        f"tenants/{tenant_id}/customers/{customer_id} "
        f"(phone_masked={phone_masked})"
    )
    return new_customer


# ---------------------------------------------------------------------------
# Cập nhật RFMS + P_churn
# ---------------------------------------------------------------------------

def update_customer_rfms(
    tenant_id: str,
    customer_id: str,
    R: float,
    F: float,
    M: float,
    S: float,
    p_churn: float,
    sentiment_score_raw: float,
    recency_days: Optional[float] = None,
) -> None:
    """
    Cập nhật điểm RFMS và P_churn sau mỗi lần xử lý feedback.

    Dùng Firestore Transaction để đọc feedback_count hiện tại rồi tăng lên 1
    (tránh race condition nếu nhiều request cùng lúc).

    Args:
        tenant_id:          ID tenant.
        customer_id:        customer_id (đã hash, từ get_or_create_customer).
        R, F, M, S:         Điểm RFMS normalized [0,1] (từ rfms_calculator).
        p_churn:            Xác suất rời bỏ [0,1] (từ churn_model).
        sentiment_score_raw: Điểm cảm xúc raw từ Fusion [0,1] (để cập nhật avg).
        recency_days:       Số ngày kể từ lần cuối (để log, không lưu riêng).

    Raises:
        Exception: Lỗi Firestore (document không tồn tại, network, ...).
    """
    db = get_firestore_client()
    customer_ref = (
        db.collection("tenants")
        .document(tenant_id)
        .collection("customers")
        .document(customer_id)
    )

    @firestore.transactional
    def _update_in_transaction(transaction, ref: DocumentReference):
        snapshot: DocumentSnapshot = ref.get(transaction=transaction)

        if not snapshot.exists:
            logger.warning(
                f"[Firestore] Customer không tồn tại khi update RFMS: {customer_id} "
                f"— bỏ qua."
            )
            return

        current_data = snapshot.to_dict()
        old_feedback_count = current_data.get("feedback_count", 0)
        old_avg_sentiment = current_data.get("avg_sentiment_score", 0.5)

        # Cập nhật avg_sentiment_score dùng running average
        new_count = old_feedback_count + 1
        new_avg_sentiment = (
            (old_avg_sentiment * old_feedback_count + sentiment_score_raw) / new_count
        )

        now = _now_utc()
        transaction.update(ref, {
            "feedback_count":       new_count,
            "last_feedback_at":     now,
            "avg_sentiment_score":  round(new_avg_sentiment, 6),
            "rfms_r":               round(R, 6),
            "rfms_f":               round(F, 6),
            "rfms_m":               round(M, 6),
            "rfms_s":               round(S, 6),
            "p_churn":              round(p_churn, 6),
            "churn_risk_level":     _sentiment_to_risk_level(p_churn),
            "updated_at":           now,
        })

    transaction = db.transaction()
    _update_in_transaction(transaction, customer_ref)

    logger.info(
        f"[Firestore] Cập nhật RFMS: tenants/{tenant_id}/customers/{customer_id} "
        f"| R={R:.4f}, F={F:.4f}, M={M:.4f}, S={S:.4f} "
        f"| P_churn={p_churn:.4f} ({_sentiment_to_risk_level(p_churn)})"
    )


# ---------------------------------------------------------------------------
# Đọc tenant config (để lấy churn_threshold tuỳ chỉnh)
# ---------------------------------------------------------------------------

def get_tenant_config(tenant_id: str) -> Optional[dict[str, Any]]:
    """
    Đọc cấu hình tenant (bao gồm churn_threshold tuỳ chỉnh nếu có).

    Returns:
        dict nếu tenant tồn tại, None nếu không tìm thấy.
    """
    db = get_firestore_client()
    doc: DocumentSnapshot = (
        db.collection("tenants").document(tenant_id).get()
    )
    if doc.exists:
        return doc.to_dict()
    logger.warning(f"[Firestore] Tenant không tồn tại: {tenant_id}")
    return None


# ---------------------------------------------------------------------------
# Helpers công khai
# ---------------------------------------------------------------------------

def get_customer_id_from_phone(phone_number: str) -> str:
    """
    Trả về customer_id từ SĐT mà không cần kết nối Firestore.
    Hữu ích khi cần biết customer_id trước khi query.
    """
    return _hash_phone(phone_number)
