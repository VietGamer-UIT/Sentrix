"""
Sentrix Backend - FastAPI Application Entry Point
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
"""

import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

from backend.api.routes import health, feedback, analyze, gamification, otp, tenant_config

# Load biến môi trường từ file .env (nếu chạy local)
load_dotenv()

# Setup logging cho ứng dụng để tương thích với Uvicorn trên Render
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sentrix Backend API",
    description=(
        "AI-Powered Multimodal Customer Experience Analytics Platform.\n"
        "Xử lý phản hồi giọng nói + văn bản từ khách hàng, "
        "phân tích cảm xúc (ABSA), tính toán churn risk (RFMS), "
        "và cảnh báo qua Zalo ZNS."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Bắt và log chi tiết lỗi 422 Unprocessable Entity (thường bị FastAPI ẩn)."""
    logger.warning(f"Validation error cho {request.method} {request.url}: {exc.errors()}")
    # Vẫn trả về 422 mặc định của FastAPI, nhưng đã có log để debug
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

# ---------------------------------------------------------------------------
# CORS
# Mặc định: whitelist cứng các domain production + localhost dev.
# Override: đặt biến ALLOWED_ORIGINS trên Render dashboard (comma-separated)
#   VD: ALLOWED_ORIGINS=https://sentrix-coral.vercel.app,https://sentrix-dashboard-eta.vercel.app
# ---------------------------------------------------------------------------
_DEFAULT_ORIGINS = [
    # Production — Vercel deployments
    "https://sentrix-coral.vercel.app",
    "https://sentrix-dashboard-eta.vercel.app",
    # Dev local
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

_env_origins = os.getenv("ALLOWED_ORIGINS", "")
_extra_origins = [o.strip() for o in _env_origins.split(",") if o.strip()]
CORS_ORIGINS = list(dict.fromkeys(_DEFAULT_ORIGINS + _extra_origins))  # deduplicate

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Đăng ký các router
# ---------------------------------------------------------------------------
app.include_router(health.router, tags=["Health"])
app.include_router(feedback.router, prefix="/api/v1", tags=["Feedback"])
app.include_router(analyze.router, prefix="/api/v1", tags=["ABSA Analysis"])
app.include_router(gamification.router, prefix="/api/v1/gamification", tags=["Gamification"])
app.include_router(otp.router, prefix="/api/v1", tags=["OTP"])
app.include_router(tenant_config.router, prefix="/api/v1", tags=["Tenant Config"])
