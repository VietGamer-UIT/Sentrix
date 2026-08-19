"""
Churn Probability Model — Mô hình RFMS
========================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect) — hỗ trợ bởi Đoàn Hoàng Việt
Giai đoạn: 7B — Tính xác suất rời bỏ khách hàng (Churn Probability)

CÔNG THỨC:
  P_churn = 1 / (1 + e^-(αR + βF + γM - δS + ε))

  Trong đó:
    R = Recency normalized   [0,1] — CAO = lâu không đến → tăng churn risk
    F = Frequency normalized [0,1] — CAO = đến thường    → giảm churn risk
    M = Monetary normalized  [0,1] — CAO = chi nhiều     → giảm churn risk
    S = Sentiment normalized [0,1] — CAO = hài lòng      → giảm churn risk
    α, β, γ, δ = hệ số trọng số (>0)
    ε = bias term (intercept)

  Dấu của từng biến trong exponent:
    +αR  → R tăng làm exponent tăng → sigmoid tăng → P_churn tăng (đúng)
    +βF  → [⚠️ nhưng F tăng nghĩa là TỐT → phải giảm churn]
         → Trong implementation: dùng (1 - F_norm) để đảo chiều, hoặc dùng hệ số âm.
         → Chọn cách dùng hệ số ÂM: exponent = αR - βF - γM - δS + ε
         → Nghĩa là: β, γ, δ > 0, và ký hiệu - ở trước chúng trong công thức.

  ⚠️ THỐNG NHẤT KÝ HIỆU: Công thức trong tài liệu dự án dùng ký hiệu
    P_churn = 1 / (1 + e^-(αR + βF + γM - δS + ε))
  Trong bản thuyết minh, βF và γM có dấu + nhưng ý nghĩa thực là:
  Frequency và Monetary CAO hơn thì churn THẤP hơn — điều này có thể gây nhầm lẫn.
  Implementation ở đây dùng quy ước: β, γ mang dấu ÂM trong exponent nội bộ
  (tức là exponent thực = αR - βF - γM - δS + ε) nhưng API công khai nhận
  α, β, γ, δ đều là số dương và tự xử lý dấu đúng. Xem docstring của
  calculate_churn_probability() để biết chi tiết.

HỆ SỐ MẶC ĐỊNH:
  ⚠️ QUAN TRỌNG: Đây là hệ số KHỞI TẠO GIẢ ĐỊNH dựa trên domain knowledge,
  KHÔNG phải hệ số đã học từ dữ liệu thật.
  Sẽ được thay bằng hệ số từ Logistic Regression (scikit-learn) khi có đủ
  dữ liệu pilot (xem README.md của thư mục này để biết kế hoạch huấn luyện).

  Heuristic ban đầu:
  - Recency quan trọng nhất (nếu lâu không đến → nguy cơ cao nhất): α = 2.5
  - Sentiment là tín hiệu sớm nhất về sự không hài lòng: δ = 2.0
  - Frequency thể hiện thói quen (khó bỏ ngay): β = 1.5
  - Monetary: khách VIP ít có xu hướng rời bỏ: γ = 1.2
  - Bias ε = -1.5 để P_churn baseline (khách trung bình) khoảng 20-30%.

NGƯỠNG CẢNH BÁO MẶC ĐỊNH:
  P_churn > 0.85 → cảnh báo cao, trigger Zalo ZNS (Giai đoạn 9)
"""

import math
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hệ số mặc định — KHỞI TẠO GIẢ ĐỊNH (chưa học từ dữ liệu thật)
# ⚠️ Xem README.md để biết cách thay thế bằng hệ số đã huấn luyện
# ---------------------------------------------------------------------------
DEFAULT_COEFFICIENTS = {
    "alpha":   2.5,    # Hệ số cho R (Recency) — dương, R tăng → churn tăng
    "beta":    1.5,    # Hệ số cho F (Frequency) — dương, F tăng → churn GIẢM
    "gamma":   1.0,    # Hệ số cho M (Monetary) — dương, M tăng → churn GIẢM
    "delta":   3.0,    # Hệ số cho S (Sentiment) — dương, S tăng → churn GIẢM (sentiment quan trọng nhất)
    "epsilon":  1.0,   # Bias term (intercept) — dương để baseline P_churn của khách 'trung bình' ~62%
                       # Cân bằng: khách tốt (R thấp, F/M/S cao) → P_churn thấp hẳn
                       # Khách xấu (R cao, F/M/S thấp) → P_churn cao hẳn
}

# Ngưỡng mặc định để trigger cảnh báo (Giai đoạn 9)
DEFAULT_CHURN_ALERT_THRESHOLD: float = 0.85


def sigmoid(x: float) -> float:
    """Hàm sigmoid: 1 / (1 + e^-x). Xử lý overflow an toàn."""
    # Tránh overflow với exp() khi x rất âm hoặc rất dương
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


def calculate_churn_probability(
    R: float,
    F: float,
    M: float,
    S: float,
    coefficients: Optional[dict] = None,
) -> float:
    """
    Tính xác suất rời bỏ khách hàng P_churn theo công thức hồi quy logistic.

    Công thức nội bộ:
        exponent = α*R - β*F - γ*M - δ*S + ε
        P_churn  = sigmoid(exponent) = 1 / (1 + e^-exponent)

    Lưu ý dấu:
        - R tăng → exponent tăng → P_churn tăng (khách lâu không đến → nguy hiểm hơn ✓)
        - F tăng → exponent giảm → P_churn giảm (khách đến thường xuyên → ít rời bỏ ✓)
        - M tăng → exponent giảm → P_churn giảm (chi nhiều hơn → ít rời bỏ ✓)
        - S tăng → exponent giảm → P_churn giảm (hài lòng hơn → ít rời bỏ ✓)

    Args:
        R: Recency normalized [0,1]   — CAO = lâu không đến
        F: Frequency normalized [0,1] — CAO = đến thường xuyên
        M: Monetary normalized [0,1]  — CAO = chi nhiều
        S: Sentiment normalized [0,1] — CAO = cảm xúc tích cực
        coefficients: dict với keys 'alpha', 'beta', 'gamma', 'delta', 'epsilon'.
                      Nếu None → dùng DEFAULT_COEFFICIENTS.
                      Truyền dict tuỳ chỉnh để thử bộ hệ số đã train thật.

    Returns:
        float: P_churn ∈ [0.0, 1.0] — xác suất rời bỏ.
               0.0 = chắc chắn không rời bỏ, 1.0 = chắc chắn rời bỏ.

    Raises:
        ValueError: Nếu R, F, M, S nằm ngoài [0, 1].
    """
    # --- Validate input ---
    for name, val in [("R", R), ("F", F), ("M", M), ("S", S)]:
        if not (0.0 <= val <= 1.0):
            raise ValueError(
                f"Tham số {name}={val} nằm ngoài [0,1]. "
                "Hãy chạy normalize_rfms() trước khi gọi calculate_churn_probability()."
            )

    # --- Lấy hệ số ---
    coef = coefficients if coefficients is not None else DEFAULT_COEFFICIENTS
    alpha   = float(coef.get("alpha",   DEFAULT_COEFFICIENTS["alpha"]))
    beta    = float(coef.get("beta",    DEFAULT_COEFFICIENTS["beta"]))
    gamma   = float(coef.get("gamma",   DEFAULT_COEFFICIENTS["gamma"]))
    delta   = float(coef.get("delta",   DEFAULT_COEFFICIENTS["delta"]))
    epsilon = float(coef.get("epsilon", DEFAULT_COEFFICIENTS["epsilon"]))

    # --- Tính exponent ---
    # Công thức: αR - βF - γM - δS + ε
    # (F, M, S dùng dấu âm vì tăng các chỉ số này = giảm rủi ro)
    exponent = alpha * R - beta * F - gamma * M - delta * S + epsilon

    # --- Tính sigmoid ---
    p_churn = sigmoid(exponent)
    p_churn = round(p_churn, 6)

    logger.debug(
        f"[Churn] R={R:.4f}, F={F:.4f}, M={M:.4f}, S={S:.4f} "
        f"→ exponent={exponent:.4f} → P_churn={p_churn:.4f}"
    )
    return p_churn


def calculate_churn_full(
    recency_days: float,
    frequency: float,
    monetary: float,
    sentiment_score: float,
    coefficients: Optional[dict] = None,
    churn_threshold: float = DEFAULT_CHURN_ALERT_THRESHOLD,
    **normalize_kwargs,
) -> dict:
    """
    Hàm tổng hợp: chuẩn hoá RFMS rồi tính P_churn trong một bước duy nhất.

    Đây là hàm convenience cho pipeline (feedback.py) — gọi khi muốn kết quả nhanh
    mà không cần gọi riêng normalize_rfms() + calculate_churn_probability().

    Args:
        recency_days:    Số ngày kể từ lần ghé thăm cuối.
        frequency:       Số lần ghé thăm trong kỳ.
        monetary:        Tổng chi tiêu (VNĐ).
        sentiment_score: Điểm cảm xúc [0,1] từ Fusion.
        coefficients:    Hệ số hồi quy (None = dùng default).
        churn_threshold: Ngưỡng để đánh dấu should_alert (default 0.85).
        **normalize_kwargs: Truyền thêm max_recency_days, max_frequency, max_monetary
                            nếu cần override bounds chuẩn hoá.

    Returns:
        {
            "p_churn": float,          # Xác suất rời bỏ [0.0, 1.0]
            "should_alert": bool,      # True nếu p_churn > churn_threshold
            "risk_level": str,         # "Thấp" | "Trung bình" | "Cao" | "Nguy hiểm"
            "R": float,                # Recency normalized
            "F": float,                # Frequency normalized
            "M": float,                # Monetary normalized
            "S": float,                # Sentiment normalized
            "coefficients_used": dict, # Hệ số đã dùng
            "threshold_used": float,   # Ngưỡng cảnh báo đã dùng
        }
    """
    from backend.rfms_model.rfms_calculator import normalize_rfms

    # --- Bước 1: Chuẩn hoá ---
    normalized = normalize_rfms(
        recency_days=recency_days,
        frequency=frequency,
        monetary=monetary,
        sentiment_score=sentiment_score,
        **normalize_kwargs,
    )
    R = normalized["R"]
    F = normalized["F"]
    M = normalized["M"]
    S = normalized["S"]

    # --- Bước 2: Tính churn ---
    p_churn = calculate_churn_probability(R, F, M, S, coefficients=coefficients)

    # ALG-05 FIX: Thống nhất ngưỡng và label với firestore_ops._sentiment_to_risk_level().
    # Trước: chúng dùng 2 bộ ngưỡng + ngôn ngữ khác nhau (Tiếng Việt vs English).
    # Giờ: cả 2 module dùng chung: low (<0.30), medium (0.30-0.85), high (>=0.85).
    # Ngưỡng 0.85 giữ nguyên — khớp churn_threshold mặc định và schema.md.
    if p_churn < 0.30:
        risk_level = "low"
    elif p_churn < 0.85:
        risk_level = "medium"
    else:
        risk_level = "high"

    coef_used = coefficients if coefficients is not None else DEFAULT_COEFFICIENTS

    result = {
        "p_churn":          round(p_churn, 6),
        "should_alert":     p_churn > churn_threshold,
        "risk_level":       risk_level,
        "R":                R,
        "F":                F,
        "M":                M,
        "S":                S,
        "coefficients_used": coef_used,
        "threshold_used":    churn_threshold,
    }

    logger.info(
        f"[Churn Full] recency={recency_days}d, freq={frequency}, "
        f"monetary={monetary:,.0f}₫, sentiment={sentiment_score:.4f} "
        f"→ P_churn={p_churn:.4f} ({risk_level}) "
        f"{'⚠️ ALERT' if result['should_alert'] else ''}"
    )
    return result
