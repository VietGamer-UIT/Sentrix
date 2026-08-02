# 🗄️ Firestore Schema — Sentrix Multi-Tenant

**Author:** Nguyễn Thanh Tuyền (AI & Data Architect)  
**Phiên bản:** 1.0  
**Cập nhật lần cuối:** 2026-08-02  
**Đọc bởi:** Tuyền (backend), Việt (dashboard cần đọc đúng field name này)

> ⚠️ **Việt lưu ý:** Mọi truy vấn Firestore từ Dashboard phải dùng **đúng tên collection và field** như tài liệu này. Nếu cần thêm field mới hoặc thấy field nào không đủ, nhắn Zalo nhóm để Tuyền cập nhật schema trước — không tự thêm field vào Firestore vì sẽ phá vỡ Security Rules và RFMS model.

---

## 📐 Lý do chọn kiến trúc nested theo `tenant_id`

Sentrix là nền tảng **multi-tenant SaaS**: mỗi doanh nghiệp (quán F&B, spa, phòng khám…) đăng ký là một **tenant** độc lập. Dữ liệu phản hồi khách hàng của quán A **tuyệt đối không được lộ** sang quán B.

Có 3 cách tổ chức dữ liệu multi-tenant phổ biến:

| Cách | Mô tả | Vấn đề |
|---|---|---|
| **Flat collection + filter** | Tất cả feedback dùng chung 1 collection, thêm field `tenant_id` | ❌ Security Rules khó viết chặt; query phải luôn có `where tenant_id ==` — nếu quên 1 lần là lộ data |
| **Tách Firestore project** | Mỗi tenant 1 Firebase project riêng | ❌ Chi phí vận hành x10, không thực tế với startup |
| **✅ Nested sub-collection** | `tenants/{tenant_id}/feedbacks/...` | ✅ Security Rules chặn theo path — không thể đọc chéo dù quên filter; phù hợp Firestore best practice |

**Kết luận:** Chọn **nested sub-collection** theo `tenant_id`. Security Rules kiểm soát ở cấp path `tenants/{tenantId}/**` — đảm bảo cách ly tuyệt đối, không phụ thuộc vào lập trình viên có nhớ `where tenant_id` hay không.

---

## 🏗️ Sơ đồ cấu trúc collection

```
Firestore (root)
│
└── tenants/                          ← Collection cấp 1
    └── {tenant_id}/                  ← Document: thông tin doanh nghiệp
        ├── [fields: xem bên dưới]
        │
        ├── feedbacks/                ← Sub-collection: phản hồi khách hàng
        │   └── {feedback_id}/        ← Document: 1 lượt phản hồi
        │       └── [fields: xem bên dưới]
        │
        └── customers/                ← Sub-collection: hồ sơ khách hàng
            └── {customer_id}/        ← Document: 1 khách hàng (theo SĐT hash)
                └── [fields: xem bên dưới]
```

---

## 📄 Collection: `tenants/{tenant_id}`

### Mô tả
Lưu thông tin doanh nghiệp đăng ký sử dụng Sentrix. Mỗi document là 1 tenant.

### `tenant_id` — quy tắc đặt tên
- Format: `{slug-ten-quan}_{timestamp_ms}` — ví dụ: `pho-ba-lan_1722500000000`
- Sinh tự động khi doanh nghiệp đăng ký, **không thay đổi sau khi tạo** (dùng làm khóa cho Security Rules).

### Schema (fields)

| Field | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `business_name` | `string` | ✅ | Tên doanh nghiệp. Ví dụ: `"Phở Bà Lan"` |
| `industry` | `string` | ✅ | Ngành. Giá trị: `"fnb"` / `"spa"` / `"dental"` / `"clinic"` |
| `plan` | `string` | ✅ | Gói dịch vụ: `"free"` / `"pro"` / `"enterprise"` |
| `owner_email` | `string` | ✅ | Email chủ tài khoản (dùng để auth Firebase) |
| `created_at` | `timestamp` | ✅ | Thời điểm đăng ký (Firestore Timestamp) |
| `is_active` | `boolean` | ✅ | `true` nếu gói còn hiệu lực, `false` nếu hết hạn |
| `zalo_phone` | `string` | ❌ | SĐT Zalo nhận cảnh báo ZNS (giai đoạn 9) |
| `churn_threshold` | `number` | ❌ | Ngưỡng P_churn trigger ZNS. Mặc định: `0.85` |

### Ví dụ JSON mẫu (document `tenants/pho-ba-lan_1722500000000`)

```json
{
  "business_name": "Phở Bà Lan",
  "industry": "fnb",
  "plan": "pro",
  "owner_email": "balan.pho@gmail.com",
  "created_at": "2026-08-01T10:00:00Z",
  "is_active": true,
  "zalo_phone": "0901234567",
  "churn_threshold": 0.85
}
```

---

## 📄 Sub-collection: `tenants/{tenant_id}/feedbacks/{feedback_id}`

### Mô tả
Mỗi document là **1 lượt phản hồi** của 1 khách hàng tại 1 thời điểm. Đây là nguồn dữ liệu cốt lõi để tính RFMS và hiển thị trên Dashboard.

### `feedback_id`
- Sinh tự động bởi Firestore (`db.collection(...).document()`) — UUID dạng `auto-id`.

### Schema (fields)

| Field | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `feedback_id` | `string` | ✅ | Trùng với document ID — lưu lại để tiện truy vấn |
| `customer_id` | `string` | ✅ | Tham chiếu đến `customers/{customer_id}` (xem bên dưới) |
| `timestamp` | `timestamp` | ✅ | Thời điểm gửi phản hồi (server-side, không tin client) |
| `location` | `string` | ✅ | Bàn / khu vực quét QR. Ví dụ: `"Ban 5"`, `"Khu VIP"` |
| `input_type` | `string` | ✅ | Loại đầu vào: `"audio"` hoặc `"text"` |
| `audio_url` | `string` | ❌ | URL file audio trên Firebase Storage (chỉ có nếu `input_type == "audio"`) |
| `audio_duration_sec` | `number` | ❌ | Thời lượng ghi âm (giây). Tối đa 15 giây theo thiết kế |
| `transcript` | `string` | ✅ | Văn bản: từ Whisper (nếu audio) hoặc gõ tay (nếu text) |
| `audio_features` | `map` | ❌ | Đặc trưng âm thanh từ Librosa (chỉ có nếu `input_type == "audio"`) |
| `audio_features.mfcc_mean` | `array<number>` | ❌ | Trung bình 13 hệ số MFCC |
| `audio_features.f0_mean` | `number` | ❌ | Cao độ giọng trung bình (Hz) |
| `audio_features.jitter` | `number` | ❌ | Độ biến thiên tần số cơ bản (%) |
| `audio_features.shimmer` | `number` | ❌ | Độ biến thiên biên độ (dB) |
| `audio_features.stress_score` | `number` | ❌ | Điểm căng thẳng tổng hợp từ Librosa: `0.0` → `1.0` |
| `aspects` | `array<map>` | ✅ | Mảng các khía cạnh từ ABSA (xem chi tiết bên dưới) |
| `sentiment_score` | `number` | ✅ | Điểm cảm xúc tổng hợp sau Fusion: `-1.0` (rất tiêu cực) → `+1.0` (rất tích cực) |
| `is_sarcasm` | `boolean` | ✅ | `true` nếu Fusion phát hiện mỉa mai (văn bản dương nhưng giọng gắt) |
| `fusion_weight_audio` | `number` | ❌ | Trọng số âm thanh dùng trong Fusion (lưu lại để debug/audit) |
| `fusion_weight_text` | `number` | ❌ | Trọng số văn bản dùng trong Fusion |
| `processing_status` | `string` | ✅ | Trạng thái xử lý: `"pending"` / `"processing"` / `"done"` / `"error"` |
| `error_message` | `string` | ❌ | Thông báo lỗi nếu `processing_status == "error"` |

### Cấu trúc 1 phần tử trong mảng `aspects`

| Field | Kiểu | Mô tả |
|---|---|---|
| `aspect` | `string` | Khía cạnh. Giá trị: `"nhan_vien"` / `"mon_an"` / `"khong_gian"` / `"gia_ca"` / `"toc_do_phuc_vu"` / `"ve_sinh"` / `"khac"` |
| `sentiment` | `string` | Cảm xúc: `"positive"` / `"negative"` / `"neutral"` |
| `score` | `number` | Điểm cảm xúc cho khía cạnh này: `-1.0` → `+1.0` |
| `reason` | `string` | Lý do LLM trích xuất. Ví dụ: `"Khách khen nhân viên cười tươi"` |
| `confidence` | `number` | Độ tin cậy của LLM: `0.0` → `1.0` |

### Ví dụ JSON mẫu (1 feedback hoàn chỉnh)

```json
{
  "feedback_id": "abc123xyz",
  "customer_id": "cust_hash_0901234567",
  "timestamp": "2026-08-02T10:35:00Z",
  "location": "Ban 5",
  "input_type": "audio",
  "audio_url": "gs://sentrix-app.appspot.com/tenants/pho-ba-lan_1722500000000/audio/abc123xyz.webm",
  "audio_duration_sec": 8.4,
  "transcript": "Phục vụ tốt quá ha, đợi có 20 phút mà",
  "audio_features": {
    "mfcc_mean": [-120.5, 80.2, -30.1, 15.4, -8.7, 5.2, -3.1, 1.8, -0.9, 0.4, -0.2, 0.1, -0.05],
    "f0_mean": 245.6,
    "jitter": 0.034,
    "shimmer": 0.28,
    "stress_score": 0.73
  },
  "aspects": [
    {
      "aspect": "toc_do_phuc_vu",
      "sentiment": "negative",
      "score": -0.82,
      "reason": "Khách phàn nàn phải chờ đến 20 phút",
      "confidence": 0.91
    },
    {
      "aspect": "nhan_vien",
      "sentiment": "positive",
      "score": 0.45,
      "reason": "Câu nói mang hàm ý khen nhưng giọng mỉa mai",
      "confidence": 0.67
    }
  ],
  "sentiment_score": -0.61,
  "is_sarcasm": true,
  "fusion_weight_audio": 0.70,
  "fusion_weight_text": 0.30,
  "processing_status": "done",
  "error_message": null
}
```

---

## 📄 Sub-collection: `tenants/{tenant_id}/customers/{customer_id}`

### Mô tả
Hồ sơ khách hàng **ẩn danh hoá một phần**: số điện thoại được hash (SHA-256) để làm `customer_id`, không lưu SĐT gốc trong Firestore (bảo vệ quyền riêng tư). Số điện thoại chỉ lưu dạng masked để hiển thị (`"090****567"`).

Đây là nơi lưu điểm RFMS và `P_churn` — Dashboard của Việt đọc collection này để hiển thị danh sách khách hàng rủi ro.

### `customer_id`
- Format: `cust_{sha256_of_phone_number[:16]}` — ví dụ: `cust_a3f8c2d1e4b7f901`
- Hash bằng SHA-256 của SĐT chuẩn hoá (bỏ khoảng trắng, chuẩn hoá về `+84...`).

### Schema (fields)

| Field | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `customer_id` | `string` | ✅ | Trùng với document ID |
| `phone_masked` | `string` | ✅ | SĐT ẩn một phần để hiển thị. Ví dụ: `"090****567"` |
| `first_seen_at` | `timestamp` | ✅ | Lần đầu tiên khách gửi feedback |
| `last_feedback_at` | `timestamp` | ✅ | Lần gần nhất gửi feedback (dùng tính R — Recency) |
| `feedback_count` | `number` | ✅ | Tổng số lần gửi feedback (dùng tính F — Frequency) |
| `total_spending` | `number` | ✅ | Tổng chi tiêu ước tính (VNĐ) — lấy từ bill nếu có tích hợp POS, hoặc để `0` nếu chưa (dùng tính M — Monetary) |
| `avg_sentiment_score` | `number` | ✅ | Trung bình `sentiment_score` của tất cả feedback (dùng tính S — Sentiment) |
| `rfms_r` | `number` | ✅ | Điểm Recency đã chuẩn hoá: `0.0` → `1.0` (1.0 = mới nhất) |
| `rfms_f` | `number` | ✅ | Điểm Frequency đã chuẩn hoá: `0.0` → `1.0` |
| `rfms_m` | `number` | ✅ | Điểm Monetary đã chuẩn hoá: `0.0` → `1.0` |
| `rfms_s` | `number` | ✅ | Điểm Sentiment đã chuẩn hoá: `0.0` → `1.0` |
| `p_churn` | `number` | ✅ | Xác suất rời bỏ: `0.0` → `1.0`. Tính bằng mô hình logistic RFMS |
| `churn_risk_level` | `string` | ✅ | Phân loại: `"low"` (< 0.5) / `"medium"` (0.5–0.85) / `"high"` (> 0.85) |
| `zns_sent_at` | `timestamp` | ❌ | Thời điểm gửi cảnh báo ZNS gần nhất (tránh gửi spam) |
| `zns_voucher_code` | `string` | ❌ | Mã voucher đã gửi kèm ZNS |
| `updated_at` | `timestamp` | ✅ | Thời điểm cập nhật RFMS/P_churn gần nhất |

### Ví dụ JSON mẫu (1 customer)

```json
{
  "customer_id": "cust_a3f8c2d1e4b7f901",
  "phone_masked": "090****567",
  "first_seen_at": "2026-07-15T08:20:00Z",
  "last_feedback_at": "2026-08-02T10:35:00Z",
  "feedback_count": 3,
  "total_spending": 450000,
  "avg_sentiment_score": -0.42,
  "rfms_r": 0.95,
  "rfms_f": 0.60,
  "rfms_m": 0.45,
  "rfms_s": 0.29,
  "p_churn": 0.87,
  "churn_risk_level": "high",
  "zns_sent_at": null,
  "zns_voucher_code": null,
  "updated_at": "2026-08-02T10:35:05Z"
}
```

---

## 🔍 Indexes cần tạo trong Firestore Console

Việt cần tạo các **Composite Index** sau để Dashboard query được nhanh:

| Collection | Fields | Order | Dùng cho |
|---|---|---|---|
| `tenants/{id}/feedbacks` | `timestamp` DESC | — | Lấy feedback mới nhất |
| `tenants/{id}/feedbacks` | `processing_status` ASC, `timestamp` DESC | — | Lọc feedback theo trạng thái |
| `tenants/{id}/customers` | `p_churn` DESC | — | Danh sách khách hàng rủi ro cao nhất |
| `tenants/{id}/customers` | `churn_risk_level` ASC, `p_churn` DESC | — | Lọc theo mức độ rủi ro |
| `tenants/{id}/customers` | `last_feedback_at` DESC | — | Khách hàng hoạt động gần đây |

---

## 📊 Dashboard — Hướng dẫn nhanh cho Việt

> Phần này dành riêng cho Việt đọc để code Dashboard không phải hỏi lại Tuyền.

**1. Lấy danh sách feedback mới nhất:**
```
collection: tenants/{tenant_id}/feedbacks
orderBy: timestamp DESC
limit: 20
```

**2. Lấy khách hàng rủi ro cao (P_churn > 0.85):**
```
collection: tenants/{tenant_id}/customers
where: churn_risk_level == "high"
orderBy: p_churn DESC
```

**3. Đọc realtime khi có feedback mới:**
```javascript
// Dùng Firestore onSnapshot listener trên collection feedbacks
// để Dashboard tự cập nhật khi có phản hồi mới
db.collection(`tenants/${tenantId}/feedbacks`)
  .orderBy('timestamp', 'desc')
  .limit(10)
  .onSnapshot(snapshot => { ... })
```

**4. Thống kê tổng quan:**
- Tổng feedback hôm nay: query `timestamp >= startOfDay`
- Điểm cảm xúc trung bình: tính `avg(sentiment_score)` client-side từ kết quả query (Firestore không có aggregate function, phải tính phía client hoặc dùng Cloud Functions — sẽ bổ sung sau nếu cần)
