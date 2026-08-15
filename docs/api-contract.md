# API Contract — Sentrix

> **Duy trì bởi:** Đoàn Hoàng Việt (Trưởng nhóm)
> **Tuyền xác nhận:** phần backend (endpoint, request/response format)
> **Tuấn tham chiếu:** khi code frontend gọi API
>
> **Cập nhật lần cuối:** 2026-08-05
> **Phiên bản:** 1.0

---

## Quy ước trạng thái

| Biểu tượng | Ý nghĩa |
|---|---|
| 🟢 **CAM KẾT** | Endpoint đã có thật trong code, đã test, **không đổi tùy tiện** — Tuấn code frontend chắc chắn theo format này |
| 🟡 **ĐANG THƯƠNG LƯỢNG** | Tuyền có thể còn đổi khi code các giai đoạn tiếp theo — Tuấn nên dùng mock data tạm, chờ xác nhận mới gọi thật |
| 🔴 **CHƯA CÓ** | Endpoint chưa tồn tại trong backend, chỉ có trong thiết kế — **KHÔNG gọi từ frontend** |

---

## Base URL

| Môi trường | URL |
|---|---|
| **Local dev** | `http://localhost:8000` |
| **Production (Render)** | `TBD` — chờ Tuyền deploy, sau đó cập nhật `VITE_API_BASE_URL` trên Vercel |

---

## 1. 🟢 `GET /health` — CAM KẾT

> **File:** `backend/api/routes/health.py`
> **Mục đích:** Kiểm tra server đang sống. Render.com dùng health-check, Việt dùng xác nhận backend đã deploy xong.

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

> *\* Phải có ít nhất 1 trong 2: `audio_file` hoặc `text_content`. Có thể gửi cả hai.*

### MIME types chấp nhận cho `audio_file`
`audio/webm`, `audio/mpeg`, `audio/wav`, `audio/ogg`, `audio/mp4`, `audio/x-m4a`, `application/octet-stream`

### Response `202 Accepted`
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "accepted",
  "message": "Phản hồi đã được nhận và đang được xử lý.",
  "tenant_id": "pho-ba-lan_1722500000000",
  "location": "Ban 5",
  "input_type": "audio",
  "transcript": "Phục vụ tốt quá ha, đợi có 20 phút mà",
  "is_suspicious": false,
  "suspicious_reason": null
}
```

| Field | Kiểu | Mô tả |
|---|---|---|
| `request_id` | `string` | UUID tracking qua các giai đoạn xử lý |
| `status` | `string` | `"accepted"` hoặc `"accepted_with_warning"` |
| `message` | `string` | Thông báo cho người dùng |
| `tenant_id` | `string` | Echo lại tenant_id đã gửi |
| `location` | `string` | Echo lại location đã gửi |
| `input_type` | `string` | `"audio"` / `"text"` / `"audio_and_text"` |
| `transcript` | `string \| null` | Kết quả STT từ Whisper (null nếu chỉ gửi text hoặc Whisper lỗi) |
| `is_suspicious` | `boolean` | Kết quả fraud filter |
| `suspicious_reason` | `string \| null` | Lý do bị đánh dấu nghi ngờ |

### Các mã lỗi

| Status Code | Khi nào | Response |
|---|---|---|
| `400` | Thiếu cả audio lẫn text, hoặc bị fraud filter từ chối | `{"detail": "..."}` |
| `413` | File audio > 5MB | `{"detail": "File audio quá lớn: XMB. Giới hạn tối đa: 5MB"}` |
| `422` | Lỗi validation form fields (FastAPI tự sinh) | `{"detail": [...]}` |
| `503` | Whisper API key lỗi xác thực | `{"detail": "STT service không khả dụng..."}` |
| `504` | Whisper timeout | `{"detail": "STT service tạm thời quá tải..."}` |

### Luồng xử lý hiện tại (Giai đoạn 3-4 của Tuyền)
```
Nhận request → validate → fraud filter → lưu audio tạm → Whisper STT → trả 202
```

### Luồng xử lý đầy đủ (sau khi Tuyền hoàn thành GĐ 5-9)
```
Nhận → validate → fraud filter → Whisper STT → Librosa features
→ ABSA (Gemini) → Dynamic Weighted Fusion → RFMS → lưu Firestore
→ [nếu P_churn > threshold] trigger Zalo ZNS
```

> ⚠️ **Tuấn lưu ý:** Các bước từ Librosa trở đi **CHƯA ĐƯỢC TÍCH HỢP** vào endpoint này. Response hiện tại chỉ có `transcript`, chưa có `aspects`, `sentiment_score`, `p_churn`. Khi Tuyền hoàn thành, response schema **SẼ MỞ RỘNG** (thêm fields) — Việt sẽ cập nhật contract này.

---

## 3. 🟡 `POST /api/v1/analyze` — ĐANG THƯƠNG LƯỢNG

> **File:** `backend/api/routes/analyze.py`
> **Mục đích:** Endpoint ABSA riêng lẻ — nhận text, trả về danh sách aspects + sentiment. Tách biệt với `/feedback`.

### ⚠️ Lưu ý quan trọng
Endpoint này **đã có code thật** nhưng đánh dấu 🟡 vì:
1. Nó import `SentimentAnalyzer` từ `backend.ai_pipeline.llM_few_shot_generator` — module này thuộc PR ABSA LLM của Tuyền **đang chờ sửa** (dataset lớn, model khai tử).
2. Tuyền có thể đổi request/response format khi sửa xong PR.
3. Chưa rõ endpoint này sẽ tồn tại song song với `/feedback` hay sẽ gộp vào.

### Request — `application/json`
```json
{
  "text": "Phục vụ tốt quá ha, đợi có 20 phút mà"
}
```

| Field | Kiểu | Bắt buộc | Mô tả |
|---|---|---|---|
| `text` | `string` | ✅ | Văn bản cần phân tích ABSA. Không được rỗng |

### Response `200 OK`
```json
{
  "status": "success",
  "aspects": [
    {
      "phrase": "đợi có 20 phút",
      "category": "toc_do_phuc_vu",
      "sentiment": "negative"
    },
    {
      "phrase": "Phục vụ tốt quá ha",
      "category": "nhan_vien",
      "sentiment": "positive"
    }
  ],
  "error": null
}
```

| Field | Kiểu | Mô tả |
|---|---|---|
| `status` | `string` | `"success"` hoặc `"partial_success"` (nếu LLM lỗi parse) |
| `aspects` | `array` | Danh sách aspects đã phân tích |
| `aspects[].phrase` | `string` | Cụm từ gốc trong text |
| `aspects[].category` | `string` | Khía cạnh phân loại |
| `aspects[].sentiment` | `string` | `"positive"` / `"negative"` / `"neutral"` |
| `error` | `string \| null` | Thông báo lỗi nếu `status == "partial_success"` |

### Các mã lỗi

| Status Code | Khi nào |
|---|---|
| `400` | Trường `text` rỗng |
| `500` | Lỗi hệ thống khi gọi Gemini/xử lý ABSA |

---

## 4. 🔴 `POST /api/gamification/spin` — CHƯA CÓ

> **Mục đích:** Vòng quay may mắn sau khi khách gửi phản hồi.
> **Trạng thái:** Tuấn đang code frontend với **mock data**. Cần Tuyền lên kế hoạch endpoint này.

### Request (DỰ KIẾN — chưa chốt)
```json
{
  "tenant_id": "pho-ba-lan_1722500000000",
  "customer_phone": "0901234567",
  "feedback_id": "abc123xyz"
}
```

### Response (DỰ KIẾN — chưa chốt)
```json
{
  "prize": "giam_10_phan_tram",
  "voucher_code": "SENTRIX-ABCD-1234",
  "message": "Chúc mừng bạn nhận được mã giảm giá 10%!"
}
```

> ⚠️ **Tuấn:** Dùng mock data hardcode trong frontend. KHÔNG gọi endpoint thật vì chưa tồn tại.

---

## 5. 🔴 `GET /api/dashboard/kpi` — CHƯA CÓ (có thể không cần)

> **Mục đích:** Tổng hợp KPI cho dashboard chủ doanh nghiệp.
> **Trạng thái thật:** Dashboard hiện thiết kế đọc **trực tiếp Firestore** (không qua REST API) theo `backend/db/schema.md`.

### Cách Tuấn nên code Dashboard hiện tại
Thay vì gọi API endpoint, đọc trực tiếp từ Firestore SDK:

```javascript
// Feedback mới nhất
db.collection(`tenants/${tenantId}/feedbacks`)
  .orderBy('timestamp', 'desc')
  .limit(20)
  .onSnapshot(snapshot => { ... })

// Khách hàng rủi ro cao
db.collection(`tenants/${tenantId}/customers`)
  .where('churn_risk_level', '==', 'high')
  .orderBy('p_churn', 'desc')
  .onSnapshot(snapshot => { ... })
```

*(Nguồn: backend/db/schema.md §Dashboard — Hướng dẫn nhanh cho Việt)*

> ⚠️ Dashboard dùng React. Deploy lên Vercel cùng web-client.

---

## 6. 🔴 `GET /api/dashboard/churn-alerts` — CHƯA CÓ (có thể không cần)

> **Tương tự mục 5** — Dashboard đọc trực tiếp Firestore collection `customers` với filter `churn_risk_level == "high"`.
> Nếu sau này cần REST API riêng (ví dụ: để Mobile App gọi), Tuyền sẽ thêm — lúc đó Việt cập nhật contract.

---

## Firestore Schema Reference (Tóm tắt cho Tuấn)

> Chi tiết đầy đủ: xem `backend/db/schema.md`

### Collections chính

| Collection path | Mục đích | Fields quan trọng nhất |
|---|---|---|
| `tenants/{tenant_id}` | Thông tin doanh nghiệp | `business_name`, `industry`, `plan`, `is_active`, `churn_threshold` |
| `tenants/{id}/feedbacks/{feedback_id}` | 1 lượt phản hồi | `transcript`, `aspects[]`, `sentiment_score`, `is_sarcasm`, `processing_status` |
| `tenants/{id}/customers/{customer_id}` | Hồ sơ khách hàng | `phone_masked`, `rfms_r/f/m/s`, `p_churn`, `churn_risk_level` |

### Aspect categories (dùng cho cả backend lẫn frontend)
`"nhan_vien"` · `"mon_an"` · `"khong_gian"` · `"gia_ca"` · `"toc_do_phuc_vu"` · `"ve_sinh"` · `"khac"`

### Sentiment values
`"positive"` · `"negative"` · `"neutral"`

### Churn risk levels
`"low"` (P < 0.5) · `"medium"` (0.5 ≤ P ≤ 0.85) · `"high"` (P > 0.85)

---

## Lịch sử cập nhật

| Ngày | Thay đổi | Người |
|---|---|---|
| 2026-08-05 | Tạo bản đầu tiên — 3 endpoint cam kết, 3 endpoint chưa có | Việt |
