"""
Semantic Validity Service — Lọc nội dung vô nghĩa/spam bằng LLM
================================================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
Module 1 — Lớp 3: Kiểm tra ngữ nghĩa

MỤC ĐÍCH:
  Sau khi có transcript từ Whisper (hoặc text nhập tay), gọi Gemini để phân loại
  phản hồi có hợp lệ không. Đây là lớp riêng biệt với ABSA — một prompt tập trung
  làm 1 việc sẽ chính xác hơn là gộp chung vào prompt ABSA.

  Lý do tách riêng (không gộp vào ABSA):
    - ABSA làm nhiều việc: extract aspects, classify sentiment, detect sarcasm.
    - Thêm validity check vào ABSA làm prompt phức tạp → giảm accuracy cả 2 task.
    - Prompt riêng nhỏ hơn → latency thấp hơn, ít token hơn → rẻ hơn.

TIÊU CHÍ INVALID:
  1. Vô nghĩa / ngẫu nhiên: "aaaa", "1234567", "test test", gõ bừa
  2. Chửi bới/tục tĩu thuần túy không kèm nội dung phản hồi thực chất
  3. Lặp y hệt transcript lần trước của cùng khách hàng (copy-paste)
  4. Rõ ràng không liên quan đến trải nghiệm dịch vụ

KẾT QUẢ:
  - "valid":   lưu bình thường, tính vào thống kê, có thể nhận voucher
  - "invalid": validity_status = "invalid_semantic", vẫn LƯU (để audit),
               KHÔNG tính vào thống kê dashboard, KHÔNG phát voucher

TIMEOUT:
  Đặt timeout ngắn hơn ABSA (mặc định 15s) vì prompt đơn giản hơn.
  Nếu Gemini timeout → fallback conservative = "valid"
  Lý do: false reject phản hồi thật tệ hơn là accept 1 phản hồi rác lọt qua.
"""

import json
import logging
import os
import re
import concurrent.futures
import asyncio
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cấu hình
# ---------------------------------------------------------------------------
SEMANTIC_CHECK_TIMEOUT_SECONDS: int = int(os.getenv("SEMANTIC_CHECK_TIMEOUT_SECONDS", "15"))

# Độ dài tối thiểu để gọi LLM (text quá ngắn → rule-based reject, tiết kiệm LLM call)
MIN_TEXT_LENGTH_FOR_LLM = 5

# Prompt phân loại — tách hoàn toàn khỏi prompt ABSA
_VALIDITY_PROMPT_TEMPLATE = """Bạn là hệ thống phân loại phản hồi khách hàng cho nền tảng thu thập ý kiến tại Việt Nam.

Nhiệm vụ: Xác định phản hồi sau có chứa nội dung thực chất về trải nghiệm dịch vụ không.

Phản hồi cần phân loại:
\"\"\"
{text}
\"\"\"

Thông tin bổ sung:
- Phản hồi trước của khách hàng này (nếu có): {last_transcript}
- Ngôn ngữ phản hồi có thể là Tiếng Việt, tiếng Anh, hoặc hỗn hợp.

Tiêu chí INVALID (bất kỳ một trong các điều kiện sau):
1. Nội dung hoàn toàn vô nghĩa hoặc ngẫu nhiên (ký tự lặp, gõ bừa, chuỗi số ngẫu nhiên)
2. Chỉ chứa chửi bới/tục tĩu thuần túy KHÔNG kèm bất kỳ nhận xét nào về dịch vụ
3. Nội dung GIỐNG HỆT hoặc gần như giống hệt phản hồi trước (copy-paste, paraphrase đơn giản)
4. Hoàn toàn không liên quan đến trải nghiệm sử dụng dịch vụ (ví dụ: nói về thời tiết, tin tức)

Tiêu chí VALID:
- Bất kỳ nhận xét nào về đồ ăn, đồ uống, phục vụ, không gian, vệ sinh, giá cả, chờ đợi, v.v.
- Kể cả phản hồi rất ngắn nhưng có nội dung ("ngon lắm", "hơi mặn", "chờ lâu")
- Kể cả phản hồi tiêu cực/chửi bới NẾU có kèm theo lý do về dịch vụ

Trả về JSON CHÍNH XÁC theo format sau (KHÔNG có text nào khác):
{{"validity": "valid", "reason": "Giải thích ngắn gọn tại sao"}}
hoặc
{{"validity": "invalid", "reason": "Giải thích ngắn gọn tại sao"}}"""


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------
@dataclass
class SemanticValidityResult:
    """Kết quả kiểm tra semantic validity."""
    is_valid: bool                 # True = hợp lệ
    validity_status: str           # "valid" | "invalid_semantic"
    reason: str                    # Lý do (từ LLM hoặc rule-based)
    checked_by: str                # "llm" | "rule_based" | "timeout_fallback"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def check_semantic_validity(
    text: str,
    last_transcript: Optional[str] = None,
) -> SemanticValidityResult:
    """
    Kiểm tra semantic validity của transcript/text.

    Chạy đồng bộ (sync) — được gọi trong ThreadPoolExecutor từ feedback.py
    giống với pattern của analyze_absa().

    Args:
        text:            Nội dung cần kiểm tra (transcript từ Whisper hoặc text nhập tay).
        last_transcript: Transcript lần trước của cùng khách hàng (để phát hiện copy-paste).

    Returns:
        SemanticValidityResult.
    """
    text = text.strip()

    # ── Kiểm tra rule-based nhanh (không cần LLM) ───────────────────────────
    if len(text) < MIN_TEXT_LENGTH_FOR_LLM:
        return SemanticValidityResult(
            is_valid=False,
            validity_status="invalid_semantic",
            reason=f"Nội dung quá ngắn ({len(text)} ký tự) để phân tích",
            checked_by="rule_based",
        )

    # ── Gọi LLM ─────────────────────────────────────────────────────────────
    try:
        result = _call_gemini_validity(text, last_transcript or "Không có")
        is_valid = result.get("validity", "valid") == "valid"
        reason   = result.get("reason", "")

        logger.info(
            f"[SemanticValidity] LLM result: validity={result.get('validity')}, "
            f"reason={reason[:100]}"
        )

        return SemanticValidityResult(
            is_valid=is_valid,
            validity_status="valid" if is_valid else "invalid_semantic",
            reason=reason,
            checked_by="llm",
        )

    except TimeoutError:
        # Conservative fallback: nếu timeout → cho qua (false reject tệ hơn false accept)
        logger.warning(
            f"[SemanticValidity] Gemini timeout sau {SEMANTIC_CHECK_TIMEOUT_SECONDS}s "
            "— fallback: valid"
        )
        return SemanticValidityResult(
            is_valid=True,
            validity_status="valid",
            reason="LLM timeout — fallback conservative",
            checked_by="timeout_fallback",
        )

    except Exception as e:
        logger.warning(f"[SemanticValidity] LLM lỗi (fallback: valid): {type(e).__name__}: {e}")
        return SemanticValidityResult(
            is_valid=True,
            validity_status="valid",
            reason=f"LLM error fallback: {type(e).__name__}",
            checked_by="timeout_fallback",
        )


# ---------------------------------------------------------------------------
# Gemini call (sync) — chạy trong thread
# ---------------------------------------------------------------------------
def _call_gemini_validity(text: str, last_transcript: str) -> dict:
    """
    Gọi Gemini API để phân loại validity. Hàm sync — dành cho thread executor.

    Returns:
        dict: {"validity": "valid"|"invalid", "reason": "..."}

    Raises:
        TimeoutError: nếu vượt SEMANTIC_CHECK_TIMEOUT_SECONDS.
        Exception:    lỗi API.
    """
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY chưa được cấu hình.")

    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash-lite")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    prompt = _VALIDITY_PROMPT_TEMPLATE.format(
        text=text[:500],  # Giới hạn 500 ký tự — bài toán classify không cần toàn bộ
        last_transcript=last_transcript[:200] if last_transcript else "Không có",
    )

    # Gọi API với request_options timeout
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.0,     # Temperature = 0 → output ổn định, không sáng tạo
            max_output_tokens=100,  # Chỉ cần JSON ngắn
        ),
        request_options={"timeout": SEMANTIC_CHECK_TIMEOUT_SECONDS},
    )

    raw_text = response.text.strip()

    # Parse JSON từ response
    return _parse_validity_json(raw_text)


def _parse_validity_json(raw_text: str) -> dict:
    """
    Parse JSON từ Gemini response. Robust với markdown code block.

    Returns:
        dict với keys "validity" và "reason".
    """
    # Tìm JSON trong markdown code block nếu có
    json_match = re.search(r'\{.*?\}', raw_text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group())
            if "validity" in data:
                return data
        except json.JSONDecodeError:
            pass

    # Thử parse toàn bộ string
    try:
        data = json.loads(raw_text)
        if "validity" in data:
            return data
    except json.JSONDecodeError:
        pass

    # Fallback: đọc từ khoá trong text nếu JSON bị lỗi format
    if "invalid" in raw_text.lower():
        return {"validity": "invalid", "reason": f"LLM response parse error: {raw_text[:100]}"}

    logger.warning(f"[SemanticValidity] Không parse được JSON từ Gemini: {raw_text[:200]}")
    return {"validity": "valid", "reason": "JSON parse error — fallback valid"}
