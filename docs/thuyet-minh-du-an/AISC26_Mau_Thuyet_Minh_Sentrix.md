# TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN
# KHOA HỆ THỐNG THÔNG TIN
# BAN TỔ CHỨC AISC’26
**MẪU CHUẨN**

# THUYẾT MINH DỰ ÁN
## ADVANCED INFORMATION SYSTEMS CONTEST 2026

---

## PHẦN I: THÔNG TIN CHUNG

**1. Tên đội thi:** Sentrix

**2. Chủ đề đăng ký:** Data Driven Business

**3. Thông tin thành viên (Liệt kê đầy đủ thông tin tất cả thành viên nhóm, tối đa 5 thành viên):**

| | Thành viên 1 | Thành viên 2 | Thành viên 3 | Thành viên 4 | Thành viên 5 |
|---|---|---|---|---|---|
| **Họ tên** | Đoàn Hoàng Việt (Trưởng nhóm) | Nguyễn Thanh Tuyền | Nguyễn Quốc Tuấn | | |
| **MSSV** | 25522061 | 25522042 | 25522018 | | |
| **Khoa** | Hệ thống Thông tin | Hệ thống Thông tin | Hệ thống Thông tin | | |
| **Trường** | Đại học Công nghệ Thông tin - ĐHQG TP.HCM | Đại học Công nghệ Thông tin - ĐHQG TP.HCM | Đại học Công nghệ Thông tin - ĐHQG TP.HCM | | |
| **Email** | 25522061@gm.uit.edu.vn | 25522042@gm.uit.edu.vn | 25522018@gm.uit.edu.vn | | |
| **Ngày sinh** | 16/04/2007 | 25/11/2007 | 10/07/2007 | | |

**4. Trưởng nhóm (thông tin từ BTC sẽ gửi đến người này)**
* Họ và tên: Đoàn Hoàng Việt
* Số điện thoại: 0327277624

| Thành viên | Vai trò | Mảng phụ trách chính |
|---|---|---|
| **Đoàn Hoàng Việt** | Trưởng nhóm & Thuyết trình viên | Khởi xướng ý tưởng, Quản trị Mô hình kinh doanh (BMC), Quản lý sản phẩm đầu ra của các thành viên, Phát triển giao diện (Dashboard/Web), Kiểm duyệt Prompt AI và Thuyết trình (Pitching). |
| **Nguyễn Thanh Tuyền** | Kiến trúc sư AI & Dữ liệu | Xây dựng Data Pipeline, Phát triển lõi xử lý âm thanh/ngôn ngữ (ABSA), Thiết kế cơ sở dữ liệu đa khách thuê (Multi-tenant). |
| **Nguyễn Quốc Tuấn** | Kỹ sư Ứng dụng & Nghiên cứu Thị trường | Thiết kế UX/UI, Nghiên cứu tài chính SME, Vận hành hậu cần & Triển khai Demo thực tế. |

---

## PHẦN II: THÔNG TIN DỰ ÁN

**1. Tên dự án (tên đề tài)**

| | |
|---|---|
| **Tên Tiếng Việt** | Sentrix – Nền tảng thu thập và phân tích trải nghiệm khách hàng đa phương thức |
| **Tên Tiếng Anh** | Sentrix – AI-Powered Multimodal Customer Experience Analytics Platform |

**Lĩnh vực:** Thương mại dịch vụ – khởi điểm ngành F&B (ẩm thực & đồ uống), mở rộng sang Spa, Nha khoa, Phòng khám (Clinic).

**2. Bối cảnh và bài toán**

**a. Bối cảnh:**
Thị trường dịch vụ thương mại tại Việt Nam, đặc biệt ngành F&B, đang trải qua giai đoạn tái cấu trúc và thanh lọc chưa từng có. Theo Báo cáo "Thị trường kinh doanh ẩm thực tại Việt Nam năm 2025" do iPOS.vn phối hợp Nestlé Professional công bố (04/2026), năm 2026 toàn thị trường F&B được dự báo đạt quy mô doanh thu khoảng 760.000 tỷ đồng với khoảng 333.600 điểm bán, tăng trưởng ổn định ở mức 4,6% (1); tuy vậy theo báo cáo 6 tháng đầu năm 2025 của cùng đơn vị này, đã có hơn 50.000 cơ sở kinh doanh phải đóng cửa chỉ trong nửa đầu năm 2025 (2). Chi phí nguyên vật liệu và mặt bằng tăng cao buộc doanh nghiệp phải chuyển từ mở rộng quy mô sang phát triển chiều sâu, khai thác giá trị vòng đời khách hàng (CLV); theo thống kê được nhiều tổ chức trích dẫn (gốc từ Bain & Company/Harvard Business Review), chi phí thu hút một khách hàng mới (CAC) có thể cao gấp 5 đến 25 lần chi phí giữ chân một khách hàng hiện hữu, tùy ngành — mốc phổ biến nhất thường được trích dẫn là gấp khoảng 5 lần (3). Đồng thời, thế hệ Gen Z và Millennials ngày càng đề cao trải nghiệm dịch vụ thực chất hơn là tiêu dùng phô trương. Đối với các dịch vụ cận cao cấp như Spa, Nha khoa, Phòng khám, giá trị một khách hàng có thể lên tới hàng chục triệu đồng mỗi năm nên rủi ro mất khách vì trải nghiệm tồi tệ càng nghiêm trọng hơn.

**b. Vấn đề cần giải quyết**

*   **Ai đang gặp vấn đề:** Các doanh nghiệp SME ngành F&B, Spa, Nha khoa, Phòng khám tại Việt Nam.
*   **Vấn đề là gì:** Công cụ khảo sát hiện tại (Google Forms, thang điểm sao) tồn tại 3 rào cản lớn:
    ① UX friction khiến khách hàng ngại phản hồi xuất phát từ các điểm nghẽn chính: biểu mẫu quá dài, yêu cầu đăng nhập rườm rà và thời gian chờ đợi lâu. Những rào cản này làm người dùng mệt mỏi và bỏ dở trước khi hoàn tất ý kiến ("nghịch lý của sự lịch sự" trong văn hoá Á Đông).
    ② Dữ liệu thu được hời hợt, không định hướng hành động (một đánh giá 3 sao không cho biết nguyên nhân gốc rễ).
    ③ Doanh nghiệp thụ động, không dự báo được khách hàng sắp rời bỏ cho đến khi họ đã bóc phốt trên mạng xã hội.
*   **Vì sao cần giải quyết:** Những điểm mù này khiến doanh nghiệp mất doanh thu và danh tiếng một cách âm thầm, trong khi chi phí thay thế một khách hàng mới đắt gấp nhiều lần chi phí giữ chân khách hàng cũ.

**c. Đối tượng hướng đến**
*   **Doanh nghiệp (khách hàng B2B trả phí SaaS):** chủ quán F&B, Spa, Nha khoa, Phòng khám quy mô SME đến chuỗi nhỏ (5–15 chi nhánh).
*   **Người dùng cuối (nguồn dữ liệu):** khách hàng trải nghiệm dịch vụ tại điểm bán, phản hồi qua giọng nói/văn bản.

**3. Mục tiêu của đề tài**

**Mục tiêu tổng quát:** Xây dựng nền tảng SaaS đa phương thức, lấy giọng nói làm trung tâm (Voice-First), ứng dụng AI để thu thập, phân tích cảm xúc và dự đoán hành vi khách hàng nhằm giúp SME tối ưu chi phí thu hút khách hàng, gia tăng tỷ lệ giữ chân và tự động hóa chăm sóc khách hàng.

**Mục tiêu cụ thể:**
*   Xây dựng giao diện thu thập phản hồi một chạm qua QR động, hỗ trợ ghi âm giọng nói tối đa 15 giây (Web Audio API).
*   Phát triển lõi phân tích cảm xúc đa phương thức: kết hợp đặc trưng âm thanh (MFCC, F0, Jitter, Shimmer qua Librosa) với phân tích cảm xúc theo khía cạnh (ABSA) từ văn bản.
*   Xây dựng và huấn luyện mô hình RFMS (Recency – Frequency – Monetary – Sentiment) để tính điểm rủi ro rời bỏ khách hàng (Churn Probability).
*   Tự động hóa quy trình cứu vãn khách hàng qua webhook tích hợp Zalo Notification Service (ZNS).
*   Xây dựng dashboard quản trị thời gian thực cho chủ doanh nghiệp (React + Firestore Listener).

**4. Tính cấp thiết, tính mới, ý tưởng khoa học của dự án** 
Dự án mang tính cấp thiết cao trong bối cảnh ngành dịch vụ Việt Nam đang bị thanh lọc mạnh và SME thiếu công cụ quản trị dữ liệu trải nghiệm khách hàng phù hợp với hành vi và ngôn ngữ người Việt. Sentrix lấy cảm hứng từ hướng nghiên cứu "Emotion recognition in customer service" được công bố tại hội nghị ISBM 2020 (4) thành sản phẩm thực tế, kết hợp cơ chế hợp nhất đa phương thức (Multimodal Fusion) giữa đặc trưng âm thanh và ABSA văn bản để nhận diện chính xác các sắc thái mỉa mai, châm biếm đặc trưng trong giao tiếp tiếng Việt — điều mà các mô hình Speech-to-Text và phân tích văn bản đơn thuần không xử lý được. Việc nâng cấp mô hình RFM cổ điển thành RFMS (bổ sung chiều Sentiment) và mô hình hóa xác suất rời bỏ bằng hồi quy logistic cũng là một đóng góp có tính ứng dụng cao. Về khả năng thương mại hóa, kiến trúc serverless và các dòng LLM chi phí thấp hiện hành (như Gemini 3.1 Flash-Lite với giá chỉ ~0,25 USD/1M token đầu vào) (9) giúp Sentrix có biên lợi nhuận SaaS khả thi ngay từ giai đoạn MVP.

**5. Các giải pháp khác hiện nay để xử lý vấn đề tương tự? Ưu điểm và hạn chế**

| Tính năng cốt lõi | Khảo sát Giấy / Google Forms | Hệ thống 1-5 Sao (Google Maps) | 🦉 Sentrix (Giải pháp của nhóm) |
|---|---|---|---|
| **Trải nghiệm một chạm (Ghi âm)** | ❌ | ❌ | ✅ |
| **Tỷ lệ phản hồi (Gamification)** | Thấp | Trung bình | ✅ **Rất cao** |
| **Phân tích cảm xúc từ Giọng nói** | ❌ | ❌ | ✅ |
| **Bóc tách nguyên nhân gốc rễ** | ❌ | ❌ | ✅ |
| **Dự báo rủi ro rời bỏ (Churn Rate)** | ❌ | ❌ | ✅ |
| **Tự động gửi Voucher cứu vãn** | ❌ | ❌ | ✅ **(Qua Zalo ZNS)** |

**6. Giải pháp đề xuất của nhóm** 
Sentrix đề xuất một pipeline xử lý dữ liệu thời gian thực gồm 4 giai đoạn: 
① Tiếp nhận phản hồi đa phương thức qua QR động và Web Audio API.
② Lõi AI chuyển đổi giọng nói (Whisper API) và bóc tách ngữ nghĩa qua Librosa (đặc trưng âm thanh) kết hợp LLM ABSA (dòng Gemini Flash-Lite/Flash hiện hành). 
③ Lưu trữ đa khách thuê (multi-tenant) an toàn trên Firebase Firestore với Security Rules theo Tenant ID.
④ Hiển thị dashboard thời gian thực và tự động kích hoạt chăm sóc khách hàng qua Zalo ZNS khi phát hiện rủi ro rời bỏ cao (RFMS).

**Ưu điểm:**
*   Giảm rào cản phản hồi bằng cơ chế Gamification ("Vòng quay may mắn") thay vì biểu mẫu nhàm chán, thu thập zero-party data hợp lệ.
*   Phân tích cảm xúc chính xác hơn nhờ hợp nhất tín hiệu âm thanh và văn bản, xử lý được sắc thái mỉa mai trong tiếng Việt.
*   Dữ liệu actionable theo từng khía cạnh dịch vụ (nhân viên, món ăn, không gian…) thay vì điểm số chung chung.
*   Chi phí vận hành thấp nhờ kiến trúc serverless và LLM giá rẻ, phù hợp với SME.
*   Có cơ chế chống gian lận/spam đa lớp để bảo vệ ngân sách marketing.

**Hạn chế:**
*   Phụ thuộc vào các API bên thứ ba (Whisper, Gemini) về chi phí và độ ổn định.
*   Độ chính xác mô hình RFMS cần dữ liệu lịch sử đủ lớn của từng doanh nghiệp để huấn luyện hệ số tối ưu.

**Khả năng mở rộng và thương mại hóa:**
*   Kiến trúc multi-tenant cho phép mở rộng sang nhiều ngành dịch vụ (F&B → Spa → Nha khoa → Clinic) và nhiều chi nhánh (chuỗi).
*   Mô hình định giá phân tầng theo mô hình B2B SaaS (xem bảng bên dưới). Gói Pro (299.000 VNĐ/tháng) là mức giá áp dụng cho phần lớn khách hàng đơn lẻ, bao gồm cả Spa, Nha khoa, Phòng khám quy mô vừa và nhỏ; mức phí cao hơn (1.000.000–2.000.000 VNĐ/tháng, gói Enterprise) chỉ được đặt ra khi tiếp cận các chuỗi nhiều chi nhánh hoặc các thương hiệu/thị trường quy mô lớn, nơi giá trị dữ liệu tổng hợp đa chi nhánh cao hơn hẳn.
*   Về dài hạn, cơ chế thu thập zero-party data bằng số điện thoại có thể nâng cấp thành ứng dụng di động B2C tích hợp đăng nhập Zalo, tích điểm và đổi voucher (xem mục 8 – Định hướng phát triển), mở thêm nguồn doanh thu B2C song song với mô hình B2B SaaS hiện tại.

*Ghi chú: Cấu trúc giá mang tính chất tham khảo dựa trên mặt bằng chung của thị trường SaaS tại Việt Nam. Các mức giá này dự kiến sẽ được hiệu chỉnh tối ưu hóa thông qua dữ liệu thu thập thực tế trong giai đoạn Pilot.*

| Gói | Giá | Nội dung chính |
|---|---|---|
| **Starter** | 99.000 VNĐ/tháng | Chỉ nhập văn bản thuần túy, không AI voice, thống kê tĩnh cơ bản. Sản phẩm "chim mồi" cho quán nhỏ. |
| **Pro** | 299.000 VNĐ/tháng | Kích hoạt toàn bộ AI đa phương thức, ABSA thời gian thực, tính năng "bơm sao Google Maps". Gói chủ lực F&B. |
| **Enterprise (Chuỗi / Thị trường lớn)** | Thương lượng (~1.000.000–2.000.000 VNĐ/tháng) | Áp dụng khi tiếp cận chuỗi 5–15 chi nhánh hoặc thương hiệu/thị trường quy mô lớn — KHÔNG áp dụng đại trà cho Spa/Nha khoa/Phòng khám đơn lẻ (các đơn vị này vẫn dùng gói Pro 299.000 VNĐ/tháng như bình thường): liên kết dữ liệu chéo, báo cáo so sánh KPI, cảnh báo churn RFMS + Zalo ZNS tự động. |

**7. Kết quả dự kiến**
Sau cuộc thi, nhóm dự kiến hoàn thành:
* [x] Prototype
* [x] Website
* [x] Mobile App
* [x] Dashboard
* [x] AI Model
* [x] Hệ thống quản trị
* [ ] Khác

**Mô tả ngắn:** Ứng dụng web thu thập phản hồi (QR + ghi âm một chạm) triển khai trên Vercel; backend FastAPI xử lý pipeline AI (Whisper, Librosa, dòng Gemini Flash-Lite/Flash hiện hành cho ABSA) trên Render.com; cơ sở dữ liệu multi-tenant Firebase Firestore; dashboard quản trị thời gian thực xây dựng bằng React (triển khai trên Vercel) hiển thị KPI nhân sự, cảnh báo rủi ro rời bỏ và tích hợp gửi ưu đãi tự động qua Zalo ZNS. Bản demo/prototype trong khuôn khổ cuộc thi được triển khai thực tế ngay tại thư viện và các tòa nhà trong khuôn viên trường để thu thập phản hồi thật và kiểm chứng dashboard thời gian thực, thay vì thử nghiệm tại các điểm kinh doanh bên ngoài; mô hình kinh doanh hướng đến thị trường F&B/Spa/Nha khoa/Phòng khám bên ngoài vẫn được giữ nguyên trong định hướng phát triển. Mobile App (Android/iOS tích điểm – đổi voucher) là hạng mục quy hoạch cho giai đoạn phát triển tiếp theo sau cuộc thi (xem mục 8).

**8. Định hướng phát triển**
*   **Hoàn thiện sản phẩm:** tối ưu mô hình ABSA tiếng Việt, mở rộng benchmark trên UIT-ViSD4SA và UIT-ABSA Restaurant7 (bộ dữ liệu đúng lĩnh vực nhà hàng).
*   **Thử nghiệm (Pilot):** triển khai bản demo/prototype thực tế ngay tại thư viện và các tòa nhà trong khuôn viên trường để thu thập phản hồi thật, kiểm chứng dashboard thời gian thực trong phạm vi cuộc thi; mô hình kinh doanh hướng ra thị trường bên ngoài (quán cà phê làm việc, nhà hàng khu vực Làng Đại học Quốc gia TP.HCM, sau đó Spa/Nha khoa/Phòng khám) vẫn được giữ nguyên trong kế hoạch go-to-market dài hạn.
*   **Thương mại hóa:** áp dụng gói Pro (299.000 VNĐ/tháng) cho phần lớn khách hàng đơn lẻ, kể cả Spa, Nha khoa, Phòng khám quy mô vừa và nhỏ; chỉ nâng lên gói Enterprise (1.000.000–2.000.000 VNĐ/tháng) khi tiếp cận các chuỗi nhiều chi nhánh hoặc thương hiệu/thị trường quy mô lớn.
*   **Phát triển ứng dụng di động (Android/iOS) cho người dùng cuối:** thay vì phản hồi ẩn danh qua nhập tay số điện thoại, khách hàng đăng nhập bằng tài khoản Zalo hoặc tài khoản Sentrix ngay trên app; hệ thống lưu lại lịch sử quét mã QR tại các điểm bán, tích lũy điểm thưởng theo mỗi lượt phản hồi hợp lệ, và cho phép đổi điểm thành voucher khi đạt mốc tích lũy.
*   **Xây dựng mô hình "Loyalty-as-a-Service":** Sentrix trích một phần nhỏ doanh thu/lợi nhuận để mua voucher từ các đối tác (quán ăn, Spa, thương hiệu bán lẻ...) làm phần thưởng đổi điểm cho người dùng app, tạo thành mạng lưới ưu đãi liên kết đa thương hiệu (cross-brand loyalty network) — vừa tăng động lực phản hồi thật của khách hàng, vừa tạo thêm nguồn thu và dữ liệu định danh bền vững (xác thực qua Zalo) chất lượng cao hơn so với zero-party data thu thập rời rạc ở giai đoạn MVP.
*   **Khởi nghiệp:** phát triển thành doanh nghiệp công nghệ B2B SaaS (kết hợp app loyalty B2C) độc lập sau cuộc thi.
*   **Công bố nghiên cứu:** tổng hợp và đóng gói kết quả thực nghiệm từ giai đoạn pilot để công bố các bài báo khoa học. Hướng nghiên cứu cốt lõi tập trung vào: (1) Đánh giá hiệu năng của phương pháp hợp nhất đa phương thức (âm thanh và văn bản) kết hợp các LLM tối ưu chi phí (như Gemini Flash-Lite) trong việc nhận diện sắc thái cảm xúc phức tạp (mỉa mai, từ lóng) của tiếng Việt; (2) Đề xuất và kiểm chứng tính hiệu quả của mô hình RFMS cải tiến trong việc dự báo chính xác xác suất rời bỏ (Churn Rate) của khách hàng ngành dịch vụ. Mục tiêu dự kiến gửi bài đến các hội nghị/tạp chí chuyên ngành uy tín về Hệ thống thông tin và Khoa học dữ liệu (như KSE, RIVF, hoặc ISBM).

| Giai đoạn | Thời gian dự kiến | Mục tiêu chính |
|---|---|---|
| **Nộp bài thuyết minh dự án AISC'26** | Tháng 8/2026 – 9/2026 | Hoàn thiện prototype, demo tại thư viện/tòa nhà trường |
| **Pilot mở rộng** | T9 – T10/2026 | Triển khai thật tại 1-2 quán cà phê/quán ăn khu Làng Đại học |
| **Thương mại hóa Pro** | T11 – T12/2026 | Bán gói Pro cho SME F&B, mở rộng Spa/Nha khoa |
| **Phát triển Mobile App** | T1/2027 | Đăng nhập Zalo, đăng nhập tài khoản trên Mobile App, tích điểm, đổi voucher, vòng quay |
| **Gọi vốn / Khởi nghiệp** | Q1/2027 trở đi | Mở rộng Enterprise, công bố nghiên cứu |

**9. Tài liệu tham khảo** 
1. iPOS.vn & Nestlé Professional, "Báo cáo thị trường Kinh doanh Ẩm thực Việt Nam 2025" (công bố 8/4/2026), đưa tin lại bởi Báo Đầu tư — https://baodautu.vn/thi-truong-fb-viet-nam-2026-huong-toi-doanh-thu-760000-ty-dong-quy-mo-333600-cua-hang-d564321.html
2. iPOS.vn & Nestlé Professional, Báo cáo thị trường F&B 6 tháng đầu năm 2025 (công bố 10/10/2025), đưa tin lại bởi VietnamBiz — https://vietnambiz.vn/cuoc-dai-thanh-loc-thi-truong-fb-50000-cua-hang-dong-cua-tren-toan-quoc-trong-nua-dau-nam-20251010102119659.htm
3. Harvard Business Review / Bain & Company (tổng hợp qua Invesp), "Customer Acquisition Vs Retention Costs" — https://www.invespcro.com/blog/customer-acquisition-retention/
4. "Chúc mừng sinh viên đã có bài báo khoa học đăng tại Hội nghị khoa học ISBM2020" - UIT — https://www.uit.edu.vn/chuc-mung-sinh-vien-da-co-bai-bao-khoa-hoc-dang-tai-hoi-nghi-khoa-hoc-isbm2020
5. Nguyen K.T.T. và cộng sự, "Span Detection for Aspect-Based Sentiment Analysis in Vietnamese", PACLIC 2021 — https://aclanthology.org/2021.paclic-1.34.pdf (arXiv:2110.07833)
6. kimkim00/UIT-ViSD4SA - GitHub (dataset & mã nguồn gốc) — https://github.com/kimkim00/UIT-ViSD4SA
7. Datasets - The UIT NLP Group — https://nlp.uit.edu.vn/datasets
8. "A Study of Vietnamese Sentiment Classification with Ensemble Pre-Trained Language Models", Vietnam Journal of Computer Science, 2024 (F1 = 75,36% trên UIT-ABSA Restaurant domain) — https://www.worldscientific.com/doi/10.1142/S2196888823500173
9. Curlscape, "Google Gemini API Pricing Guide 2026" (đối chiếu trang giá chính thức của Google, cập nhật 12/7/2026) — https://curlscape.com/blog/google-gemini-api-pricing-guide-2026
10. PhoNLP: A joint multi-task learning model for Vietnamese POS tagging, NER and dependency parsing - ACL Anthology — https://aclanthology.org/2021.naacl-demos.1/

---

## PHỤ LỤC — NỘI DUNG BỔ SUNG CHO DATA DRIVEN BUSINESS

**Nguồn dữ liệu dự kiến sử dụng:**
*   Dữ liệu phản hồi giọng nói/văn bản thu thập trực tiếp từ khách hàng qua QR tại điểm bán (dữ liệu tự thu thập).
*   Dữ liệu định danh zero-party (số điện thoại) qua cơ chế Gamification.
*   Bộ dữ liệu học thuật tiếng Việt UIT-ViSD4SA do nhóm nghiên cứu UIT công bố: 35.396 nhãn (spans) trên 11.122 bình luận (nguyên gốc là đánh giá điện thoại thông minh trên sàn TMĐT, dùng để benchmark phương pháp luận ABSA tiếng Việt nói chung) (5)(6)(7).
*   Bộ dữ liệu UIT-ABSA Restaurant7 — đúng lĩnh vực nhà hàng/F&B: thu thập từ một website đánh giá nhà hàng tiếng Việt, gán nhãn thủ công theo 12 khía cạnh (aspect) và 3 phân cực cảm xúc, phù hợp hơn để benchmark trực tiếp cho use-case của Sentrix so với UIT-ViSD4SA (8).
*   Dữ liệu huấn luyện/đánh giá thực tế cho ngành F&B/Spa sẽ do nhóm tự thu thập qua pilot tại trường và bổ sung từ dữ liệu đánh giá công khai trên Kaggle (Foody, ShopeeFood).
*   Dữ liệu đánh giá F&B từ Kaggle (Foody, ShopeeFood) để làm giàu từ vựng tiếng lóng.

**Phương pháp thu thập và xử lý dữ liệu:**
*   Thu thập qua Web Audio API (ghi âm ≤15 giây) hoặc nhập văn bản trực tiếp trên ứng dụng web.
*   Lọc nhiễu/chống gian lận sơ bộ trên FastAPI trước khi gọi API bên ngoài để tiết kiệm chi phí.
*   Chuyển giọng nói thành văn bản bằng Whisper API; trích xuất đặc trưng âm thanh bằng Librosa (MFCC, F0, Jitter, Shimmer).
*   Chuẩn hóa kết quả thành JSON có cấu trúc (khía cạnh – cảm xúc – lý do) qua LLM, lưu trữ trong Firestore theo Tenant ID.

**Thuật toán hoặc mô hình phân tích:**
*   Aspect-Based Sentiment Analysis (ABSA) qua LLM (dòng Gemini Flash-Lite/Flash hiện hành hoặc GPT-4o-mini/GPT-5-mini), có tham chiếu kỹ thuật phân tích cú pháp phụ thuộc PhoNLP.
*   Thuật toán hợp nhất trọng số động (Dynamic Weighted Fusion) giữa tín hiệu âm thanh và văn bản.
*   Mô hình RFMS và hồi quy logistic dự đoán xác suất rời bỏ khách hàng (Churn Probability).

Chỉ số rủi ro rời bỏ của khách hàng (Churn Probability - P_churn) được hệ thống mô hình hóa thông qua một phương trình hồi quy logistic dự đoán, trong đó điểm số cảm xúc (S) được trích xuất từ phân tích ABSA đóng vai trò là trọng số động nhạy cảm nhất đối với sự thay đổi hành vi:

`P_churn = 1 / (1 + e^(-(αR + βF + γM - δS + ϵ)))`

Trong phương trình học máy này, α, β, γ, δ là các hệ số được huấn luyện liên tục dựa trên dữ liệu lịch sử của từng doanh nghiệp. Một khách hàng có lịch sử ghé thăm dày đặc (F cao) nhưng đột ngột ghi nhận điểm cảm xúc sụt giảm nghiêm trọng (S cực âm) sẽ kích hoạt một độ lệch chuẩn lớn, đẩy P_churn vượt qua ngưỡng an toàn (ví dụ: trên 85%).

**Chỉ số đánh giá hiệu quả:**
*   F1-Score benchmark học thuật đã công bố: 62,76% F1-macro cho tác vụ Span Detection trên UIT-ViSD4SA (mô hình BiLSTM-CRF gốc) (6); 75,36% F1-weighted cho tác vụ ACSA trên UIT-ABSA Restaurant domain (mô hình ensemble PhoBERT/XLM) (8). Mức F1 > 85% mà Sentrix hướng tới khi triển khai thực tế là mục tiêu nội bộ của nhóm (chưa phải kết quả đã đo được) và sẽ cần tinh chỉnh Prompt Engineering, kiểm thử trên dữ liệu thật thu tại pilot để đánh giá lại.
*   Ngưỡng cảnh báo rủi ro rời bỏ (Churn Probability > 85%) — đây là ngưỡng đề xuất ban đầu của nhóm, sẽ được hiệu chỉnh dần theo dữ liệu lịch sử thực tế của từng doanh nghiệp, không phải một chuẩn ngành đã được kiểm chứng.
*   Tỷ lệ phản hồi (response rate) qua QR, doanh thu định kỳ hàng tháng (MRR).

**Kết quả phân tích hoặc dashboard dự kiến:**
*   Dashboard thời gian thực hiển thị KPI nhân sự theo từng khía cạnh dịch vụ, cảnh báo khách hàng rủi ro rời bỏ cao, và bộ lọc "bơm sao Google Maps".

**Phụ lục — Bảng công nghệ cốt lõi**

| Thành phần hệ thống | Công nghệ áp dụng | Vai trò chuyên biệt | Tối ưu chi phí đạt được |
|---|---|---|---|
| **Giao diện khách hàng (End-user)** | HTML5, React, Web Audio API | Hiển thị QR động, ghi âm một chạm, Gamification thu SĐT. | Hosting tĩnh miễn phí qua nền tảng phân phối biên (Vercel). |
| **Tiền xử lý & trích xuất âm thanh** | Python FastAPI, Librosa, Whisper API | Lọc nhiễu, trích xuất MFCCs/F0, chuyển đổi Speech-to-Text độ trễ thấp. | Xử lý nhẹ trên serverless, chi phí API tính theo giây vi mô. |
| **Lõi phân tích NLP & ABSA** | Gemini (dòng Flash-Lite/Flash hiện hành, ví dụ Gemini 3.1 Flash-Lite) hoặc GPT-4o-mini | Bóc tách khía cạnh phàn nàn, nhận diện mỉa mai, phân cực cảm xúc thành JSON. | Giá dòng Flash-Lite hiện hành ~0,25 USD/1M token đầu vào (7/2026) [9], giữ biên lợi nhuận SaaS cao. |
| **Cơ sở dữ liệu & định danh** | Firebase Firestore, Firebase Auth | Lưu dữ liệu phi cấu trúc, xác thực đa khách thuê (multi-tenant). | Miễn phí ở quy mô MVP (Spark Plan), bảo mật phân vùng tuyệt đối. |
