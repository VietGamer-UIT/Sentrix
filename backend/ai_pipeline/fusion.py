"""
Dynamic Weighted Fusion — Sentrix
===================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
Giai đoạn: 6B — Hợp nhất tín hiệu văn bản (ABSA) và âm thanh (Librosa)

MỤC ĐÍCH:
  Kết hợp kết quả ABSA (phân tích cảm xúc qua nội dung câu chữ) với
  đặc trưng âm thanh (mức độ căng thẳng từ Librosa) để đưa ra
  điểm cảm xúc cuối cùng (Sentiment Score = S trong công thức RFMS).

NGUYÊN TẮC FUSION:
  - Khi văn bản và âm thanh ĐỒNG THUẬN (cả hai đều tiêu cực / cả hai đều tích cực)
    → kết quả = trung bình có trọng số (text 60%, audio 40%).
  - Khi MÂU THUẪN (text tích cực nhưng audio căng thẳng cao):
    → ƯU TIÊN tín hiệu âm thanh vì người nói mỉa mai thường giữ nguyên câu chữ
      nhưng thay đổi giọng điệu. Đặt cờ is_sarcasm_suspected = True.
    → Điều chỉnh điểm về phía tín hiệu âm thanh.

NGƯỠNG MÂU THUẪN (đề xuất ban đầu — sẽ tinh chỉnh khi có dữ liệu thật):
  - text_sentiment_score > 0.5 (tích cực)  VÀ  audio_stress_score > 0.45
  → Được xem là mâu thuẫn, nghi ngờ mỉa mai.

  Lý do chọn 0.45: Theo nghiên cứu âm học, người nói mỉa mai thường có
  jitter/shimmer cao hơn bình thường ~20-30%, tương đương stress_score ~0.4-0.5.
  Ngưỡng 0.45 là giá trị bảo thủ, tránh nhận định sai khi người nói chỉ hơi lo lắng.

KẾT QUẢ TRẢ VỀ:
  {
    "sentiment_score": float [0.0 → 1.0],  # Dùng làm S trong RFMS
    "overall_sentiment": "Tích cực" | "Tiêu cực" | "Trung lập",
    "is_sarcasm_suspected": bool,
    "text_sentiment_score": float,
    "audio_stress_score": float,
    "fusion_mode": "agreement" | "conflict_audio_wins",
    "aspects": list[dict],  # Pass-through từ ABSA
  }
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ngưỡng Fusion — ghi rõ đây là giá trị ĐỀ XUẤT, sẽ tinh chỉnh sau
# ---------------------------------------------------------------------------
SARCASM_TEXT_POSITIVE_THRESHOLD = 0.5   # text_score > này → văn bản tích cực
SARCASM_AUDIO_STRESS_THRESHOLD = 0.45   # stress_score > này → audio căng thẳng cao

# Trọng số khi đồng thuận: text 60%, audio 40%
TEXT_WEIGHT = 0.60
AUDIO_WEIGHT = 0.40


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_text_sentiment_score(aspects: list[dict]) -> float:
    """
    Tính điểm cảm xúc từ list[dict] kết quả ABSA.

    Quy đổi:
      Tích cực → +1.0
      Trung lập → 0.5
      Tiêu cực → 0.0

    Trả về trung bình cộng, normalize về [0, 1].
    Nếu không có aspect nào → 0.5 (trung lập).
    """
    if not aspects:
        return 0.5

    score_map = {
        "tích cực": 1.0,
        "trung lập": 0.5,
        "tiêu cực": 0.0,
    }

    scores = []
    for aspect in aspects:
        sentiment_raw = str(aspect.get("sentiment", "")).lower().strip()
        score = score_map.get(sentiment_raw, 0.5)
        scores.append(score)

    return round(sum(scores) / len(scores), 4) if scores else 0.5


def _sentiment_label(score: float) -> str:
    """Chuyển điểm số → nhãn cảm xúc dễ đọc."""
    if score >= 0.65:
        return "Tích cực"
    elif score <= 0.35:
        return "Tiêu cực"
    else:
        return "Trung lập"


# ---------------------------------------------------------------------------
# Hàm chính
# ---------------------------------------------------------------------------

def dynamic_weighted_fusion(
    absa_result: dict,
    audio_features: Optional[dict] = None,
) -> dict:
    """
    Hợp nhất tín hiệu văn bản (ABSA) và âm thanh (Librosa) thành điểm S.

    Args:
        absa_result: Output từ `analyze_absa()`:
                     {"is_spam": bool, "aspects": list[dict], ...}
        audio_features: Output từ `extract_audio_features()`:
                        {"stress_score": float, "f0_mean": float, ...}
                        Có thể là None nếu không có audio (text-only input).

    Returns:
        {
            "sentiment_score": float,        # S dùng cho RFMS [0.0 → 1.0]
            "overall_sentiment": str,        # Nhãn đọc được
            "is_sarcasm_suspected": bool,    # Cờ mỉa mai
            "text_sentiment_score": float,
            "audio_stress_score": float | None,
            "fusion_mode": str,
            "aspects": list[dict],
            "is_spam": bool,
        }
    """
    is_spam = absa_result.get("is_spam", False)
    aspects = absa_result.get("aspects", [])

    # --- Trường hợp SPAM: trả về điểm rất thấp ---
    if is_spam:
        logger.info("[Fusion] Input bị đánh dấu SPAM — sentiment_score = 0.1")
        return {
            "sentiment_score": 0.1,
            "overall_sentiment": "Tiêu cực",
            "is_sarcasm_suspected": False,
            "text_sentiment_score": 0.1,
            "audio_stress_score": None,
            "fusion_mode": "spam",
            "aspects": [],
            "is_spam": True,
        }

    # --- Tính điểm text ---
    text_score = _compute_text_sentiment_score(aspects)

    # --- Tính điểm audio ---
    audio_stress = None
    if audio_features and isinstance(audio_features, dict):
        audio_stress = audio_features.get("stress_score")
        if audio_stress is not None:
            audio_stress = float(audio_stress)

    # --- Kiểm tra MÂU THUẪN ---
    is_sarcasm_suspected = False
    fusion_mode = "text_only"
    final_score = text_score

    if audio_stress is not None:
        is_conflict = (
            text_score > SARCASM_TEXT_POSITIVE_THRESHOLD
            and audio_stress > SARCASM_AUDIO_STRESS_THRESHOLD
        )

        if is_conflict:
            # MÂU THUẪN: văn bản tích cực nhưng giọng căng thẳng → mỉa mai
            is_sarcasm_suspected = True
            fusion_mode = "conflict_audio_wins"

            # Điều chỉnh điểm: ưu tiên tín hiệu âm thanh
            # Audio stress_score [0,1] nhưng đây là độ căng thẳng (cao = tiêu cực)
            # Chuyển: audio_sentiment = 1 - stress_score
            audio_sentiment_score = 1.0 - audio_stress
            # Blend: 30% text + 70% audio (audio wins khi mâu thuẫn)
            final_score = round(0.30 * text_score + 0.70 * audio_sentiment_score, 4)

            logger.warning(
                f"[Fusion] PHÁT HIỆN MÂU THUẪN! "
                f"text={text_score:.2f} (tích cực), "
                f"audio_stress={audio_stress:.2f} (căng thẳng cao) "
                f"→ nghi ngờ MỈA MAI. final_score={final_score:.2f}"
            )
        else:
            # ĐỒNG THUẬN: blend bình thường
            audio_sentiment_score = 1.0 - audio_stress
            final_score = round(
                TEXT_WEIGHT * text_score + AUDIO_WEIGHT * audio_sentiment_score, 4
            )
            fusion_mode = "agreement"
            logger.info(
                f"[Fusion] Đồng thuận: text={text_score:.2f}, "
                f"audio_sentiment={audio_sentiment_score:.2f} "
                f"→ final_score={final_score:.2f}"
            )

    result = {
        "sentiment_score": final_score,
        "overall_sentiment": _sentiment_label(final_score),
        "is_sarcasm_suspected": is_sarcasm_suspected,
        "text_sentiment_score": text_score,
        "audio_stress_score": audio_stress,
        "fusion_mode": fusion_mode,
        "aspects": aspects,
        "is_spam": False,
    }

    logger.info(
        f"[Fusion] Kết quả: sentiment_score={final_score:.4f}, "
        f"overall={result['overall_sentiment']}, "
        f"sarcasm={is_sarcasm_suspected}, "
        f"mode={fusion_mode}"
    )
    return result
