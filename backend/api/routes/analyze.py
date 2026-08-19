"""
Analyze Route — POST /api/v1/analyze
=====================================
Author: Ngưyễn Thanh Tuyền (AI & Data Architect)
Mục đích:
- Endpoint phân tích cảm xúc khía cạnh (ABSA) dựa trên Gemini LLM.
- Chuyển từ app riêng rẽ (api_main.py cũ) sang APIRouter để gộp chung với app chính.

⚠️  DEPRECATED / INTERNAL ONLY (BUG E3, 2026-08-19)

Route này DÙNG SAI DOMAIN: categories đang dùng cho e-commerce
(GENERAL, PERFORMANCE, BATTERY, CAMERA, SCREEN, FEATURES, PRICE, SER&ACC, STORAGE)
Thay vì categories F&B (nhan_vien, mon_an, khong_gian, gia_ca, toc_do_phuc_vu, ve_sinh).

Sử dụng nội bộ (dev/debug) hoặc loại bỏ sau. KHÔNG dùng trong demo với giám khảo.
Endpoint chính đồng hành: POST /api/v1/feedback (dùng absa_llm.py với F&B categories).
"""

import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from backend.ai_pipeline.llM_few_shot_generator import SentimentAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter()

# Khởi tạo Analyzer (Singleton/Global level để dùng chung cho mọi requests)
analyzer = SentimentAnalyzer()

# --- Định nghĩa các Pydantic Models cho Request / Response ---

class AnalyzeRequest(BaseModel):
    text: str

class AspectItem(BaseModel):
    phrase: str
    category: str
    sentiment: str

class AnalyzeResponse(BaseModel):
    status: str
    aspects: List[AspectItem]
    error: Optional[str] = None


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="[DEPRECATED] Phân tích ABSA từ text (categories e-commerce — không dùng cho demo F&B)",
    description=(
        "⚠️ DEPRECATED: Route này dùng categories e-commerce (BATTERY, CAMERA, SCREEN...) "
        "không phù hợp với use case F&B. "
        "Dùng POST /api/v1/feedback để phân tích feedback F&B đúng domain."
    ),
    deprecated=True,
)
async def analyze_sentiment(request: AnalyzeRequest):
    """
    [DEPRECATED — internal/debug only]
    Endpoint nhận chuỗi văn bản và trả về aspects cùng cảm xúc.

    Lưu ý: Route này dùng categories E-COMMERCE (BATTERY, CAMERA, SCREEN...)
    thay vì categories F&B (nhan_vien, mon_an, khong_gian...). Kết quả sẽ
    không có ý nghĩa khi dùng cho feedback quán ăn/spa/phòng khám.
    Dùng POST /api/v1/feedback thay thế.
    """
    logger.warning(
        "[Analyze] ⚠️  Route DEPRECATED đang được gọi: /api/v1/analyze. "
        "Route này dùng categories e-commerce (BATTERY, CAMERA...) không phù hợp F&B. "
        "Dùng /api/v1/feedback thay thế."
    )
    user_input = request.text.strip()
    
    if not user_input:
        raise HTTPException(status_code=400, detail="Trường 'text' không được để trống.")
        
    try:
        # Gọi phương thức phân tích từ class SentimentAnalyzer
        result: Dict[str, Any] = analyzer.analyze_review(user_input)
        
        # Nếu LLM bị lỗi parse JSON bên trong lõi, nó sẽ trả về mảng rỗng kèm key "error"
        if "error" in result:
            logger.warning(f"Lỗi từ lõi ABSA: {result['error']}")
            return AnalyzeResponse(
                status="partial_success",
                aspects=[],
                error=f"LLM Processing Error: {result['error']}"
            )
            
        # Extract danh sách aspects
        aspects_raw = result.get("aspects", [])
        
        # Validate và cast dữ liệu vào Pydantic Model (tránh LLM hallucination sai format)
        aspects_validated: List[AspectItem] = []
        for item in aspects_raw:
            try:
                validated_item = AspectItem(
                    phrase=str(item.get("phrase", "")),
                    category=str(item.get("category", "")),
                    sentiment=str(item.get("sentiment", ""))
                )
                aspects_validated.append(validated_item)
            except Exception as item_err:
                logger.error(f"Lỗi validate aspect item: {item_err} (Item: {item})")
                
        return AnalyzeResponse(
            status="success",
            aspects=aspects_validated
        )

    except Exception as e:
        logger.error(f"Lỗi hệ thống khi xử lý yêu cầu: {e}")
        raise HTTPException(status_code=500, detail="Lỗi nội bộ máy chủ khi phân tích ABSA.")
