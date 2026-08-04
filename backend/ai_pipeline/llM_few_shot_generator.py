"""
LLM Few-Shot Generator cho ABSA (Dynamic Few-Shot Prompting)
============================================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
Mục đích:
- Sử dụng Google Gemini 1.5 Flash để phân tích ABSA.
- Load dữ liệu mẫu đã làm sạch (cleaned_absa_data.json).
- Lựa chọn động (dynamic) một số ví dụ từ tập dữ liệu mẫu.
- Chèn vào System Prompt và gọi API Gemini để trả về JSON chuẩn xác.
"""

import os
import json
import random
import logging
from typing import List, Dict, Any
import google.generativeai as genai

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Lõi xử lý ABSA sử dụng Dynamic Few-Shot Prompting với Gemini LLM.
    """
    
    def __init__(self, data_filepath: str = None) -> None:
        """
        Khởi tạo Analyzer, load dữ liệu mẫu để làm Few-Shot.
        """
        # Cấu hình Gemini API
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("Chưa thiết lập GEMINI_API_KEY trong môi trường!")
        
        genai.configure(api_key=api_key)
        
        # Sử dụng model Gemini thông qua biến môi trường (mặc định: gemini-3.1-flash-lite)
        model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-3.1-flash-lite")
        self.model = genai.GenerativeModel(model_name)
        
        # Load dữ liệu sạch
        if data_filepath is None:
            data_filepath = os.path.join(os.path.dirname(__file__), "cleaned_absa_data.json")
            
        self.examples_data: List[Dict[str, Any]] = []
        
        if os.path.exists(data_filepath):
            try:
                with open(data_filepath, "r", encoding="utf-8") as f:
                    self.examples_data = json.load(f)
                logger.info(f"Đã load {len(self.examples_data)} câu ví dụ từ {data_filepath}")
            except Exception as e:
                logger.error(f"Lỗi khi load dữ liệu: {e}")
        else:
            logger.error(f"Không tìm thấy file dữ liệu: {data_filepath}")


    def get_dynamic_examples(self, user_input: str, k: int = 5) -> str:
        """
        Lấy động k ví dụ từ tập dữ liệu sạch.
        Hiện tại sử dụng Random Sampling. (Trong tương lai có thể nâng cấp lên Semantic Search/Vector DB).
        
        Args:
            user_input: Chuỗi review cần phân tích (để dành cho thuật toán similarity sau này)
            k: Số lượng ví dụ cần lấy
            
        Returns:
            Chuỗi string đã format chứa các ví dụ Few-Shot.
        """
        if not self.examples_data:
            return ""
            
        # Random choice k examples
        sampled = random.sample(self.examples_data, min(k, len(self.examples_data)))
        
        examples_str = ""
        for i, ex in enumerate(sampled, 1):
            review = ex.get("review", "")
            aspects = ex.get("aspects", [])
            
            # Format output dưới dạng JSON string để model học theo
            aspects_json = json.dumps(aspects, ensure_ascii=False)
            
            examples_str += f"Ví dụ {i}:\n"
            examples_str += f"Input: {review}\n"
            examples_str += f"Output JSON: {aspects_json}\n\n"
            
        return examples_str


    def analyze_review(self, user_input: str) -> Dict[str, Any]:
        """
        Gửi input của user kèm theo Few-Shot Prompt cho Gemini để trích xuất ABSA.
        
        Args:
            user_input: Phản hồi của khách hàng
            
        Returns:
            Dictionary (JSON) chứa danh sách các aspects, category và sentiment.
        """
        if not user_input or not user_input.strip():
            return {"aspects": []}
            
        # Lấy các ví dụ động
        few_shot_examples = self.get_dynamic_examples(user_input, k=3)
        
        # Xây dựng System Prompt hoàn chỉnh
        prompt = f"""Bạn là một trợ lý AI chuyên nghiệp về Aspect-Based Sentiment Analysis (ABSA) cho ngôn ngữ tiếng Việt.
Nhiệm vụ của bạn là đọc một lời đánh giá (review) của khách hàng và trích xuất các khía cạnh (aspects), phân loại (category) và cảm xúc (sentiment).

Các Category hợp lệ bao gồm: GENERAL, PERFORMANCE, BATTERY, CAMERA, DESIGN, SCREEN, FEATURES, PRICE, SER&ACC, STORAGE.
Các Sentiment hợp lệ bao gồm: POSITIVE, NEGATIVE, NEUTRAL.

{few_shot_examples}
Yêu cầu bắt buộc:
1. Trích xuất chính xác cụm từ (phrase) từ câu gốc thể hiện khía cạnh đó.
2. Phân loại Category và Sentiment cho cụm từ đó.
3. CHỈ TRẢ VỀ một mảng JSON (Array) đúng chuẩn, không kèm theo bất kỳ văn bản giải thích nào khác (không có ```json format block). Nếu không tìm thấy, trả về mảng rỗng [].

Input thực tế: {user_input}
Output JSON:"""

        try:
            # Gọi API Gemini
            response = self.model.generate_content(prompt)
            output_text = response.text.strip()
            
            # Parse JSON từ kết quả trả về của LLM
            # Có thể có trường hợp LLM bao bọc code block ```json ... ```
            if output_text.startswith("```json"):
                output_text = output_text[7:]
            if output_text.endswith("```"):
                output_text = output_text[:-3]
                
            aspects_list = json.loads(output_text.strip())
            
            return {"aspects": aspects_list}
            
        except json.JSONDecodeError as e:
            logger.error(f"Lỗi parse JSON từ LLM output: {e}\nOutput LLM: {output_text}")
            return {"aspects": [], "error": "LLM returned invalid JSON"}
            
        except Exception as e:
            logger.error(f"Lỗi khi gọi Gemini API: {e}")
            return {"aspects": [], "error": str(e)}


if __name__ == "__main__":
    # Test script nhanh
    analyzer = SentimentAnalyzer()
    test_text = "Phục vụ tốt, món ăn ngon nhưng không gian hơi ồn ào và chật hẹp."
    print("Testing với câu:", test_text)
    result = analyzer.analyze_review(test_text)
    print("Kết quả:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
