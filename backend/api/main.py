"""
Sentrix Backend - FastAPI Application Entry Point
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.api.routes import health, feedback

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
# CORS — cho phép Frontend (web-client & dashboard của Việt) gọi được API.
# Origins sẽ được cấu hình cụ thể theo môi trường sau; hiện để * cho dev local.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # TODO: thu hẹp lại khi deploy production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Đăng ký các router
# ---------------------------------------------------------------------------
app.include_router(health.router, tags=["Health"])
app.include_router(feedback.router, prefix="/api/v1", tags=["Feedback"])
