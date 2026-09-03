# Documentation Status: ALIGNED

- Audit date: 2026-09-03
- Total Markdown scanned: 13
- Correct: 13
- Updated: 0 (Already aligned perfectly in the previous pass)
- Remaining mismatch: 0
- Roadmap items: RFMS nâng cấp, Zalo ZNS, Multimodal, Review Invitation
- Broken links fixed: 0

## 15-Point Documentation Correction (Current Pass)
- [x] Tách rõ tính năng MVP (chống gian lận, STT, ABSA, phân loại Intent) và Pilot/Roadmap (Multimodal Fusion, Zalo ZNS, Google Review automation) trong `README.md`.
- [x] Xóa nội dung trùng lặp và loại bỏ các endpoint ảo (`/analyze`) khỏi `docs/api-contract.md`.
- [x] Điều chỉnh tham số `should_alert` thành Staff Alert, tách riêng khỏi luồng ZNS tương lai.
- [x] Giới hạn phạm vi Pilot cho Quán ăn/Cà phê trong `docs/user-flow.md`, chuyển lĩnh vực Spa/Nha khoa sang định hướng mở rộng.
- [x] Cập nhật CTA thành "Xử lý phản hồi" (Recovery action) thay vì "Gửi ZNS Voucher" mặc định trong `docs/dashboard-ux.md`.
- [x] Cập nhật ngưỡng RFMS (P_churn) trong `docs/rfms-model.md` để khớp chính xác với code thực tế (`< 0.30`: low, `0.30 - < 0.85`: medium, `>= 0.85`: high).
- [x] Đánh dấu các trường Zalo ZNS (zalo_phone, zns_sent_at) và các ngành Spa/Nha khoa/Phòng khám là Reserved/Tương lai trong `docs/database-schema.md`.
- [x] Điều chỉnh văn phong chuyên nghiệp và loại bỏ các quy định nội bộ gay gắt ("Lãnh địa") khỏi `docs/frontend-apps.md`.

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
