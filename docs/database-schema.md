# Firestore Schema - Sentrix Multi-Tenant

**Author:** Nguyễn Thanh Tuyền
**Phiên bản:** 1.0
**Cập nhật lần cuối:** 2026-08-02
**Đọc bởi:** Tuyền, Việt

> **Việt lưu ý:** Mọi truy vấn Firestore từ Dashboard phải dùng **đúng tên collection và field** như tài liệu này. Nếu cần thêm field mới, nhắn nhóm để Tuyền cập nhật schema trước, không tự thêm field vào Firestore vì sẽ phá vỡ Security Rules và RFMS model.

---

## Lý do chọn kiến trúc nested theo tenant_id

Sentrix phục vụ nhiều doanh nghiệp. Mỗi doanh nghiệp là một tenant độc lập. Dữ liệu của quán A tuyệt đối không được lộ sang quán B.

Các cách tổ chức dữ liệu:

| Cách | Mô tả | Vấn đề |
|---|---|---|
| **Flat collection và filter** | Tất cả feedback dùng chung 1 collection, thêm field tenant_id | Security Rules khó viết chặt; query phải luôn có điều kiện lọc, quên là lộ data |
| **Tách Firestore project** | Mỗi tenant 1 Firebase project riêng | Chi phí vận hành cao |
| **Nested sub-collection** | `tenants/{tenant_id}/feedbacks/...` | Security Rules chặn theo path, cách ly tuyệt đối, phù hợp best practice |

**Kết luận:** Chọn **nested sub-collection**.

---

## Sơ đồ cấu trúc collection

```
Firestore root
│
└── tenants/
    └── {tenant_id}/
        ├── [thông tin doanh nghiệp]
        │
        ├── feedbacks/
        │   └── {feedback_id}/
        │       └── [1 lượt phản hồi]
        │
        └── customers/
            └── {customer_id}/
                └── [hồ sơ khách hàng]
```

---

## Collection: `tenants/{tenant_id}`

### Mô tả
Lưu thông tin doanh nghiệp đăng ký sử dụng Sentrix. Mỗi document là 1 tenant.

### Quy tắc đặt tên tenant_id
- Format: `{slug-ten-quan}_{timestamp_ms}`. Ví dụ: `pho-ba-lan_1722500000000`
- Sinh tự động khi doanh nghiệp đăng ký, không thay đổi sau khi tạo.

### Schema

| Field | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `business_name` | `string` | Có | Tên doanh nghiệp |
| `industry` | `string` | Có | Ngành: `fnb`, `spa`, `dental`, `clinic` |
| `plan` | `string` | Có | Gói dịch vụ: `free`, `pro`, `enterprise` |
| `owner_email` | `string` | Có | Email chủ tài khoản |
| `created_at` | `timestamp` | Có | Thời điểm đăng ký |
| `is_active` | `boolean` | Có | Trạng thái gói dịch vụ |
| `zalo_phone` | `string` | Không | SĐT Zalo nhận cảnh báo ZNS (kế hoạch tương lai) |
| `churn_threshold` | `number` | Không | Ngưỡng P_churn trigger ZNS. Mặc định: 0.85 |

---

## Sub-collection: `tenants/{tenant_id}/feedbacks/{feedback_id}`

### Mô tả
Mỗi document là 1 lượt phản hồi. Đây là nguồn dữ liệu cốt lõi để tính RFMS và hiển thị trên Dashboard.
Sinh tự động bởi Firestore.

### Schema

| Field | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `feedback_id` | `string` | Có | Trùng với document ID |
| `customer_id` | `string` | Có | Tham chiếu đến customers |
| `timestamp` | `timestamp` | Có | Thời điểm gửi phản hồi |
| `location` | `string` | Có | Bàn / khu vực quét QR |
| `input_type` | `string` | Có | Loại đầu vào: `audio` hoặc `text` |
| `audio_url` | `string` | Không | URL file audio trên Firebase Storage |
| `audio_duration_sec` | `number` | Không | Thời lượng ghi âm |
| `transcript` | `string` | Có | Văn bản: từ Whisper hoặc gõ tay |
| `audio_features` | `map` | Không | Đặc trưng âm thanh từ Librosa |
| `audio_features.mfcc_mean` | `array<number>` | Không | Trung bình 13 hệ số MFCC |
| `audio_features.f0_mean` | `number` | Không | Cao độ giọng trung bình |
| `audio_features.jitter` | `number` | Không | Độ biến thiên tần số cơ bản |
| `audio_features.shimmer` | `number` | Không | Độ biến thiên biên độ |
| `audio_features.stress_score` | `number` | Không | Điểm căng thẳng từ Librosa |
| `aspects` | `array<map>` | Có | Mảng các khía cạnh từ ABSA |
| `sentiment_score` | `number` | Có | Điểm cảm xúc tổng hợp sau Fusion |
| `is_sarcasm` | `boolean` | Có | Phát hiện mỉa mai |
| `fusion_weight_audio` | `number` | Không | Trọng số âm thanh dùng trong Fusion |
| `fusion_weight_text` | `number` | Không | Trọng số văn bản dùng trong Fusion |
| `processing_status` | `string` | Có | Trạng thái xử lý |
| `error_message` | `string` | Không | Thông báo lỗi |

### Cấu trúc 1 phần tử trong mảng aspects

| Field | Kiểu | Mô tả |
|---|---|---|
| `aspect` | `string` | Khía cạnh phân tích |
| `sentiment` | `string` | Cảm xúc: positive, negative, neutral |
| `score` | `number` | Điểm cảm xúc cho khía cạnh này |
| `reason` | `string` | Lý do LLM trích xuất |
| `confidence` | `number` | Độ tin cậy của LLM |

---

## Sub-collection: `tenants/{tenant_id}/customers/{customer_id}`

### Mô tả
Hồ sơ khách hàng ẩn danh hoá. Số điện thoại được hash bằng SHA-256 để làm customer_id. Số điện thoại chỉ lưu dạng masked để hiển thị.
Đây là nơi lưu điểm RFMS và P_churn.

### Schema

| Field | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `customer_id` | `string` | Có | Trùng với document ID |
| `phone_masked` | `string` | Có | SĐT ẩn một phần để hiển thị |
| `first_seen_at` | `timestamp` | Có | Lần đầu tiên khách gửi feedback |
| `last_feedback_at` | `timestamp` | Có | Lần gần nhất gửi feedback |
| `feedback_count` | `number` | Có | Tổng số lần gửi feedback |
| `total_spending` | `number` | Có | Tổng chi tiêu ước tính |
| `avg_sentiment_score` | `number` | Có | Trung bình sentiment_score |
| `rfms_r` | `number` | Có | Điểm Recency đã chuẩn hoá |
| `rfms_f` | `number` | Có | Điểm Frequency đã chuẩn hoá |
| `rfms_m` | `number` | Có | Điểm Monetary đã chuẩn hoá |
| `rfms_s` | `number` | Có | Điểm Sentiment đã chuẩn hoá |
| `p_churn` | `number` | Có | Xác suất rời bỏ |
| `churn_risk_level` | `string` | Có | Phân loại rủi ro |
| `zns_sent_at` | `timestamp` | Không | Thời điểm gửi cảnh báo ZNS gần nhất |
| `zns_voucher_code` | `string` | Không | Mã voucher đã gửi kèm ZNS |
| `updated_at` | `timestamp` | Có | Thời điểm cập nhật gần nhất |

---

## Indexes cần tạo trong Firestore Console

Các Composite Index cần tạo để Dashboard query nhanh:

| Collection | Fields | Order | Dùng cho |
|---|---|---|---|
| `tenants/{id}/feedbacks` | `timestamp` DESC | - | Lấy feedback mới nhất |
| `tenants/{id}/feedbacks` | `processing_status` ASC, `timestamp` DESC | - | Lọc feedback theo trạng thái |
| `tenants/{id}/customers` | `p_churn` DESC | - | Danh sách khách hàng rủi ro cao nhất |
| `tenants/{id}/customers` | `churn_risk_level` ASC, `p_churn` DESC | - | Lọc theo mức độ rủi ro |
| `tenants/{id}/customers` | `last_feedback_at` DESC | - | Khách hàng hoạt động gần đây |

---

## Hướng dẫn query cơ bản

Lấy danh sách feedback mới nhất:
```
collection: tenants/{tenant_id}/feedbacks
orderBy: timestamp DESC
limit: 20
```

Lấy khách hàng rủi ro cao:
```
collection: tenants/{tenant_id}/customers
where: churn_risk_level == "high"
orderBy: p_churn DESC
```
