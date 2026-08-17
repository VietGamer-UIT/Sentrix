"""
Test Giai đoạn 3 — Fraud Filter (unit test thuần)
----------------------------------------------------
Chạy: pytest backend/tests/test_fraud_filter.py -v
"""

import pytest
from backend.api.middleware.fraud_filter import basic_fraud_filter, FraudFilterResult


class TestAudioFraudFilter:
    def test_audio_empty_file_rejected(self):
        """Audio 0 byte → should_reject=True."""
        result = basic_fraud_filter(audio_bytes=0)
        assert result.is_suspicious is True
        assert result.should_reject is True
        assert "rỗng" in result.reason.lower() or "0 byte" in result.reason.lower()

    def test_audio_too_short_rejected(self):
        """Audio < 800 bytes (~< 1 giây) → should_reject=True."""
        result = basic_fraud_filter(audio_bytes=500)
        assert result.is_suspicious is True
        assert result.should_reject is True
        assert "ngắn" in result.reason.lower()

    def test_audio_valid_size_passes(self):
        """Audio 50KB → hợp lệ."""
        result = basic_fraud_filter(audio_bytes=50_000)
        assert result.is_suspicious is False
        assert result.should_reject is False

    def test_audio_boundary_exactly_min(self):
        """Audio đúng 800 bytes → hợp lệ (ngưỡng là <800)."""
        result = basic_fraud_filter(audio_bytes=800)
        assert result.is_suspicious is False


class TestTextFraudFilter:
    def test_empty_text_rejected(self):
        """Text rỗng → should_reject=True."""
        result = basic_fraud_filter(text_content="")
        assert result.is_suspicious is True
        assert result.should_reject is True

    def test_whitespace_only_rejected(self):
        """Text chỉ toàn khoảng trắng → should_reject=True."""
        result = basic_fraud_filter(text_content="   \t\n  ")
        assert result.is_suspicious is True
        assert result.should_reject is True

    def test_too_short_text_rejected(self):
        """Text 1-2 ký tự → should_reject=True."""
        result = basic_fraud_filter(text_content="ok")
        assert result.is_suspicious is True
        assert result.should_reject is True

    def test_repeated_single_char_flagged(self):
        """'aaaaaaaaaa' → is_suspicious=True."""
        result = basic_fraud_filter(text_content="aaaaaaaaaa")
        assert result.is_suspicious is True

    def test_repeated_pattern_flagged(self):
        """'asdasdasdasd' → is_suspicious=True."""
        result = basic_fraud_filter(text_content="asdasdasdasd")
        assert result.is_suspicious is True

    def test_valid_vietnamese_text_passes(self):
        """Phản hồi tiếng Việt bình thường → hợp lệ."""
        result = basic_fraud_filter(text_content="Phục vụ tốt, món ăn ngon, không gian thoáng mát.")
        assert result.is_suspicious is False
        assert result.should_reject is False

    def test_valid_short_but_meaningful_text_passes(self):
        """Text ngắn nhưng có nghĩa (>= 3 ký tự) → hợp lệ."""
        result = basic_fraud_filter(text_content="Tốt")
        assert result.is_suspicious is False

    def test_sarcasm_text_not_flagged(self):
        """'Phục vụ tốt quá ha' không bị flag vì pattern tự nhiên."""
        result = basic_fraud_filter(text_content="Phục vụ tốt quá ha")
        assert result.is_suspicious is False

    def test_do_an_ngon_tuyet_not_flagged(self):
        """'đồ ăn ngon tuyệt' — cụm từ thực tế gặp bug — không được flag."""
        result = basic_fraud_filter(text_content="đồ ăn ngon tuyệt")
        assert result.is_suspicious is False
        assert result.should_reject is False

    def test_nhan_vien_phuc_vu_kem_not_flagged(self):
        """'nhân viên phục vụ kém' — cụm từ thực tế gặp bug — không được flag."""
        result = basic_fraud_filter(text_content="nhân viên phục vụ kém")
        assert result.is_suspicious is False
        assert result.should_reject is False

    def test_single_word_meaningful_passes(self):
        """'Ngon' — câu đánh giá 1 từ tiếng Việt hợp lệ."""
        result = basic_fraud_filter(text_content="Ngon")
        assert result.is_suspicious is False

    def test_long_vietnamese_review_passes(self):
        """Câu phản hồi dài bình thường không bị flag."""
        result = basic_fraud_filter(
            text_content="Mình đã ăn ở đây nhiều lần rồi, lần nào cũng hài lòng. Món phở bò rất ngon, nước dùng đậm đà."
        )
        assert result.is_suspicious is False


class TestCombinedInput:
    def test_valid_audio_and_text_passes(self):
        """Cả audio và text đều hợp lệ."""
        result = basic_fraud_filter(
            audio_bytes=10_000,
            text_content="Món ăn ngon lắm",
        )
        assert result.is_suspicious is False

    def test_valid_audio_only_passes(self):
        """Chỉ có audio hợp lệ, không có text."""
        result = basic_fraud_filter(audio_bytes=10_000, text_content=None)
        assert result.is_suspicious is False

    def test_valid_text_only_passes(self):
        """Chỉ có text hợp lệ, không có audio."""
        result = basic_fraud_filter(audio_bytes=None, text_content="Phục vụ ổn")
        assert result.is_suspicious is False
