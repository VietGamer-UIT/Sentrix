# 🧠 LÃNH ĐỊA BACKEND & AI PIPELINE
**Người cai quản:** Nguyễn Thanh Tuyền (AI & Data Architect)

## 📌 QUY TẮC CỦA LÃNH ĐỊA NÀY
1. **Chỉ Tuyền mới được sửa code ở đây.** Mọi logic xử lý, database, AI đều nằm gọn trong này. Việt và Tuấn tuyệt đối không chạm vào thư mục này để tránh lỗi môi trường Python.
2. Mọi API khi viết xong PHẢI có tài liệu (Swagger/Postman) để Việt có thể gọi được từ Frontend. Viết API xong mà Việt không biết gọi thế nào thì coi như chưa làm.
3. Code AI (Whisper, Librosa) phải bọc trong các hàm (function) gọn gàng, không vứt bừa bãi ngoài script.

## 🎯 NHIỆM VỤ CỦA TUYỀN
Hệ thống não bộ của Sentrix:
- `api/`: Các endpoint FastAPI cho Frontend gọi tới.
- `ai_pipeline/`: Chứa code gọi Whisper (STT) và Gemini (ABSA), trích xuất đặc trưng Librosa.
- `rfms_model/`: Mô hình thuật toán tính toán điểm rời bỏ (Churn).
- `db/`: Các file cấu hình kết nối Firebase Firestore.

## 📝 CHECKLIST CÔNG VIỆC BẮT ĐẦU CỦA TUYỀN
- [ ] 1. Khởi tạo môi trường ảo `venv` trong thư mục `backend/` và tạo file `requirements.txt`.
- [ ] 2. Trong `api/`, viết một cái API FastAPI cơ bản (`GET /`) trả về `{"message": "Backend Sentrix Is Running!"}`.
- [ ] 3. Tạo Firebase Project, lấy file credentials JSON bỏ vào đây (Nhớ thêm vào `.gitignore` để không bị lộ lên mạng).
- [ ] 4. Gửi link API hoặc Swagger UI vào Zalo để Việt xem thử.
