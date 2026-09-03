# RFMS Model - Tài liệu kỹ thuật
**Author:** Nguyễn Thanh Tuyền, hỗ trợ bởi Đoàn Hoàng Việt
**Giai đoạn:** 7 - Mô hình RFMS và Churn Probability

---

## Tổng quan

Thư mục này chứa lõi mô hình RFMS (Recency-Frequency-Monetary-Sentiment) dùng để tính **xác suất rời bỏ khách hàng** theo công thức hồi quy logistic:

```
P_churn = 1 / (1 + e^-(αR - βF - γM - δS + ε))
```

| Biến | Ý nghĩa | Chiều tác động |
|------|---------|----------------|
| **R** (Recency) | Số ngày kể từ lần ghé thăm cuối | R tăng -> P_churn tăng (lâu không đến = nguy hiểm) |
| **F** (Frequency) | Số lần ghé thăm trong kỳ | F tăng -> P_churn giảm (thường xuyên = trung thành) |
| **M** (Monetary) | Tổng chi tiêu trong kỳ (VNĐ) | M tăng -> P_churn giảm (chi nhiều = gắn bó) |
| **S** (Sentiment) | Điểm cảm xúc từ ABSA và Fusion | S tăng -> P_churn giảm (hài lòng = ít rời bỏ) |

---

## ⚠️ Tuyên bố quan trọng về hệ số mặc định

**Bộ hệ số hiện tại là GIẢ ĐỊNH BAN ĐẦU.**

Chúng được đặt dựa trên kiến thức ngành F&B tại Việt Nam và tham khảo nghiên cứu học thuật, **KHÔNG phải** là kết quả của quá trình học máy trên dữ liệu thực tế.

Hệ quả:
- P_churn tính ra mang tính chất tương đối.
- Ngưỡng cảnh báo 85% là khởi điểm giả định, cần điều chỉnh trong tương lai.
- Tính năng này mang tính chất Pilot, sẽ được nâng cấp thành mô hình học từ dữ liệu thật sau khi có đủ dữ liệu.

---

## Định hướng nâng cấp RFMS (Roadmap)

Khi Sentrix có đủ dữ liệu thực tế sau giai đoạn Pilot (khoảng 500+ feedback mỗi tenant), quy trình cập nhật hệ số dự kiến sẽ là:

### Bước 1: Thu thập nhãn thật
Theo dõi khách hàng sau 60-90 ngày kể từ lần feedback cuối:
- Khách không quay lại sau 90 ngày -> `churned = 1`
- Khách có ít nhất 1 lần quay lại -> `churned = 0`

### Bước 2: Tạo training dataset
```python
# Mỗi hàng là 1 khách hàng tại 1 thời điểm snapshot
X = [[R_norm, F_norm, M_norm, S_norm], ...]
y = [0, 1, 0, 1, ...]
```

### Bước 3: Huấn luyện Logistic Regression
```python
from sklearn.linear_model import LogisticRegression

model = LogisticRegression(C=1.0, max_iter=1000)
model.fit(X_train, y_train)

# Lấy hệ số học được
coefficients = {
    "alpha":   model.coef_[0][0],   # Hệ số cho R
    "beta":    -model.coef_[0][1],  # Hệ số cho F
    "gamma":   -model.coef_[0][2],  # Hệ số cho M
    "delta":   -model.coef_[0][3],  # Hệ số cho S
    "epsilon": model.intercept_[0], # Bias
}
```

### Bước 4: Cập nhật DEFAULT_COEFFICIENTS
Sau khi huấn luyện, thay bộ hệ số mặc định bằng bộ đã học.

---

## Files trong thư mục này

| File | Mô tả |
|------|-------|
| `rfms_calculator.py` | Chuẩn hoá RFMS về khoảng 0-1 (Min-Max normalization) |
| `churn_model.py` | Tính P_churn theo sigmoid và xếp mức rủi ro |
| `README.md` | Tài liệu này |

---

## Cách dùng trong pipeline

```python
from backend.rfms_model.churn_model import calculate_churn_full

result = calculate_churn_full(
    recency_days=45,
    frequency=3,
    monetary=250_000,
    sentiment_score=0.72,
)

print(result["p_churn"])       # -> 0.412
print(result["risk_level"])    # -> "Trung bình"
print(result["should_alert"])  # -> False (chưa vượt ngưỡng 85%)
```

---

## Ngưỡng cảnh báo mặc định

| P_churn | Mức rủi ro | Hành động |
|---------|-----------|-----------|
| < 0.30 | 🟢 Thấp | Không cần can thiệp |
| 0.30 - 0.59 | 🟡 Trung bình | Theo dõi thêm |
| 0.60 - 0.84 | 🟠 Cao | Lên kế hoạch re-engagement |
| >= 0.85 | 🔴 Nguy hiểm | Kích hoạt cảnh báo (Tương lai sẽ gọi Zalo ZNS) |
