"""
Sentrix Backend - FastAPI Application Entry Point
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.api.routes import health, feedback, analyze

# Load biến môi trường từ file .env (nếu chạy local)
load_dotenv()

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
