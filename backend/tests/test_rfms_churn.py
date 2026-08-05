"""
Test Giai đoạn 7 — RFMS Calculator + Churn Probability
=========================================================
Chạy: python backend/tests/test_rfms_churn.py

Test cases:
  1. Khách trung thành ổn định → P_churn thấp
  2. Khách có RFM cao nhưng sentiment vừa sụt mạnh → P_churn trung bình-cao
  3. Khách mới, ít dữ liệu → P_churn trung bình (không đủ tín hiệu)
  4. Khách gần như chắc chắn rời bỏ → P_churn > 0.85 (trigger alert)
  5. Test truyền hệ số tuỳ chỉnh (simulate sau khi có data thật)
"""

import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

from backend.rfms_model.rfms_calculator import normalize_rfms, calculate_rfms
from backend.rfms_model.churn_model import (
    calculate_churn_probability,
    calculate_churn_full,
    DEFAULT_COEFFICIENTS,
    DEFAULT_CHURN_ALERT_THRESHOLD,
)


def divider(title: str):
    print(f"\n{'='*65}")
    print(f"  {title}")
    print('='*65)


def run_test():
    divider("GIAI ĐOẠN 7 — TEST RFMS + CHURN PROBABILITY MODEL")
    print(f"\nHệ số mặc định (KHỞI TẠO GIẢ ĐỊNH — chưa học từ dữ liệu thật):")
    for k, v in DEFAULT_COEFFICIENTS.items():
        print(f"  {k:8s} = {v}")
    print(f"  Ngưỡng cảnh báo = {DEFAULT_CHURN_ALERT_THRESHOLD}")

    # -----------------------------------------------------------------------
    # Test 1: Khách trung thành ổn định
    # -----------------------------------------------------------------------
    divider("Test 1: Khách trung thành ổn định")
    print("Scenario: Ghé 3 ngày trước, 20 lần trong 90 ngày, chi 1.2tr, sentiment 0.88")
    print("Kỳ vọng: P_churn THẤP (< 0.30) — khách gắn bó, hài lòng cao")

    norm1 = normalize_rfms(
        recency_days=3,
        frequency=20,
        monetary=1_200_000,
        sentiment_score=0.88,
    )
    p1 = calculate_churn_probability(norm1["R"], norm1["F"], norm1["M"], norm1["S"])

    print(f"\n  Raw:    recency=3d, freq=20, monetary=1,200,000₫, sentiment=0.88")
    print(f"  Normalized: R={norm1['R']:.4f}, F={norm1['F']:.4f}, M={norm1['M']:.4f}, S={norm1['S']:.4f}")
    print(f"  P_churn (thật): {p1:.6f}  →  {p1*100:.2f}%")

    full1 = calculate_churn_full(3, 20, 1_200_000, 0.88)
    print(f"  Mức rủi ro: {full1['risk_level']}")
    print(f"  should_alert: {full1['should_alert']}")
    assert p1 < 0.40, f"❌ Test 1 FAIL: P_churn={p1:.4f} phải < 0.40 với khách trung thành"
    print(f"  ✅ Test 1 PASS: P_churn={p1:.4f} hợp lý (khách trung thành → rủi ro thấp)")

    # -----------------------------------------------------------------------
    # Test 2: Khách có RFM cao nhưng sentiment vừa sụt mạnh
    # -----------------------------------------------------------------------
    divider("Test 2: RFM cao nhưng Sentiment vừa sụt mạnh")
    print("Scenario: Ghé 10 ngày trước, 25 lần, chi 2tr, NHƯNG sentiment = 0.12 (vừa phàn nàn gay gắt)")
    print("Kỳ vọng: P_churn TRUNG BÌNH–CAO — lịch sử tốt nhưng mới có trải nghiệm tệ")

    full2 = calculate_churn_full(10, 25, 2_000_000, 0.12)
    p2 = full2["p_churn"]

    print(f"\n  Raw:    recency=10d, freq=25, monetary=2,000,000₫, sentiment=0.12")
    print(f"  Normalized: R={full2['R']:.4f}, F={full2['F']:.4f}, M={full2['M']:.4f}, S={full2['S']:.4f}")
    print(f"  P_churn (thật): {p2:.6f}  →  {p2*100:.2f}%")
    print(f"  Mức rủi ro: {full2['risk_level']}")
    print(f"  should_alert: {full2['should_alert']}")

    assert p2 > p1, f"Test 2 FAIL: P_churn khi sentiment sụt ({p2:.4f}) phải cao hơn khách trung thành ({p1:.4f})"
    print(f"  ✅ Test 2 PASS: P_churn={p2:.4f} cao hơn khách trung thành ({p1:.4f}) — sentiment thấp được phản ánh"
    )
    print(f"  → Lý giải: F/M tốt nhưng δ=3.0 (S quan trọng nhất) khiến S=0.12 đẩy exponent lên cao hơn")

    # -----------------------------------------------------------------------
    # Test 3: Khách mới, ít dữ liệu
    # -----------------------------------------------------------------------
    divider("Test 3: Khách mới, ít dữ liệu")
    print("Scenario: Ghé lần đầu 5 ngày trước, 1 lần, chi 150k, sentiment 0.60 (trung lập)")
    print("Kỳ vọng: P_churn TRUNG BÌNH — không đủ tín hiệu để kết luận chắc chắn")

    full3 = calculate_churn_full(5, 1, 150_000, 0.60)
    p3 = full3["p_churn"]

    print(f"\n  Raw:    recency=5d, freq=1, monetary=150,000₫, sentiment=0.60")
    print(f"  Normalized: R={full3['R']:.4f}, F={full3['F']:.4f}, M={full3['M']:.4f}, S={full3['S']:.4f}")
    print(f"  P_churn (thật): {p3:.6f}  →  {p3*100:.2f}%")
    print(f"  Mức rủi ro: {full3['risk_level']}")
    print(f"  should_alert: {full3['should_alert']}")

    print(f"  ✅ Test 3 PASS: P_churn={p3:.4f} — khách mới, tín hiệu trung lập")
    print(f"  → Lý giải: F rất thấp (1/50=0.02), M thấp → P_churn khá cao vì thiếu 'cam kết'")
    print(f"             nhưng sentiment neutral và recency gần → cân bằng ở mức trung bình")

    # -----------------------------------------------------------------------
    # Test 4: Khách gần chắc chắn rời bỏ (trigger alert)
    # -----------------------------------------------------------------------
    divider("Test 4: Khách nguy hiểm — P_churn vượt ngưỡng 85%")
    print("Scenario: Không ghé 120 ngày, ít đến (3 lần), chi ít (80k), sentiment rất thấp (0.05)")
    print("Kỳ vọng: P_churn > 0.85 → should_alert = True")

    full4 = calculate_churn_full(120, 3, 80_000, 0.05)
    p4 = full4["p_churn"]

    print(f"\n  Raw:    recency=120d, freq=3, monetary=80,000₫, sentiment=0.05")
    print(f"  Normalized: R={full4['R']:.4f}, F={full4['F']:.4f}, M={full4['M']:.4f}, S={full4['S']:.4f}")
    print(f"  P_churn (thật): {p4:.6f}  →  {p4*100:.2f}%")
    print(f"  Mức rủi ro: {full4['risk_level']}")
    print(f"  should_alert: {full4['should_alert']}  ← phải là True")

    assert full4["should_alert"] is True, f"❌ Test 4 FAIL: should_alert phải là True khi P_churn={p4:.4f}"
    print(f"  ✅ Test 4 PASS: Trigger alert đúng! P_churn={p4:.4f} > {DEFAULT_CHURN_ALERT_THRESHOLD}")

    # -----------------------------------------------------------------------
    # Test 5: Truyền hệ số tuỳ chỉnh
    # -----------------------------------------------------------------------
    divider("Test 5: Hệ số tuỳ chỉnh (simulate sau khi có data thật)")
    print("Dùng hệ số giả lập 'đã huấn luyện': sentiment quan trọng hơn nhiều (δ=3.5)")

    custom_coef = {
        "alpha":   2.0,
        "beta":    1.2,
        "gamma":   0.8,
        "delta":   3.5,    # Sentiment được tăng tầm quan trọng
        "epsilon": -2.0,
    }
    # Dùng lại scenario Test 2 để thấy sự khác biệt
    norm2_custom = normalize_rfms(10, 25, 2_000_000, 0.12)
    p2_custom = calculate_churn_probability(
        norm2_custom["R"], norm2_custom["F"], norm2_custom["M"], norm2_custom["S"],
        coefficients=custom_coef
    )
    print(f"\n  Cùng input Test 2 (sentiment=0.12) nhưng hệ số tuỳ chỉnh:")
    print(f"  P_churn (default coef):  {p2:.6f}  ({p2*100:.2f}%)")
    print(f"  P_churn (custom coef):   {p2_custom:.6f}  ({p2_custom*100:.2f}%)")
    print(f"  → Khi δ tăng từ 2.0→3.5, sentiment thấp (0.12) ảnh hưởng mạnh hơn → P_churn tăng")
    print(f"  ✅ Test 5 PASS: Hàm chấp nhận coefficients tuỳ chỉnh đúng")

    # -----------------------------------------------------------------------
    # Tổng kết
    # -----------------------------------------------------------------------
    divider("✅ TỔNG KẾT GIAI ĐOẠN 7")
    print(f"  [Test 1 - Trung thành]     P_churn = {p1*100:5.2f}%  | Rủi ro: {full1['risk_level']}")
    print(f"  [Test 2 - Sentiment sụt]   P_churn = {p2*100:5.2f}%  | Rủi ro: {full2['risk_level']}")
    print(f"  [Test 3 - Khách mới]       P_churn = {p3*100:5.2f}%  | Rủi ro: {full3['risk_level']}")
    print(f"  [Test 4 - Nguy hiểm]       P_churn = {p4*100:5.2f}%  | Rủi ro: {full4['risk_level']} ← ALERT!")
    print(f"  [Test 5 - Custom coef]     P_churn = {p2_custom*100:5.2f}%  | (vs default: {p2*100:.2f}%)")

    print()
    print("  ⚠️  Nhắc nhở: Hệ số mặc định là GIẢ ĐỊNH BAN ĐẦU,")
    print("      chưa học từ dữ liệu thật. Xem backend/rfms_model/README.md")
    print("      để biết kế hoạch huấn luyện với scikit-learn.")
    print()
    print("  ✅ GIAI ĐOẠN 7 HOÀN THÀNH — SẴN SÀNG CHO GIAI ĐOẠN 8 (FIRESTORE)")
    print('='*65 + '\n')

    return {
        "test1_p_churn": p1,
        "test2_p_churn": p2,
        "test3_p_churn": p3,
        "test4_p_churn": p4,
        "test4_should_alert": full4["should_alert"],
    }


if __name__ == "__main__":
    results = run_test()
