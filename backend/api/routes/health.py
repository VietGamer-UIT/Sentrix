"""
Health Check Endpoint
---------------------
GET /health  →  {"status": "ok", "version": "0.1.0"}

Dùng để:
- Kiểm tra server đang sống (ping từ Postman/browser).
- Render.com dùng để health-check container trước khi route traffic vào.
- Việt dùng để xác nhận backend đã deploy xong trước khi frontend gọi API thật.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    message: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Trả về trạng thái hoạt động của server. Dùng để ping xem backend có sống không.",
)
async def health_check() -> HealthResponse:
    """
    Endpoint kiểm tra server còn sống.

    Returns:
        HealthResponse: JSON với status "ok" và version hiện tại.
    """
    return HealthResponse(
        status="ok",
        version="0.1.0",
        message="Sentrix Backend is running! 🚀",
    )
