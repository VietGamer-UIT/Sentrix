"""
Test Giai đoạn 6 — ABSA LLM + Dynamic Weighted Fusion
=======================================================
Chạy:
  # Với API key trong .env:
  python backend/tests/test_absa_fusion.py

  # Hoặc truyền thẳng qua env:
  $env:GEMINI_API_KEY="AIza..."; python backend/tests/test_absa_fusion.py

Test cases:
  1. Câu khen thật lòng → Tích cực
  2. Câu chê thẳng      → Tiêu cực
  3. Câu mỉa mai (text) → LLM phát hiện sarcasm hoặc Fusion phát hiện từ audio
  4. Spam/Nonsense      → is_spam = True
  5. Fusion mâu thuẫn   → is_sarcasm_suspected = True, audio wins
"""

import os
import sys
import json
import logging
from pathlib import Path

# Load .env nếu có
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
    load_dotenv(Path(__file__).parent.parent.parent / "backend" / ".env")
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.WARNING,  # Bật INFO để debug, WARNING để gọn output
    format="%(asctime)s [%(levelname)s] %(message)s"
)

from backend.ai_pipeline.absa_llm import analyze_absa, ABSAAuthError, ABSAParseError, ABSAError
from backend.ai_pipeline.fusion import dynamic_weighted_fusion


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def run_absa_test(label: str, text: str) -> dict:
    print(f"\n--- {label} ---")
    print(f"Input: {text!r}")
    result = analyze_absa(text)
    print(f"is_spam: {result['is_spam']}")
    print(f"aspects: {json.dumps(result['aspects'], ensure_ascii=False, indent=2)}")
    return result


def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ THIẾU GEMINI_API_KEY!")
        print("Cách chạy:")
        print("  1. Tạo file .env ở thư mục gốc dự án (D:\\Sentrix\\.env)")
        print("     Nội dung: GEMINI_API_KEY=AIza...")
        print("  2. Hoặc: $env:GEMINI_API_KEY='AIza...'; python backend/tests/test_absa_fusion.py")
        sys.exit(1)

    print_section("TEST 6A: ABSA LLM với 4 câu mẫu tiếng Việt")

    # ---- Test 1: Khen thật lòng ----
    r1 = run_absa_test(
        "Test 1: Khen thật lòng",
        "Món phở ngon lắm, nước dùng đậm đà. Nhân viên phục vụ nhiệt tình và thân thiện!"
    )

    # ---- Test 2: Chê thẳng ----
    r2 = run_absa_test(
        "Test 2: Chê thẳng thắn",
        "Chờ 45 phút mới có đồ ăn, món ra nguội ngắt. Nhân viên thái độ khó chịu kinh khủng."
    )

    # ---- Test 3: Mỉa mai (text) ----
    r3 = run_absa_test(
        "Test 3: Mỉa mai rõ ràng",
        "Phục vụ tốt quá ha, đợi mãi mới ra! Không gian cũng 'đẹp' lắm nhỉ."
    )

    # ---- Test 4: Spam ----
    r4 = run_absa_test(
        "Test 4: Spam / Nonsense",
        "aaaa 111 !!! xzxzxzxz"
    )

    # ---- Test 5: Fusion mâu thuẫn (audio stress cao nhưng text tích cực) ----
    print_section("TEST 6B: Dynamic Weighted Fusion — mâu thuẫn text vs audio")

    # Giả lập: text nói "hay lắm" nhưng audio có stress_score = 0.72 (rất căng thẳng)
    fake_positive_absa = {
        "is_spam": False,
        "aspects": [
            {"aspect": "Chất lượng món ăn", "sentiment": "Tích cực", "reason": "Ngon lắm"},
            {"aspect": "Thái độ nhân viên", "sentiment": "Tích cực", "reason": "Thân thiện"},
        ],
        "raw_llm_output": ""
    }
    fake_stressed_audio = {
        "f0_mean": 320.5,
        "jitter": 0.065,
        "shimmer": 0.92,
        "stress_score": 0.72,   # RẤT căng thẳng — vượt ngưỡng 0.45
        "duration_sec": 4.5,
        "sample_rate": 22050,
    }

    print(f"\n--- Test 5: Fusion mâu thuẫn ---")
    print(f"ABSA (text): {json.dumps(fake_positive_absa['aspects'], ensure_ascii=False)}")
    print(f"Audio stress_score: {fake_stressed_audio['stress_score']} (ngưỡng conflict: 0.45)")

    fusion_result = dynamic_weighted_fusion(fake_positive_absa, fake_stressed_audio)
    print(f"\nKết quả Fusion:")
    print(json.dumps({
        k: v for k, v in fusion_result.items() if k != "aspects"
    }, ensure_ascii=False, indent=2))
    print(f"  → is_sarcasm_suspected = {fusion_result['is_sarcasm_suspected']}")
    print(f"  → fusion_mode = {fusion_result['fusion_mode']}")
    print(f"  → sentiment_score = {fusion_result['sentiment_score']} (giảm từ text={fusion_result['text_sentiment_score']})")

    # ---- Test 6: Fusion đồng thuận ----
    print(f"\n--- Test 6: Fusion đồng thuận (cả hai tiêu cực) ---")
    fusion_agree = dynamic_weighted_fusion(r2, {"stress_score": 0.68, "f0_mean": 290.0, "jitter": 0.055})
    print(f"  → sentiment_score = {fusion_agree['sentiment_score']}")
    print(f"  → overall_sentiment = {fusion_agree['overall_sentiment']}")
    print(f"  → is_sarcasm_suspected = {fusion_agree['is_sarcasm_suspected']}")
    print(f"  → fusion_mode = {fusion_agree['fusion_mode']}")

    print_section("✅ KẾT QUẢ TỔNG KẾT")
    print(f"[Test 1 - Khen]    sentiment_score = {dynamic_weighted_fusion(r1, {'stress_score': 0.08})['sentiment_score']}")
    print(f"[Test 2 - Chê]     sentiment_score = {dynamic_weighted_fusion(r2, {'stress_score': 0.65})['sentiment_score']}")
    print(f"[Test 3 - Mỉa mai] is_spam={r3['is_spam']}, aspects={len(r3['aspects'])} found")
    print(f"[Test 4 - Spam]    is_spam={r4['is_spam']}")
    print(f"[Test 5 - Conflict] is_sarcasm={fusion_result['is_sarcasm_suspected']}, mode={fusion_result['fusion_mode']}")


if __name__ == "__main__":
    main()
