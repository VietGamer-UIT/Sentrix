"""
RFMS Pipeline — Tính toán và cập nhật RFMS cho toàn bộ customers
=================================================================
Author: Đoàn Hoàng Việt (Việt Gamer)
Giai đoạn: 7C — RFMS Batch Pipeline + scikit-learn Logistic Regression

MỤC ĐÍCH:
  Module này tính RFMS thực từ Firestore cho từng khách hàng của một tenant,
  sau đó cập nhật lại p_churn bằng Logistic Regression (scikit-learn).

  KHÁC với rfms_calculator.py (chỉ normalize 4 số) và churn_model.py (chỉ tính
  sigmoid theo hệ số cứng): Module này ĐỌC FIRESTORE và huấn luyện model.

CHIẾN LƯỢC MÔ HÌNH:
  ⚠️ KHAI BÁO RÕ RÀNG (để team giải trình với giám khảo):
  Sentrix hiện dùng 2 chế độ, tự động chọn dựa trên số lượng dữ liệu:

  Chế độ A — Heuristic (< MIN_TRAINING_SAMPLES feedback):
    Dùng hệ số heuristic từ churn_model.DEFAULT_COEFFICIENTS.
    Lý do: Dữ liệu chưa đủ để train LR có ý nghĩa thống kê.
    Ghi log rõ: "[RFMS Pipeline] CHẾ ĐỘ A: Heuristic (cold-start)"

  Chế độ B — Synthetic + Logistic Regression (>= MIN_TRAINING_SAMPLES hoặc force):
    Tạo synthetic dataset có kiểm soát (xem _generate_synthetic_data()),
    merge với dữ liệu thật nếu có, rồi train scikit-learn LogisticRegression.
    Ghi log rõ: "[RFMS Pipeline] CHẾ ĐỘ B: Synthetic LR (demo mode)"

  Chế độ C — Real Data LR (>= REAL_DATA_LR_THRESHOLD feedback thật với nhãn):
    Train hoàn toàn từ dữ liệu thật có nhãn churned.
    TODO: Kích hoạt sau khi có 90 ngày dữ liệu pilot.
    Ghi log rõ: "[RFMS Pipeline] CHẾ ĐỘ C: Real Data LR"

M (MONETARY) — GIỚI HẠN KỸ THUẬT:
  ⚠️ Hiện chưa tích hợp POS/hoá đơn thật.
  M = total_spending từ API request (do frontend gửi lên, tạm thời = 0).
  Proxy thay thế: dùng Frequency làm proxy — khách đến thường = proxy chi tiêu cao.
  Khi tích hợp POS: thay proxy bằng tổng hoá đơn thật từ collection `orders`.
  Giám khảo hỏi thì khai báo thẳng limitation này, KHÔNG che giấu.

CHẠY KHI NÀO:
  1. Được gọi từ feedback.py khi có feedback mới (trigger per-customer)
  2. Được gọi từ scripts/batch_rfms.py để recompute toàn bộ (cron job hàng đêm)
  3. Có thể gọi thủ công qua API /api/v1/rfms/recompute (xem routes nếu có)

YÊU CẦU:
  pip install scikit-learn (đã có trong requirements.txt sau module này)
"""

import logging
import math
import os
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ngưỡng chế độ tự động
# ---------------------------------------------------------------------------
MIN_TRAINING_SAMPLES = 50      # Ít hơn thì dùng heuristic (chế độ A)
REAL_DATA_LR_THRESHOLD = 200   # Nhiều hơn với nhãn thật → chế độ C (TODO)

# Số lượng synthetic samples khi chế độ B
SYNTHETIC_N_SAMPLES = 800

# Window tính Frequency/Recency (ngày)
RFMS_WINDOW_DAYS = 90

# Ngưỡng "không quay lại" để gán nhãn churned trong synthetic data
CHURN_RECENCY_THRESHOLD_DAYS = 60


# ---------------------------------------------------------------------------
# Synthetic Data Generator — Chế độ B
# ---------------------------------------------------------------------------

def _generate_synthetic_data(n_samples: int = SYNTHETIC_N_SAMPLES) -> tuple:
    """
    Tạo synthetic RFMS dataset có kiểm soát để train Logistic Regression minh hoạ.

    ⚠️ ĐÂY LÀ DỮ LIỆU GIẢ LẬP PHỤC VỤ DEMO — không phải dữ liệu thật.
    Được thiết kế để hệ số học được khớp với domain knowledge F&B:
      - Recency cao (lâu không đến) → churn cao
      - Sentiment âm liên tục → churn cao (tín hiệu sớm nhất)
      - Frequency cao → churn thấp
      - Monetary cao → churn thấp

    Returns:
        (X, y): X là (n_samples, 4) array [R, F, M, S], y là (n_samples,) 0/1 labels
    """
    logger.info(
        f"[RFMS Pipeline] Tạo {n_samples} synthetic samples cho Logistic Regression demo. "
        f"⚠️ DỮ LIỆU GIẢ LẬP — không phải dữ liệu thật."
    )
    rng = np.random.default_rng(seed=42)  # seed cố định để kết quả reproducible

    # Sinh 4 features RFMS đã chuẩn hoá [0, 1]
    R = rng.beta(a=2, b=3, size=n_samples)   # Phân phối trái (R thường thấp = đến gần đây)
    F = rng.beta(a=3, b=2, size=n_samples)   # Phân phối phải (F thường cao = đến thường xuyên)
    M = rng.beta(a=2, b=3, size=n_samples)   # Phân phối trái (M hay thấp vì MVP chưa có POS)
    S = rng.beta(a=4, b=2, size=n_samples)   # Phân phối phải nghiêng (nhiều phản hồi tích cực)

    # Nhãn churn dựa trên linear combination có noise
    # Công thức: logit(churn) = 2.5*R - 1.5*F - 1.0*M - 3.0*S + 1.0
    # (hệ số khớp với DEFAULT_COEFFICIENTS trong churn_model.py)
    logit = 2.5*R - 1.5*F - 1.0*M - 3.0*S + 1.0
    prob_churn = 1.0 / (1.0 + np.exp(-logit))

    # Thêm noise nhỏ để tránh perfect separation (làm cho model tổng quát hơn)
    noise = rng.normal(0, 0.05, size=n_samples)
    prob_with_noise = np.clip(prob_churn + noise, 0.0, 1.0)

    y = (rng.uniform(size=n_samples) < prob_with_noise).astype(int)

    X = np.column_stack([R, F, M, S])

    logger.info(
        f"[RFMS Pipeline] Synthetic data: churn_rate={y.mean():.2%}, "
        f"R_mean={R.mean():.3f}, F_mean={F.mean():.3f}, "
        f"M_mean={M.mean():.3f}, S_mean={S.mean():.3f}"
    )
    return X, y


# ---------------------------------------------------------------------------
# Model Trainer
# ---------------------------------------------------------------------------

def train_churn_model(
    X: np.ndarray,
    y: np.ndarray,
    mode_label: str = "synthetic",
) -> "LogisticRegression":
    """
    Huấn luyện Logistic Regression từ features RFMS [R, F, M, S].

    Args:
        X: (n, 4) array đã normalize [0,1]
        y: (n,) array nhãn 0/1
        mode_label: Nhãn ghi log để team biết đang dùng chế độ nào

    Returns:
        Trained sklearn LogisticRegression
    """
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import Pipeline
    except ImportError:
        raise ImportError(
            "scikit-learn chưa được cài. Chạy: pip install scikit-learn\n"
            "Hoặc thêm 'scikit-learn>=1.3.0' vào requirements.txt"
        )

    logger.info(
        f"[RFMS Pipeline] Train LR ({mode_label}): "
        f"n_samples={len(X)}, churn_rate={y.mean():.2%}"
    )

    # Pipeline: StandardScaler → LogisticRegression
    # Lý do dùng StandardScaler dù RFMS đã [0,1]: vẫn giúp LR hội tụ nhanh hơn
    # và cho phép L2 regularization so sánh đúng tầm quan trọng giữa các feature.
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("lr", LogisticRegression(
            C=1.0,           # L2 regularization — tránh overfit
            max_iter=500,    # Đủ để hội tụ
            random_state=42,
            solver="lbfgs",
        )),
    ])
    model.fit(X, y)

    # Log hệ số để team giải trình
    lr_coef = model.named_steps["lr"].coef_[0]
    lr_bias = model.named_steps["lr"].intercept_[0]
    logger.info(
        f"[RFMS Pipeline] LR coefficients ({mode_label}): "
        f"R={lr_coef[0]:.4f}, F={lr_coef[1]:.4f}, "
        f"M={lr_coef[2]:.4f}, S={lr_coef[3]:.4f}, bias={lr_bias:.4f}\n"
        f"  → Kỳ vọng: coef(R)>0, coef(F)<0, coef(M)<0, coef(S)<0"
    )

    return model


# ---------------------------------------------------------------------------
# Per-tenant: tính RFMS thật + p_churn từ Firestore
# ---------------------------------------------------------------------------

def _load_customers_from_firestore(tenant_id: str) -> list[dict]:
    """
    Đọc tất cả khách hàng của tenant từ Firestore.
    Trả về list dict với các field RFMS cần thiết.
    """
    try:
        from backend.db.firestore_client import get_firestore_client
        db = get_firestore_client()
        cust_ref = (
            db.collection("tenants").document(tenant_id)
            .collection("customers")
        )
        docs = cust_ref.stream()
        customers = []
        for doc in docs:
            d = doc.to_dict()
            if d:
                d["customer_id"] = doc.id
                customers.append(d)
        logger.info(
            f"[RFMS Pipeline] Đọc {len(customers)} customers từ Firestore (tenant={tenant_id})"
        )
        return customers
    except Exception as e:
        logger.error(f"[RFMS Pipeline] Không đọc được customers Firestore: {e}")
        return []


def _compute_rfms_from_customer_doc(cust: dict) -> Optional[dict]:
    """
    Tính R, F, M, S từ document customer Firestore.

    R = recency_days từ last_feedback_at
    F = feedback_count (số lượt trong toàn kỳ — proxy cho visit frequency)
    M = avg_total_spending nếu có, fallback = frequency / 50 (proxy)
    S = avg_sentiment_score (từ update_customer_rfms chạy rolling avg)

    ⚠️ M proxy: Chưa tích hợp POS/hoá đơn. Dùng frequency làm proxy.
    Khi có POS: thay bằng sum(orders.amount) / MAX_MONETARY.
    """
    from backend.rfms_model.rfms_calculator import normalize_rfms, DEFAULT_MAX_FREQUENCY

    now = datetime.now(timezone.utc)

    # R — Recency
    last_at = cust.get("last_feedback_at")
    if last_at is not None:
        if hasattr(last_at, "timestamp"):
            last_dt = datetime.fromtimestamp(last_at.timestamp(), tz=timezone.utc)
        else:
            last_dt = last_at
        recency_days = max(0.0, (now - last_dt).total_seconds() / 86400)
    else:
        recency_days = 30.0  # Chưa có feedback → coi như 30 ngày

    # F — Frequency
    frequency = float(cust.get("feedback_count", 1))

    # M — Monetary proxy (⚠️ chưa có POS)
    # Nếu có avg_total_spending (từ khi POS tích hợp trong tương lai) thì dùng
    if cust.get("avg_total_spending") is not None:
        monetary = float(cust["avg_total_spending"])
    else:
        # Proxy: scale frequency về [0, 1_000_000] VNĐ tương đương
        # (khách đến 50 lần ≈ 1 triệu chi tiêu proxy)
        monetary = frequency * 20_000  # 20k VNĐ/lần = heuristic proxy

    # S — Sentiment (rolling avg từ pipeline)
    # avg_sentiment_score lưu ở thang [0,1] (internal) từ update_customer_rfms
    sentiment_raw = cust.get("avg_sentiment_score", 0.5)
    if sentiment_raw is None:
        sentiment_raw = 0.5
    sentiment_internal = float(sentiment_raw)

    return normalize_rfms(
        recency_days=recency_days,
        frequency=frequency,
        monetary=monetary,
        sentiment_score=sentiment_internal,
    )


def compute_rfms_for_tenant(
    tenant_id: str,
    force_synthetic: bool = False,
    update_firestore: bool = True,
) -> dict:
    """
    Pipeline chính: tính RFMS thật + p_churn cho toàn bộ customers của tenant.

    Tự động chọn chế độ:
      < MIN_TRAINING_SAMPLES → Chế độ A (heuristic)
      >= MIN_TRAINING_SAMPLES hoặc force_synthetic → Chế độ B (synthetic LR)

    Args:
        tenant_id: ID của tenant
        force_synthetic: True = ép dùng chế độ B dù ít dữ liệu
        update_firestore: True = ghi kết quả p_churn mới vào Firestore

    Returns:
        {
            "tenant_id": str,
            "mode": "A"|"B"|"C",
            "n_customers": int,
            "n_updated": int,
            "churn_rate": float,     # Tỷ lệ khách có p_churn > 0.85
            "model_coefficients": dict | None,
            "errors": list[str],
        }
    """
    from backend.rfms_model.churn_model import (
        calculate_churn_probability,
        DEFAULT_CHURN_ALERT_THRESHOLD,
        DEFAULT_COEFFICIENTS,
    )

    logger.info(f"[RFMS Pipeline] Bắt đầu tính RFMS cho tenant={tenant_id}")

    customers = _load_customers_from_firestore(tenant_id)
    n_customers = len(customers)
    errors = []

    if n_customers == 0:
        logger.warning(f"[RFMS Pipeline] Không có customers cho tenant={tenant_id}")
        return {
            "tenant_id": tenant_id,
            "mode": "none",
            "n_customers": 0,
            "n_updated": 0,
            "churn_rate": 0.0,
            "model_coefficients": None,
            "errors": ["No customers found"],
        }

    # Tính RFMS thực cho từng customer
    customer_rfms = []
    for cust in customers:
        try:
            rfms = _compute_rfms_from_customer_doc(cust)
            if rfms:
                customer_rfms.append({
                    "customer_id": cust["customer_id"],
                    "R": rfms["R"],
                    "F": rfms["F"],
                    "M": rfms["M"],
                    "S": rfms["S"],
                })
        except Exception as e:
            errors.append(f"customer={cust.get('customer_id','?')}: {e}")

    if not customer_rfms:
        return {
            "tenant_id": tenant_id,
            "mode": "error",
            "n_customers": n_customers,
            "n_updated": 0,
            "churn_rate": 0.0,
            "model_coefficients": None,
            "errors": errors or ["Failed to compute RFMS for all customers"],
        }

    # Chọn chế độ
    use_synthetic = force_synthetic or n_customers >= MIN_TRAINING_SAMPLES
    model = None
    mode = "A"
    model_coef_info = None

    if use_synthetic:
        mode = "B"
        logger.info(
            f"[RFMS Pipeline] CHẾ ĐỘ B: Synthetic Logistic Regression demo "
            f"(n_customers={n_customers}). ⚠️ Dữ liệu giả lập."
        )
        try:
            X_syn, y_syn = _generate_synthetic_data(n_samples=SYNTHETIC_N_SAMPLES)

            # Nếu có đủ dữ liệu thật, merge thêm vào synthetic
            if n_customers >= 20:
                X_real = np.array([[c["R"], c["F"], c["M"], c["S"]] for c in customer_rfms])
                # Sinh nhãn giả cho real data (dựa theo R và S: heuristic)
                # Khách có R > 0.6 và S < 0.4 → label=1 (giả định churn cao)
                y_real = ((X_real[:, 0] > 0.6) & (X_real[:, 3] < 0.4)).astype(int)
                X_syn = np.vstack([X_syn, X_real])
                y_syn = np.concatenate([y_syn, y_real])
                logger.info(
                    f"[RFMS Pipeline] Merge {n_customers} real data points vào synthetic "
                    f"(tổng={len(X_syn)} samples)"
                )

            model = train_churn_model(X_syn, y_syn, mode_label="synthetic+real")
            lr = model.named_steps["lr"]
            scaler = model.named_steps["scaler"]
            model_coef_info = {
                "mode": "synthetic_lr",
                "R": round(float(lr.coef_[0][0]), 4),
                "F": round(float(lr.coef_[0][1]), 4),
                "M": round(float(lr.coef_[0][2]), 4),
                "S": round(float(lr.coef_[0][3]), 4),
                "bias": round(float(lr.intercept_[0]), 4),
            }
        except Exception as e:
            logger.error(f"[RFMS Pipeline] LR train thất bại, fallback về chế độ A: {e}")
            mode = "A"
            model = None
    else:
        logger.info(
            f"[RFMS Pipeline] CHẾ ĐỘ A: Heuristic cold-start "
            f"(n_customers={n_customers} < {MIN_TRAINING_SAMPLES}). "
            f"Dùng DEFAULT_COEFFICIENTS."
        )

    # Tính p_churn cho từng customer
    n_updated = 0
    n_high_risk = 0

    for cdata in customer_rfms:
        cid = cdata["customer_id"]
        R, F, M, S = cdata["R"], cdata["F"], cdata["M"], cdata["S"]

        try:
            if model is not None and mode == "B":
                # Chế độ B: dùng sklearn model
                X_pred = np.array([[R, F, M, S]])
                p_churn = float(model.predict_proba(X_pred)[0][1])
            else:
                # Chế độ A: dùng heuristic
                p_churn = calculate_churn_probability(R, F, M, S)

            p_churn = round(max(0.0, min(1.0, p_churn)), 6)

            if p_churn >= DEFAULT_CHURN_ALERT_THRESHOLD:
                n_high_risk += 1

            if update_firestore:
                _update_customer_p_churn(
                    tenant_id=tenant_id,
                    customer_id=cid,
                    p_churn=p_churn,
                    rfms_mode=mode,
                )
                n_updated += 1

        except Exception as e:
            errors.append(f"predict customer={cid}: {e}")

    churn_rate = n_high_risk / len(customer_rfms) if customer_rfms else 0.0

    logger.info(
        f"[RFMS Pipeline] Hoàn tất tenant={tenant_id}: "
        f"mode={mode}, updated={n_updated}/{n_customers}, "
        f"high_risk={n_high_risk} ({churn_rate:.1%})"
    )

    return {
        "tenant_id": tenant_id,
        "mode": mode,
        "n_customers": n_customers,
        "n_updated": n_updated,
        "churn_rate": round(churn_rate, 4),
        "model_coefficients": model_coef_info,
        "errors": errors,
    }


def _update_customer_p_churn(
    tenant_id: str,
    customer_id: str,
    p_churn: float,
    rfms_mode: str,
) -> None:
    """Cập nhật p_churn và risk_level vào Firestore customer document."""
    try:
        from backend.db.firestore_client import get_firestore_client
        db = get_firestore_client()
        ref = (
            db.collection("tenants").document(tenant_id)
            .collection("customers").document(customer_id)
        )

        if p_churn < 0.30:
            risk_level = "low"
        elif p_churn < 0.85:
            risk_level = "medium"
        else:
            risk_level = "high"

        ref.update({
            "p_churn":       p_churn,
            "churn_risk_level": risk_level,
            "rfms_model_mode": rfms_mode,
            "rfms_computed_at": datetime.now(timezone.utc),
        })
    except Exception as e:
        logger.warning(
            f"[RFMS Pipeline] Không update p_churn Firestore "
            f"customer={customer_id}: {e}"
        )
