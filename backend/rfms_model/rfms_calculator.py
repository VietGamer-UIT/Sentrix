"""
RFMS Calculator — Chuẩn hoá chỉ số RFMS
==========================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect) — hỗ trợ bởi Đoàn Hoàng Việt
Giai đoạn: 7A — Chuẩn hoá 4 chỉ số RFMS về thang [0, 1]

MỤC ĐÍCH:
  Chuẩn hoá 4 chỉ số RFMS (Recency, Frequency, Monetary, Sentiment) về cùng
  một thang đo [0.0 → 1.0] trước khi đưa vào công thức hồi quy logistic
  tính P_churn (Giai đoạn 7B).

  Tại sao cần chuẩn hoá?
  - Recency tính bằng ngày (có thể = 365), Frequency tính bằng lần (có thể = 50),
    Monetary tính bằng VNĐ (có thể = 5,000,000). Nếu không chuẩn hoá, các hệ số
    hồi quy α,β,γ,δ sẽ bị dominated bởi các biến có giá trị tuyệt đối lớn.
  - Chuẩn hoá về [0,1] đảm bảo các hệ số có thể so sánh tầm quan trọng tương đối.

PHƯƠNG PHÁP CHUẨN HOÁ:
  Min-Max normalization với bounds được định nghĩa sẵn (business domain knowledge):
  - R_norm = clip(recency_days / MAX_RECENCY_DAYS)  → 0 = mới nhất, 1 = lâu nhất
  - F_norm = clip(frequency / MAX_FREQUENCY)        → 0 = ít nhất, 1 = nhiều nhất
  - M_norm = clip(monetary / MAX_MONETARY)          → 0 = ít nhất, 1 = nhiều nhất
  - S_norm = sentiment_score (đã là [0,1] từ Fusion) → pass-through, clip [0,1]

  ⚠️ NOTE VỀ RECENCY:
    Recency_norm CAO (= 1.0) nghĩa là khách KHÔNG VÀO ĐÃ LÂU → rủi ro CAO.
    Trong công thức RFMS, hệ số α > 0 sẽ làm P_churn tăng khi R_norm tăng.

BOUNDS MẶC ĐỊNH (business heuristics — cần calibrate với dữ liệu pilot thật):
  MAX_RECENCY_DAYS = 180  → Khách không đến > 6 tháng → coi là nguy hiểm tối đa
  MAX_FREQUENCY    = 50   → Khách đến > 50 lần trong kỳ → tần suất tối đa
  MAX_MONETARY     = 5_000_000  → Khách chi > 5 triệu trong kỳ → mức tối đa
"""

import logging
import math
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bounds mặc định — business domain knowledge cho F&B/Spa/Nha khoa VN
# ⚠️ Sẽ cần calibrate khi có dữ liệu pilot thật (xem README.md)
# ---------------------------------------------------------------------------
DEFAULT_MAX_RECENCY_DAYS: float = 180.0      # 6 tháng
DEFAULT_MAX_FREQUENCY: float    = 50.0       # 50 lần ghé thăm trong kỳ
DEFAULT_MAX_MONETARY: float     = 5_000_000.0  # 5 triệu VNĐ


def _clip(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clip giá trị về [min_val, max_val]."""
    return max(min_val, min(max_val, value))


def normalize_rfms(
    recency_days: float,
    frequency: float,
    monetary: float,
    sentiment_score: float,
    max_recency_days: float = DEFAULT_MAX_RECENCY_DAYS,
    max_frequency: float    = DEFAULT_MAX_FREQUENCY,
    max_monetary: float     = DEFAULT_MAX_MONETARY,
) -> dict:
    """
    Chuẩn hoá 4 chỉ số RFMS về thang [0.0, 1.0].

    Args:
        recency_days:    Số ngày kể từ lần ghé thăm cuối cùng.
                         0 = hôm nay, 180+ = lâu rồi không đến.
        frequency:       Số lần ghé thăm trong kỳ đo lường (thường 90 hoặc 180 ngày).
                         0 = chưa đến lần nào, 50+ = khách trung thành cao.
        monetary:        Tổng chi tiêu trong kỳ (VNĐ).
                         0 = chưa chi gì, 5_000_000+ = khách VIP.
        sentiment_score: Điểm cảm xúc tổng hợp từ Fusion (Giai đoạn 6).
                         0.0 = rất tiêu cực, 1.0 = rất tích cực.
                         ĐÃ ở thang [0,1] → pass-through, chỉ clip để an toàn.
        max_recency_days: Giá trị Recency tối đa trong normalization.
        max_frequency:    Giá trị Frequency tối đa.
        max_monetary:     Giá trị Monetary tối đa.

    Returns:
        dict với:
        {
            "R": float,  # Recency normalized [0,1] — CAO = nguy hiểm (lâu không đến)
            "F": float,  # Frequency normalized [0,1] — CAO = tốt (đến thường xuyên)
            "M": float,  # Monetary normalized [0,1] — CAO = tốt (chi nhiều)
            "S": float,  # Sentiment normalized [0,1] — CAO = tốt (cảm xúc tích cực)
            "raw": dict, # Giá trị thô ban đầu (để debug/log)
        }

    Raises:
        ValueError: Nếu các bounds không hợp lệ (≤ 0).
    """
    # --- Validate bounds ---
    if max_recency_days <= 0 or max_frequency <= 0 or max_monetary <= 0:
        raise ValueError(
            "Các bounds (max_recency_days, max_frequency, max_monetary) "
            "phải là số dương."
        )

    # --- Normalize ---
    R = _clip(recency_days / max_recency_days)    # cao = lâu không đến = nguy hiểm
    F = _clip(frequency / max_frequency)          # cao = đến thường = tốt
    M = _clip(monetary / max_monetary)            # cao = chi nhiều = tốt
    S = _clip(sentiment_score)                    # đã là [0,1], chỉ clip an toàn

    result = {
        "R": round(R, 6),
        "F": round(F, 6),
        "M": round(M, 6),
        "S": round(S, 6),
        "raw": {
            "recency_days":    recency_days,
            "frequency":       frequency,
            "monetary":        monetary,
            "sentiment_score": sentiment_score,
        },
        "bounds_used": {
            "max_recency_days": max_recency_days,
            "max_frequency":    max_frequency,
            "max_monetary":     max_monetary,
        },
    }

    logger.debug(
        f"[RFMS Norm] R={R:.4f}, F={F:.4f}, M={M:.4f}, S={S:.4f} "
        f"(raw: recency={recency_days}d, freq={frequency}, "
        f"monetary={monetary:,.0f}₫, sentiment={sentiment_score:.4f})"
    )
    return result


# Alias ngắn hơn để dễ gọi từ pipeline
def calculate_rfms(
    recency_days: float,
    frequency: float,
    monetary: float,
    sentiment_score: float,
    **kwargs,
) -> dict:
    """
    Alias của normalize_rfms() — tên ngắn hơn, dùng được cả 2 cách gọi.

    Xem normalize_rfms() để biết chi tiết tham số và kết quả.
    """
    return normalize_rfms(recency_days, frequency, monetary, sentiment_score, **kwargs)
