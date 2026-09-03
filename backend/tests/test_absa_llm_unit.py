"""
Unit Tests Giai đoạn 6 — ABSA LLM + Dynamic Weighted Fusion
=============================================================
Chạy: pytest backend/tests/test_absa_llm_unit.py -v

- Unit tests: Mock Gemini API để test logic xử lý lỗi và parse JSON
  mà KHÔNG tốn API quota.
- Fusion tests: Không cần mock vì fusion.py không gọi API.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from backend.ai_pipeline.absa_llm import (
    analyze_absa,
    _strip_markdown,
    _parse_llm_output,
    ABSAAuthError,
    ABSAParseError,
    ABSAError,
    DEFAULT_MODEL,
)
from backend.ai_pipeline.fusion import (
    dynamic_weighted_fusion,
    _compute_text_sentiment_score,
    _sentiment_label,
    SARCASM_TEXT_POSITIVE_THRESHOLD,
    SARCASM_AUDIO_STRESS_THRESHOLD,
)


# ---------------------------------------------------------------------------
# Test: Helpers
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_strip_markdown_json_block(self):
        raw = "```json\n[{\"a\": 1}]\n```"
        assert _strip_markdown(raw) == '[{"a": 1}]'

    def test_strip_markdown_plain_backtick(self):
        raw = "```\n[]\n```"
        assert _strip_markdown(raw) == "[]"

    def test_strip_markdown_already_clean(self):
        raw = '[{"aspect": "test"}]'
        assert _strip_markdown(raw) == '[{"aspect": "test"}]'

    def test_parse_valid_list(self):
        raw = '[{"aspect": "Thái độ", "sentiment": "Tích cực", "reason": "Tốt"}]'
        result = _parse_llm_output(raw)
        assert isinstance(result, list)
        assert result[0]["aspect"] == "Thái độ"

    def test_parse_valid_spam_dict(self):
        raw = '{"is_spam": true, "aspects": []}'
        result = _parse_llm_output(raw)
        assert isinstance(result, dict)
        assert result["is_spam"] is True

    def test_parse_invalid_json_raises(self):
        with pytest.raises(ABSAParseError):
            _parse_llm_output("INVALID JSON HERE {{{")

    def test_compute_text_score_all_positive(self):
        aspects = [
            {"aspect": "A", "sentiment": "Tích cực"},
            {"aspect": "B", "sentiment": "Tích cực"},
        ]
        assert _compute_text_sentiment_score(aspects) == 1.0

    def test_compute_text_score_all_negative(self):
        aspects = [{"aspect": "A", "sentiment": "Tiêu cực"}]
        assert _compute_text_sentiment_score(aspects) == 0.0

    def test_compute_text_score_mixed(self):
        aspects = [
            {"aspect": "A", "sentiment": "Tích cực"},
            {"aspect": "B", "sentiment": "Tiêu cực"},
        ]
        assert _compute_text_sentiment_score(aspects) == 0.5

    def test_compute_text_score_empty(self):
        assert _compute_text_sentiment_score([]) == 0.5

    def test_sentiment_label_positive(self):
        assert _sentiment_label(0.8) == "Tích cực"

    def test_sentiment_label_negative(self):
        assert _sentiment_label(0.2) == "Tiêu cực"

    def test_sentiment_label_neutral(self):
        assert _sentiment_label(0.5) == "Trung lập"


# ---------------------------------------------------------------------------
# Test: analyze_absa — Logic lỗi (mock API)
# ---------------------------------------------------------------------------

class TestAnalyzeABSA:
    def _mock_env(self):
        return {"GEMINI_API_KEY": "fake-key-for-testing", "GEMINI_MODEL_NAME": DEFAULT_MODEL}

    def _mock_client(self, return_text: str):
        """Tạo mock cho google.genai.Client."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = return_text
        mock_client.models.generate_content.return_value = mock_response
        return mock_client

    def test_empty_text_returns_spam(self):
        """Text rỗng → is_spam=True ngay, không gọi API."""
        result = analyze_absa("")
        assert result["is_spam"] is True
        assert result["aspects"] == []

    def test_whitespace_text_returns_spam(self):
        result = analyze_absa("   ")
        assert result["is_spam"] is True

    def test_missing_api_key_raises_auth_error(self):
        """Không có GEMINI_API_KEY → ABSAAuthError."""
        env_without_key = {}
        with patch.dict("os.environ", env_without_key, clear=True):
            with pytest.raises(ABSAAuthError, match="GEMINI_API_KEY"):
                analyze_absa("Phục vụ tốt")

    def test_valid_positive_review_parsed(self):
        """LLM trả về JSON hợp lệ (tích cực) → aspects đầy đủ."""
        mock_output = '[{"aspect": "Chất lượng món ăn", "sentiment": "Tích cực", "reason": "Ngon lắm"}]'
        with patch.dict("os.environ", self._mock_env()):
            with patch("google.genai.Client") as mock_cls:
                mock_cls.return_value = self._mock_client(mock_output)
                result = analyze_absa("Món ăn ngon lắm")
        assert result["is_spam"] is False
        assert len(result["aspects"]) == 1
        assert result["aspects"][0]["sentiment"] == "Tích cực"

    def test_spam_signal_from_llm(self):
        """LLM trả về {is_spam: true} → is_spam=True."""
        mock_output = '{"is_spam": true, "aspects": []}'
        with patch.dict("os.environ", self._mock_env()):
            with patch("google.genai.Client") as mock_cls:
                mock_cls.return_value = self._mock_client(mock_output)
                result = analyze_absa("aaaa bbb 123 xz")
        assert result["is_spam"] is True
        assert result["aspects"] == []

    def test_markdown_wrapped_json_parsed(self):
        """LLM bọc trong ```json ... ``` → vẫn parse được."""
        mock_output = '```json\n[{"aspect": "Giá cả", "sentiment": "Trung lập", "reason": "Hơi đắt"}]\n```'
        with patch.dict("os.environ", self._mock_env()):
            with patch("google.genai.Client") as mock_cls:
                mock_cls.return_value = self._mock_client(mock_output)
                result = analyze_absa("Giá hơi đắt")
        assert len(result["aspects"]) == 1
        assert result["aspects"][0]["aspect"] == "Giá cả"

    def test_invalid_json_retry_succeeds(self):
        """Lần 1 JSON lỗi, lần 2 thành công → retry hoạt động."""
        good_output = '[{"aspect": "Thái độ nhân viên", "sentiment": "Tiêu cực", "reason": "Chậm"}]'
        call_count = [0]

        def mock_generate(*args, **kwargs):
            call_count[0] += 1
            mock_resp = MagicMock()
            if call_count[0] == 1:
                mock_resp.text = "INVALID JSON"
            else:
                mock_resp.text = good_output
            return mock_resp

        with patch.dict("os.environ", self._mock_env()):
            with patch("google.genai.Client") as mock_cls:
                mock_client = MagicMock()
                mock_cls.return_value = mock_client
                mock_client.models.generate_content.side_effect = mock_generate
                with patch("backend.ai_pipeline.absa_llm.time.sleep"):  # skip delay
                    result = analyze_absa("Phục vụ chậm")
        assert call_count[0] == 2
        assert len(result["aspects"]) == 1

    def test_invalid_json_both_retries_fail_raises(self):
        """Cả 2 lần đều trả JSON sai → ABSAParseError."""
        with patch.dict("os.environ", self._mock_env()):
            with patch("google.genai.Client") as mock_cls:
                mock_client = MagicMock()
                mock_cls.return_value = mock_client
                mock_resp = MagicMock()
                mock_resp.text = "NOT JSON AT ALL"
                mock_client.models.generate_content.return_value = mock_resp
                with patch("backend.ai_pipeline.absa_llm.time.sleep"):
                    with pytest.raises(ABSAParseError):
                        analyze_absa("Test")


# ---------------------------------------------------------------------------
# Test: Dynamic Weighted Fusion
# ---------------------------------------------------------------------------

class TestDynamicWeightedFusion:
    """Không cần mock — fusion.py hoàn toàn offline."""

    def _make_absa(self, aspects, is_spam=False):
        return {"is_spam": is_spam, "aspects": aspects, "raw_llm_output": ""}

    def _make_audio(self, stress_score):
        return {
            "f0_mean": 200.0,
            "jitter": 0.01,
            "shimmer": 0.3,
            "stress_score": stress_score,
            "duration_sec": 3.0,
            "sample_rate": 22050,
        }

    def test_spam_returns_low_score(self):
        result = dynamic_weighted_fusion(
            self._make_absa([], is_spam=True), None
        )
        assert result["sentiment_score"] <= 0.2
        assert result["is_spam"] is True
        assert result["fusion_mode"] == "spam"

    def test_text_only_no_audio(self):
        """Không có audio → dùng text score thuần."""
        aspects = [{"aspect": "A", "sentiment": "Tích cực"}, {"aspect": "B", "sentiment": "Tích cực"}]
        result = dynamic_weighted_fusion(self._make_absa(aspects), None)
        assert result["sentiment_score"] == 1.0
        assert result["fusion_mode"] == "text_only"
        assert result["is_sarcasm_suspected"] is False

    def test_conflict_sarcasm_detected(self):
        """
        Text tích cực (score > 0.5) + audio stress cao (> 0.45)
        → is_sarcasm_suspected = True, audio wins.
        """
        positive_aspects = [
            {"aspect": "Thái độ nhân viên", "sentiment": "Tích cực", "reason": "Tốt"},
            {"aspect": "Món ăn", "sentiment": "Tích cực", "reason": "Ngon"},
        ]
        # stress_score = 0.72 → vượt ngưỡng SARCASM_AUDIO_STRESS_THRESHOLD
        result = dynamic_weighted_fusion(
            self._make_absa(positive_aspects),
            self._make_audio(0.72)
        )
        assert result["is_sarcasm_suspected"] is True
        assert result["fusion_mode"] == "conflict_audio_wins"
        # Score phải thấp hơn score gốc của text (1.0) do audio kéo xuống
        assert result["sentiment_score"] < result["text_sentiment_score"]

    def test_agreement_both_negative(self):
        """Cả text lẫn audio đều tiêu cực → đồng thuận, score thấp."""
        negative_aspects = [{"aspect": "A", "sentiment": "Tiêu cực"}]
        result = dynamic_weighted_fusion(
            self._make_absa(negative_aspects),
            self._make_audio(0.70)  # stress cao = âm thanh tiêu cực
        )
        assert result["fusion_mode"] == "agreement"
        assert result["is_sarcasm_suspected"] is False
        assert result["sentiment_score"] < 0.5

    def test_agreement_both_positive(self):
        """Cả hai tích cực → score cao."""
        positive_aspects = [{"aspect": "A", "sentiment": "Tích cực"}]
        result = dynamic_weighted_fusion(
            self._make_absa(positive_aspects),
            self._make_audio(0.05)  # stress thấp = bình tĩnh
        )
        assert result["fusion_mode"] == "agreement"
        assert result["sentiment_score"] > 0.5

    def test_sarcasm_threshold_boundary(self):
        """Stress đúng bằng ngưỡng → KHÔNG bị đánh dấu mỉa mai."""
        positive_aspects = [{"aspect": "A", "sentiment": "Tích cực"}]
        # stress_score == ngưỡng (không vượt qua)
        result = dynamic_weighted_fusion(
            self._make_absa(positive_aspects),
            self._make_audio(SARCASM_AUDIO_STRESS_THRESHOLD)
        )
        # Bằng ngưỡng → KHÔNG conflict (phải > ngưỡng)
        assert result["is_sarcasm_suspected"] is False

    def test_output_has_all_required_fields(self):
        """Kiểm tra output có đủ tất cả field cần thiết."""
        result = dynamic_weighted_fusion(
            self._make_absa([{"aspect": "A", "sentiment": "Trung lập"}]),
            self._make_audio(0.3)
        )
        required_fields = [
            "sentiment_score", "overall_sentiment", "is_sarcasm_suspected",
            "text_sentiment_score", "audio_stress_score", "fusion_mode",
            "aspects", "is_spam"
        ]
        for field in required_fields:
            assert field in result, f"Thiếu field: {field}"

    def test_sentiment_score_in_range(self):
        """sentiment_score luôn nằm trong [-1, +1] (external scale theo schema.md).

        Lý do: fusion.py convert internal [0,1] → external [-1,+1] theo công thức:
            external = (internal - 0.5) * 2
        Vậy:
            internal 0.0  → external -1.0  (rất tiêu cực)
            internal 0.5  → external  0.0  (trung lập)
            internal 1.0  → external +1.0  (rất tích cực)
        Khi sarcasm (conflict path) final_score có thể ở đầu dải internal, vẫn hợp lệ.
        """
        for stress in [0.0, 0.3, 0.5, 0.7, 1.0]:
            result = dynamic_weighted_fusion(
                self._make_absa([{"aspect": "A", "sentiment": "Tích cực"}]),
                self._make_audio(stress)
            )
            assert -1.0 <= result["sentiment_score"] <= 1.0, (
                f"sentiment_score={result['sentiment_score']} ngoài [-1,+1] với stress={stress}"
            )
