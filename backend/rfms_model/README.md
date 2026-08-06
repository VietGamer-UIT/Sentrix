# RFMS Model — Tài liệu kỹ thuật
**Author:** Nguyễn Thanh Tuyền (AI & Data Architect) — hỗ trợ bởi Đoàn Hoàng Việt  
**Giai đoạn:** 7 — Mô hình RFMS + Churn Probability

---

## Tổng quan

Thư mục này chứa lõi mô hình RFMS (Recency–Frequency–Monetary–Sentiment) dùng để tính
**xác suất rời bỏ khách hàng (P_churn)** theo công thức hồi quy logistic:

```
P_churn = 1 / (1 + e^-(αR - βF - γM - δS + ε))
```

| Biến | Ý nghĩa | Chiều tác động |
|------|---------|----------------|
| **R** (Recency) | Số ngày kể từ lần ghé thăm cuối | R tăng → P_churn **tăng** (lâu không đến = nguy hiểm) |
| **F** (Frequency) | Số lần ghé thăm trong kỳ | F tăng → P_churn **giảm** (thường xuyên = trung thành) |
| **M** (Monetary) | Tổng chi tiêu trong kỳ (VNĐ) | M tăng → P_churn **giảm** (chi nhiều = gắn bó) |
| **S** (Sentiment) | Điểm cảm xúc từ ABSA+Fusion [0,1] | S tăng → P_churn **giảm** (hài lòng = ít rời bỏ) |

---

## ⚠️ Tuyên bố quan trọng về hệ số mặc định

**Bộ hệ số hiện tại (α=2.5, β=1.5, γ=1.2, δ=2.0, ε=-1.5) là GIẢ ĐỊNH BAN ĐẦU.**

Chúng được đặt dựa trên **domain knowledge** về ngành F&B/Spa/Phòng khám tại Việt Nam
và tham khảo nghiên cứu học thuật về Customer Churn Prediction, **KHÔNG phải** là kết quả
của quá trình học máy trên dữ liệu thực tế.

Hệ quả:
- P_churn tính ra **CÓ Ý NGHĨA TƯƠNG ĐỐI** (khách A nguy hiểm hơn khách B), nhưng **giá trị tuyệt đối chưa calibrate**.
- Ngưỡng cảnh báo 85% cũng là **khởi điểm giả định**, cần điều chỉnh.
- **KHÔNG nên sử dụng bộ hệ số này để ra quyết định kinh doanh quan trọng** cho đến khi có dữ liệu pilot thật.

---

## Kế hoạch huấn luyện hệ số thật (Sau giai đoạn Pilot)

Khi Sentrix có đủ dữ liệu thực tế (~500+ feedback/tenant), quy trình cập nhật hệ số sẽ là:

### Bước 1: Thu thập nhãn thật
Theo dõi khách hàng sau 60-90 ngày kể từ lần feedback cuối:
- Khách không quay lại sau 90 ngày → `churned = 1`
- Khách có ít nhất 1 lần quay lại → `churned = 0`

### Bước 2: Tạo training dataset
```python
# Mỗi hàng là 1 khách hàng tại 1 thời điểm snapshot
X = [[R_norm, F_norm, M_norm, S_norm], ...]  # Features
y = [0, 1, 0, 1, ...]                        # Labels (churned hay không)
```

### Bước 3: Huấn luyện Logistic Regression
```python
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

model = LogisticRegression(C=1.0, max_iter=1000)
model.fit(X_train, y_train)

# Lấy hệ số học được
coefficients = {
    "alpha":   model.coef_[0][0],   # Hệ số cho R
    "beta":    -model.coef_[0][1],  # Hệ số cho F (đảo dấu vì F giảm churn)
    "gamma":   -model.coef_[0][2],  # Hệ số cho M
    "delta":   -model.coef_[0][3],  # Hệ số cho S
    "epsilon": model.intercept_[0], # Bias
}
```

### Bước 4: Cập nhật DEFAULT_COEFFICIENTS trong `churn_model.py`
Sau khi huấn luyện, thay bộ hệ số mặc định bằng bộ đã học.
Pipeline tự động dùng hệ số mới mà không cần thay đổi code khác.

### Bước 5: Validation
```python
from sklearn.metrics import roc_auc_score, classification_report
print(classification_report(y_test, model.predict(X_test)))
print(f"AUC-ROC: {roc_auc_score(y_test, model.predict_proba(X_test)[:,1]):.4f}")
```
Mục tiêu: AUC-ROC ≥ 0.75 trước khi deploy hệ số mới.

---

## Files trong thư mục này

| File | Mô tả |
|------|-------|
| `rfms_calculator.py` | Chuẩn hoá RFMS về [0,1] (Min-Max normalization) |
| `churn_model.py` | Tính P_churn theo sigmoid + xếp mức rủi ro |
| `README.md` | Tài liệu này |

---

## Cách dùng trong pipeline

```python
from backend.rfms_model.churn_model import calculate_churn_full

result = calculate_churn_full(
    recency_days=45,
    frequency=3,
    monetary=250_000,
    sentiment_score=0.72,   # Từ Dynamic Weighted Fusion (Giai đoạn 6)
)

print(result["p_churn"])       # → 0.412
print(result["risk_level"])    # → "Trung bình"
print(result["should_alert"])  # → False (chưa vượt ngưỡng 85%)
```

---

## Ngưỡng cảnh báo mặc định

| P_churn | Mức rủi ro | Hành động |
|---------|-----------|-----------|
| < 0.30 | 🟢 Thấp | Không cần can thiệp |
| 0.30 – 0.59 | 🟡 Trung bình | Theo dõi thêm |
| 0.60 – 0.84 | 🟠 Cao | Lên kế hoạch re-engagement |
| ≥ 0.85 | 🔴 Nguy hiểm | **Trigger Zalo ZNS** (Giai đoạn 9) |

---

*Cần phối hợp với Việt: Dashboard cần hiển thị P_churn và risk_level — xem schema Firestore trong `backend/db/schema.md`.*
