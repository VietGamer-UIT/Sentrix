"""
test_intent_service.py — Unit tests for Intent Classification
=============================================================
Chạy: pytest backend/tests/test_intent_service.py -v

Toàn bộ tests dùng mock Gemini Client — không tốn API quota.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from backend.services.intent_service import classify_intent, VALID_INTENTS, IntentResult


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _mock_client(response_text: str):
    """Tạo mock google.genai.Client trả response_text."""
    mock_client   = MagicMock()
    mock_response = MagicMock()
    mock_response.text = response_text
    mock_client.models.generate_content.return_value = mock_response
    return mock_client


def _env():
    return {"GEMINI_API_KEY": "fake-key", "ENABLE_INTENT_CLASSIFICATION": "true"}


# ---------------------------------------------------------------------------
# Test: Feature Flag & Guard Clauses
# ---------------------------------------------------------------------------

class TestGuards:
    def test_empty_text_returns_invalid(self):
        """Văn bản rỗng → INVALID ngay, không gọi API."""
        result = classify_intent("")
        assert result["intent"] == "INVALID"
        assert result["confidence"] == 1.0

    def test_whitespace_only_returns_invalid(self):
        """Văn bản chỉ khoảng trắng → INVALID."""
        result = classify_intent("   ")
        assert result["intent"] == "INVALID"

    def test_missing_api_key_returns_fallback(self):
        """Không có GEMINI_API_KEY → fallback FEEDBACK."""
        with patch.dict("os.environ", {}, clear=True):
            result = classify_intent("Mon an ngon")
        assert result["intent"] == "FEEDBACK"

    def test_feature_flag_disabled_returns_fallback(self):
        """ENABLE_INTENT_CLASSIFICATION=false → fallback FEEDBACK."""
        env = {"GEMINI_API_KEY": "fake", "ENABLE_INTENT_CLASSIFICATION": "false"}
        with patch.dict("os.environ", env, clear=True):
            result = classify_intent("Toi can them nuoc")
        assert result["intent"] == "FEEDBACK"


# ---------------------------------------------------------------------------
# Test: Happy Path
# ---------------------------------------------------------------------------

class TestIntentClassification:
    def test_support_request_detected(self):
        """'Toi can mot ly tra da' → SUPPORT_REQUEST."""
        llm_output = json.dumps({
            "intent": "SUPPORT_REQUEST",
            "confidence": 0.97,
            "reason": "Yeu cau truc tiep can nhan vien phuc vu"
        })
        with patch.dict("os.environ", _env()):
            with patch("google.genai.Client") as mock_cls:
                mock_cls.return_value = _mock_client(llm_output)
                result = classify_intent("Toi can mot ly tra da")

        assert result["intent"] == "SUPPORT_REQUEST"
        assert result["confidence"] == pytest.approx(0.97)
        assert "reason" in result
        assert len(result["reason"]) > 0

    def test_feedback_detected(self):
        """'Mon an ngon nhung cho hoi lau' → FEEDBACK."""
        llm_output = json.dumps({
            "intent": "FEEDBACK",
            "confidence": 0.92,
            "reason": "Phan hoi trai nghiem co gia tri"
        })
        with patch.dict("os.environ", _env()):
            with patch("google.genai.Client") as mock_cls:
                mock_cls.return_value = _mock_client(llm_output)
                result = classify_intent("Mon an ngon nhung cho hoi lau")

        assert result["intent"] == "FEEDBACK"
        assert result["confidence"] >= 0.0

    def test_invalid_detected(self):
        """'aaaa 123 xyz' → INVALID."""
        llm_output = json.dumps({
            "intent": "INVALID",
            "confidence": 0.98,
            "reason": "Ky tu rac, khong co noi dung"
        })
        with patch.dict("os.environ", _env()):
            with patch("google.genai.Client") as mock_cls:
                mock_cls.return_value = _mock_client(llm_output)
                result = classify_intent("aaaa 123 xyz")

        assert result["intent"] == "INVALID"

    def test_result_has_all_required_fields(self):
        """Output phải có intent, confidence, reason."""
        llm_output = json.dumps({
            "intent": "FEEDBACK",
            "confidence": 0.85,
            "reason": "Feedback binh thuong"
        })
        with patch.dict("os.environ", _env()):
            with patch("google.genai.Client") as mock_cls:
                mock_cls.return_value = _mock_client(llm_output)
                result = classify_intent("Quan dep")

        assert "intent" in result
        assert "confidence" in result
        assert "reason" in result
        assert result["intent"] in VALID_INTENTS
        assert 0.0 <= result["confidence"] <= 1.0


# ---------------------------------------------------------------------------
# Test: Error Handling & Fallback
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_invalid_json_from_llm_returns_fallback(self):
        """LLM trả JSON lỗi → fallback FEEDBACK (không crash)."""
        with patch.dict("os.environ", _env()):
            with patch("google.genai.Client") as mock_cls:
                mock_cls.return_value = _mock_client("NOT JSON AT ALL")
                result = classify_intent("Test")
        assert result["intent"] == "FEEDBACK"

    def test_unknown_intent_from_llm_returns_feedback(self):
        """LLM trả intent không hợp lệ → normalize về FEEDBACK."""
        llm_output = json.dumps({
            "intent": "GARBAGE_INTENT",
            "confidence": 0.5,
            "reason": "test"
        })
        with patch.dict("os.environ", _env()):
            with patch("google.genai.Client") as mock_cls:
                mock_cls.return_value = _mock_client(llm_output)
                result = classify_intent("Test")
        assert result["intent"] == "FEEDBACK"

    def test_api_exception_returns_fallback(self):
        """API raise exception → fallback FEEDBACK (không crash)."""
        with patch.dict("os.environ", _env()):
            with patch("google.genai.Client") as mock_cls:
                mock_client = MagicMock()
                mock_cls.return_value = mock_client
                mock_client.models.generate_content.side_effect = Exception("API error")
                result = classify_intent("Test")
        assert result["intent"] == "FEEDBACK"

    def test_confidence_clamped_to_range(self):
        """confidence LLM trả ngoài [0,1] → bị clamp."""
        llm_output = json.dumps({
            "intent": "FEEDBACK",
            "confidence": 5.0,  # > 1.0
            "reason": "test"
        })
        with patch.dict("os.environ", _env()):
            with patch("google.genai.Client") as mock_cls:
                mock_cls.return_value = _mock_client(llm_output)
                result = classify_intent("Test")
        assert result["confidence"] <= 1.0

    def test_markdown_wrapped_json_parsed(self):
        """LLM bọc trong `json...` → vẫn parse được."""
        inner = json.dumps({"intent": "SUPPORT_REQUEST", "confidence": 0.9, "reason": "OK"})
        llm_output = f"`json\n{inner}\n`"
        with patch.dict("os.environ", _env()):
            with patch("google.genai.Client") as mock_cls:
                mock_cls.return_value = _mock_client(llm_output)
                result = classify_intent("Can them ghe")
        assert result["intent"] == "SUPPORT_REQUEST"
