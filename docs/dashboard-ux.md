# Đề xuất UX cho Dashboard Chủ Quán (Dựa trên Mockup)

Tài liệu này đề xuất cách chuyển đổi layout từ template mẫu (DashStack) sang Dashboard thực tế phục vụ cho Sentrix. Trọng tâm là giúp chủ quán nắm bắt ngay lập tức sức khỏe dịch vụ và có hành động can thiệp kịp thời.

## 1. Khu vực Tổng quan (Thay thế biểu đồ Revenue lớn phía trên)
Trong ảnh mockup, phần trên cùng đang là một biểu đồ vùng (Area Chart) rất lớn chiếm nhiều diện tích. Đối với Sentrix, chủ quán cần nhìn thấy ngay các con số tổng quát. Đề xuất:
- **Tùy chọn 1:** Thay thế (hoặc thu nhỏ) biểu đồ này để chèn 1 hàng gồm 4 thẻ (Card) hiển thị 4 KPI cốt lõi:
  1. **Tổng phản hồi:** Tổng số lượt quét QR và để lại đánh giá.
  2. **Điểm Sentiment:** Điểm trung bình AI chấm (vd: 85% Tích cực).
  3. **Tỷ lệ Churn theo RFMS:** Tỷ lệ khách hàng có rủi ro rời bỏ.
  4. **Tỷ lệ dùng Voucher:** Tỷ lệ khách quay lại dùng voucher đã phát qua Zalo.
- **Tùy chọn 2:** Nếu giữ nguyên biểu đồ lớn, hãy dùng nó để vẽ đường xu hướng kép (Dual Line/Area Chart) so sánh **Số lượng phản hồi** và **Điểm Sentiment trung bình** theo từng ngày trong tháng.

## 2. Khu vực Chi tiết & Hành động (Thay thế 3 widget bên dưới)
Trong ảnh có 3 widget: Customers (Donut chart), Featured Product, và Sales Analytics (Line chart). Ta sẽ map lại như sau:

### Widget 1 (Bên trái - Thay cho Customers Donut Chart)
- **Đề xuất:** Giữ nguyên dạng Donut Chart, nhưng dùng để hiển thị **Cơ cấu Sentiment** (Tỷ lệ % Tích cực - Xanh lá, Trung tính - Vàng, Tiêu cực - Đỏ) HOẶC **Phân loại Churn risk** (Nguy cơ cao, Nguy cơ thấp, Trung thành).
- Điều này giúp chủ quán nhìn một phát là biết tỷ lệ khách đang bất mãn chiếm bao nhiêu phần trăm.

### Widget 2 (Ở giữa - Thay cho Featured Product)
- **Đề xuất:** Xóa bỏ phần hiển thị sản phẩm. Đây sẽ là khu vực quan trọng nhất mang tính chất Actionable (Hành động ngay).
- **Nội dung:** Hiển thị danh sách **"Phản hồi rủi ro cao"** (Top các phản hồi tiêu cực nhất trong ngày, được AI phân tích).
- **UX Hành động:** 
  - Mỗi hàng phản hồi (list item) sẽ hiện tên khách (ẩn một phần), điểm Sentiment, và lý do (vd: "Đồ ăn nguội").
  - **BẮT BUỘC:** Bên cạnh mỗi dòng, đặt một nút bấm nổi bật: **"Xử lý phản hồi"** (Recovery action). 
  - Khi chủ quán click, hệ thống ghi nhận trạng thái xử lý hoặc cấp mã voucher. (Tích hợp gửi tự động qua Zalo ZNS là định hướng mở rộng tương lai).

### Widget 3 (Bên phải - Thay cho Sales Analytics Line Chart)
- **Đề xuất:** Sử dụng biểu đồ đường (Line chart) này để theo dõi **Tỷ lệ dùng Voucher** qua thời gian. 
- Hoặc dùng để đối chiếu tỷ lệ Churn qua các tháng, qua đó đánh giá xem sau khi dùng Sentrix để xử lý phản hồi/cấp voucher, tỷ lệ khách quay lại có tăng lên (đường đồ thị đi lên) hay không.

## 3. Lưu ý chung về UI
- **Màu sắc:** Thay vì màu tím/cam nhạt của template, hãy đổi màu chart sang dải màu đặc trưng của Sentrix (xanh dương/xanh ngọc) hoặc màu theo ngữ nghĩa (Xanh = Tốt, Đỏ = Xấu).
- **Font chữ:** To rõ, các nút CTA như "Xử lý phản hồi" cần có màu sắc tương phản mạnh để thu hút sự chú ý.
