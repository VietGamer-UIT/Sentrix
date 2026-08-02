"""
FastAPI Wrapper cho ABSA (Proof of Concept)
===================================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
Mục đích:
- Khởi tạo app FastAPI cung cấp endpoint POST /api/v1/analyze.
- Tích hợp lõi phân tích ABSA từ llM_few_shot_generator.py.
- Bắt lỗi khi LLM trả về kết quả không mong muốn hoặc fail (Hallucination).
"""

import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import class SentimentAnalyzer từ file bên cạnh
# Lưu ý import path tương đối với CWD
from backend.ai_pipeline.llM_few_shot_generator import SentimentAnalyzer

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Khởi tạo FastAPI App
app = FastAPI(
    title="ABSA LLM API",
    description="Endpoint phân tích cảm xúc khía cạnh (ABSA) dựa trên Gemini LLM.",
    version="1.0.0"
)

# CORS Middleware (cho phép gọi từ mọi origin trong giai đoạn POC)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze_sentiment(request: AnalyzeRequest):
    """
    Endpoint nhận chuỗi văn bản (đánh giá của khách hàng) và trả về các aspects cùng cảm xúc.
    Sử dụng Dynamic Few-Shot Prompting + Gemini LLM.
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
        # Bắt lỗi không mong muốn, trả về 500
        raise HTTPException(status_code=500, detail="Lỗi nội bộ máy chủ khi phân tích ABSA.")


if __name__ == "__main__":
    # Để chạy bằng code Python: `python backend/ai_pipeline/api_main.py`
    import uvicorn
    uvicorn.run("backend.ai_pipeline.api_main:app", host="0.0.0.0", port=8001, reload=True)
