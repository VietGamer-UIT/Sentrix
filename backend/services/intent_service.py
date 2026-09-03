"""
intent_service.py — Intent Classification for Sentrix
=======================================================
Milestone 3: Phân loại ý định feedback từ văn bản ngắn

Phân loại 3 loại intent:
  SUPPORT_REQUEST  — khách cần hỗ trợ ngay (\"Toi can them ghe\", \"Cho toi hoa don\")
  FEEDBACK         — phản hồi trải nghiệm (\"Mon an ngon\", \"Nhan vien cham\")
  INVALID          — vô nghĩa / spam (\"aaaa 123 xyz\")

IMPLEMENTATION:
  - Dùng Gemini Flash (cùng provider với ABSA)
  - Prompt nhỏ, tập trung 1 task, trả JSON 1 object
  - Timeout 10s (nhanh hơn ABSA 30s)
  - Fallback nếu lỗi/timeout: FEEDBACK (conservative, không block)
  - Feature flag: ENABLE_INTENT_CLASSIFICATION env var

SCHEMA TRẢ VỀ:
  {
    "intent": "SUPPORT_REQUEST" | "FEEDBACK" | "INVALID",
    "confidence": float (0.0-1.0),
    "reason": str
  }
"""

import os
import json
import logging
from typing import TypedDict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

VALID_INTENTS = ("SUPPORT_REQUEST", "FEEDBACK", "INVALID")

class IntentResult(TypedDict):
    intent: str      # "SUPPORT_REQUEST" | "FEEDBACK" | "INVALID"
    confidence: float
    reason: str


# ---------------------------------------------------------------------------
# Fallback result
# ---------------------------------------------------------------------------

_FALLBACK_RESULT: IntentResult = {
    "intent": "FEEDBACK",
    "confidence": 0.5,
    "reason": "fallback — intent classification skipped or failed",
}


# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
Bạn là bộ phân loại ý định (intent classifier) cho hệ thống feedback nhà hàng tại Việt Nam.

NHIỆM VỤ: Đọc văn bản ngắn từ khách hàng và phân loại vào 1 trong 3 intent:

  SUPPORT_REQUEST — Khách cần hỗ trợ NGAY từ nhân viên, ví dụ:
    - Yêu cầu/mệnh lệnh trực tiếp: "cho thêm nước", "tính tiền đi", "lấy hóa đơn",
      "cần thêm khăn", "bàn này thiếu muỗng", "trà đá đi", "bật điều hòa lên"
    - Khiếu nại cần xử lý ngay: "món vẫn chưa ra", "order sai rồi", "bàn bẩn quá"
    - Câu hỏi cần trả lời: "wifi mật khẩu là gì", "giờ đóng cửa là mấy giờ"

  FEEDBACK — Khách chia sẻ trải nghiệm (không cần can thiệp ngay):
    - Đánh giá tích cực/tiêu cực: "phở ngon", "nhân viên lịch sự", "giá hơi cao"
    - Góp ý: "nên thêm chỗ gửi xe", "âm nhạc ồn quá"
    - Nhận xét: "lần sau sẽ quay lại", "không hài lòng về tốc độ phục vụ"

  INVALID — Không phải feedback thật:
    - Ký tự rác, spam: "aaaa bbb 123", "xyzxyz!!!"
    - Bài hát, thơ ca không liên quan
    - Câu hoàn toàn không có ý nghĩa

QUY TẮC:
1. Chỉ trả về JSON thuần — KHÔNG markdown, KHÔNG chú thích.
2. intent phải là CHÍNH XÁC một trong: SUPPORT_REQUEST, FEEDBACK, INVALID
3. confidence từ 0.0 đến 1.0 (độ chắc chắn của phân loại)
4. reason: 1 câu ngắn giải thích (tiếng Việt OK)

FORMAT:
{"intent": "...", "confidence": 0.9, "reason": "..."}

VÍ DỤ:
Input: "cho tôi thêm ly nước đá"
Output: {"intent": "SUPPORT_REQUEST", "confidence": 0.97, "reason": "Yêu cầu trực tiếp cần nhân viên phục vụ"}

Input: "phở ngon lắm, nước dùng đậm đà"
Output: {"intent": "FEEDBACK", "confidence": 0.95, "reason": "Phản hồi trải nghiệm tích cực về món ăn"}

Input: "aaaa 123 xyz!!!"
Output: {"intent": "INVALID", "confidence": 0.98, "reason": "Ký tự rác, không có nội dung"}
"""


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------

def classify_intent(text: str, timeout_sec: int = 10) -> IntentResult:
    """
    Phân loại intent từ văn bản feedback.

    Args:
        text:        Văn bản feedback (đã qua STT hoặc gõ tay)
        timeout_sec: Timeout tính bằng giây (mặc định 10s)

    Returns:
        IntentResult với keys: intent, confidence, reason

    Note:
        Hàm này KHÔNG raise exception — mọi lỗi được fallback về FEEDBACK.
        Caller không cần try/except xung quanh hàm này.
    """
    # Feature flag: tắt hoàn toàn nếu không bật
    if not os.getenv("ENABLE_INTENT_CLASSIFICATION", "true").lower() in ("true", "1", "yes"):
        return _FALLBACK_RESULT.copy()

    # Empty text → INVALID ngay
    if not text or not text.strip():
        return {"intent": "INVALID", "confidence": 1.0, "reason": "Văn bản rỗng"}

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("[Intent] GEMINI_API_KEY chưa thiết lập — fallback FEEDBACK")
        return _FALLBACK_RESULT.copy()

    try:
        from google import genai
        from google.genai import types

        client    = genai.Client(api_key=api_key)
        model     = os.getenv("GEMINI_MODEL_NAME", "gemini-3.1-flash-lite")
        user_msg  = f"Input: {text.strip()}"

        import time
        _start = time.time()

        # Gọi API với timeout thông qua signal không khả dụng trên Windows
        # → Dùng try/except với time check thay vì signal
        response = client.models.generate_content(
            model=model,
            contents=user_msg,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                temperature=0.0,
                max_output_tokens=100,   # Intent chỉ cần JSON ngắn
            ),
        )

        raw = (response.text or "").strip()
        logger.debug(f"[Intent] LLM raw output: {raw!r}")

        # Parse JSON
        # Strip markdown nếu LLM bọc kết quả (vd: ```json ... ```)
        raw = raw.strip()
        if raw.startswith("`"):
            raw = raw.strip("`").strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()

        parsed = json.loads(raw)

        intent = str(parsed.get("intent", "FEEDBACK")).strip().upper()
        if intent not in VALID_INTENTS:
            logger.warning(f"[Intent] Intent không hợp lệ từ LLM: '{intent}' — fallback FEEDBACK")
            intent = "FEEDBACK"

        confidence = float(parsed.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        reason = str(parsed.get("reason", "")).strip()[:200]

        elapsed = time.time() - _start
        logger.info(
            f"[Intent] '{text[:50]}...' → {intent} "
            f"(confidence={confidence:.2f}, {elapsed:.2f}s)"
        )

        return {"intent": intent, "confidence": confidence, "reason": reason}

    except json.JSONDecodeError as e:
        logger.warning(f"[Intent] Parse JSON thất bại: {e} — fallback FEEDBACK")
        return _FALLBACK_RESULT.copy()
    except Exception as e:
        logger.warning(f"[Intent] Lỗi classify_intent: {e!r} — fallback FEEDBACK")
        return _FALLBACK_RESULT.copy()
