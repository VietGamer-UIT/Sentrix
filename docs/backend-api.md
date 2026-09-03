# Backend & AI Pipeline - Sentrix

Dự án Sentrix Backend API. Đội ngũ phát triển tập trung vào AI Pipeline và API xử lý phản hồi khách hàng.

---

## 📋 Mục lục
1. [Sơ đồ pipeline xử lý](#-sơ-đồ-pipeline-xử-lý)
2. [Cấu trúc thư mục](#-cấu-trúc-thư-mục)
3. [Cài đặt và chạy local](#-cài-đặt-và-chạy-local)
4. [Biến môi trường](#-biến-môi-trường)
5. [API Endpoints](#-api-endpoints)
6. [Tiến trình phát triển](#-tiến-trình-phát-triển)
7. [Chạy tests](#-chạy-tests)

---

## 🔄 Sơ đồ pipeline xử lý

```
 [Khách hàng quét QR]
        │
        ▼
 POST /api/v1/feedback
 (audio file / text / tổng chi tiêu / thông tin khách hàng)
        │
        ▼
 ┌─────────────────────────────────────────────────────────────┐
 │  [1] Lớp bảo vệ chống gian lận (Rate Limit, OTP, Audio QC)  │
 │  [2] Semantic Validity Classifier                           │
 └──────────────────────────┬──────────────────────────────────┘
                            │
              ┌─────────────┴──────────────┐
              ▼ (nếu có voice)             ▼ (nếu chỉ có text)
   [3] STT (Groq Whisper)             transcript = text gốc
       voice -> transcript
              │
              ▼ (nếu có voice)
   [4] Trích xuất đặc trưng (Librosa)
       MFCC, F0, Jitter, Shimmer
              │
               └─────────────┬──────────────┘
                            ▼
                 [5] Phân tích NLP (Gemini)
                     Chuyển âm thanh thành văn bản
                     Phân tích cảm xúc theo khía cạnh
                            │
                            ▼
                 [6] Xử lý Kết quả (Fusion cơ bản)
                     Chỉ kết hợp văn bản và điểm đặc trưng âm thanh phụ (Roadmap: Multimodal thực thụ)
                     -> sentiment_score
                            │
                            ▼
                 [7] Tính RFMS và Xác suất Churn
                     -> P_churn
                            │
                            ▼
              ┌─────────────────────────────────┐
              │ [8] Lưu Firestore đa khách hàng  │
              └──────────────┬──────────────────┘
                             │
              ┌──────────────┴─────────────────────────────────┐
              │  Nếu cần thiết -> Ghi nhận log cảnh báo         │
              └──────────────┬─────────────────────────────────┘
                             ▼
              Response 202 Accepted
```

*Lưu ý: Zalo ZNS và các tích hợp review tự động hiện tại đang nằm trong định hướng (roadmap), mã code hiện tại chỉ thực hiện ghi log cấu hình giả lập.*

---

## 📁 Cấu trúc thư mục

```
backend/
├── api/
│   ├── main.py                        - Khởi tạo FastAPI app
│   ├── routes/
│   │   ├── health.py                  - Endpoint kiểm tra
│   │   └── feedback.py                - Endpoint chính xử lý pipeline
│   └── middleware/
│       └── fraud_filter.py            - Các bộ lọc sơ bộ
│
├── ai_pipeline/
│   ├── stt_whisper.py                 - STT sử dụng API Whisper
│   ├── audio_features_librosa.py      - Tính toán đặc trưng Librosa
│   ├── absa_llm.py                    - Khởi tạo Gemini Flash-Lite ABSA
│   └── fusion.py                      - Gộp đặc trưng đa phương thức
│
├── rfms_model/
│   ├── rfms_calculator.py             - Cập nhật chỉ số RFMS
│   └── churn_model.py                 - Thuật toán cảnh báo sớm
│
├── db/
│   ├── firestore_client.py            - Khởi tạo Firebase Admin
│   └── firestore_ops.py               - Các thao tác DB
│
├── webhooks/
│   └── zalo_zns.py                    - Hook webhook (tính năng roadmap)
│
├── tests/
│   ├── test_health.py                 
│   ├── test_audio_features.py         
│   ├── test_absa_fusion.py            
│   ├── test_rfms_churn.py             
│   ├── test_firestore_integration.py  
│   └── test_zalo_zns.py               
│
├── requirements.txt                   - Dependencies
```

---

## 🚀 Cài đặt và chạy local

### Cài đặt môi trường

```bash
git clone https://github.com/VietGamer-UIT/Sentrix.git
cd Sentrix

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

pip install -r backend/requirements.txt
```

*Nếu gặp lỗi `librosa` trên Windows, chạy thêm `pip install soundfile`.*

### Cấu hình biến môi trường

```bash
cp .env.example .env
```
Cập nhật `.env` với các khóa API thực tế. Xem mục Biến môi trường.

### Chạy server

```bash
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🔐 Biến môi trường

| Biến | Chức năng |
|------|-----------|
| `WHISPER_API_KEY` | API key Groq Whisper |
| `GEMINI_API_KEY` | API key Google Gemini |
| `FIREBASE_CREDENTIALS_PATH` | File JSON service account Firestore |
| `FIREBASE_PROJECT_ID` | Firestore Config (dùng nếu không có file JSON) |
| `FIREBASE_PRIVATE_KEY` | Firestore Config (dùng nếu không có file JSON) |
| `FIREBASE_CLIENT_EMAIL` | Firestore Config (dùng nếu không có file JSON) |
| `ZALO_ACCESS_TOKEN` | (Roadmap) Dành cho module Zalo |
| `ZALO_TEMPLATE_ID` | (Roadmap) Dành cho module Zalo |

---

## 📡 API Endpoints

### `GET /health`
Kiểm tra trạng thái hệ thống.

### `POST /api/v1/feedback`
Endpoint chính để nhận thông tin từ Web Client.
* Bắt buộc có dữ liệu `tenant_id`, `location` và tối thiểu 1 trường `audio_file` hoặc `text_content`.
* Cung cấp kết quả phản hồi 202 Accepted nhanh chóng.

---

## ✅ Tiến trình phát triển

Hầu hết các logic tích hợp AI (STT, ABSA, Fusion) và ghi nhận Firestore cơ bản (MVP) đã hoàn thành và sẵn sàng cho giai đoạn Pilot.
Một số cải tiến về hiệu suất hệ thống như xử lý message queue đang nằm trong kế hoạch.

---

## 🧪 Chạy tests

```bash
pytest backend/tests/ -v
```
Hệ thống bao gồm các bài test tính năng đảm bảo quá trình xử lý Audio, Text, RFMS và Firestore kết nối ổn định.
