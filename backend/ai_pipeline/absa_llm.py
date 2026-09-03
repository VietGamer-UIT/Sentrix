"""
ABSA (Aspect-Based Sentiment Analysis) via LLM — Sentrix v2
=============================================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
Giai đoạn: 6A — Phân tích ABSA bằng Gemini Flash-Lite

MỤC ĐÍCH:
  Đưa văn bản phản hồi của khách hàng (từ Whisper STT hoặc gõ tay) vào LLM
  để bóc tách từng khía cạnh (aspect) kèm cảm xúc và lý do.
  Xuất ra JSON chuẩn để giai đoạn 7 (Fusion) và 8 (RFMS) sử dụng.

MODEL:
  Sử dụng `gemini-3.1-flash-lite` — dòng Flash-Lite tốc độ cao, chi phí thấp,
  phù hợp cho tác vụ phân tích cảm xúc có cấu trúc.
  Có thể ghi đè qua biến môi trường GEMINI_MODEL_NAME.

FORMAT KẾT QUẢ V2 (2026-08-26):
  {
    "overall_sentiment": float  [-1.0 → +1.0],
    "is_spam": bool,
    "sarcasm_detected": bool,
    "key_phrase": str,          # Trích ngắn lý do chính (~15 từ), dùng cho preview dashboard
    "aspects": [
      {
        "aspect":    str,    # enum: xem FIXED_ASPECTS bên dưới
        "sentiment": float,  # -1.0 → +1.0 (không phải string "Tích cực/Tiêu cực")
        "mentioned": bool,   # True nếu khía cạnh này được đề cập rõ ràng
        "reason":    str     # Trích ngắn từ văn bản gốc
      }, ...
    ]
  }

  ⚠️ THAY ĐỔI SO VỚI V1:
    - "sentiment" giờ là float [-1.0, +1.0] thay vì string "Tích cực/Tiêu cực/Trung lập"
    - Thêm "overall_sentiment" float cho toàn bộ phản hồi
    - Thêm "key_phrase" cho preview dashboard (thay vì dùng transcript dài)
    - Thêm "mentioned" để tránh kéo điểm trung bình khía cạnh bằng aspect chưa được đề cập
    - Danh sách aspects cố định (6 khía cạnh F&B) — khớp với mock dashboard hiện tại

KHÍA CẠNH CỐ ĐỊNH (FIXED_ASPECTS):
  Khớp với biểu đồ "Cảm xúc theo khía cạnh" trên dashboard mock:
  - "mon_an"        → Chất lượng món ăn / nước uống
  - "nhan_vien"     → Thái độ / phục vụ nhân viên
  - "khong_gian"    → Không gian / môi trường / âm nhạc
  - "gia_ca"        → Giá cả / cost-value
  - "toc_do"        → Tốc độ phục vụ / thời gian chờ
  - "ve_sinh"       → Vệ sinh sạch sẽ (bàn, WC, dụng cụ ăn)
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
DEFAULT_MODEL = "gemini-3.1-flash-lite"
VALID_FALLBACK_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash",
]

# ---------------------------------------------------------------------------
# Danh sách khía cạnh cố định — khớp với dashboard mock
# Thứ tự này quan trọng: dùng để validate output LLM
# ---------------------------------------------------------------------------
FIXED_ASPECTS = [
    "mon_an",       # Chất lượng món ăn / nước uống
    "nhan_vien",    # Thái độ / phục vụ nhân viên
    "khong_gian",   # Không gian / môi trường
    "gia_ca",       # Giá cả
    "toc_do",       # Tốc độ phục vụ / thời gian chờ
    "ve_sinh",      # Vệ sinh sạch sẽ
]

# Label tiếng Việt đẹp để hiển thị dashboard
ASPECT_LABELS_VI = {
    "mon_an":     "Món ăn",
    "nhan_vien":  "Nhân viên",
    "khong_gian": "Không gian",
    "gia_ca":     "Giá cả",
    "toc_do":     "Tốc độ phục vụ",
    "ve_sinh":    "Vệ sinh",
}

# ---------------------------------------------------------------------------
# System Prompt V2 — trả JSON có cấu trúc đầy đủ
# ---------------------------------------------------------------------------
SYSTEM_PROMPT_V2 = """\
Bạn là chuyên gia phân tích cảm xúc khách hàng (ABSA) cho ngành F&B (Nhà hàng, Quán ăn, Cà phê) tại Việt Nam.
Bạn thấu hiểu tiếng Việt tự nhiên, từ lóng, teencode (Shopee, Facebook, TikTok).

NHIỆM VỤ:
Đọc phản hồi của khách hàng và trả về JSON đúng định dạng bên dưới — KHÔNG thêm markdown, KHÔNG thêm chú thích.

6 KHÍA CẠNH CỐ ĐỊNH (aspect key trong JSON):
  mon_an     → Chất lượng món ăn / nước uống
  nhan_vien  → Thái độ / phục vụ của nhân viên
  khong_gian → Không gian / môi trường / âm nhạc
  gia_ca     → Giá cả / cost-value
  toc_do     → Tốc độ phục vụ / thời gian chờ
  ve_sinh    → Vệ sinh sạch sẽ (bàn, WC, dụng cụ ăn)

ĐIỂM CẢM XÚC: float từ -1.0 (rất tiêu cực) đến +1.0 (rất tích cực), 0.0 = trung lập.

ĐỊNH DẠNG JSON BẮT BUỘC (phải trả đủ 6 khía cạnh):
{
  "overall_sentiment": <float -1.0 → +1.0>,
  "is_spam": <bool>,
  "sarcasm_detected": <bool>,
  "key_phrase": "<trích tối đa 15 từ lý do chính, hoặc chuỗi rỗng nếu spam>",
  "aspects": [
    {"aspect": "mon_an",     "sentiment": <float>, "mentioned": <bool>, "reason": "<trích ngắn hoặc ''>"},
    {"aspect": "nhan_vien",  "sentiment": <float>, "mentioned": <bool>, "reason": "<trích ngắn hoặc ''>"},
    {"aspect": "khong_gian", "sentiment": <float>, "mentioned": <bool>, "reason": "<trích ngắn hoặc ''>"},
    {"aspect": "gia_ca",     "sentiment": <float>, "mentioned": <bool>, "reason": "<trích ngắn hoặc ''>"},
    {"aspect": "toc_do",     "sentiment": <float>, "mentioned": <bool>, "reason": "<trích ngắn hoặc ''>"},
    {"aspect": "ve_sinh",    "sentiment": <float>, "mentioned": <bool>, "reason": "<trích ngắn hoặc ''>"}
  ]
}

QUY TẮC BẮT BUỘC:
1. Luôn trả đủ 6 khía cạnh theo thứ tự trên — nếu không đề cập thì "mentioned": false, "sentiment": 0.0, "reason": "".
2. Nếu spam/ký tự rác/bài hát/thơ không liên quan đánh giá quán: is_spam=true, overall_sentiment=0.0, tất cả mentioned=false.
3. Phát hiện mỉa mai (sarcasm): câu nghe tích cực nhưng giọng điệu ngụ ý tiêu cực → sarcasm_detected=true, đảo dấu sentiment.
4. key_phrase: trích từ văn bản gốc (không tự bịa), tối đa 15 từ. Nếu spam thì "".
5. overall_sentiment = trung bình có trọng số của các aspect được đề cập (không phải toán học đơn giản — LLM tự đánh giá).
6. "reason" phải là trích dẫn ngắn từ văn bản gốc, không tự bịa.

HIỂU TỪ LÓNG & TEENCODE:
- "10đ", "quá đỉnh", "xịn xò", "ngon nhức nách" → rất tích cực (+0.8 đến +1.0)
- "chê", "tệ vl", "bực mình", "khum baoh quay lại" → rất tiêu cực (-0.8 đến -1.0)
- "nv rep nhanh xỉu" = nhân viên phản hồi nhanh → tích cực nhan_vien
- "đợi mòn mỏi" → tiêu cực toc_do

VÍ DỤ 1 — Phản hồi thật:
Input: "Món phở ngon lắm, nước dùng đậm đà. Nhưng nhân viên hơi lạnh lùng, đợi lâu quá."
Output:
{
  "overall_sentiment": -0.1,
  "is_spam": false,
  "sarcasm_detected": false,
  "key_phrase": "phở ngon, nước dùng đậm đà, nhưng nhân viên lạnh lùng đợi lâu",
  "aspects": [
    {"aspect": "mon_an",     "sentiment":  0.8, "mentioned": true,  "reason": "Món phở ngon lắm, nước dùng đậm đà"},
    {"aspect": "nhan_vien",  "sentiment": -0.5, "mentioned": true,  "reason": "nhân viên hơi lạnh lùng"},
    {"aspect": "khong_gian", "sentiment":  0.0, "mentioned": false, "reason": ""},
    {"aspect": "gia_ca",     "sentiment":  0.0, "mentioned": false, "reason": ""},
    {"aspect": "toc_do",     "sentiment": -0.7, "mentioned": true,  "reason": "đợi lâu quá"},
    {"aspect": "ve_sinh",    "sentiment":  0.0, "mentioned": false, "reason": ""}
  ]
}

VÍ DỤ 2 — Spam:
Input: "aaaaaaaaaa 123 !!!"
Output:
{
  "overall_sentiment": 0.0, "is_spam": true, "sarcasm_detected": false, "key_phrase": "",
  "aspects": [
    {"aspect": "mon_an",     "sentiment": 0.0, "mentioned": false, "reason": ""},
    {"aspect": "nhan_vien",  "sentiment": 0.0, "mentioned": false, "reason": ""},
    {"aspect": "khong_gian", "sentiment": 0.0, "mentioned": false, "reason": ""},
    {"aspect": "gia_ca",     "sentiment": 0.0, "mentioned": false, "reason": ""},
    {"aspect": "toc_do",     "sentiment": 0.0, "mentioned": false, "reason": ""},
    {"aspect": "ve_sinh",    "sentiment": 0.0, "mentioned": false, "reason": ""}
  ]
}

VÍ DỤ 3 — Mỉa mai:
Input: "Phục vụ tốt quá ha, đợi mãi mới ra"
Output:
{
  "overall_sentiment": -0.6,
  "is_spam": false,
  "sarcasm_detected": true,
  "key_phrase": "phục vụ chậm, đợi mãi mới ra",
  "aspects": [
    {"aspect": "mon_an",     "sentiment":  0.0, "mentioned": false, "reason": ""},
    {"aspect": "nhan_vien",  "sentiment": -0.5, "mentioned": true,  "reason": "Phục vụ tốt quá ha — mỉa mai"},
    {"aspect": "khong_gian", "sentiment":  0.0, "mentioned": false, "reason": ""},
    {"aspect": "gia_ca",     "sentiment":  0.0, "mentioned": false, "reason": ""},
    {"aspect": "toc_do",     "sentiment": -0.7, "mentioned": true,  "reason": "đợi mãi mới ra"},
    {"aspect": "ve_sinh",    "sentiment":  0.0, "mentioned": false, "reason": ""}
  ]
}
"""


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


def _parse_llm_output_v2(raw_text: str) -> dict:
    """
    Parse JSON v2 từ output của LLM.
    Validate và normalize các field bắt buộc.
    Raise ABSAParseError nếu không parse được.
    """
    cleaned = _strip_markdown(raw_text)
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ABSAParseError(
            f"Không thể parse JSON từ LLM: {e}\nRaw output: {raw_text[:300]}"
        ) from e

    # Normalize — đảm bảo luôn có đủ fields dù LLM thiếu
    if not isinstance(result, dict):
        raise ABSAParseError(f"LLM trả về type không hợp lệ: {type(result)}")

    # Đảm bảo overall_sentiment là float trong [-1, +1]
    try:
        overall = float(result.get("overall_sentiment", 0.0))
        result["overall_sentiment"] = max(-1.0, min(1.0, overall))
    except (TypeError, ValueError):
        result["overall_sentiment"] = 0.0

    result.setdefault("is_spam", False)
    result.setdefault("sarcasm_detected", False)
    result.setdefault("key_phrase", "")

    # Normalize aspects — đảm bảo đủ 6 khía cạnh theo thứ tự cố định
    raw_aspects = result.get("aspects", [])
    if not isinstance(raw_aspects, list):
        raw_aspects = []

    # Build dict từ raw aspects để tra cứu theo key
    aspect_map = {}
    for a in raw_aspects:
        if isinstance(a, dict) and "aspect" in a:
            key = a["aspect"]
            # Normalize sentiment của aspect
            try:
                sent = float(a.get("sentiment", 0.0))
                sent = max(-1.0, min(1.0, sent))
            except (TypeError, ValueError):
                sent = 0.0
            aspect_map[key] = {
                "aspect":    key,
                "sentiment": round(sent, 3),
                "mentioned": bool(a.get("mentioned", False)),
                "reason":    str(a.get("reason", ""))[:200],
                "label_vi":  ASPECT_LABELS_VI.get(key, key),
            }

    # Xây dựng lại danh sách 6 khía cạnh cố định theo thứ tự chuẩn
    normalized_aspects = []
    for aspect_key in FIXED_ASPECTS:
        if aspect_key in aspect_map:
            normalized_aspects.append(aspect_map[aspect_key])
        else:
            # Khía cạnh không được LLM đề cập → placeholder (mentioned=False)
            normalized_aspects.append({
                "aspect":    aspect_key,
                "sentiment": 0.0,
                "mentioned": False,
                "reason":    "",
                "label_vi":  ASPECT_LABELS_VI.get(aspect_key, aspect_key),
            })

    result["aspects"] = normalized_aspects
    return result


def _build_fallback_result(reason: str = "absa_error") -> dict:
    """
    Kết quả fallback khi ABSA thất bại — trả về trung lập.
    Ghi rõ lý do để dashboard phân biệt 'trung lập thật' vs 'ABSA fail'.
    """
    return {
        "overall_sentiment": 0.0,
        "is_spam": False,
        "sarcasm_detected": False,
        "key_phrase": "",
        "aspects": [
            {
                "aspect":    key,
                "sentiment": 0.0,
                "mentioned": False,
                "reason":    "",
                "label_vi":  ASPECT_LABELS_VI[key],
            }
            for key in FIXED_ASPECTS
        ],
        "_absa_fallback": True,
        "_fallback_reason": reason,
    }


# ---------------------------------------------------------------------------
# Hàm chính
# ---------------------------------------------------------------------------

def analyze_absa(text: str, retry_on_parse_error: bool = True) -> dict:
    """
    Phân tích ABSA cho một đoạn văn bản tiếng Việt (v2 — structured aspects).

    Args:
        text: Văn bản phản hồi cần phân tích.
        retry_on_parse_error: Nếu True, thử lại 1 lần nếu LLM trả JSON lỗi.

    Returns:
        {
            "overall_sentiment": float,    # [-1.0, +1.0] — tổng thể
            "is_spam":          bool,
            "sarcasm_detected": bool,
            "key_phrase":       str,       # Preview ~15 từ cho dashboard
            "aspects": [                   # Luôn đủ 6 khía cạnh cố định
                {
                    "aspect":    str,      # enum: mon_an|nhan_vien|khong_gian|gia_ca|toc_do|ve_sinh
                    "sentiment": float,    # [-1.0, +1.0]
                    "mentioned": bool,     # False → không tính vào biểu đồ trung bình
                    "reason":    str,
                    "label_vi":  str,      # Label tiếng Việt đẹp
                }, ...
            ],
            "raw_llm_output": str,         # Output thô từ LLM (debug)
            "_absa_fallback": bool,        # True nếu ABSA thất bại
        }

    Raises:
        ABSAAuthError:  Thiếu API key.
        ABSAParseError: LLM trả JSON sai định dạng và retry cũng thất bại.
        ABSAError:      Các lỗi API khác.
    """
    from google import genai
    from google.genai import types

    if not text or not text.strip():
        result = _build_fallback_result("empty_text")
        result["raw_llm_output"] = ""
        return result

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
                        system_instruction=SYSTEM_PROMPT_V2,
                        temperature=0.0,       # Deterministic — không sáng tạo khi phân tích
                        max_output_tokens=800, # V2 cần nhiều hơn V1 vì 6 aspects
                    ),
                )
                return response.text or ""
            except Exception as e:
                err_str = str(e).lower()
                if "not_found" in err_str or "not found" in err_str or "404" in err_str:
                    logger.warning(
                        f"[ABSA] Model '{m_name}' khong ton tai (404), thu model du phong..."
                    )
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
        logger.info(f"[ABSA] LLM raw output: {raw_output[:300]}")
    except Exception as e:
        err_msg = str(e).lower()
        if "api_key" in err_msg or "permission" in err_msg or "unauthorized" in err_msg:
            raise ABSAAuthError(f"Lỗi xác thực Gemini API: {e}") from e
        raise ABSAError(f"Lỗi khi gọi Gemini API: {e}") from e

    # --- Parse lần 1 ---
    try:
        parsed = _parse_llm_output_v2(raw_output)
    except ABSAParseError:
        if not retry_on_parse_error:
            raise
        logger.warning("[ABSA] Parse lỗi lần 1 — thử lại sau 1 giây...")
        time.sleep(1)
        try:
            raw_output = _call_api()
            parsed = _parse_llm_output_v2(raw_output)
        except ABSAParseError:
            logger.error("[ABSA] Retry cũng thất bại — trả về lỗi rõ ràng")
            raise

    parsed["raw_llm_output"] = raw_output
    parsed.setdefault("_absa_fallback", False)

    logger.info(
        f"[ABSA v2] overall={parsed['overall_sentiment']:.3f}, "
        f"is_spam={parsed['is_spam']}, sarcasm={parsed['sarcasm_detected']}, "
        f"mentioned_aspects={sum(1 for a in parsed['aspects'] if a['mentioned'])}/6"
    )
    return parsed
