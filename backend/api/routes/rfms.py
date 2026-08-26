"""
RFMS Recompute Route — POST /api/v1/rfms/recompute
====================================================
Author: Đoàn Hoàng Việt (Việt Gamer)
Module 3 — RFMS Pipeline API

MỤC ĐÍCH:
  Cho phép gọi batch recompute RFMS + p_churn cho toàn bộ customers của tenant.
  Hữu ích cho:
    - Demo live trước giám khảo (chạy pipeline thật thay vì số cứng)
    - Cron job hàng đêm (gọi qua scripts/batch_rfms.py)
    - Debug / test pipeline

ENDPOINTS:
  POST /api/v1/rfms/recompute
    Body: { "tenant_id": "...", "force_synthetic": false }
    → Chạy RFMS pipeline cho tenant, trả về kết quả tổng hợp

  GET /api/v1/rfms/status/{tenant_id}
    → Lấy thống kê nhanh về RFMS của tenant (không recompute)
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class RFMSRecomputeRequest(BaseModel):
    """Body cho POST /rfms/recompute."""
    tenant_id: str
    force_synthetic: bool = False  # True = ép dùng synthetic LR dù ít data


class RFMSRecomputeResponse(BaseModel):
    """Response sau khi chạy pipeline."""
    tenant_id: str
    mode: str                        # "A" (heuristic) | "B" (synthetic LR) | "C" (real data LR)
    mode_label: str                  # Mô tả chế độ cho giám khảo
    n_customers: int
    n_updated: int
    churn_rate: float                # Tỷ lệ khách high-risk (p_churn > 0.85)
    model_coefficients: Optional[dict]  # Hệ số LR (None nếu chế độ A)
    errors: list[str]
    message: str


MODE_LABELS = {
    "A": "Heuristic cold-start — dùng hệ số giả định domain knowledge (chưa đủ data train)",
    "B": "Synthetic Logistic Regression — train trên dữ liệu giả lập có kiểm soát (demo mode)",
    "C": "Real Data Logistic Regression — train trên dữ liệu thật có nhãn churned",
    "none": "Không có khách hàng nào để tính",
    "error": "Pipeline thất bại",
}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/recompute",
    response_model=RFMSRecomputeResponse,
    summary="Recompute RFMS + p_churn cho toàn bộ customers của tenant",
)
async def recompute_rfms(req: RFMSRecomputeRequest):
    """
    Chạy RFMS batch pipeline cho một tenant.

    Tự động chọn chế độ:
    - Chế độ A (Heuristic): ít data → dùng hệ số giả định
    - Chế độ B (Synthetic LR): đủ data hoặc force_synthetic=true → train scikit-learn

    ⚠️ Chú ý: Chạy pipeline này có thể mất vài giây nếu tenant có nhiều customers.
    """
    if not req.tenant_id or not req.tenant_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id không được để trống.",
        )

    tenant_id = req.tenant_id.strip()
    logger.info(
        f"[RFMS Route] Nhận yêu cầu recompute: tenant={tenant_id}, "
        f"force_synthetic={req.force_synthetic}"
    )

    try:
        from backend.rfms_model.rfms_pipeline import compute_rfms_for_tenant
        result = compute_rfms_for_tenant(
            tenant_id=tenant_id,
            force_synthetic=req.force_synthetic,
            update_firestore=True,
        )
    except ImportError as e:
        # scikit-learn chưa cài
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"scikit-learn chưa được cài đặt: {e}. "
                "Chạy: pip install scikit-learn>=1.3.0"
            ),
        )
    except Exception as e:
        logger.error(f"[RFMS Route] Pipeline thất bại: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RFMS pipeline thất bại: {type(e).__name__}: {e}",
        )

    mode = result.get("mode", "A")
    n_errors = len(result.get("errors", []))

    if n_errors > 0:
        logger.warning(
            f"[RFMS Route] Pipeline hoàn tất với {n_errors} lỗi: "
            f"{result['errors'][:3]}"
        )

    return RFMSRecomputeResponse(
        tenant_id=tenant_id,
        mode=mode,
        mode_label=MODE_LABELS.get(mode, mode),
        n_customers=result.get("n_customers", 0),
        n_updated=result.get("n_updated", 0),
        churn_rate=result.get("churn_rate", 0.0),
        model_coefficients=result.get("model_coefficients"),
        errors=result.get("errors", [])[:10],  # Giới hạn 10 lỗi đầu
        message=(
            f"Pipeline {mode} hoàn tất: "
            f"{result.get('n_updated', 0)}/{result.get('n_customers', 0)} customers cập nhật, "
            f"{result.get('churn_rate', 0):.1%} high-risk. "
            + (f"({n_errors} lỗi — xem field errors)" if n_errors else "Không có lỗi.")
        ),
    )


@router.get(
    "/status/{tenant_id}",
    summary="Lấy thống kê RFMS nhanh của tenant (không recompute)",
)
async def get_rfms_status(tenant_id: str):
    """
    Đọc thống kê RFMS hiện tại của tenant từ Firestore (không chạy lại pipeline).
    Trả về số lượng khách theo risk_level và churn_rate tổng.
    """
    if not tenant_id or not tenant_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id không được để trống.",
        )

    try:
        from backend.db.firestore_client import get_firestore_client
        db = get_firestore_client()
        cust_ref = (
            db.collection("tenants").document(tenant_id.strip())
            .collection("customers")
        )
        docs = list(cust_ref.stream())

        total = len(docs)
        risk_counts = {"high": 0, "medium": 0, "low": 0, "unknown": 0}
        p_churn_values = []

        for doc in docs:
            d = doc.to_dict() or {}
            risk = d.get("churn_risk_level", "unknown")
            if risk in risk_counts:
                risk_counts[risk] += 1
            else:
                risk_counts["unknown"] += 1
            if d.get("p_churn") is not None:
                p_churn_values.append(float(d["p_churn"]))

        avg_p_churn = sum(p_churn_values) / len(p_churn_values) if p_churn_values else 0.0

        return {
            "tenant_id": tenant_id,
            "total_customers": total,
            "risk_distribution": risk_counts,
            "avg_p_churn": round(avg_p_churn, 4),
            "high_risk_rate": round(risk_counts["high"] / total, 4) if total else 0.0,
        }

    except Exception as e:
        logger.error(f"[RFMS Route] Status thất bại: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi đọc RFMS status: {e}",
        )
