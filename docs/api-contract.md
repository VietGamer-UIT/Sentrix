> **Phiên bản:** 1.3

---

## Quy ước trạng thái

| Biểu tượng | Ý nghĩa |
|---|---|
| 🟢 **CAM KẾT** | Endpoint đã có thật trong code, đã test, **không đổi tùy tiện**. |
| 🟡 **ĐANG THƯƠNG LƯỢNG** | Có thể thay đổi trong tương lai, cần chờ xác nhận mới gọi thật. |
| 🔴 **CHƯA CÓ** | Endpoint chưa tồn tại trong backend, chỉ có trong thiết kế — **KHÔNG gọi từ frontend** |

---

## Base URL

| Môi trường | URL |
|---|---|
| **Local dev** | `http://localhost:8000` |
| **Production (Render)** | `https://sentrix.onrender.com` — đã deploy, cập nhật `VITE_API_BASE_URL` trên Vercel |

---

## 1. 🟢 `GET /health` — CAM KẾT

> **File:** `backend/api/routes/health.py`
> **Mục đích:** Kiểm tra server đang sống. Dùng cho health-check trên nền tảng deploy.

**Request:** Không có body/params.

**Response `200 OK`:**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "message": "Sentrix Backend is running! 🚀"
}
```

| Field | Kiểu | Mô tả |
|---|---|---|
| `status` | `string` | Luôn `"ok"` nếu server sống |
| `version` | `string` | Phiên bản backend hiện tại |
| `message` | `string` | Thông báo xác nhận |

---

## 2. 🟢 `POST /api/v1/feedback` — CAM KẾT

> **File:** `backend/api/routes/feedback.py`
> **Mục đích:** Nhận phản hồi khách hàng (audio và/hoặc text) từ Web Client sau khi quét QR.

### Request — `multipart/form-data`

| Field | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `tenant_id` | `string` | ✅ | ID doanh nghiệp, lấy từ QR code. VD: `"pho-ba-lan_1722500000000"` |
| `location` | `string` | ✅ | Bàn/khu vực quét QR. VD: `"Ban 5"`. Min 1, max 100 ký tự |
| `audio_file` | `file` | ❌* | File ghi âm (WebM/MP3/WAV/OGG/MP4/M4A). Tối đa **5MB** (~15 giây) |
| `text_content` | `string` | ❌* | Văn bản gõ tay. Tối đa 2000 ký tự |
| `customer_phone` | `string` | ❌ | SĐT khách hàng. Dùng để tính RFMS cá nhân hóa. Backend sẽ hash trước khi lưu |
| `total_spending` | `float` | ❌ | Chi tiêu lần này (VND). Mặc định 0.0 |

> *\* Phải có ít nhất 1 trong 2: `audio_file` hoặc `text_content`. Có thể gửi cả hai.*

### MIME types chấp nhận cho `audio_file`
`audio/webm`, `audio/mpeg`, `audio/wav`, `audio/ogg`, `audio/mp4`, `audio/x-m4a`, `application/octet-stream`
> ⚠️ Backend tự strip codec suffix (ví dụ `audio/webm;codecs=opus` → `audio/webm`). Frontend không cần xử lý thêm.

### Response `202 Accepted` (Full Pipeline)
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "feedback_id": "abc123firestore",
  "status": "processed",
  "message": "Phan hoi da duoc xu ly va luu thanh cong.",
  "tenant_id": "pho-ba-lan_1722500000000",
  "location": "Ban 5",
  "input_type": "audio",
  "transcript": "Phục vụ tốt quá ha, đợi có 20 phút mà",
  "sentiment_score": -0.21,
  "overall_sentiment": "Tiêu cực",
  "is_sarcasm_suspected": true,
  "p_churn": 0.74,
  "churn_risk_level": "medium",
  "should_alert": false,
  "is_suspicious": false,
  "suspicious_reason": null
}
```

| Field | Kiểu | Mô tả |
|---|---|---|
| `request_id` | `string` | UUID tracking |
| `feedback_id` | `string\|null` | Firestore document ID (null nếu lưu lỗi) |
| `status` | `string` | `"processed"` / `"processed_with_warning"` |
| `sentiment_score` | `float` | Điểm cảm xúc tổng hợp **[-1.0 → +1.0]** (âm = tiêu cực, dương = tích cực) |
| `overall_sentiment` | `string` | `"Tích cực"` / `"Tiêu cực"` / `"Trung lập"` |
| `is_sarcasm_suspected` | `boolean` | True nếu phát hiện mỉa mai |
| `p_churn` | `float` | Xác suất rời bỏ [0.0 → 1.0] (tín hiệu quản trị, không phải dự đoán chắc chắn) |
| `churn_risk_level` | `string` | `"low"` / `"medium"` / `"high"` |
| `should_alert` | `boolean` | True nếu cần Staff Alert (Yêu cầu hỗ trợ hoặc Cảnh báo rủi ro) |
| `zns_status` | `string` | Roadmap / future integration (hiện tại không trả về hoặc để null) |

### Các mã lỗi

| Status Code | Khi nào | Response |
|---|---|---|
| `400` | Thiếu cả audio lẫn text, hoặc bị fraud filter từ chối | `{"detail": "..."}` |
| `413` | File audio > 5MB | `{"detail": "File audio quá lớn: XMB. Giới hạn tối đa: 5MB"}` |
| `422` | Lỗi validation form fields (FastAPI tự sinh) | `{"detail": [...]}` |
| `503` | Whisper API key lỗi xác thực | `{"detail": "STT service không khả dụng..."}` |

### Luồng xử lý đầy đủ
```
POST feedback → validation → fraud checks
→ voice → STT → intent / feedback classification
→ phân tích cảm xúc (NLP) → action (staff alert nếu cần)
→ lưu Firestore
```
*(Zalo ZNS, Multimodal Fusion là tính năng Roadmap)*

---

## 4. 🟢 `POST /api/v1/gamification/spin` — CAM KẾT

> **File:** `backend/api/routes/gamification.py`
> **Cập nhật:** 2026-08-20 — Endpoint đã **LIVE trên Render**. Gọi API thật, không dùng mock.
> **Trạng thái trước:** 🔴 CHƯA CÓ (doc cũ ngày 05/08 — đã lỗi thời)

### Request — `multipart/form-data`

| Field | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `tenant_id` | `string` | ✅ | ID doanh nghiệp |
| `customer_phone` | `string` | ✅ | SĐT khách hàng (lấy từ sessionStorage `sentrix_customer_phone`) |
| `feedback_id` | `string` | ❌ | Firestore feedback ID (để backend link voucher vào feedback đúng) |

### Response `200 OK`
```json
{
  "prize": "giam_10",
  "prize_label": "Giảm 10%",
  "voucher_code": "SENTRIX-10-7624",
  "message": "Chúc mừng bạn nhận được: Giảm 10%!"
}
```

| Field | Kiểu | Mô tả |
|---|---|---|
| `prize` | `string` | ID phần thưởng: `"giam_10"` / `"giam_20"` / `"tang_banh"` / `"giam_5"` / `"uong_mien_phi"` / `"chuc_may_man"` |
| `prize_label` | `string` | Tên hiển thị đầy đủ của phần thưởng |
| `voucher_code` | `string` | Mã voucher (rỗng `""` nếu prize = `"chuc_may_man"`) |
| `message` | `string` | Thông báo kết quả cho khách |

### Prize IDs (phải khớp với `SPIN_PRIZES` trong `gamification.js`)

| prize id | Tỷ lệ | Có voucher? |
|---|---|---|
| `giam_10` | 35% | ✅ `SENTRIX-10-{4 số cuối SĐT}` |
| `giam_20` | 20% | ✅ `SENTRIX-20-{4 số cuối SĐT}` |
| `tang_banh` | 15% | ✅ `SENTRIX-BANH-{4 số cuối SĐT}` |
| `giam_5` | 20% | ✅ `SENTRIX-5-{4 số cuối SĐT}` |
| `uong_mien_phi` | 5% | ✅ `SENTRIX-FREE-{4 số cuối SĐT}` |
| `chuc_may_man` | 5% | ❌ (rỗng) |

> ✅ Gọi API thật tại `${VITE_API_BASE_URL}/api/v1/gamification/spin`.
> KHÔNG dùng mock random ở client — prize được quyết định server-side (bảo mật, không hack được JS).
> `gamification.js` đã được cập nhật để gọi endpoint thật. Đảm bảo `VITE_API_BASE_URL` đúng trên Vercel.

---

## 5. 🔴 `GET /api/dashboard/kpi` — CHƯA CÓ (có thể không cần)

> **Mục đích:** Tổng hợp KPI cho dashboard chủ doanh nghiệp.
> **Trạng thái thật:** Dashboard hiện thiết kế đọc **trực tiếp Firestore** (không qua REST API) theo `docs/database-schema.md`.

### Cách truy xuất Dashboard hiện tại
Thay vì gọi API endpoint, đọc trực tiếp từ Firestore SDK:

```javascript
// Feedback mới nhất
db.collection(`tenants/${tenantId}/feedbacks`)
  .orderBy('timestamp', 'desc')
  .limit(50)
  .onSnapshot(snapshot => { ... })

// Khách hàng rủi ro cao
db.collection(`tenants/${tenantId}/customers`)
  .orderBy('p_churn', 'desc')
  .limit(30)
  .onSnapshot(snapshot => { ... })
```

*(Nguồn: docs/database-schema.md)*

> ⚠️ Dashboard dùng React. Deploy lên Vercel cùng web-client.

---

## 6. 🔴 `GET /api/dashboard/churn-alerts` — CHƯA CÓ (có thể không cần)

> **Tương tự mục 5** — Dashboard đọc trực tiếp Firestore collection `customers` với filter `churn_risk_level == "high"`.
> Nếu sau này cần REST API riêng (ví dụ: để Mobile App gọi), hợp đồng API sẽ được cập nhật.

---

## Firestore Schema Reference

> Chi tiết đầy đủ: xem `docs/database-schema.md`

### Collections chính

| Collection path | Mục đích | Fields quan trọng nhất |
|---|---|---|
| `tenants/{tenant_id}` | Thông tin doanh nghiệp | `business_name`, `industry`, `plan`, `is_active`, `churn_threshold` |
| `tenants/{id}/feedbacks/{feedback_id}` | 1 lượt phản hồi | `transcript`, `aspects[]`, `sentiment_score [-1,+1]`, `is_sarcasm`, `processing_status` |
| `tenants/{id}/customers/{customer_id}` | Hồ sơ khách hàng | `phone_masked`, `rfms_r/f/m/s`, `p_churn`, `churn_risk_level`, `feedback_count` |

### Aspect categories (dùng cho cả backend lẫn frontend)
`"nhan_vien"` · `"mon_an"` · `"khong_gian"` · `"gia_ca"` · `"toc_do_phuc_vu"` · `"ve_sinh"` · `"vi_tri"` · `"khac"`

### Sentiment values (lưu trong Firestore)
`"positive"` · `"negative"` · `"neutral"`

### Churn risk levels
`"low"` (P < 0.30) · `"medium"` (0.30 ≤ P < 0.85) · `"high"` (P ≥ 0.85)

### `sentiment_score` scale
**[-1.0 → +1.0]** — âm là tiêu cực, 0 là trung lập, dương là tích cực.
> ⚠️ Lưu ý: Dashboard cũ (trước 2026-08-15) có thể hiện `+0.50` cho data cũ bị ABSA timeout — đây là artifact data chứ không phải trung lập thật.

---

## Lịch sử cập nhật

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-08-05 | Tạo bản đầu tiên — 3 endpoint cam kết, 3 endpoint chưa có | Team |
| 2026-08-20 | **v1.2:** Cập nhật mục 4 gamification/spin từ 🔴→🟢 (endpoint đã LIVE). Cập nhật mục 2 feedback response schema đầy đủ. Cập nhật Production URL. Thêm churn risk level thresholds đúng. | Team |




