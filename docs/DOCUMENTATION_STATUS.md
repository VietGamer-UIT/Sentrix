# Documentation Status

- Audit date: 2026-09-03
- Total Markdown scanned: 13
- Correct: 13
- Updated: 0 (Already aligned perfectly in the previous pass)
- Remaining mismatch: 0
- Roadmap items: RFMS nâng cấp, Zalo ZNS, Tích hợp đánh giá tự động (Review Invitation)
- Broken links fixed: 0

## Major documentation corrections (Previous Pass)
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
