"""
Analyze Route — POST /api/v1/analyze
=====================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
Mục đích:
- Endpoint phân tích cảm xúc khía cạnh (ABSA) dựa trên Gemini LLM.
- Chuyển từ app riêng rẽ (api_main.py cũ) sang APIRouter để gộp chung với app chính.
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
    summary="Phân tích ABSA từ text",
    description="Nhận chuỗi văn bản và trả về các aspects cùng cảm xúc bằng Dynamic Few-Shot Prompting + Gemini LLM."
)
async def analyze_sentiment(request: AnalyzeRequest):
    """
    Endpoint nhận chuỗi văn bản (đánh giá của khách hàng) và trả về các aspects cùng cảm xúc.
    """
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
