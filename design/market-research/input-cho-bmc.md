# Bước 2.5: Input cho Business Model Canvas (BMC)

Từ các phân tích về đối thủ cạnh tranh, mô hình tài chính và kết quả dự kiến từ khảo sát, dưới đây là bộ thông số tổng hợp làm đầu vào cốt lõi cho Business Model Canvas (BMC) của Sentrix.

## 1. Thông số Tài chính & Thị trường

- **Phân khúc khách hàng (Customer Segments):** 
  - Trọng tâm ban đầu: Doanh nghiệp SME (quán cà phê, tiệm ăn) tại khu vực Làng Đại học Quốc gia TP.HCM.
  - Mở rộng: Spa, Nha khoa, Phòng khám quy mô nhỏ đến chuỗi vừa (5-15 chi nhánh).
- **Dòng doanh thu (Revenue Streams):**
  - Gói Starter: 99.000 VNĐ/tháng (Sản phẩm "chim mồi", không AI voice) (Nguồn: Báo cáo Thuyết minh dự án AISC'26).
  - Gói Pro (Chủ lực): 299.000 VNĐ/tháng (Trải nghiệm AI toàn diện) (Nguồn: Báo cáo Thuyết minh dự án AISC'26).
  - Gói Enterprise: 1.000.000 - 2.000.000 VNĐ/tháng (Theo thỏa thuận) (Nguồn: Báo cáo Thuyết minh dự án AISC'26).
- **Cấu trúc chi phí (Cost Structure):**
  - Chi phí biến đổi (API Whisper, Gemini, ZNS...): Ước tính ~33.125 VNĐ/khách hàng/tháng (Dữ liệu giả định).
  - Chi phí cố định: Ước tính 15.000.000 VNĐ/tháng (*Chưa xác minh được, cần nhóm tự khảo sát thêm*).
- **Chỉ số sinh lời:** Biên lợi nhuận gộp dự kiến đạt khoảng **88,9%** đối với gói Pro (Dữ liệu giả định). Điểm hòa vốn kỳ vọng ở mức ~57 khách hàng SME.
- **Giải pháp giá trị (Value Propositions):** Thu thập voice-first 15s kết hợp "Vòng quay may mắn" tăng tỷ lệ phản hồi; Phân tích cảm xúc ABSA bóc tách nguyên nhân gốc rễ; Tự động hóa gửi voucher Zalo ZNS để ngăn chặn tỷ lệ rời bỏ (Churn Rate).

## 2. Định hướng phát triển B2C dài hạn (Mở rộng hệ sinh thái)

Bên cạnh mô hình B2B SaaS hiện tại, hệ sinh thái Sentrix sẽ được mở rộng thêm một lớp dịch vụ mới nhằm tăng độ kết dính và giá trị của dữ liệu.

### 2.1. Xây dựng Mobile App (Tích điểm đa thương hiệu)
Thay vì khách hàng chỉ quét QR và để lại phản hồi dạng ẩn danh hoặc web app một lần, Sentrix sẽ đề xuất xây dựng ứng dụng di động Mobile App dành cho người tiêu dùng (End-users).
- **Cơ chế hoạt động:** Khách hàng đăng nhập app Sentrix để quét mã tại bất kỳ cửa hàng nào thuộc mạng lưới đối tác của Sentrix.
- **Tích điểm - Đổi voucher:** Mỗi lượt phản hồi hợp lệ sẽ được cộng điểm thưởng. Người dùng có thể tích điểm và đổi lấy voucher của các thương hiệu khác nhau trong cùng mạng lưới.

### 2.2. Hình thành mô hình "Loyalty-as-a-Service"
- Sentrix sẽ đóng vai trò trung gian, tạo ra một mạng lưới ưu đãi liên kết đa thương hiệu (Cross-brand loyalty network).
- Sentrix sẽ trích một phần nhỏ doanh thu/lợi nhuận B2B để mua lại voucher từ chính các đối tác quán ăn, Spa, tạo kho quà tặng hấp dẫn nhằm duy trì động lực cho người dùng B2C.
- **Lợi ích chiến lược:** 
  - Khuyến khích phản hồi trung thực và thường xuyên hơn từ người dùng B2C.
  - Xây dựng được tập dữ liệu định danh bền vững và chất lượng cao (thay vì dữ liệu zero-party rời rạc), qua đó nâng cao chất lượng báo cáo hành vi khách hàng cho các chủ doanh nghiệp B2B.

> **Kỷ luật dữ liệu:** Các con số về chi phí API và ngưỡng điểm hòa vốn mang tính chất giả định tại thời điểm lập kế hoạch dựa trên giá niêm yết hiện hành của các đối tác công nghệ. Các chi phí ẩn khác về hạ tầng, vận hành cần nhóm tiếp tục tự khảo sát thêm để hoàn thiện BMC chuẩn xác nhất.
