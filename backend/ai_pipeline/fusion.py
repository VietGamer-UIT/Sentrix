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

NGƯỠNG MÂU THUẪN (tinh chỉnh — v2, dựa trên phản hồi dữ liệu thực):
  - text_sentiment_score > 0.5 (tích cực)  VÀ  audio_stress_score > 0.80
  → Được xem là mâu thuẫn, nghi ngờ mỉa mai.

  Tại sao ngưỡng cao (0.80) thay vì 0.45 như trước?
  → Vì Librosa chưa ổn định: tiếng ồn nền, quán đông, micro kém đều
    khiến stress_score tăng giả tạo dù khách hàng có giọng bình thường.
  → KHI Librosa được kiểm tra kỹ và ổn định hơn: hạ về ~0.55–0.60 là hợp lý.

TRỌNG SỐ (PROVISIONAL — tạm thời trong khi Whisper + Librosa chưa ổn định):
  Mục tiêu dài hạn: ưu tiên giọng nói (audio 60%, text 40%) vì giọng
  chứa cảm xúc thật mà người nói khó kiểm soát hơn. Tuy nhiên
  hiện tại Whisper STT và Librosa chưa được QA kỹ → tạm dùng text làm chủ
  đạo (80%) để đảm bảo kết quả chính xác.
  TODO: Khi Whisper + Librosa QA xong → đổi TEXT_WEIGHT=0.40, AUDIO_WEIGHT=0.60.

KẾT QUẢ TRẢ VỀ:
  {
    "sentiment_score": float [0.0 → 1.0],  # Dùng làm S trong RFMS
    "overall_sentiment": "Tích cực" | "Tiêu cực" | "Trung lập",
    "is_sarcasm_suspected": bool,
    "text_sentiment_score": float,
    "audio_stress_score": float,
    "fusion_mode": "agreement" | "conflict_audio_wins",
    "aspects": list[dict],  # Pass-through từ ABSA, đã được normalize
  }

THAY ĐỔI (fix phân loại khía cạnh):
  - Thêm ASPECT_CATEGORY_MAP: map free-text aspect tiếng Việt → enum category
  - Thêm hàm normalize_aspects_for_db(): chuẩn hóa aspects list trước khi lưu DB
    + thêm field 'category' (enum), 'score' (numeric [-1, 1]), 'sentiment_en' (eng)
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ngưỡng Fusion
# ---------------------------------------------------------------------------
SARCASM_TEXT_POSITIVE_THRESHOLD = 0.5   # text_score > này → văn bản tích cực

# Ngưỡng mỉa mai tạm thời cao (0.80) vì Librosa chưa ổn định:
# tiếng ồn nền / micro kém có thể đẩy stress_score lên giả tạo.
# TODO: Khi Librosa QA xong → hạ về 0.55–0.60
SARCASM_AUDIO_STRESS_THRESHOLD  = 0.80

# TRọNG SỐ PROVISIONAL — tạm thời trong khi Whisper + Librosa chưa ổn định.
# Mục tiêu dài hạn (khi audio QA xong): TEXT_WEIGHT=0.40, AUDIO_WEIGHT=0.60
# (vì giọng nói phản ánh cảm xúc thật mà người nói khó che giấu hơn)
TEXT_WEIGHT  = 0.80  # PROVISIONAL: sẽ giảm xuống 0.40 khi audio ổn định
AUDIO_WEIGHT = 0.20  # PROVISIONAL: sẽ tăng lên 0.60 khi audio ổn định


# ---------------------------------------------------------------------------
# Bảng map aspect category — free-text tiếng Việt → enum chuẩn DB
# ---------------------------------------------------------------------------
ASPECT_CATEGORY_MAP: dict[str, str] = {
    # Nhân viên / phục vụ
    "thái độ nhân viên": "nhan_vien",
    "nhân viên": "nhan_vien",
    "phục vụ": "nhan_vien",
    "thái độ phục vụ": "nhan_vien",
    "thái độ": "nhan_vien",
    "nhân viên phục vụ": "nhan_vien",

    # Món ăn / dịch vụ
    "chất lượng món ăn": "mon_an",
    "món ăn": "mon_an",
    "đồ ăn": "mon_an",
    "thức ăn": "mon_an",
    "đồ uống": "mon_an",
    "đồ uống / món ăn": "mon_an",
    "chất lượng dịch vụ": "mon_an",
    "dịch vụ": "mon_an",

    # Không gian / môi trường
    "không gian": "khong_gian",
    "môi trường": "khong_gian",
    "không gian / môi trường": "khong_gian",
    "không khí": "khong_gian",
    "trang trí": "khong_gian",
    "âm nhạc": "khong_gian",

    # Giá cả
    "giá cả": "gia_ca",
    "giá": "gia_ca",
    "chi phí": "gia_ca",
    "giá tiền": "gia_ca",

    # Tốc độ phục vụ / thời gian chờ
    "thời gian chờ đợi": "toc_do_phuc_vu",
    "tốc độ phục vụ": "toc_do_phuc_vu",
    "thời gian chờ": "toc_do_phuc_vu",
    "tốc độ": "toc_do_phuc_vu",
    "thời gian chờ đợi / tốc độ phục vụ": "toc_do_phuc_vu",
    "chờ đợi": "toc_do_phuc_vu",

    # Vệ sinh
    "vệ sinh": "ve_sinh",
    "vệ sinh sạch sẽ": "ve_sinh",
    "sạch sẽ": "ve_sinh",

    # Vị trí / tiện lợi
    "vị trí": "vi_tri",
    "vị trí / tiện lợi": "vi_tri",
    "tiện lợi": "vi_tri",
    "bãi đỗ xe": "vi_tri",
}

# Map sentiment tiếng Việt → tiếng Anh (enum DB)
SENTIMENT_VN_TO_EN: dict[str, str] = {
    "tích cực": "positive",
    "tiêu cực": "negative",
    "trung lập": "neutral",
}

# Map sentiment tiếng Việt → numeric score [-1.0, 1.0] (cho DB schema field 'score')
SENTIMENT_VN_TO_SCORE: dict[str, float] = {
    "tích cực": 1.0,
    "tiêu cực": -1.0,
    "trung lập": 0.0,
}


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


def _normalize_aspect_category(aspect_text: str) -> str:
    """
    Map free-text aspect tiếng Việt (từ LLM) → enum category chuẩn DB.

    Tra cứu trong ASPECT_CATEGORY_MAP (case-insensitive, strip whitespace).
    Nếu không tìm thấy → trả về 'khac' (fallback).

    Args:
        aspect_text: Tên khía cạnh tự do từ LLM. Ví dụ: "Chất lượng món ăn"

    Returns:
        str: Enum category. Ví dụ: "mon_an"
    """
    key = aspect_text.strip().lower()
    return ASPECT_CATEGORY_MAP.get(key, "khac")


def normalize_aspects_for_db(aspects: list[dict]) -> list[dict]:
    """
    Chuẩn hóa danh sách aspects từ ABSA LLM → format chuẩn DB schema.

    Input (từ LLM):
        [
            {"aspect": "Chất lượng món ăn", "sentiment": "Tích cực", "reason": "Ngon lắm"},
            ...
        ]

    Output (chuẩn DB):
        [
            {
                "aspect":       "Chất lượng món ăn",   # giữ nguyên text gốc
                "category":     "mon_an",               # enum chuẩn hóa
                "sentiment":    "Tích cực",             # tiếng Việt (giữ nguyên)
                "sentiment_en": "positive",             # tiếng Anh (cho query)
                "score":        1.0,                    # numeric [-1.0, 1.0]
                "reason":       "Ngon lắm",             # từ LLM
                "confidence":   None,                   # LLM hiện không trả confidence
            },
            ...
        ]

    Args:
        aspects: List dict từ ABSA LLM output.

    Returns:
        List dict đã normalize theo schema.md.
    """
    normalized = []
    for item in aspects:
        aspect_text = str(item.get("aspect", "")).strip()
        sentiment_raw = str(item.get("sentiment", "")).strip()
        sentiment_key = sentiment_raw.lower()

        normalized_item = {
            "aspect":       aspect_text,
            "category":     _normalize_aspect_category(aspect_text),
            "sentiment":    sentiment_raw,
            "sentiment_en": SENTIMENT_VN_TO_EN.get(sentiment_key, "neutral"),
            "score":        SENTIMENT_VN_TO_SCORE.get(sentiment_key, 0.0),
            "reason":       str(item.get("reason", "")).strip(),
            "confidence":   item.get("confidence"),  # None nếu LLM không trả về
        }

        # Nếu LLM có sarcasm_suspected, truyền qua
        if item.get("sarcasm_suspected"):
            normalized_item["sarcasm_suspected"] = True

        normalized.append(normalized_item)

    return normalized


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
            "aspects": list[dict],           # Đã normalize theo schema DB
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

    # --- Normalize aspects để lưu DB ---
    normalized_aspects = normalize_aspects_for_db(aspects)

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
        "aspects": normalized_aspects,
        "is_spam": False,
    }

    logger.info(
        f"[Fusion] Kết quả: sentiment_score={final_score:.4f}, "
        f"overall={result['overall_sentiment']}, "
        f"sarcasm={is_sarcasm_suspected}, "
        f"mode={fusion_mode}"
    )
    return result
