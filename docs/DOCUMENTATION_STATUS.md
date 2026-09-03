# Documentation Status

- Last updated: 2026-09-03
- Files updated: 7 (README.md, backend/README.md, backend/ai_pipeline/README.md, backend/rfms_model/README.md, backend/db/schema.md, apps/README.md, docs/SENTRIX_CURRENT_SYSTEM_MAP.md)
- Files intentionally unchanged: Còn lại (chủ yếu là các file nháp, thiết kế không chứa claim sai lệch với sản phẩm).

## Major documentation corrections
- Làm rõ tính năng "Action-oriented" nhận diện intent và tạo alert cho nhân viên.
- Thêm cơ chế "Feedback Recovery & Review Invitation" vào đúng luồng tính năng.
- Đồng nhất các lớp bảo vệ "Anti-fraud 4 lớp" (tần suất, thời lượng/SNR, ngữ nghĩa LLM, ngân sách voucher).
- Ghi rõ mô hình RFMS hiện tại là thử nghiệm (Pilot) với hệ số giả định.
- Chuyển tính năng Zalo ZNS vào phần định hướng/roadmap.
- Chuẩn hóa toàn bộ dấu "-" và loại bỏ cách viết cường điệu AI thay thế nhân viên.

## Current MVP scope
- Phương thức đầu vào: Voice và Text qua mã QR.
- STT: Groq Whisper.
- NLP/ABSA: Gemini Flash-Lite.
- Intent Classification: Nhận diện SUPPORT_REQUEST, FEEDBACK, INVALID.
- Dashboard: Cảnh báo realtime cho cửa hàng qua Firestore.

## Current known limitations
- Chưa tích hợp hệ thống POS nên `total_spending` chưa tự động.
- Chưa xử lý bằng Message Queue/Microservices mà chạy trực tiếp trong backend API.
- Cần làm mới Zalo ZNS Token thủ công.
