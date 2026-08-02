# Đề xuất UX cho Dashboard Chủ Quán (Tham khảo cho Frontend)

Tài liệu này ghi chú các đề xuất về mặt trải nghiệm người dùng (UX) dành cho Dashboard của chủ quán/quản lý. Việt (Frontend) tham khảo để tối ưu giao diện React nhé.

## 1. Ưu tiên hiển thị (Above the Fold)
Chủ quán F&B/Spa thường rất bận rộn, họ cần thấy ngay "sức khỏe" của quán trong 3 giây đầu tiên. Do đó, phần trên cùng của Dashboard cần hiển thị to, rõ 4 KPI cốt lõi sau:

- **Tổng phản hồi:** Tổng số lượt feedback (âm thanh + văn bản) nhận được trong ngày/tuần. (Kèm % tăng giảm so với kỳ trước).
- **Điểm Sentiment (Cảm xúc):** Điểm trung bình (ví dụ 4.2/5 hoặc 85%) dựa trên phân tích AI (ABSA). Dùng màu sắc trực quan (Xanh lá = Tốt, Vàng = Bình thường, Đỏ = Tệ).
- **Tỷ lệ Churn (Rời bỏ) theo RFMS:** Tỷ lệ khách hàng có nguy cơ không quay lại dựa trên mô hình RFMS. Con số này cần làm nổi bật (nếu cao) để báo động.
- **Tỷ lệ dùng Voucher:** Tỷ lệ chuyển đổi từ việc khách nhận voucher (qua Gamification/Zalo ZNS) đến lúc mang tới quán sử dụng.

## 2. Actionable Insights (Thông tin có thể hành động ngay)
Dashboard không chỉ để xem số liệu mà phải giúp chủ quán xử lý vấn đề ngay lập tức.

- **Top 5 phản hồi tiêu cực cần xử lý gấp:** Thay vì hiển thị danh sách tất cả phản hồi xen kẽ, hãy tách riêng một khu vực (hoặc widget) hiển thị 5 đánh giá tiêu cực nhất (Sentiment score thấp nhất) hoặc có cảnh báo rủi ro (Churn risk) cao nhất trong ngày.
- **Nút "Gửi ZNS Voucher":** Bên cạnh mỗi phản hồi tiêu cực này, CẦN CÓ một nút Call-to-Action (ví dụ: "Xin lỗi & Gửi ZNS Voucher"). Khi bấm vào, hệ thống tự động gọi API gửi tin nhắn Zalo ZNS kèm voucher để xoa dịu khách hàng ngay lập tức. Điều này mang lại giá trị cốt lõi của Sentrix (chăm sóc khách hàng tự động).

## 3. Lưu ý chung về UI
- Dùng biểu đồ đơn giản (Line chart cho xu hướng, Donut chart cho phân loại cảm xúc theo khía cạnh như Không gian, Đồ ăn, Phục vụ).
- Tránh dùng các bảng biểu (table) quá nhiều cột.
- Font chữ to, màu sắc tương phản cao vì chủ quán có thể xem qua tablet hoặc màn hình máy POS.
