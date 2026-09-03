# Sentrix Documentation Traceability Matrix

| Requirement | Thuyết minh FINAL | Markdown | Code evidence | Status |
| ----------- | ----------------- | -------- | ------------- | ------ |
| **Product Flow** | QR -> Voice/Text -> STT -> NLP -> action -> dashboard | Mô tả chính xác trong `README.md`, `docs/backend-api.md`, `docs/user-flow.md` | `backend/api/routes/feedback.py` (pipeline các bước từ nhận request đến trả về 202) | PASS |
| **Voice Processing** | Voice -> STT -> transcript -> NLP (chưa có multimodal model thực sự) | `README.md` và `docs/SENTRIX_CURRENT_SYSTEM_MAP.md` ghi nhận luồng STT -> Text -> NLP, ghi rõ multimodal là roadmap. | `backend/ai_pipeline/stt_whisper.py` và `backend/api/routes/feedback.py` | PASS |
| **Support Request** | "Tôi cần một ly trà đá" -> support request -> alert | Có trong `README.md`, `docs/SENTRIX_CURRENT_SYSTEM_MAP.md` (Action-oriented) | `backend/api/routes/feedback.py` (phân loại `SUPPORT_REQUEST` bằng `classify_intent`) | PASS |
| **ABSA Aspects** | food, staff, space, price, service speed, hygiene, others | Đã liệt kê trong `docs/api-contract.md`, `docs/database-schema.md` | `docs/api-contract.md` (Aspect categories) và cấu hình prompt LLM | PASS |
| **Anti-fraud** | 4 lớp: tần suất, chất lượng âm thanh, ngữ nghĩa, ngân sách | Mô tả rõ ràng 4 lớp trong `README.md`, `docs/SENTRIX_CURRENT_SYSTEM_MAP.md` | `backend/api/middleware/fraud_filter.py`, các validation checks trong `feedback.py` | PASS |
| **Privacy / Data** | Xóa audio sau STT, hash SĐT, consent window | `README.md` ghi chú bảo mật theo NĐ 356, `docs/database-schema.md` mô tả hash. | `backend/api/routes/feedback.py` có hàm dọn dẹp file tạm, schema lưu masked phone. | PASS |
| **Technology** | React, Web Audio API, FastAPI, Groq Whisper, Gemini, Firestore, Vercel, Render | `README.md`, `docs/SENTRIX_CURRENT_SYSTEM_MAP.md` và `docs/backend-api.md` liệt kê chính xác các tech này. | `requirements.txt`, `render.yaml`, `backend/ai_pipeline/` imports | PASS |
| **RFMS** | Mô hình thử nghiệm, hệ số giả định, huấn luyện lại là lộ trình tương lai (roadmap) | `README.md` (Roadmap), `docs/rfms-model.md` | `backend/rfms_model/churn_model.py` (sử dụng hệ số tĩnh) | PASS |
| **Zalo ZNS** | Định hướng thương mại hóa (roadmap) | Đưa vào Roadmap trong `README.md`, `docs/SENTRIX_CURRENT_SYSTEM_MAP.md` | Chỉ có webhook/log giả lập, tính năng thực sự bị comment out hoặc bypass trong code | PASS |
| **Review Invitation** | Phân luồng đánh giá tốt ra ngoài, đánh giá xấu giữ lại, nằm trong thử nghiệm | Thêm vào Roadmap và luồng cơ bản trong `README.md`, `docs/SENTRIX_CURRENT_SYSTEM_MAP.md` | Backend trả kết quả, frontend có thể hiện (nhưng automation tích hợp API maps chưa có) | PASS |
| **Business Content** | Tập trung Làng Đại học, pilot kiểm chứng, chưa tính tiền ngay | Mô tả trong `README.md` | Cấu hình mặc định (fallback data) | PASS |

