# Sentrix - AI-Powered Multimodal Customer Experience Analytics Platform

Sentrix là nền tảng SaaS thu thập và phân tích trải nghiệm khách hàng đa phương thức qua QR và giọng nói. Hệ thống kết hợp Whisper (Speech-to-Text), Librosa, LLM ABSA, và mô hình RFMS để dự đoán churn, sử dụng Firebase Firestore cho multi-tenant và Zalo ZNS cho webhook cảnh báo.

## Cấu trúc thư mục

- `apps/`: Giao diện người dùng (Web client cho khách hàng & Dashboard quản trị) - Phụ trách: **Việt**
- `backend/`: Lõi xử lý AI, API, và Database - Phụ trách: **Tuyền**
- `design/`: Thiết kế UX/UI và tài liệu nghiên cứu thị trường - Phụ trách: **Tuấn**
- `docs/`: Tài liệu dự án (Thuyết minh, BMC, Pitch deck)
- `deploy/`: Cấu hình deploy Vercel và Render
- `assets/`: Tài nguyên tĩnh (Logo, mã QR)

## Hướng dẫn cài đặt nhanh

### 1. Clone repository
```bash
git clone <url-repo-cua-ban>
cd Sentrix
```

### 2. Cài đặt Backend (FastAPI)
```bash
cd backend/api
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt # (Sau này sẽ có file này)
```

### 3. Cài đặt Frontend (React/Next.js)
```bash
cd apps/web-client
npm install
# hoặc yarn install
```
