"""
Tenant Config Routes — GET/PUT /api/v1/tenants/{tenant_id}/voucher-config
=========================================================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
Module 1 — Lớp 4: API quản lý cấu hình voucher budget

MỤC ĐÍCH:
  Cho phép chủ quán (qua Dashboard) đọc và cập nhật cấu hình phát voucher.
  Thay đổi có hiệu lực ngay, không cần restart backend.

  Dashboard sẽ gọi:
    GET  /api/v1/tenants/{tenant_id}/voucher-config  → đọc config hiện tại
    PUT  /api/v1/tenants/{tenant_id}/voucher-config  → cập nhật daily_limit / win_rate

LƯU Ý:
  Hiện tại chưa có auth middleware (Firebase ID token verification) vì MVP.
  TODO: Thêm verify_firebase_token dependency khi hoàn thiện auth system.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Path, status
from pydantic import BaseModel, field_validator

from backend.services.voucher_budget_service import get_voucher_config, set_voucher_config

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class VoucherConfigResponse(BaseModel):
    tenant_id: str
    daily_voucher_limit: int
    win_rate_percent: float
    vouchers_issued_today: int
    last_reset_date: str


class VoucherConfigUpdateRequest(BaseModel):
    daily_voucher_limit: Optional[int] = None
    win_rate_percent: Optional[float] = None

    @field_validator("daily_voucher_limit")
    @classmethod
    def validate_limit(cls, v):
        if v is not None and v < 0:
            raise ValueError("daily_voucher_limit phải >= 0")
        return v

    @field_validator("win_rate_percent")
    @classmethod
    def validate_rate(cls, v):
        if v is not None and not (0.0 <= v <= 100.0):
            raise ValueError("win_rate_percent phải trong khoảng [0, 100]")
        return v


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.get(
    "/tenants/{tenant_id}/voucher-config",
    response_model=VoucherConfigResponse,
    summary="Đọc cấu hình voucher budget của tenant",
)
async def get_voucher_config_endpoint(
    tenant_id: str = Path(..., description="ID của tenant"),
):
    """Đọc cấu hình phát voucher: daily_limit, win_rate, số đã phát hôm nay."""
    logger.info(f"[TenantConfig] GET voucher-config: {tenant_id}")
    try:
        config = get_voucher_config(tenant_id)
        return VoucherConfigResponse(
            tenant_id=tenant_id,
            daily_voucher_limit=int(config.get("daily_voucher_limit", 50)),
            win_rate_percent=float(config.get("win_rate_percent", 30.0)),
            vouchers_issued_today=int(config.get("vouchers_issued_today", 0)),
            last_reset_date=str(config.get("last_reset_date", "")),
        )
    except Exception as e:
        logger.error(f"[TenantConfig] Lỗi đọc config: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không đọc được cấu hình voucher. Vui lòng thử lại.",
        )


@router.put(
    "/tenants/{tenant_id}/voucher-config",
    response_model=VoucherConfigResponse,
    summary="Cập nhật cấu hình voucher budget của tenant",
    description=(
        "Chủ quán dùng endpoint này để chỉnh daily_voucher_limit và win_rate_percent. "
        "Thay đổi có hiệu lực ngay cho các lượt phản hồi tiếp theo."
    ),
)
async def update_voucher_config_endpoint(
    body: VoucherConfigUpdateRequest,
    tenant_id: str = Path(..., description="ID của tenant"),
):
    """
    Cập nhật cấu hình phát voucher.
    Chỉ cập nhật field nào được truyền vào (partial update).
    """
    logger.info(f"[TenantConfig] PUT voucher-config: {tenant_id} → {body.model_dump(exclude_none=True)}")

    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cần ít nhất 1 field để cập nhật: daily_voucher_limit hoặc win_rate_percent.",
        )

    try:
        set_voucher_config(tenant_id, updates)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"[TenantConfig] Lỗi cập nhật config: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Không lưu được cấu hình. Vui lòng thử lại.",
        )

    # Đọc lại config sau khi cập nhật để trả về giá trị mới nhất
    config = get_voucher_config(tenant_id)
    return VoucherConfigResponse(
        tenant_id=tenant_id,
        daily_voucher_limit=int(config.get("daily_voucher_limit", 50)),
        win_rate_percent=float(config.get("win_rate_percent", 30.0)),
        vouchers_issued_today=int(config.get("vouchers_issued_today", 0)),
        last_reset_date=str(config.get("last_reset_date", "")),
    )
