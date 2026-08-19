# Sentrix — AI-Powered Multimodal Customer Experience Analytics Platform

Nền tảng phân tích trải nghiệm khách hàng đa phương thức (giọng nói + văn bản) dành cho ngành F&B Việt Nam. Dùng Whisper STT, Gemini ABSA, Librosa audio features, RFMS churn model và Zalo ZNS.

---

## 🏗️ Cấu trúc dự án

```
Sentrix/
├── backend/          # FastAPI — AI pipeline, RFMS, Firestore ops
├── apps/
│   ├── web-client/   # React — giao diện khách hàng (quét QR → ghi âm → quay thưởng)
│   └── dashboard/    # React — dashboard chủ quán (báo cáo, churn alert)
├── docs/             # Tài liệu kỹ thuật
├── design/           # Figma exports, assets
├── firestore.rules   # Firestore Security Rules
└── render.yaml       # Render deploy config
```

---

## 🚀 Cài đặt & Chạy local

### Backend (Python 3.11+)

```bash
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env   # điền các API key thật
uvicorn backend.main:app --reload --port 8000
```

### Web Client (Node 18+)

```bash
cd apps/web-client
npm install
cp .env.example .env         # điền VITE_API_BASE_URL
npm run dev                  # http://localhost:5173
```

### Dashboard

```bash
cd apps/dashboard
npm install
cp .env.example .env
npm run dev                  # http://localhost:5174
```

### Biến môi trường cần thiết

Xem [`.env.example`](.env.example) ở root. Các key cần có:

| Biến | Mô tả |
|---|---|
| `FIREBASE_PROJECT_ID` | Firebase project |
| `FIREBASE_CLIENT_EMAIL` | Service account email |
| `FIREBASE_PRIVATE_KEY` | Service account private key |
| `WHISPER_API_KEY` | OpenAI API key (Whisper STT) |
| `GEMINI_API_KEY` | Google AI Studio key |
| `GEMINI_MODEL_NAME` | Mặc định: `gemini-3.1-flash-lite` |

---

## 🔧 Luồng dữ liệu chính

```
Khách quét QR → Ghi âm/Gõ text
  → POST /api/v1/feedback (FastAPI)
    → Fraud Filter → Whisper STT ‖ Librosa (song song)
    → Gemini ABSA → Fusion (text + audio weights)
    → RFMS Calculator → Churn Model → Firestore
  → 202 Accepted (sentiment, p_churn, feedback_id)
  → SpinPage: POST /api/v1/gamification/spin (backend quyết định prize)
  → Dashboard hiển thị realtime
```

Chi tiết: xem [`docs/`](docs/) và [`backend/README.md`](backend/README.md).

---

## 🛠️ Deploy

- **Backend:** Render (Web Service, `render.yaml`)
- **Frontend:** Vercel (auto-deploy từ `main`)
- **Database:** Firestore (Firebase)
- **Firestore Rules:** `firebase deploy --only firestore:rules`

> **Cold start:** Render free tier ngủ sau ~15 phút không có traffic. Cài cron job (cron-job.org) ping `GET /health` mỗi 10 phút để giữ container ấm khi demo.

---

## 📚 Tài liệu kỹ thuật

- [`CONTRIBUTING.md`](CONTRIBUTING.md) — Quy trình git & commit
- [`backend/README.md`](backend/README.md) — API reference, cấu trúc backend
- [`backend/db/schema.md`](backend/db/schema.md) — Firestore schema
- [`docs/api-contract.md`](docs/api-contract.md) — API contract frontend–backend
