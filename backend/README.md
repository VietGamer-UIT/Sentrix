# 🧠 Backend & AI Pipeline — Sentrix

**Người cai quản:** Nguyễn Thanh Tuyền (AI & Data Architect)  
**Hỗ trợ giai đoạn 5–9:** Đoàn Hoàng Việt (Project Lead)  
**Trạng thái:** ✅ **Tất cả 9 giai đoạn hoàn thành — sẵn sàng ghép frontend**

> ⚠️ Chỉ Tuyền (hoặc người được ủy quyền) mới được sửa code trong `backend/`. Xem `CONTRIBUTING.md` ở root để biết quy tắc lãnh địa.

---

## 📋 Mục lục
1. [Sơ đồ pipeline end-to-end](#-sơ-đồ-pipeline-end-to-end)
2. [Cấu trúc thư mục](#-cấu-trúc-thư-mục)
3. [Cài đặt & chạy local](#-cài-đặt--chạy-local)
4. [Biến môi trường](#-biến-môi-trường)
5. [API Endpoints](#-api-endpoints)
6. [Tiến trình 9 giai đoạn](#-tiến-trình-9-giai-đoạn)
7. [Chạy tests](#-chạy-tests)
8. [Cần phối hợp với Việt / Tuấn](#-cần-phối-hợp-với-việt--tuấn)

---

## 🔄 Sơ đồ pipeline end-to-end

```
 [Khách hàng quét QR]
        │
        ▼
 POST /api/v1/feedback
 (audio file / text / cả hai + customer_phone + total_spending)
        │
        ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  [1] Validate input (MIME type, kích thước, có audio/text)  │
 │  [2] Fraud Filter (audio quá ngắn? text toàn rác?)          │
 └──────────────────────────┬──────────────────────────────────┘
                            │
              ┌─────────────┴──────────────┐
              ▼ (nếu có audio)             ▼ (nếu chỉ có text)
   [3] Whisper STT                    transcript = text gốc
       audio → transcript
              │
              ▼ (nếu có audio)
   [4] Librosa Feature Extraction
       MFCC · F0 · Jitter · Shimmer · stress_score
              │
              └─────────────┬──────────────┘
                            ▼
                 [5] ABSA qua Gemini Flash-Lite
                     Phân tích từng khía cạnh:
                     nhan_vien · mon_an · khong_gian
                     gia_ca · toc_do_phuc_vu · ve_sinh
                            │
                            ▼
                 [6] Dynamic Weighted Fusion
                     · Phát hiện mỉa mai (sarcasm)
                     · Kết hợp text + audio
                     → sentiment_score [0.0 – 1.0]
                            │
                            ▼
                 [7] RFMS + Churn Probability
                     R (Recency) · F (Frequency)
                     M (Monetary) · S (Sentiment)
                     → P_churn = sigmoid(αR − βF − γM − δS + ε)
                            │
                            ▼
              ┌─────────────────────────────────┐
              │ [8] Lưu Firestore (multi-tenant) │
              │  tenants/{tenant_id}/            │
              │    feedbacks/{feedback_id}       │
              │    customers/{customer_id}       │
              │    (RFMS + P_churn cập nhật)     │
              └──────────────┬──────────────────┘
                             │
              ┌──────────────┴─────────────────────────────────┐
              │  P_churn > threshold (mặc định 0.85)?           │
              │  AND có customer_phone?                          │
              └──────────────┬─────────────────────────────────┘
                    YES ──── ▼
              [9] Zalo ZNS / ZBS Template Message
                  → Gửi cảnh báo + mã voucher cho khách
                  → Cập nhật zns_sent_at vào Firestore
                            │
                            ▼ (dù ZNS có lỗi cũng không crash)
              ─────────────────────────────
              Response 202 Accepted
              {
                feedback_id, sentiment_score,
                overall_sentiment, is_sarcasm_suspected,
                p_churn, churn_risk_level, should_alert
              }
```

> **Đặc điểm thiết kế quan trọng:**
> - Mỗi bước **graceful degradation**: nếu Whisper/Librosa/ABSA lỗi → ghi log, dùng giá trị mặc định, tiếp tục pipeline.
> - ZNS (Bước 9) **không bao giờ crash** pipeline chính — lỗi ZNS chỉ được log lại.
> - Firestore cách ly hoàn toàn theo `tenant_id` — đảm bảo data của tenant A không lộ sang tenant B.

---

## 📁 Cấu trúc thư mục

```
backend/
├── api/
│   ├── main.py                        # FastAPI app, đăng ký router, CORS
│   ├── routes/
│   │   ├── health.py                  # GET /health
│   │   └── feedback.py                # POST /api/v1/feedback — PIPELINE CHÍNH
│   └── middleware/
│       └── fraud_filter.py            # Lọc spam sơ bộ (audio quá ngắn, text rác)
│
├── ai_pipeline/
│   ├── stt_whisper.py                 # [G4] Whisper STT: audio → transcript
│   ├── audio_features_librosa.py      # [G5] Librosa: MFCC, F0, Jitter, Shimmer
│   ├── absa_llm.py                    # [G6] ABSA qua Gemini Flash-Lite
│   ├── fusion.py                      # [G6] Dynamic Weighted Fusion + sarcasm detection
│   └── README.md                      # Hướng dẫn dataset parsing
│
├── rfms_model/
│   ├── rfms_calculator.py             # [G7] Min-Max normalization RFMS → [0,1]
│   ├── churn_model.py                 # [G7] P_churn = sigmoid(αR − βF − γM − δS + ε)
│   └── README.md                      # Tài liệu hệ số + kế hoạch huấn luyện thật
│
├── db/
│   ├── firestore_client.py            # [G2/G8] Firebase Admin SDK singleton
│   ├── firestore_ops.py               # [G8] CRUD: save_feedback, get_or_create_customer,
│   │                                  #           update_customer_rfms (transactional)
│   └── schema.md                      # [G2] Tài liệu schema Firestore (ĐỌC TRƯỚC KHI CODE)
│
├── webhooks/
│   └── zalo_zns.py                    # [G9] Gửi ZNS/ZBS Template Message + error handling
│
├── tests/
│   ├── test_health.py                 # [G1] Health check
│   ├── test_audio_features.py         # [G5] Librosa feature extraction
│   ├── test_absa_fusion.py            # [G6] ABSA + Fusion + sarcasm detection
│   ├── test_rfms_churn.py             # [G7] RFMS normalization + P_churn model
│   ├── test_firestore_integration.py  # [G8] Multi-tenant isolation + CRUD
│   └── test_zalo_zns.py               # [G9] ZNS mock tests (9 cases)
│
├── requirements.txt                   # Tất cả thư viện Python
└── README.md                          # File này
```

---

## 🚀 Cài đặt & chạy local

### Bước 1 — Clone repo
```bash
git clone https://github.com/VietGamer-UIT/Sentrix.git
cd Sentrix
```

### Bước 2 — Tạo môi trường ảo Python
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate
```

### Bước 3 — Cài thư viện
```bash
pip install -r backend/requirements.txt
```

> ⚠️ **Lưu ý:** `librosa` phụ thuộc vào `libsndfile`. Nếu gặp lỗi trên Windows:
> ```bash
> pip install soundfile
> ```

### Bước 4 — Tạo file `.env`
```bash
# Windows:
copy .env.example .env
# macOS/Linux:
cp .env.example .env
```
Mở `.env` và điền các giá trị thật (xem mục [Biến môi trường](#-biến-môi-trường)).

### Bước 5 — Chạy server
```bash
# Luôn chạy từ thư mục GỐC repo (không cd vào backend/)
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Bước 6 — Kiểm tra
| URL | Mô tả |
|-----|-------|
| `http://localhost:8000/health` | Health check |
| `http://localhost:8000/docs` | Swagger UI (thử API trực tiếp) |
| `http://localhost:8000/redoc` | ReDoc (tài liệu đẹp) |

---

## 🔐 Biến môi trường

Tất cả biến môi trường cần thiết — **KHÔNG commit `.env` lên GitHub**.

| Biến | Bắt buộc | Dùng ở giai đoạn | Ghi chú |
|------|----------|------------------|---------|
| `OPENAI_API_KEY` | ✅ | G4 — Whisper STT | Lấy tại platform.openai.com |
| `GEMINI_API_KEY` | ✅ | G6 — ABSA Gemini | Lấy tại aistudio.google.com |
| `FIREBASE_CREDENTIALS_PATH` | ⭐ | G8 — Firestore | Ưu tiên dùng file JSON này |
| `FIREBASE_PROJECT_ID` | ✅* | G8 — Firestore | *Chỉ cần nếu không có file JSON |
| `FIREBASE_PRIVATE_KEY` | ✅* | G8 — Firestore | *Chỉ cần nếu không có file JSON |
| `FIREBASE_CLIENT_EMAIL` | ✅* | G8 — Firestore | *Chỉ cần nếu không có file JSON |
| `ZALO_ACCESS_TOKEN` | ✅ | G9 — Zalo ZNS | Hết hạn sau **25 giờ** — phải refresh! |
| `ZALO_TEMPLATE_ID` | ✅ | G9 — Zalo ZNS | ID template đã được Zalo duyệt |

> **Cách lấy Firebase credentials:**  
> Firebase Console → Project Settings → Service Accounts → **Generate new private key** → tải về `serviceAccountKey.json`  
> Đặt `FIREBASE_CREDENTIALS_PATH=backend/serviceAccountKey.json` trong `.env`

> **Cách lấy Zalo Access Token:**  
> Zalo Developer → OA của doanh nghiệp → OAuth 2.0 (v4) → lấy `access_token`  
> Token hết hạn **25h** — cần refresh bằng `refresh_token`. Xem tài liệu tại developers.zalo.me

---

## 📡 API Endpoints

### `GET /health`
Kiểm tra server sống.

**Response 200:**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "message": "Sentrix Backend is running! 🚀"
}
```

---

### `POST /api/v1/feedback`
**Endpoint chính** — nhận phản hồi khách hàng và chạy toàn bộ AI pipeline.

**Form Data (multipart/form-data):**

| Field | Kiểu | Bắt buộc | Mô tả |
|-------|------|----------|-------|
| `tenant_id` | string | ✅ | ID doanh nghiệp (lấy từ QR code) |
| `location` | string | ✅ | Bàn / khu vực quét QR. VD: `"Ban 5"` |
| `audio_file` | file | ⭐ | File ghi âm (WebM/MP3/WAV/OGG, tối đa 5MB) |
| `text_content` | string | ⭐ | Phản hồi gõ tay (tối đa 2000 ký tự) |
| `customer_phone` | string | ❌ | SĐT khách hàng — cần để tính RFMS & gửi ZNS |
| `total_spending` | float | ❌ | Tổng chi tiêu lần này (VNĐ). Mặc định: 0 |

> ⭐ Phải có ít nhất `audio_file` HOẶC `text_content`.

**Response 202 Accepted:**
```json
{
  "request_id": "uuid-...",
  "feedback_id": "firestore-auto-id",
  "status": "processed",
  "message": "Phan hoi da duoc xu ly va luu thanh cong.",
  "tenant_id": "pho-ba-lan_1722500000000",
  "location": "Ban 5",
  "input_type": "audio",
  "transcript": "Phục vụ hơi chậm nhưng đồ ăn ngon",
  "sentiment_score": 0.42,
  "overall_sentiment": "Trung lap",
  "is_sarcasm_suspected": false,
  "p_churn": 0.31,
  "churn_risk_level": "medium",
  "should_alert": false,
  "is_suspicious": false,
  "suspicious_reason": null
}
```

**Mức rủi ro churn (`churn_risk_level`):**

| Giá trị | P_churn | Ý nghĩa |
|---------|---------|---------|
| `"low"` | < 0.50 | Khách trung thành — không cần can thiệp |
| `"medium"` | 0.50 – 0.84 | Theo dõi thêm |
| `"high"` | ≥ 0.85 | **Trigger Zalo ZNS** (nếu có `customer_phone`) |

---

## ✅ Tiến trình 9 giai đoạn

| # | Giai đoạn | Nhánh Git | Người thực hiện | Trạng thái |
|---|-----------|-----------|-----------------|-----------|
| 1 | Khung FastAPI + môi trường | `feature/tuyen-fastapi-skeleton` | Tuyền | ✅ Merged |
| 2 | Schema Firestore multi-tenant | `feature/tuyen-firestore-schema` | Tuyền | ✅ Merged |
| 3 | Endpoint nhận phản hồi | `feature/tuyen-feedback-endpoint` | Tuyền | ✅ Merged |
| 4 | Whisper STT | `feature/tuyen-whisper-stt` | Tuyền | ✅ Merged |
| 5 | Librosa audio features | `feature/viet-librosa-features` | Tuyền *(Việt hỗ trợ)* | ✅ Merged |
| 6 | ABSA LLM + Dynamic Fusion | `feature/viet-absa-fusion` | Tuyền *(Việt hỗ trợ)* | ✅ Merged |
| 7 | RFMS + Churn Probability | `feature/viet-rfms-model` | Tuyền *(Việt hỗ trợ)* | ✅ Merged |
| 8 | Lưu Firestore end-to-end | `feature/viet-firestore-integration` | Tuyền *(Việt hỗ trợ)* | ✅ Merged |
| 9 | Webhook Zalo ZNS | `feature/viet-zalo-webhook` | Tuyền *(Việt hỗ trợ)* | ✅ Merged |

**🎉 100% backend AI pipeline hoàn thành!**

---

## 🧪 Chạy tests

```bash
# Chạy toàn bộ test suite (từ thư mục gốc repo)
pytest backend/tests/ -v

# Chạy từng file test riêng lẻ
python backend/tests/test_rfms_churn.py
python backend/tests/test_zalo_zns.py
python backend/tests/test_firestore_integration.py --logic-only
```

**Kết quả test hiện tại (không cần credentials thật):**

| Test file | Số tests | Kết quả |
|-----------|---------|---------|
| `test_audio_features.py` | 5 | ✅ Pass |
| `test_absa_fusion.py` | 6 | ✅ Pass |
| `test_rfms_churn.py` | 5 | ✅ Pass |
| `test_firestore_integration.py` (logic-only) | 5 | ✅ Pass |
| `test_zalo_zns.py` | 9 | ✅ Pass |

> **Test đầy đủ với Firebase thật:** chạy `test_firestore_integration.py` (không có `--logic-only`) sau khi cấu hình credentials.

---

## 🤝 Cần phối hợp với Việt / Tuấn

> *Tuyền ghi lại ở đây thay vì tự ý sửa file của người khác. Sau khi ghi xong, đã nhắn Zalo nhóm.*

### 🔴 Ưu tiên cao — cần xác nhận trước khi demo

**[Việt — Dashboard]**

1. **Response JSON format:** Dashboard đọc `POST /api/v1/feedback` response — xác nhận các field dưới đây đủ để hiển thị chưa, hay cần bổ sung?
   ```json
   { "sentiment_score", "overall_sentiment", "is_sarcasm_suspected",
     "p_churn", "churn_risk_level", "should_alert", "feedback_id" }
   ```

2. **Firestore realtime listener:** Dashboard dùng `onSnapshot` trên `tenants/{tenant_id}/feedbacks` — cần Việt tạo **Firestore Composite Index** theo hướng dẫn trong `backend/db/schema.md` (mục "Indexes cần tạo").

3. **Trường `customer_phone` từ frontend:** Pipeline ZNS chỉ gửi được khi có `customer_phone` trong form data. Frontend có form điền SĐT khách hàng không, hay chỉ có QR anonymous? Nếu anonymous → ZNS sẽ không gửi được (cần bàn lại UX).

4. **Hiển thị `aspects` trên Dashboard:** Mảng `aspects` trong `feedbacks/{id}` có đủ thông tin để Việt render biểu đồ sentiment per-aspect không? Format từng item:
   ```json
   { "aspect": "toc_do_phuc_vu", "sentiment": "Tieu cuc",
     "score": -0.82, "reason": "Cho qua lau", "confidence": 0.91 }
   ```

**[Tuấn — Deployment / DevOps]**

5. **Zalo OA thật:** Cần Tuấn (hoặc người phụ trách OA) tạo **template ZNS trên Zalo OA Manager** và cung cấp:
   - `ZALO_TEMPLATE_ID` — ID template đã được Zalo duyệt
   - `ZALO_ACCESS_TOKEN` — Token OAuth 2.0 (hết hạn sau 25h, cần refresh định kỳ)
   - Cấu trúc template mẫu gợi ý:
     ```
     Xin chào! Sentrix ghi nhận trải nghiệm {{aspect}} của bạn
     chưa được như ý. Chúng tôi muốn có cơ hội phục vụ bạn tốt hơn —
     tặng bạn ưu đãi {{voucher_code}} cho lần ghé thăm tiếp theo! 🎁
     ```

6. **Firebase credentials cho production (Render):** Hiện tại backend chạy local với `serviceAccountKey.json`. Khi deploy lên Render, cần Tuấn thêm 3 biến môi trường vào Render Dashboard:
   - `FIREBASE_PROJECT_ID`
   - `FIREBASE_PRIVATE_KEY` (copy nguyên từ JSON, giữ `\n`)
   - `FIREBASE_CLIENT_EMAIL`

7. **Token refresh tự động Zalo:** `ZALO_ACCESS_TOKEN` hết hạn **mỗi 25 giờ**. MVP hiện tại cần refresh thủ công. Nếu muốn tự động, cần Tuấn implement cron job dùng `ZALO_REFRESH_TOKEN` để làm mới token (xem OAuth v4 flow tại developers.zalo.me).

### 🟡 Ưu tiên trung bình — cải thiện sau demo

8. **RFMS hệ số thật:** Hệ số mặc định trong `churn_model.py` là khởi tạo giả định. Sau khi có dữ liệu pilot (~500 feedback), Tuyền sẽ train lại bằng scikit-learn. Xem kế hoạch chi tiết trong `backend/rfms_model/README.md`.

9. **`total_spending` từ POS:** Hiện tại field `monetary` (M trong RFMS) dựa vào `total_spending` gửi từ client. Nếu có tích hợp POS, cần phối hợp để lấy giá trị chính xác hơn từ bill thật.

10. **Async task queue:** Pipeline hiện chạy đồng bộ (Whisper → Librosa → ABSA → Firestore → ZNS trong 1 request). Khi scale lên nhiều tenant, cần chuyển sang Celery/Redis task queue. Ghi nhận để lên kế hoạch sau.

---

## 📌 Ghi chú kỹ thuật quan trọng

### Về Zalo ZNS (Giai đoạn 9)
- Từ **01/01/2026**, ZNS đã hợp nhất vào **ZBS Template Message** — endpoint không đổi: `https://business.openapi.zalo.me/message/template`
- Module `zalo_zns.py` xử lý đầy đủ: token hết hạn (error 216), rate limit (error 147/148), timeout, retry 1 lần
- **ZNS không bao giờ crash pipeline chính** — mọi lỗi đều được bắt và log

### Về RFMS Churn Model (Giai đoạn 7)
- Hệ số hiện tại: `α=2.5, β=1.5, γ=1.0, δ=3.0, ε=1.0` — **chưa học từ dữ liệu thật**
- Xem `backend/rfms_model/README.md` để biết kế hoạch huấn luyện với scikit-learn

### Về Multi-Tenant Isolation (Giai đoạn 8)
- Mọi CRUD đều đi qua path `tenants/{tenant_id}/...` — Security Rules kiểm soát ở cấp path
- `customer_id` = `cust_{sha256_of_phone[:16]}` — SĐT gốc **không lưu trong Firestore**
- Dashboard của Việt đọc `tenants/{tenant_id}/customers` — sắp xếp theo `p_churn DESC` để lấy danh sách rủi ro

---

*README này được cập nhật lần cuối: 2026-08-05 bởi Đoàn Hoàng Việt (thay mặt Nguyễn Thanh Tuyền)*
