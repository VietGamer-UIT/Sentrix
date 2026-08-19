"""
ABSA (Aspect-Based Sentiment Analysis) via LLM — Sentrix
==========================================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
Giai đoạn: 6A — Phân tích ABSA bằng Gemini Flash-Lite

MỤC ĐÍCH:
  Đưa văn bản phản hồi của khách hàng (từ Whisper STT hoặc gõ tay) vào LLM
  để bóc tách từng khía cạnh (aspect) kèm cảm xúc và lý do.
  Xuất ra JSON chuẩn để giai đoạn 7 (Fusion) và 8 (RFMS) sử dụng.

MODEL:
  Sử dụng `gemini-2.0-flash-lite` — dòng Flash-Lite tốc độ cao, chi phí thấp,
  phù hợp cho tác vụ phân tích cảm xúc có cấu trúc.
  Có thể ghi đè qua biến môi trường GEMINI_MODEL_NAME.

KẾT QUẢ TRẢ VỀ:
  [
    {
      "aspect": "Thái độ nhân viên",
      "sentiment": "Tiêu cực",
      "reason": "Nhân viên phục vụ chậm"
    },
    ...
  ]

  Hoặc nếu phát hiện spam/nonsense:
  {"is_spam": true, "aspects": [], "reason": "Văn bản không chứa nội dung có nghĩa"}
"""

import os
import json
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cấu hình model
# ---------------------------------------------------------------------------
DEFAULT_MODEL = "gemini-2.0-flash-lite"
VALID_FALLBACK_MODELS = ["gemini-2.0-flash-lite", "gemini-1.5-flash-8b", "gemini-1.5-flash"]


# Prompt hệ thống — thiết kế để LLM trả về JSON thuần, không markdown
SYSTEM_PROMPT = """Bạn là chuyên gia phân tích cảm xúc khách hàng (ABSA) cho ngành dịch vụ F&B (Nhà hàng, Quán ăn, Cà phê) tại Việt Nam. Mặc dù chuyên môn là F&B, bạn có khả năng thấu hiểu sâu sắc ngôn ngữ tự nhiên tiếng Việt, từ lóng mạng, và teencode thường thấy trên các nền tảng thương mại điện tử, mạng xã hội (Shopee, Tiki, Facebook, Tiktok).

NHIỆM VỤ:
Đọc phản hồi của khách hàng và trích xuất từng khía cạnh được đề cập kèm cảm xúc và lý do.

CÁC KHÍA CẠNH THƯỜNG GẶP (trong F&B):
- Thái độ nhân viên
- Chất lượng món ăn / nước uống
- Không gian / môi trường
- Giá cả
- Thời gian chờ đợi / Tốc độ phục vụ
- Vệ sinh sạch sẽ
- Vị trí / Tiện lợi

CẢM XÚC HỢP LỆ: "Tích cực", "Tiêu cực", "Trung lập"

HIỂU TỪ LÓNG & TEENCODE (Dựa trên dữ liệu mạng):
- Các từ lóng: sp (sản phẩm/món), auth/fake (thật/giả - có thể hiểu là chất lượng), rep (trả lời), ship (giao hàng), baoh (bao giờ), thui (thôi), vs (với), k/ko/khum (không), chê, xu cà na, 10đ không có nhưng, xịn xò, quá đỉnh.
- Ví dụ: "Quán này 10đ nha, nv rep nhanh xỉu" -> Tích cực về Thái độ nhân viên.
- Ví dụ: "Đợi mòn mỏi luôn, khum baoh quay lại" -> Tiêu cực về Tốc độ phục vụ.

QUY TẮC BẮT BUỘC:
1. Chỉ trả về JSON thuần — KHÔNG có markdown, KHÔNG có ```json, KHÔNG có chú thích.
2. Nếu văn bản là spam, ký tự rác, không có nghĩa, HOẶC là bài hát, thơ ca, những câu nói lãng mạn không liên quan đến đánh giá nhà hàng → trả về: {"is_spam": true, "aspects": []}
3. Nếu văn bản có nghĩa → trả về mảng JSON: [{"aspect": "...", "sentiment": "...", "reason": "..."}]
4. "reason" phải là trích dẫn ngắn từ văn bản gốc, không tự bịa.
5. Phát hiện MỈA MAI: nếu câu nghe có vẻ tích cực nhưng giọng điệu hoặc ngữ cảnh ám chỉ tiêu cực (ví dụ: "phục vụ tốt quá ha"), đánh dấu sentiment là "Tiêu cực" và ghi rõ "sarcasm_suspected": true trong reason của khía cạnh đó.

VÍ DỤ 1 (Phản hồi thật):
Input: "Món phở ngon lắm, nước dùng đậm đà. Nhưng nhân viên hơi lạnh lùng và chậm."
Output: [{"aspect": "Chất lượng món ăn", "sentiment": "Tích cực", "reason": "Món phở ngon lắm, nước dùng đậm đà"}, {"aspect": "Thái độ nhân viên", "sentiment": "Tiêu cực", "reason": "nhân viên hơi lạnh lùng và chậm"}]

VÍ DỤ 2 (Spam ký tự rác):
Input: "aaaaaaaaaa 123 !!!"
Output: {"is_spam": true, "aspects": []}

VÍ DỤ 3 (Mỉa mai):
Input: "Phục vụ tốt quá ha, đợi mãi mới ra"
Output: [{"aspect": "Thái độ nhân viên", "sentiment": "Tiêu cực", "reason": "Đợi mãi mới ra — mỉa mai", "sarcasm_suspected": true}]

VÍ DỤ 4 (Spam thơ ca, không liên quan):
Input: "ôm hoài những kỷ niệm đã cũ, lẩn trốn mình trong mộng dài thiên thu"
Output: {"is_spam": true, "aspects": []}"""

# ---------------------------------------------------------------------------
# Exceptions riêng
# ---------------------------------------------------------------------------

class ABSAError(Exception):
    """Base exception cho mọi lỗi ABSA."""
    pass

class ABSAAuthError(ABSAError):
    """Lỗi xác thực API key."""
    pass

class ABSAParseError(ABSAError):
    """LLM trả về JSON không parse được sau khi đã retry."""
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ABSAAuthError(
            "Chưa thiết lập GEMINI_API_KEY. "
            "Thêm vào file .env: GEMINI_API_KEY=your-key-here"
        )
    return key


def _strip_markdown(text: str) -> str:
    """Loại bỏ markdown code block nếu LLM bọc kết quả."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _parse_llm_output(raw_text: str) -> dict | list:
    """
    Parse JSON từ output của LLM.
    Trả về list (aspects) hoặc dict (spam signal).
    Raise ABSAParseError nếu không parse được.
    """
    cleaned = _strip_markdown(raw_text)
    try:
        result = json.loads(cleaned)
        return result
    except json.JSONDecodeError as e:
        raise ABSAParseError(
            f"Không thể parse JSON từ LLM: {e}\nRaw output: {raw_text[:300]}"
        ) from e


# ---------------------------------------------------------------------------
# Hàm chính
# ---------------------------------------------------------------------------

def analyze_absa(text: str, retry_on_parse_error: bool = True) -> dict:
    """
    Phân tích ABSA cho một đoạn văn bản tiếng Việt.

    Args:
        text: Văn bản phản hồi cần phân tích.
        retry_on_parse_error: Nếu True, thử lại 1 lần nếu LLM trả JSON lỗi.

    Returns:
        {
            "is_spam": bool,       # True nếu LLM nhận diện spam/nonsense
            "aspects": list[dict], # Danh sách khía cạnh, [] nếu spam
            "raw_llm_output": str  # Output thô từ LLM (debug)
        }

    Raises:
        ABSAAuthError:  Thiếu API key.
        ABSAParseError: LLM trả JSON sai định dạng và retry cũng thất bại.
        ABSAError:      Các lỗi API khác.
    """
    from google import genai
    from google.genai import types

    if not text or not text.strip():
        return {"is_spam": True, "aspects": [], "raw_llm_output": ""}

    api_key = _get_api_key()
    model_name = os.getenv("GEMINI_MODEL_NAME", DEFAULT_MODEL)

    client = genai.Client(api_key=api_key)

    user_message = f"Input: {text.strip()}\nOutput:"

    models_to_try = [model_name] + [m for m in VALID_FALLBACK_MODELS if m != model_name]

    def _call_api() -> str:
        last_err = None
        for m_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=m_name,
                    contents=user_message,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.0,      # Deterministic — không sáng tạo khi phân tích
                        max_output_tokens=512,
                    ),
                )
                return response.text or ""
            except Exception as e:
                err_str = str(e).lower()
                if "not_found" in err_str or "not found" in err_str or "404" in err_str:
                    logger.warning(f"[ABSA] Model '{m_name}' khong ton tai (404), thu model du phong...")
                    last_err = e
                    continue
                else:
                    raise e
        if last_err:
            raise last_err
        return ""

    # --- Lần gọi đầu ---
    try:
        raw_output = _call_api()
        logger.info(f"[ABSA] LLM raw output: {raw_output[:200]}")
    except Exception as e:
        err_msg = str(e).lower()
        if "api_key" in err_msg or "permission" in err_msg or "unauthorized" in err_msg:
            raise ABSAAuthError(f"Lỗi xác thực Gemini API: {e}") from e
        raise ABSAError(f"Lỗi khi gọi Gemini API: {e}") from e

    # --- Parse lần 1 ---
    try:
        parsed = _parse_llm_output(raw_output)
    except ABSAParseError:
        if not retry_on_parse_error:
            raise
        logger.warning("[ABSA] Parse lỗi lần 1 — thử lại sau 1 giây...")
        time.sleep(1)
        try:
            raw_output = _call_api()
            parsed = _parse_llm_output(raw_output)
        except ABSAParseError:
            logger.error("[ABSA] Retry cũng thất bại — trả về lỗi rõ ràng")
            raise

    # --- Normalize kết quả ---
    if isinstance(parsed, dict):
        # Trường hợp spam/nonsense
        is_spam = parsed.get("is_spam", False)
        aspects = parsed.get("aspects", [])
    elif isinstance(parsed, list):
        is_spam = False
        aspects = parsed
    else:
        is_spam = True
        aspects = []

    return {
        "is_spam": is_spam,
        "aspects": aspects,
        "raw_llm_output": raw_output,
    }
