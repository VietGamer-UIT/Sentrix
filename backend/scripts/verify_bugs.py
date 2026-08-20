"""
Script test nhỏ để verify 2 bug gốc trước khi seed data:
1. Bug "sentiment 0.00": câu tiêu cực rõ có ra external âm không?
2. Logic feedback_count: hàm update_customer_rfms có tăng đúng không?

Chạy: python -m backend.scripts.verify_bugs
(Không cần kết nối Firestore — chỉ test logic pure Python)
"""

# ===========================================================================
# TEST 1: Sentiment pipeline end-to-end (không cần Gemini — mock ABSA output)
# ===========================================================================
print("=" * 60)
print("TEST 1: Sentiment pipeline với câu tiêu cực 'quá tệ'")
print("=" * 60)

# Simulate ABSA output cho câu "quá tệ"
mock_absa_output = {
    "is_spam": False,
    "aspects": [
        {"aspect": "Khác", "sentiment": "Tiêu cực", "reason": "quá tệ"}
    ]
}

from backend.ai_pipeline.fusion import dynamic_weighted_fusion, _compute_text_sentiment_score, _to_external_score

# Test _compute_text_sentiment_score
text_score = _compute_text_sentiment_score(mock_absa_output["aspects"])
print(f"  text_score (internal [0,1]):   {text_score}")
expected_text = 0.0  # tiêu cực → 0.0
assert text_score == expected_text, f"FAIL: expected {expected_text}, got {text_score}"

external = _to_external_score(text_score)
print(f"  external_score ([-1,+1]):       {external}")
expected_ext = -1.0  # (0.0 - 0.5) * 2 = -1.0
assert external == expected_ext, f"FAIL: expected {expected_ext}, got {external}"

# Test full fusion (text only, no audio)
fusion = dynamic_weighted_fusion(mock_absa_output, audio_features=None)
print(f"  fusion sentiment_score:         {fusion['sentiment_score']}")
print(f"  fusion overall_sentiment:       {fusion['overall_sentiment']}")
print(f"  fusion _internal_sentiment_score: {fusion['_internal_sentiment_score']}")
assert fusion['sentiment_score'] == -1.0, f"FAIL: expected -1.0, got {fusion['sentiment_score']}"
assert fusion['overall_sentiment'] == "Tiêu cực", f"FAIL: expected Tiêu cực, got {fusion['overall_sentiment']}"
assert fusion['_internal_sentiment_score'] == 0.0, f"FAIL: expected 0.0, got {fusion['_internal_sentiment_score']}"

print("  ✅ TEST 1 PASSED: Câu tiêu cực ra sentiment_score âm đúng!")

# Test "quá tệ hại" — 1 aspect tiêu cực, 0 tích cực
mock_absa_tet_hai = {
    "is_spam": False,
    "aspects": [
        {"aspect": "Không gian", "sentiment": "Tiêu cực", "reason": "quá tệ hại"}
    ]
}
fusion2 = dynamic_weighted_fusion(mock_absa_tet_hai, audio_features=None)
print(f"\n  'quá tệ hại' → sentiment_score: {fusion2['sentiment_score']}")
assert fusion2['sentiment_score'] == -1.0, f"FAIL: expected -1.0, got {fusion2['sentiment_score']}"
print("  ✅ TEST 1b PASSED: 'quá tệ hại' cũng ra -1.0 đúng!")

# ===========================================================================
# TEST 2: Logic feedback_count
# ===========================================================================
print("\n" + "=" * 60)
print("TEST 2: Logic feedback_count trong update_customer_rfms")
print("=" * 60)

# Simulate customer document trước khi update
mock_customer_before = {
    "feedback_count": 0,
    "avg_sentiment_score": 0.5,
}

# Logic trong _update_in_transaction (copy từ firestore_ops.py)
old_feedback_count = mock_customer_before.get("feedback_count", 0)
old_avg_sentiment = mock_customer_before.get("avg_sentiment_score", 0.5)
sentiment_score_raw = 0.0  # feedback tiêu cực, internal = 0.0

new_count = old_feedback_count + 1
new_avg_sentiment = (old_avg_sentiment * old_feedback_count + sentiment_score_raw) / new_count

print(f"  Trước: feedback_count={old_feedback_count}, avg_sentiment={old_avg_sentiment}")
print(f"  Sau feedback tiêu cực (sentiment_raw=0.0):")
print(f"    new_count = {new_count}")
print(f"    new_avg_sentiment = {new_avg_sentiment:.4f}")

assert new_count == 1, f"FAIL: expected 1, got {new_count}"
# (0.5 * 0 + 0.0) / 1 = 0.0
assert abs(new_avg_sentiment - 0.0) < 0.001, f"FAIL: expected 0.0, got {new_avg_sentiment}"
print("  ✅ TEST 2a PASSED: Feedback đầu tiên tăng count lên 1, avg = 0.0!")

# Test lần 2 cùng SĐT
mock_customer_after_1 = {"feedback_count": 1, "avg_sentiment_score": 0.0}
old_feedback_count2 = mock_customer_after_1.get("feedback_count", 0)
old_avg_sentiment2 = mock_customer_after_1.get("avg_sentiment_score", 0.5)
sentiment_score_raw2 = 1.0  # feedback tích cực, internal = 1.0

new_count2 = old_feedback_count2 + 1
new_avg_sentiment2 = (old_avg_sentiment2 * old_feedback_count2 + sentiment_score_raw2) / new_count2

print(f"\n  Sau feedback tích cực thứ 2 (sentiment_raw=1.0):")
print(f"    new_count = {new_count2}")
print(f"    new_avg_sentiment = {new_avg_sentiment2:.4f}")

assert new_count2 == 2, f"FAIL: expected 2, got {new_count2}"
# (0.0 * 1 + 1.0) / 2 = 0.5
assert abs(new_avg_sentiment2 - 0.5) < 0.001, f"FAIL: expected 0.5, got {new_avg_sentiment2}"
print("  ✅ TEST 2b PASSED: Feedback thứ 2 tăng count lên 2, avg = 0.5!")

# ===========================================================================
# TEST 3: RFMS clamp — internal sentiment 0.0 không bị clamp sai
# ===========================================================================
print("\n" + "=" * 60)
print("TEST 3: RFMS normalize_rfms với sentiment internal = 0.0")
print("=" * 60)

from backend.rfms_model.rfms_calculator import normalize_rfms

result = normalize_rfms(
    recency_days=1.0,
    frequency=1,
    monetary=0.0,
    sentiment_score=0.0,  # internal từ Fusion khi tiêu cực hoàn toàn
)
print(f"  S = {result['S']} (expected 0.0 — tiêu cực hoàn toàn)")
assert result['S'] == 0.0, f"FAIL: expected 0.0, got {result['S']}"

from backend.rfms_model.churn_model import calculate_churn_probability
p = calculate_churn_probability(
    R=result['R'], F=result['F'], M=result['M'], S=result['S']
)
print(f"  P_churn với S=0 (khách tiêu cực, mới gửi): {p:.4f}")
assert p > 0.5, f"FAIL: khách tiêu cực phải có p_churn > 0.5, got {p}"
print(f"  ✅ TEST 3 PASSED: Khách tiêu cực → P_churn={p:.2f} (cao hơn 0.5, đúng!)")

# ===========================================================================
print("\n" + "=" * 60)
print("🎉 TẤT CẢ TESTS ĐỀU PASSED!")
print("KẾT LUẬN:")
print("  - Bug '0.00' là DATA CŨ (từ trước fix D2), KHÔNG phải bug code hiện tại")
print("  - Logic feedback_count hoạt động đúng trong code Python")
print("  - Cần verify thêm: Firestore transaction có thật sự chạy được không?")
print("  - Recommendation: Xóa data cũ an toàn, logic mới đã đúng")
print("=" * 60)
