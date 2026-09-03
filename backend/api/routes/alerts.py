"""
alerts.py — REST API cho Staff Alerts
======================================
Milestone 4: Staff Alert CRUD

Endpoints:
  GET  /api/v1/tenants/{tenant_id}/alerts
  POST /api/v1/tenants/{tenant_id}/alerts          (internal, từ feedback pipeline)
  PATCH /api/v1/tenants/{tenant_id}/alerts/{alert_id}/acknowledge
  PATCH /api/v1/tenants/{tenant_id}/alerts/{alert_id}/resolve
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.db.firestore_ops import (
    create_alert,
    get_alerts,
    acknowledge_alert,
    resolve_alert,
    ALERT_STATUS_CREATED,
    ALERT_STATUS_ACKNOWLEDGED,
    ALERT_STATUS_RESOLVED,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tenants/{tenant_id}/alerts", tags=["alerts"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class CreateAlertRequest(BaseModel):
    feedback_id: str
    location:    str
    transcript:  str
    intent:      str = "SUPPORT_REQUEST"


class AlertResponse(BaseModel):
    alert_id:        str
    feedback_id:     str
    location:        str
    status:          str
    intent:          str
    transcript:      str
    created_at:      Optional[str] = None
    acknowledged_at: Optional[str] = None
    resolved_at:     Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "",
    status_code=201,
    summary="Tạo alert mới (SUPPORT_REQUEST từ feedback pipeline)",
)
async def post_alert(tenant_id: str, body: CreateAlertRequest):
    """
    Tạo staff alert khi khách có yêu cầu hỗ trợ (SUPPORT_REQUEST).
    Thường được gọi nội bộ từ POST /api/v1/feedback sau khi intent classify.
    """
    try:
        alert_id = create_alert(
            tenant_id=tenant_id,
            feedback_id=body.feedback_id,
            location=body.location,
            transcript=body.transcript,
            intent=body.intent,
        )
        return {"alert_id": alert_id, "status": "CREATED"}
    except Exception as e:
        logger.error(f"[Alert API] Loi tao alert: {e}")
        raise HTTPException(status_code=500, detail=f"Loi tao alert: {e}")


@router.get(
    "",
    summary="Lấy danh sách alerts của tenant",
)
async def list_alerts(
    tenant_id: str,
    status: Optional[str] = Query(None, description="Lọc theo status: CREATED|ACKNOWLEDGED|RESOLVED"),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Lấy danh sách alerts, mới nhất trước.
    Dashboard dùng endpoint này để hiện realtime alerts.
    """
    valid_statuses = {ALERT_STATUS_CREATED, ALERT_STATUS_ACKNOWLEDGED, ALERT_STATUS_RESOLVED, None}
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"status không hợp lệ: {status}")

    try:
        alerts = get_alerts(tenant_id=tenant_id, limit=limit, status_filter=status)
        # Convert datetime -> ISO string
        for a in alerts:
            for field in ("created_at", "acknowledged_at", "resolved_at"):
                if a.get(field) and hasattr(a[field], "isoformat"):
                    a[field] = a[field].isoformat()
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        logger.error(f"[Alert API] Loi lay alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Loi lay alerts: {e}")


@router.patch(
    "/{alert_id}/acknowledge",
    summary="Nhân viên ghi nhận alert",
)
async def patch_acknowledge(tenant_id: str, alert_id: str):
    """Nhân viên ghi nhận alert → status ACKNOWLEDGED."""
    try:
        ok = acknowledge_alert(tenant_id=tenant_id, alert_id=alert_id)
        if not ok:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} khong ton tai")
        return {"alert_id": alert_id, "status": ALERT_STATUS_ACKNOWLEDGED}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Alert API] Loi acknowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/{alert_id}/resolve",
    summary="Nhân viên xử lý xong alert",
)
async def patch_resolve(tenant_id: str, alert_id: str):
    """Nhân viên đã xử lý xong → status RESOLVED."""
    try:
        ok = resolve_alert(tenant_id=tenant_id, alert_id=alert_id)
        if not ok:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} khong ton tai")
        return {"alert_id": alert_id, "status": ALERT_STATUS_RESOLVED}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Alert API] Loi resolve: {e}")
        raise HTTPException(status_code=500, detail=str(e))
