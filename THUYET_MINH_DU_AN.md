# THUYẾT MINH DỰ ÁN
**ADVANCED INFORMATION SYSTEMS CONTEST 2026**

---

## PHẦN I: THÔNG TIN CHUNG

**1. Tên đội thi:** Sentrix
**2. Chủ đề đăng ký:** Data Driven Business
**3. Thông tin thành viên:**

| Vị trí | Thành viên 1 (Trưởng nhóm) | Thành viên 2 | Thành viên 3 |
|---|---|---|---|
| **Họ tên** | Đoàn Hoàng Việt | Nguyễn Thanh Tuyền | Nguyễn Quốc Tuấn |
| **MSSV** | 25522061 | 25522042 | 25522018 |
| **Khoa** | Hệ thống Thông tin | Hệ thống Thông tin | Hệ thống Thông tin |
| **Trường** | Đại học Công nghệ Thông tin - ĐHQG TP.HCM | Đại học Công nghệ Thông tin - ĐHQG TP.HCM | Đại học Công nghệ Thông tin - ĐHQG TP.HCM |
| **Email** | 25522061@gm.uit.edu.vn | 25522042@gm.uit.edu.vn | 25522018@gm.uit.edu.vn |
| **Ngày sinh** | 16/04/2007 | 25/11/2007 | 10/07/2007 |
| **Vai trò & Phụ trách chính** | **Quản lý dự án, DevOps & Full-stack Support:** Khởi xướng ý tưởng, quản trị mô hình kinh doanh (BMC), thuyết trình (Pitching). Quản lý hệ thống API Key, thiết lập môi trường, chịu trách nhiệm Deploy toàn bộ hệ thống (Vercel, Render) và hỗ trợ cả Frontend lẫn Backend. | **Backend Developer & AI Engineer:** Xây dựng kiến trúc hệ thống Backend (Python FastAPI). Phát triển lõi AI xử lý âm thanh/ngôn ngữ đa phương thức (Whisper, Librosa, Gemini ABSA). Thiết kế cơ sở dữ liệu đa khách thuê (Multi-tenant) trên Firestore. | **Frontend Developer & UX/UI Designer:** Phát triển toàn bộ giao diện người dùng bằng React (Web-Client và Dashboard). Thiết kế UX/UI trải nghiệm một chạm. Xử lý kết nối API từ Backend và tối ưu hóa hiệu năng hiển thị thời gian thực. |

**4. Trưởng nhóm (thông tin từ BTC sẽ gửi đến người này)**
- Họ và tên: Đoàn Hoàng Việt
- Số điện thoại: 0327277624

---

## PHẦN II: THÔNG TIN DỰ ÁN

**1. Tên dự án (tên đề tài)**
- **Tên Tiếng Việt:** Sentrix – Nền tảng thu thập và phân tích trải nghiệm khách hàng đa phương thức
- **Tên Tiếng Anh:** Sentrix – AI-Powered Multimodal Customer Experience Analytics Platform
- **Lĩnh vực:** Thương mại dịch vụ – khởi điểm ngành F&B (ẩm thực & đồ uống), mở rộng sang Spa, Nha khoa, Phòng khám (Clinic).

### 2. Bối cảnh và bài toán

**a. Bối cảnh:**
Thị trường dịch vụ thương mại tại Việt Nam, đặc biệt ngành F&B, đang trải qua giai đoạn tái cấu trúc và thanh lọc chưa từng có. Theo Báo cáo "Thị trường kinh doanh ẩm thực tại Việt Nam năm 2025" do iPOS.vn phối hợp Nestlé Professional công bố (04/2026), năm 2026 toàn thị trường F&B được dự báo đạt quy mô doanh thu khoảng 760.000 tỷ đồng với khoảng 333.600 điểm bán, tăng trưởng ổn định ở mức 4,6%; tuy vậy báo cáo 6 tháng đầu năm 2025 cũng chỉ ra hơn 50.000 cơ sở kinh doanh phải đóng cửa. Chi phí nguyên vật liệu và mặt bằng tăng cao buộc doanh nghiệp phải chuyển từ mở rộng quy mô sang phát triển chiều sâu, khai thác giá trị vòng đời khách hàng (CLV). Chi phí thu hút một khách hàng mới (CAC) có thể cao gấp 5 đến 25 lần chi phí giữ chân khách hàng hiện hữu. Thế hệ Gen Z và Millennials ngày càng đề cao trải nghiệm dịch vụ thực chất.

**b. Vấn đề cần giải quyết:**
- **Ai đang gặp vấn đề:** Các doanh nghiệp SME ngành F&B, Spa, Nha khoa, Phòng khám tại Việt Nam.
- **Vấn đề là gì:** Công cụ khảo sát hiện tại (Google Forms, thang điểm sao) tồn tại 3 rào cản lớn:
  1. UX friction khiến khách hàng ngại phản hồi xuất phát từ các điểm nghẽn chính: biểu mẫu quá dài, yêu cầu đăng nhập rườm rà.
  2. Dữ liệu thu được hời hợt, không định hướng hành động (đánh giá 3 sao không cho biết nguyên nhân gốc rễ).
  3. Doanh nghiệp thụ động, không dự báo được khách hàng sắp rời bỏ cho đến khi họ bóc phốt trên mạng xã hội.
- **Vì sao cần giải quyết:** Những điểm mù này khiến doanh nghiệp mất doanh thu và danh tiếng một cách âm thầm.

**c. Đối tượng hướng đến:**
- **Doanh nghiệp (B2B SaaS):** chủ quán F&B, Spa, Nha khoa, Phòng khám quy mô SME đến chuỗi nhỏ.
- **Người dùng cuối:** khách hàng trải nghiệm dịch vụ tại điểm bán, phản hồi qua giọng nói/văn bản.

### 3. Mục tiêu của đề tài
**Mục tiêu tổng quát:** Xây dựng nền tảng SaaS đa phương thức, lấy giọng nói làm trung tâm (Voice-First), ứng dụng AI để thu thập, phân tích cảm xúc và dự đoán hành vi khách hàng.

**Mục tiêu cụ thể:**
- Xây dựng giao diện thu thập phản hồi một chạm qua QR động, hỗ trợ ghi âm giọng nói (Web Audio API).
- Phát triển lõi phân tích cảm xúc đa phương thức (MFCC, F0 qua Librosa kết hợp ABSA qua LLM).
- Xây dựng và huấn luyện mô hình RFMS để tính điểm rủi ro rời bỏ khách hàng (Churn Probability).
- Tự động hóa quy trình cứu vãn khách hàng qua webhook Zalo ZNS.
- Xây dựng Dashboard quản trị thời gian thực cho chủ doanh nghiệp bằng **React, Vite + Firestore Listener**.

### 4. Tính cấp thiết, tính mới, ý tưởng khoa học
Sentrix lấy cảm hứng từ hướng nghiên cứu "Emotion recognition in customer service" kết hợp cơ chế hợp nhất đa phương thức (Multimodal Fusion) giữa đặc trưng âm thanh và ABSA văn bản để nhận diện sắc thái mỉa mai, châm biếm đặc trưng trong giao tiếp tiếng Việt. Việc nâng cấp mô hình RFM cổ điển thành RFMS (bổ sung chiều Sentiment) cũng là một đóng góp có tính ứng dụng cao. Về khả năng thương mại hóa, kiến trúc serverless và các dòng LLM chi phí thấp hiện hành (Gemini Flash-Lite) giúp Sentrix có biên lợi nhuận SaaS khả thi.

### 5. Các giải pháp khác hiện nay so với Sentrix
Sentrix vượt trội hoàn toàn so với Khảo sát Giấy / Google Forms và Hệ thống 1-5 Sao (Google Maps) nhờ:
- Trải nghiệm một chạm (Ghi âm)
- Tỷ lệ phản hồi rất cao (Gamification)
- Phân tích cảm xúc từ Giọng nói và bóc tách nguyên nhân gốc rễ
- Dự báo rủi ro rời bỏ (Churn Rate)
- Tự động gửi Voucher cứu vãn qua Zalo ZNS

### 6. Giải pháp đề xuất của nhóm
Sentrix đề xuất một pipeline xử lý dữ liệu thời gian thực gồm 4 giai đoạn:
1. Tiếp nhận phản hồi đa phương thức qua QR động và Web Audio API (xây dựng bằng React).
2. Lõi AI backend (Python FastAPI) chuyển đổi giọng nói (Whisper API), bóc tách ngữ nghĩa (Librosa) kết hợp LLM ABSA (Gemini Flash-Lite).
3. Lưu trữ đa khách thuê (multi-tenant) an toàn trên Firebase Firestore với Security Rules.
4. Hiển thị Dashboard thời gian thực (xây dựng bằng React) và tự động kích hoạt Zalo ZNS khi rủi ro rời bỏ cao.

### 7. Kết quả dự kiến
Sau cuộc thi, nhóm dự kiến hoàn thành:
- [x] Prototype & Website (React Web-Client)
- [x] Dashboard (React)
- [x] AI Model (Python FastAPI)
- [x] Hệ thống quản trị (Firebase, Render, Vercel)

*Mô tả ngắn:* Ứng dụng web thu thập phản hồi (QR + ghi âm một chạm) triển khai trên Vercel; backend FastAPI xử lý pipeline AI trên Render.com; cơ sở dữ liệu multi-tenant Firebase Firestore; dashboard quản trị thời gian thực xây dựng bằng **React** hiển thị KPI. Bản demo/prototype được triển khai thực tế ngay tại khuôn viên trường.

### 8. Định hướng phát triển
- Hoàn thiện sản phẩm: tối ưu mô hình ABSA tiếng Việt, mở rộng benchmark.
- Thử nghiệm (Pilot): triển khai bản demo thực tế tại thư viện, Làng Đại học Quốc gia TP.HCM.
- Thương mại hóa: áp dụng gói Pro cho SME F&B, mở rộng Spa/Nha khoa/Phòng khám.
- Phát triển Mobile App (T1/2027) tích hợp Zalo, tích điểm, đổi voucher.
- Xây dựng mô hình "Loyalty-as-a-Service".
- Công bố nghiên cứu bài báo khoa học.

### 9. Phụ lục — Bảng công nghệ cốt lõi

| Thành phần hệ thống | Công nghệ áp dụng | Vai trò chuyên biệt | Tối ưu chi phí đạt được |
|---|---|---|---|
| **Giao diện khách hàng (Web-Client & Dashboard)** | **React, Vite, Web Audio API, Tailwind CSS** | Hiển thị QR động, ghi âm một chạm, Gamification, Dashboard quản trị thời gian thực. | Hosting tĩnh miễn phí qua nền tảng phân phối biên (Vercel). |
| **Tiền xử lý & trích xuất âm thanh** | Python FastAPI, Librosa, Whisper API | Lọc nhiễu, trích xuất MFCCs/F0, chuyển đổi Speech-to-Text độ trễ thấp. | Xử lý nhẹ trên serverless (Render), chi phí API tính theo giây vi mô. |
| **Lõi phân tích NLP & ABSA** | Gemini (Flash-Lite / Flash 3.1) | Bóc tách khía cạnh phàn nàn, nhận diện mỉa mai, phân cực cảm xúc thành JSON. | Giữ biên lợi nhuận SaaS cao nhờ chi phí token rẻ của dòng Flash. |
| **Cơ sở dữ liệu & DevOps** | Firebase (Firestore, Auth), GitHub Actions | Lưu dữ liệu phi cấu trúc, xác thực đa khách thuê (multi-tenant), CI/CD. | Miễn phí ở quy mô MVP (Spark Plan), bảo mật phân vùng tuyệt đối bằng Security Rules. |
