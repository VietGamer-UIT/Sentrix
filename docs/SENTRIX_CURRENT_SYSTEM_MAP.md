# SENTRIX - CURRENT SYSTEM MAP
Generated: 2026-09-03 | Phase: DEMO / MVP / PILOT-READY
Source: Code scan thực tế, không giả định

## WORKING FEATURES (Cập nhật từ Codebase hiện tại)
- **Đa phương thức đầu vào:** Khách hàng quét QR để gửi phản hồi qua Voice hoặc Text (không cần cài app).
- **Luồng xử lý Voice:** Voice -> Whisper STT (Groq) -> NLP Analysis -> Firestore.
- **Phân tích NLP:** Sử dụng Gemini Flash-Lite để thực hiện ABSA (phân tích cảm xúc theo khía cạnh: món ăn, nhân viên, không gian, tốc độ phục vụ...).
- **Action-oriented (Hướng hành động):** Nhận diện yêu cầu hỗ trợ (SUPPORT_REQUEST) từ khách hàng để tạo cảnh báo (alert) ngay cho nhân viên. Phân loại luồng FEEDBACK và INVALID.
- **Chống gian lận 4 lớp:** 
  1. Tần suất (Hash số điện thoại).
  2. Chất lượng dữ liệu (Thời lượng, SNR gate).
  3. Ngữ nghĩa (Semantic Validity qua LLM).
  4. Ngân sách voucher.
- **Bảo mật và quyền riêng tư (Theo NĐ 356/2025/NĐ-CP):** Xóa audio gốc trên server ngay sau khi xử lý STT thành công. Hỗ trợ phản hồi ẩn danh.
- **Gamification:** Cơ chế phát voucher theo ngân sách và vòng quay may mắn (spin) trên Web Client.
- **Dashboard quản trị:** 
  - Giao diện thời gian thực cho chủ quán.
  - Auth qua Firebase Google Sign-In.

## THÔNG TIN CẦN XỬ LÝ (Kế hoạch / Định hướng)
- **Feedback Recovery & Review Invitation:** Luồng phân loại khách tích cực (mời chia sẻ Google Maps) và tiêu cực (giữ lại xử lý nội bộ) đang được thử nghiệm, tích hợp tự động đang nằm trong kế hoạch.
- **Mô hình RFMS + P_churn:** Hiện đang ở mức thử nghiệm với hệ số giả định. Sẽ cập nhật và huấn luyện trên dữ liệu thật sau Pilot.
- **Zalo ZNS Production:** Việc cảnh báo qua Zalo ZNS khi P_churn cao đang nằm trong định hướng thương mại hóa, cần phê duyệt template chính thức.
- **Staff Alert Lifecycle:** Giao diện chi tiết để nhân viên đánh dấu (acknowledge/resolve) các alert trên Dashboard cần được hoàn thiện thêm.
