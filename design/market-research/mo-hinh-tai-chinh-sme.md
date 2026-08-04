# Bước 2.3: Mô hình tài chính cho Doanh nghiệp SME

> **Lưu ý quan trọng:** Tất cả các số liệu về tỷ lệ chuyển đổi, chi phí biến đổi và chi phí cố định dưới đây là số liệu giả định nhằm mục đích lập mô hình. Các thông số này sẽ được hiệu chỉnh lại sau khi chạy pilot thực tế.

## 1. Ước tính chi phí API (Cost of Goods Sold - COGS)

Các chi phí cốt lõi để vận hành hệ thống AI cho mỗi lượt phản hồi dựa trên bảng giá tham khảo:
- **Whisper API (OpenAI):** ~0.006 USD/phút (Nguồn: Bảng giá chính thức của OpenAI - *Chưa xác minh được mức chiết khấu cho đối tác, cần nhóm tự khảo sát thêm*).
- **Gemini 3.1 Flash-Lite (Google):** ~0.25 USD/1 triệu token đầu vào (Nguồn: Báo cáo Thuyết minh dự án AISC'26, trích dẫn Curlscape cập nhật 12/7/2026).
- **Zalo ZNS:** ~200 VNĐ/tin nhắn (Nguồn: Bảng giá Zalo Cloud hiện hành - *Chưa xác minh được chiết khấu theo sản lượng, cần nhóm tự khảo sát thêm*).

**Giả định sử dụng cho 1 khách hàng F&B (quy mô SME) trong 1 tháng:**
- Số lượt phản hồi thu được: 500 lượt/tháng.
- Thời lượng ghi âm trung bình: 10 giây/lượt ➔ Tổng = 5,000 giây (~83.3 phút).
- Số lượng token văn bản cần xử lý (Prompt + Text) trung bình: 200 token/lượt ➔ Tổng = 100,000 token.
- Tỷ lệ kích hoạt ZNS (Khách hàng không hài lòng): 10% ➔ 50 tin nhắn ZNS/tháng.

**Bảng tính chi phí trên mỗi khách hàng/tháng:**
- **Whisper API:** 83.3 phút × 0.006 USD ≈ 0.5 USD (~12.500 VNĐ).
- **Gemini API:** (100,000 / 1,000,000) × 0.25 USD = 0.025 USD (~625 VNĐ).
- **Zalo ZNS:** 50 tin nhắn × 200 VNĐ = 10.000 VNĐ.
- **Chi phí khác (Hosting Vercel/Render, Firestore):** Cơ bản miễn phí hoặc ở mức rất thấp (Spark Plan), ước tính quy đổi khấu hao ~10.000 VNĐ/tháng (*Chưa xác minh được, cần nhóm tự khảo sát thêm*).
➔ **Tổng chi phí trực tiếp (COGS) ước tính:** ~33.125 VNĐ/tháng.

## 2. Bảng so sánh doanh thu và biên lợi nhuận gộp

Cơ cấu gói cước dự kiến (Nguồn: Đề xuất trong Báo cáo Thuyết minh dự án AISC'26):
- **Gói Pro:** 299.000 VNĐ/tháng (Áp dụng cho đơn lẻ SME như quán cà phê, tiệm ăn, Spa vừa và nhỏ).
- **Gói Enterprise:** 1.000.000 - 2.000.000 VNĐ/tháng (Áp dụng cho chuỗi 5-15 chi nhánh).

**Tính toán Biên lợi nhuận gộp (Gross Margin) đối với Gói Pro:**
- **Doanh thu:** 299.000 VNĐ.
- **Chi phí (COGS):** ~33.125 VNĐ.
- **Lợi nhuận gộp:** 265.875 VNĐ.
- **Biên lợi nhuận gộp (Gross Margin):** (265.875 / 299.000) × 100% ≈ **88,9%**.

## 3. Phân tích điểm hòa vốn (Break-even Point)

- **Chi phí cố định (Fixed Costs) giả định:** Bao gồm chi phí vận hành nền tảng lõi, máy chủ, marketing và nhân sự quản trị. Giả định ở mức: 15.000.000 VNĐ/tháng (*Chưa xác minh được chi tiết các khoản mục, cần nhóm tự khảo sát thêm*).
- **Lợi nhuận gộp trên mỗi khách hàng (Gói Pro):** 265.875 VNĐ.
- **Điểm hòa vốn (Số lượng khách hàng cần đạt):** 15.000.000 / 265.875 ≈ **57 khách hàng**.

*(Như vậy, mô hình kinh doanh có thể duy trì vận hành ổn định và hòa vốn dòng tiền chỉ với khoảng 57 cửa hàng đăng ký sử dụng Gói Pro).*
