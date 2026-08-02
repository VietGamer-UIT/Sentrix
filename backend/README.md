# 🧠 LÃNH ĐỊA BACKEND & AI PIPELINE — SENTRIX

**Người cai quản:** Nguyễn Thanh Tuyền (AI & Data Architect)

> ⚠️ Chỉ Tuyền mới được sửa code trong thư mục `backend/`. Xem `CONTRIBUTING.md` và `README.md` ở root repo để hiểu quy tắc lãnh địa.

---

## 📁 Cấu trúc thư mục

```
backend/
├── api/
│   ├── main.py           # FastAPI app, khởi tạo app và đăng ký router
│   └── routes/
│       ├── health.py     # GET /health — kiểm tra server sống
│       └── ...           # (thêm ở các giai đoạn sau)
├── ai_pipeline/           # Code Whisper STT + Librosa + ABSA (Giai đoạn 4–6)
├── rfms_model/            # Thuật toán RFMS + Churn Probability (Giai đoạn 7)
├── db/                    # Cấu hình Firebase Firestore multi-tenant (Giai đoạn 2, 8)
├── webhooks/              # Zalo ZNS webhook trigger (Giai đoạn 9)
├── tests/
│   └── test_health.py    # Unit test cho /health
├── requirements.txt       # Danh sách thư viện Python (ghi chú giai đoạn dùng)
└── README.md              # File này
```

---

## 🚀 Cách chạy backend (local dev)

### 1. Clone repo & di chuyển vào thư mục gốc
```bash
git clone https://github.com/VietGamer-UIT/Sentrix.git
cd Sentrix
```

### 2. Tạo môi trường ảo Python (bắt buộc, tránh xung đột thư viện)
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Cài đặt thư viện
```bash
pip install -r backend/requirements.txt
```

### 4. Tạo file `.env` từ `.env.example` và điền giá trị thật
```bash
# Sao chép file mẫu
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux

# Mở .env bằng editor và điền API key thật vào
```

### 5. Chạy server
```bash
# Chạy từ thư mục gốc repo (d:\Sentrix), KHÔNG cd vào backend/
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

> **Tại sao phải chạy từ root?** Vì lệnh `uvicorn backend.api.main:app` dùng Python package path — cần `backend/` là package con của thư mục gốc, có file `backend/__init__.py`.

### 6. Kiểm tra server
Mở trình duyệt hoặc Postman:
- **Health check:** `GET http://localhost:8000/health`
- **Swagger UI (tài liệu API):** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 🧪 Chạy tests

```bash
# Chạy từ thư mục gốc repo
pytest backend/tests/ -v
```

---

## 🗺️ Tiến trình 9 giai đoạn

| # | Giai đoạn | Nhánh Git | Trạng thái |
|---|---|---|---|
| 1 | Khung FastAPI + môi trường | `feature/tuyen-fastapi-skeleton` | ✅ Xong |
| 2 | Schema Firestore multi-tenant | `feature/tuyen-firestore-schema` | ⏳ Chờ |
| 3 | Endpoint nhận phản hồi (audio/text) | `feature/tuyen-feedback-endpoint` | ⏳ Chờ |
| 4 | Tích hợp Whisper STT | `feature/tuyen-whisper-stt` | ⏳ Chờ |
| 5 | Trích xuất đặc trưng Librosa | `feature/tuyen-librosa-features` | ⏳ Chờ |
| 6 | ABSA LLM + Dynamic Weighted Fusion | `feature/tuyen-absa-llm` | ⏳ Chờ |
| 7 | RFMS + Churn Probability | `feature/tuyen-rfms-model` | ⏳ Chờ |
| 8 | Lưu Firestore multi-tenant | `feature/tuyen-firestore-integration` | ⏳ Chờ |
| 9 | Webhook Zalo ZNS | `feature/tuyen-zalo-webhook` | ⏳ Chờ |

---

## 🔌 API Endpoints hiện có

### `GET /health`
Kiểm tra server đang hoạt động.

**Response 200 OK:**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "message": "Sentrix Backend is running! 🚀"
}
```

---

## 📝 Cần phối hợp với Việt/Tuấn

> *Ghi lại ở đây thay vì tự ý sửa file của người khác. Sau khi ghi xong, nhắn Zalo nhóm.*

*(Hiện tại chưa có yêu cầu phối hợp.)*

---

## 🔐 Biến môi trường cần thiết

Xem file `.env.example` ở thư mục gốc repo để biết danh sách đầy đủ.
Tuyền cần điền các biến sau (giá trị thật trong `.env` cục bộ — **KHÔNG commit `.env` lên GitHub**):

| Biến | Dùng ở đâu |
|---|---|
| `WHISPER_API_KEY` | Giai đoạn 4 — OpenAI Whisper API |
| `GEMINI_API_KEY` | Giai đoạn 6 — Gemini Flash-Lite ABSA |
| `FIREBASE_PROJECT_ID` | Giai đoạn 2, 8 — Firestore connection |
| `FIREBASE_PRIVATE_KEY` | Giai đoạn 2, 8 — Service Account auth |
| `FIREBASE_CLIENT_EMAIL` | Giai đoạn 2, 8 — Service Account auth |
| `ZALO_APP_ID` | Giai đoạn 9 — Zalo ZNS |
| `ZALO_ACCESS_TOKEN` | Giai đoạn 9 — Zalo ZNS |
| `ZALO_REFRESH_TOKEN` | Giai đoạn 9 — Zalo ZNS |
