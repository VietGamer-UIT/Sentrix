# Phân tích luồng trải nghiệm khách hàng (User Flow)

Đây là tài liệu mô tả chi tiết toàn bộ luồng thao tác của khách hàng cuối (Customer Journey) khi sử dụng Sentrix để phản hồi dịch vụ tại các quán ăn, quán cà phê (Ưu tiên Pilot tại Làng Đại học). Lĩnh vực Spa / Nha khoa / Phòng khám thuộc định hướng mở rộng tương lai. Mục tiêu là tối giản thao tác tối đa để giảm ma sát.

## Các bước trong luồng trải nghiệm

### Bước 0: Tiếp cận (Touchpoint)
- **Hành động:** Khách hàng ngồi vào bàn hoặc đang thanh toán tại quầy, nhìn thấy mã QR được in trên standee bàn hoặc trên hóa đơn.
- **Trạng thái cảm xúc:** Thoải mái, có thể đang chờ món hoặc chuẩn bị rời đi. 
- **Rủi ro (Drop-off risk):** QR không nổi bật, không có "Call to Action" (lời kêu gọi) đủ hấp dẫn để khách hàng tò mò quét.
- **Giải pháp tối ưu UX:** Cần thiết kế mã QR đi kèm thông điệp kích thích (Ví dụ: "Đánh giá ngay, nhận voucher liền tay!").

### Bước 1: Quét QR & Truy cập Web-client
- **Hành động:** Khách dùng camera điện thoại hoặc Zalo quét mã QR. Trình duyệt tự động mở trang web-client của Sentrix.
- **Trạng thái cảm xúc:** Chờ đợi.
- **Rủi ro (Drop-off risk):** Thời gian tải trang lâu, yêu cầu tải app, hoặc bắt buộc đăng nhập (Zalo/Google).
- **Giải pháp tối ưu UX:** Không yêu cầu tải app, không đăng nhập. Trang web phải load cực nhanh (dưới 2 giây). Giao diện tối giản.

### Bước 2: Màn hình chào (Landing Page)
- **Hành động:** Khách thấy tên quán, lời chào ngắn gọn, các biểu tượng đánh giá nhanh (emoji/sao) và một nút Ghi âm cực kỳ nổi bật ở trung tâm.
- **Trạng thái cảm xúc:** Tò mò, xem có dễ dùng không.
- **Rủi ro (Drop-off risk):** Quá nhiều nút bấm hoặc chữ, giao diện phức tạp khiến khách ngại đọc.
- **Giải pháp tối ưu UX:** Single primary action - Chỉ một hành động chính (Nút Ghi âm lớn). Nút gõ văn bản thiết kế nhỏ hơn (secondary action) dành cho người không tiện nói.

### Bước 3: Thu thập phản hồi (Ghi âm / Gõ Text)
- **Hành động:** Khách bấm giữ nút ghi âm và nói (tối đa 15s) hoặc gõ văn bản. Màn hình hiện hiệu ứng sóng âm và đồng hồ đếm ngược trực quan.
- **Trạng thái cảm xúc:** Đang tập trung diễn đạt ý kiến.
- **Rủi ro (Drop-off risk):** Khách không biết mic có đang thu âm hay không, hoặc thời gian ghi âm quá dài khiến họ ngập ngừng.
- **Giải pháp tối ưu UX:** Hiệu ứng visual (sóng âm) phản hồi tức thời theo giọng nói. Giới hạn 15 giây để khách nói ngắn gọn, đi thẳng vào vấn đề.

### Bước 4: Xác nhận gửi thành công
- **Hành động:** Sau khi nhả nút hoặc hết 15s, hệ thống tự động gửi phản hồi. Màn hình hiện thông báo cảm ơn với hiệu ứng mượt mà.
- **Trạng thái cảm xúc:** Hài lòng vì đã hoàn thành đóng góp ý kiến.
- **Rủi ro (Drop-off risk):** Hiệu ứng loading quay đều chậm chạp khiến khách tưởng lỗi mạng và đóng tab.
- **Giải pháp tối ưu UX:** Xử lý bất đồng bộ (gửi ngầm), hiển thị ngay màn hình thành công (optimistic UI) không cần chờ server phân tích xong.

### Bước 5: Gamification (Vòng quay may mắn)
- **Hành động:** Ngay sau lời cảm ơn, một mini-game "Vòng quay may mắn" xuất hiện, mời khách hàng nhập số điện thoại để quay thưởng.
- **Trạng thái cảm xúc:** Hào hứng, mong đợi phần thưởng (động lực chính để để lại SĐT).
- **Rủi ro (Drop-off risk):** Khách ngại lộ thông tin cá nhân hoặc quy trình quay thưởng rườm rà.
- **Giải pháp tối ưu UX:** Giải thích rõ SĐT chỉ dùng để định danh nhận phần thưởng. Chỉ 1 ô nhập SĐT và 1 nút "Quay ngay".

### Bước 6: Kết quả & Nhận Voucher
- **Hành động:** Vòng quay dừng lại ở phần thưởng (nếu khách đủ điều kiện hợp lệ). Màn hình hiển thị mã voucher kèm hướng dẫn sử dụng.
- **Trạng thái cảm xúc:** Vui vẻ, có khả năng quay lại quán lần sau để dùng voucher.
- **Rủi ro (Drop-off risk):** Không biết cách nhận hay cách dùng voucher.
- **Giải pháp tối ưu UX:** Hiển thị rõ ràng mã voucher trên màn hình (để khách có thể chụp ảnh màn hình lưu lại). Gửi tự động qua Zalo ZNS là định hướng tích hợp tương lai (phụ thuộc tích hợp thực tế).
