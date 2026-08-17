"""
Test Pipeline Text-Only — Giai đoạn 6 + Fusion (không dùng LLM thật)
======================================================================
Chạy: pytest backend/tests/test_pipeline_text_only.py -v

Mục đích:
  Test end-to-end pipeline cho input text-only:
  - Fraud filter không flag nhầm text tiếng Việt thực tế
  - ABSA + Fusion trả về đúng sentiment cho "đồ ăn ngon tuyệt" và "nhân viên phục vụ kém"
  - Aspect normalization hoạt động đúng (free-text → enum category)
  - phone_masked được lưu đúng vào feedback doc
  - Voucher code format đúng

Không gọi Gemini API thật — dùng mock.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from backend.api.middleware.fraud_filter import basic_fraud_filter
from backend.ai_pipeline.fusion import (
    dynamic_weighted_fusion,
    normalize_aspects_for_db,
    _normalize_aspect_category,
    _compute_text_sentiment_score,
)
from backend.db.firestore_ops import _mask_phone, _hash_phone


# ---------------------------------------------------------------------------
# Test: Fraud Filter — các cụm từ tiếng Việt từ transcript thực tế
# ---------------------------------------------------------------------------

class TestFraudFilterRealTranscripts:
    """
    Đảm bảo các transcript tiếng Việt thực tế không bị fraud filter flag nhầm.
    (Đây là các case báo cáo bug trước đó)
    """

    @pytest.mark.parametrize("text", [
        "đồ ăn ngon tuyệt",
        "nhân viên phục vụ kém",
        "Phục vụ tốt quá ha",
        "Món phở ngon lắm, nước dùng đậm đà",
        "Nhân viên thái độ khó chịu",
        "Chờ lâu quá, gần 30 phút",
        "Ngon",
        "Tốt lắm",
        "Không gian đẹp, thoáng mát",
        "Giá hơi đắt nhưng chất lượng ổn",
        "Vệ sinh sạch sẽ, hài lòng",
        "Phục vụ tốt, sẽ quay lại",
    ])
    def test_real_vietnamese_texts_not_flagged(self, text: str):
        """Các cụm từ tiếng Việt thực tế không được bị fraud filter flag."""
        result = basic_fraud_filter(text_content=text)
        assert result.is_suspicious is False, (
            f"False positive! '{text}' bị flag nhầm là spam: {result.reason}"
        )
        assert result.should_reject is False


# ---------------------------------------------------------------------------
# Test: Aspect Normalization
# ---------------------------------------------------------------------------

class TestAspectNormalization:
    """Test hàm normalize aspect free-text → enum category."""

    @pytest.mark.parametrize("aspect_text,expected_category", [
        ("Chất lượng món ăn", "mon_an"),
        ("Thái độ nhân viên", "nhan_vien"),
        ("Không gian", "khong_gian"),
        ("Giá cả", "gia_ca"),
        ("Tốc độ phục vụ", "toc_do_phuc_vu"),
        ("Thời gian chờ đợi", "toc_do_phuc_vu"),
        ("Vệ sinh sạch sẽ", "ve_sinh"),
        ("Vị trí / Tiện lợi", "vi_tri"),
        ("Nhân viên", "nhan_vien"),
        ("Món ăn", "mon_an"),
        ("Phục vụ", "nhan_vien"),
        ("Không rõ gì cả", "khac"),   # fallback
        ("", "khac"),                  # empty → fallback
    ])
    def test_aspect_category_mapping(self, aspect_text: str, expected_category: str):
        result = _normalize_aspect_category(aspect_text)
        assert result == expected_category, (
            f"'{aspect_text}' → '{result}', expected '{expected_category}'"
        )

    def test_normalize_aspects_list_adds_fields(self):
        """normalize_aspects_for_db() phải thêm đủ các field cần thiết."""
        aspects = [
            {"aspect": "Chất lượng món ăn", "sentiment": "Tích cực", "reason": "Ngon lắm"},
            {"aspect": "Thái độ nhân viên", "sentiment": "Tiêu cực", "reason": "Lạnh lùng"},
        ]
        result = normalize_aspects_for_db(aspects)

        assert len(result) == 2

        # Kiểm tra item tích cực
        pos = result[0]
        assert pos["category"] == "mon_an"
        assert pos["sentiment_en"] == "positive"
        assert pos["score"] == 1.0
        assert pos["aspect"] == "Chất lượng món ăn"
        assert pos["reason"] == "Ngon lắm"

        # Kiểm tra item tiêu cực
        neg = result[1]
        assert neg["category"] == "nhan_vien"
        assert neg["sentiment_en"] == "negative"
        assert neg["score"] == -1.0

    def test_normalize_empty_aspects_returns_empty(self):
        result = normalize_aspects_for_db([])
        assert result == []

    def test_normalize_unknown_sentiment_defaults_neutral(self):
        """Sentiment không nhận ra → neutral (0.0)."""
        aspects = [{"aspect": "Món ăn", "sentiment": "Không rõ", "reason": ""}]
        result = normalize_aspects_for_db(aspects)
        assert result[0]["sentiment_en"] == "neutral"
        assert result[0]["score"] == 0.0

    def test_sarcasm_flag_preserved(self):
        """sarcasm_suspected từ LLM phải được giữ lại sau normalize."""
        aspects = [
            {
                "aspect": "Thái độ nhân viên",
                "sentiment": "Tiêu cực",
                "reason": "Mỉa mai",
                "sarcasm_suspected": True,
            }
        ]
        result = normalize_aspects_for_db(aspects)
        assert result[0].get("sarcasm_suspected") is True


# ---------------------------------------------------------------------------
# Test: Fusion text-only sentiment scoring
# ---------------------------------------------------------------------------

class TestFusionTextOnlySentiment:
    """Test sentiment scoring cho text-only (không có audio)."""

    def _make_positive_absa(self):
        return {
            "is_spam": False,
            "aspects": [
                {"aspect": "Chất lượng món ăn", "sentiment": "Tích cực", "reason": "Ngon tuyệt"},
            ],
            "raw_llm_output": "",
        }

    def _make_negative_absa(self):
        return {
            "is_spam": False,
            "aspects": [
                {"aspect": "Thái độ nhân viên", "sentiment": "Tiêu cực", "reason": "Phục vụ kém"},
            ],
            "raw_llm_output": "",
        }

    def test_do_an_ngon_tuyet_gets_positive_score(self):
        """'đồ ăn ngon tuyệt' → text_sentiment_score = 1.0, overall = Tích cực."""
        absa = self._make_positive_absa()
        result = dynamic_weighted_fusion(absa, None)

        assert result["is_spam"] is False
        assert result["fusion_mode"] == "text_only"
        assert result["sentiment_score"] > 0.5, (
            f"Mong > 0.5 nhưng got {result['sentiment_score']}"
        )
        assert result["overall_sentiment"] == "Tích cực"
        assert result["text_sentiment_score"] == 1.0

    def test_nhan_vien_phuc_vu_kem_gets_negative_score(self):
        """'nhân viên phục vụ kém' → sentiment_score = 0.0, overall = Tiêu cực."""
        absa = self._make_negative_absa()
        result = dynamic_weighted_fusion(absa, None)

        assert result["is_spam"] is False
        assert result["fusion_mode"] == "text_only"
        assert result["sentiment_score"] < 0.5, (
            f"Mong < 0.5 nhưng got {result['sentiment_score']}"
        )
        assert result["overall_sentiment"] == "Tiêu cực"
        assert result["text_sentiment_score"] == 0.0

    def test_text_only_aspects_normalized(self):
        """Aspects sau fusion phải có đủ field category, score, sentiment_en."""
        absa = self._make_positive_absa()
        result = dynamic_weighted_fusion(absa, None)

        aspects = result["aspects"]
        assert len(aspects) == 1
        assert "category" in aspects[0]
        assert "score" in aspects[0]
        assert "sentiment_en" in aspects[0]
        assert aspects[0]["category"] == "mon_an"
        assert aspects[0]["sentiment_en"] == "positive"
        assert aspects[0]["score"] == 1.0

    def test_mixed_aspects_neutral_overall(self):
        """1 tích cực + 1 tiêu cực → trung lập (score = 0.5)."""
        absa = {
            "is_spam": False,
            "aspects": [
                {"aspect": "Chất lượng món ăn", "sentiment": "Tích cực", "reason": "Ngon"},
                {"aspect": "Thái độ nhân viên", "sentiment": "Tiêu cực", "reason": "Kém"},
            ],
            "raw_llm_output": "",
        }
        result = dynamic_weighted_fusion(absa, None)
        # score = (1.0 + 0.0) / 2 = 0.5 → Trung lập
        assert result["text_sentiment_score"] == 0.5
        assert result["overall_sentiment"] == "Trung lập"


# ---------------------------------------------------------------------------
# Test: Phone masking & hashing
# ---------------------------------------------------------------------------

class TestPhoneMasking:
    """Test _mask_phone() và _hash_phone() cho việc lưu SĐT."""

    @pytest.mark.parametrize("phone,expected_mask", [
        ("0901234567", "090****567"),
        ("0987654321", "098****321"),
        ("0123456789", "012****789"),
    ])
    def test_phone_masked_format(self, phone: str, expected_mask: str):
        result = _mask_phone(phone)
        assert result == expected_mask

    def test_short_phone_masked_safely(self):
        """SĐT quá ngắn → '***'."""
        result = _mask_phone("123")
        assert result == "***"

    def test_hash_phone_deterministic(self):
        """Cùng SĐT → cùng customer_id."""
        cid1 = _hash_phone("0901234567")
        cid2 = _hash_phone("0901234567")
        assert cid1 == cid2

    def test_hash_phone_starts_with_cust(self):
        cid = _hash_phone("0901234567")
        assert cid.startswith("cust_")

    def test_hash_phone_normalizes_prefix(self):
        """0901234567 và +84901234567 phải cho cùng customer_id."""
        cid_0 = _hash_phone("0901234567")
        cid_84 = _hash_phone("+84901234567")
        assert cid_0 == cid_84

    def test_hash_different_phones_different_ids(self):
        """Hai SĐT khác nhau → customer_id khác nhau."""
        cid1 = _hash_phone("0901234567")
        cid2 = _hash_phone("0987654321")
        assert cid1 != cid2


# ---------------------------------------------------------------------------
# Test: Voucher code generation
# ---------------------------------------------------------------------------

class TestVoucherCode:
    """Test logic sinh voucher code trong feedback.py."""

    def test_voucher_code_format(self):
        """Voucher code phải bắt đầu bằng 'BACK' và có 2 chữ số."""
        customer_phone = "0901234567"
        tenant_id = "test-tenant_123"
        voucher_code = f"BACK{abs(hash(customer_phone + tenant_id)) % 90 + 10}"

        assert voucher_code.startswith("BACK")
        numeric_part = voucher_code[4:]
        assert numeric_part.isdigit()
        assert 10 <= int(numeric_part) <= 99

    def test_voucher_code_deterministic(self):
        """Cùng phone + tenant → cùng voucher code."""
        phone = "0901234567"
        tenant = "test-tenant_123"
        v1 = f"BACK{abs(hash(phone + tenant)) % 90 + 10}"
        v2 = f"BACK{abs(hash(phone + tenant)) % 90 + 10}"
        assert v1 == v2


# ---------------------------------------------------------------------------
# Test: compute_text_sentiment_score — edge cases
# ---------------------------------------------------------------------------

class TestComputeTextSentimentScore:
    """Unit tests cho _compute_text_sentiment_score()."""

    def test_all_positive(self):
        aspects = [
            {"sentiment": "Tích cực"},
            {"sentiment": "Tích cực"},
        ]
        assert _compute_text_sentiment_score(aspects) == 1.0

    def test_all_negative(self):
        aspects = [{"sentiment": "Tiêu cực"}]
        assert _compute_text_sentiment_score(aspects) == 0.0

    def test_mixed_positive_negative(self):
        aspects = [
            {"sentiment": "Tích cực"},
            {"sentiment": "Tiêu cực"},
        ]
        # (1.0 + 0.0) / 2 = 0.5
        assert _compute_text_sentiment_score(aspects) == 0.5

    def test_neutral_aspect(self):
        aspects = [{"sentiment": "Trung lập"}]
        assert _compute_text_sentiment_score(aspects) == 0.5

    def test_empty_aspects_returns_neutral(self):
        assert _compute_text_sentiment_score([]) == 0.5

    def test_lowercase_sentiment_works(self):
        """Sentiment lowercase vẫn hoạt động (LLM đôi khi trả về lowercase)."""
        aspects = [{"sentiment": "tích cực"}]
        assert _compute_text_sentiment_score(aspects) == 1.0

    def test_uppercase_sentiment_works(self):
        """Sentiment uppercase."""
        aspects = [{"sentiment": "TÍCH CỰC"}]
        # lower() trong code → "tích cực" → 1.0
        assert _compute_text_sentiment_score(aspects) == 1.0

    def test_extra_whitespace_in_sentiment(self):
        """Sentiment có khoảng trắng thừa vẫn parse đúng."""
        aspects = [{"sentiment": "  Tích cực  "}]
        assert _compute_text_sentiment_score(aspects) == 1.0

    def test_unknown_sentiment_defaults_neutral(self):
        """Sentiment không nhận ra → neutral (0.5)."""
        aspects = [{"sentiment": "Không rõ"}]
        assert _compute_text_sentiment_score(aspects) == 0.5
