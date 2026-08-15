# Pitch Deck Outline — Sentrix (AISC'26)

> **Người soạn:** Đoàn Hoàng Việt (Trưởng nhóm & Thuyết trình viên)
> **Cập nhật:** 2026-08-05
> **Trạng thái:** Khung cấu trúc hoàn chỉnh — phần demo đánh dấu `[TODO]` chờ sản phẩm thật

---

## Cấu Trúc Slide

### Slide 1 — Trang Bìa
- **Tên dự án:** Sentrix — AI-Powered Multimodal Customer Experience Analytics
- **Đội:** 3 sinh viên năm nhất, Khoa Hệ thống Thông tin, ĐH Công nghệ Thông tin (UIT)
- **Chủ đề:** Data Driven Business
- **Logo/mascot:** 🦉 (con cú — biểu tượng Sentrix)

---

### Slide 2 — Vấn Đề (The Problem)

**Headline:** *"50.000 cửa hàng đóng cửa — nhưng không phải vì thiếu khách, mà vì không nghe được khách"*

**3 rào cản lớn:**

| # | Rào cản | Chi tiết |
|---|---|---|
| ① | **UX friction** | Biểu mẫu khảo sát quá dài, khách ngại phản hồi — "nghịch lý của sự lịch sự" trong văn hoá Á Đông |
| ② | **Dữ liệu hời hợt** | Đánh giá 3 sao không cho biết nguyên nhân gốc rễ — non-actionable |
| ③ | **Thụ động** | Doanh nghiệp không dự báo được khách sắp rời bỏ cho đến khi bị bóc phốt trên MXH |

**Số liệu dẫn chứng:**
- Quy mô thị trường F&B: **760.000 tỷ VNĐ**, **333.600 điểm bán** *(Nguồn: iPOS.vn & Nestlé, 04/2026 [1])*
- Chi phí thu hút KH mới đắt gấp **5–25 lần** giữ chân KH cũ *(Nguồn: Bain & Company / HBR [3])*
- Hơn **50.000** cơ sở đóng cửa trong nửa đầu 2025 *(Nguồn: iPOS.vn [2])*

---

### Slide 3 — Giải Pháp (The Solution)

**Headline:** *"Sentrix: Nghe — Hiểu — Hành động. Trong 15 giây."*

**Pipeline 4 bước:**
```
① QR một chạm    →    ② AI nghe + hiểu    →    ③ Dashboard real-time    →    ④ Zalo ZNS cứu vãn
   (15s ghi âm)       (Whisper + ABSA)        (KPI + churn alerts)        (voucher tự động)
```

**USP cốt lõi:**
- **Voice-first:** Khách hàng nói 15 giây thay vì gõ 5 phút
- **ABSA (Aspect-Based Sentiment Analysis):** Bóc tách nguyên nhân gốc rễ theo từng khía cạnh (nhân viên, món ăn, không gian, giá cả, tốc độ, vệ sinh)
- **Gamification:** Vòng quay may mắn tăng tỷ lệ phản hồi + thu thập SĐT zero-party data
- **RFMS + Auto-rescue:** Dự đoán churn, tự động gửi voucher trước khi mất khách

---

### Slide 4 — Demo Sản Phẩm

> **[TODO — Hoàn thiện sau khi có sản phẩm thật chạy được]**

**Kịch bản demo dự kiến:**
1. Giám khảo quét QR → mở web-client
2. Nhấn ghi âm → nói câu nhận xét (xem `demo-script.md` cho câu mẫu)
3. Nhấn gửi → Vòng quay may mắn
4. Chuyển sang laptop → Dashboard cập nhật real-time
5. (Tuỳ chọn) ZNS trigger demo

**Cần chờ:**
- [ ] Tuấn hoàn thiện web-client + dashboard
- [ ] Tuyền hoàn thiện pipeline ABSA
- [ ] Test E2E toàn luồng
- [ ] Quay video backup phòng trường hợp demo live bị lỗi mạng

---

### Slide 5 — Mô Hình Kinh Doanh

**B2B SaaS phân tầng:**

| Gói | Giá/tháng | Mục tiêu |
|---|---|---|
| Starter | 99K₫ | Chim mồi, quán nhỏ |
| **Pro** | **299K₫** | **Chủ lực — AI toàn diện** |
| Enterprise | 1M–2M₫ | Chuỗi 5–15 chi nhánh |

**Chỉ số tài chính:**
- COGS/KH: ~33.125₫/tháng *(giả định — mo-hinh-tai-chinh-sme.md)*
- Biên lợi nhuận gộp (Pro): **~88,9%**
- Điểm hoà vốn: **~57 khách hàng** gói Pro
- Chi phí cố định: ~15M₫/tháng *(giả định, chưa xác minh)*

*(Nguồn: design/market-research/mo-hinh-tai-chinh-sme.md)*

> *Lưu ý khi thuyết trình: Nhấn mạnh biên LN cao nhờ serverless + LLM chi phí thấp. Chủ động ghi nhận "giả định" trước khi giám khảo hỏi — thể hiện sự minh bạch.*

---

### Slide 6 — Công Nghệ

**Bảng công nghệ cốt lõi:**

| Thành phần | Công nghệ | Vai trò |
|---|---|---|
| Giao diện KH | React, Web Audio API | QR động, ghi âm một chạm, Gamification |
| STT + Audio | Whisper API, Librosa | Speech-to-Text, trích MFCC/F0/Jitter/Shimmer |
| NLP / ABSA | Gemini Flash-Lite | Bóc tách khía cạnh, phát hiện mỉa mai |
| Churn Prediction | RFMS + Logistic Regression | Dự đoán xác suất rời bỏ |
| Database | Firebase Firestore | Multi-tenant, Security Rules theo Tenant ID |
| Deploy | Vercel (FE) + Render (BE) | Serverless, chi phí thấp |

**Công thức RFMS:**
```
P_churn = 1 / (1 + e^(-(αR + βF + γM - δS + ε)))
```
- R = Recency, F = Frequency, M = Monetary, **S = Sentiment** (chiều mới, khác RFM cổ điển)
- α, β, γ, δ huấn luyện trên dữ liệu lịch sử từng doanh nghiệp

*(Nguồn: Thuyết minh §II.3, PHỤ LỤC)*

---

### Slide 7 — So Sánh Đối Thủ

| Tính năng | Google Forms | Đánh giá sao | SurveyMonkey | **Sentrix** |
|---|---|---|---|---|
| Thu thập Voice-first | ❌ | ❌ | ❌ | ✅ |
| Phân tích cảm xúc ABSA | ❌ | ❌ | Cơ bản | ✅ Chi tiết |
| Gamification tăng response rate | ❌ | ❌ | ❌ | ✅ |
| Dự báo churn | ❌ | ❌ | ❌ | ✅ |
| Auto-rescue (Zalo ZNS) | ❌ | ❌ | Cần Zapier | ✅ Native |

*(Nguồn: design/market-research/doi-thu-canh-tranh.md)*

---

### Slide 8 — Đội Ngũ

| Thành viên | Vai trò | Phụ trách |
|---|---|---|
| **Đoàn Hoàng Việt** | Trưởng nhóm & Thuyết trình viên | PM, BMC, Deploy, Tích hợp, Pitching |
| **Nguyễn Thanh Tuyền** | Kiến trúc sư AI & Dữ liệu | AI Pipeline, ABSA, RFMS, Backend, Database |
| **Nguyễn Quốc Tuấn** | Kỹ sư Ứng dụng & Nghiên cứu TT | UX/UI, Frontend, Market Research, Demo Logistics |

- 3 sinh viên năm nhất, Khoa HTTT, ĐH CNTT — ĐHQG TP.HCM
- Quy trình làm việc: Git flow chặt chẽ, lãnh địa code riêng, PR review bắt buộc

---

### Slide 9 — Roadmap & Tầm Nhìn

| Giai đoạn | Thời gian | Mục tiêu |
|---|---|---|
| **AISC'26** | T8–T9/2026 | Prototype + demo tại UIT |
| **Pilot mở rộng** | T9–T10/2026 | 1–2 quán tại Làng ĐH |
| **Thương mại hoá** | T11–T12/2026 | Bán gói Pro cho SME F&B, mở rộng Spa/Nha khoa |
| **Mobile App** | T1/2027 | Tích điểm, đổi voucher, Loyalty-as-a-Service |
| **Gọi vốn** | Q1/2027+ | Mở rộng Enterprise, công bố nghiên cứu |

*(Nguồn: Thuyết minh §II.8)*

**Tầm nhìn dài hạn:** Từ SaaS B2B → hệ sinh thái Loyalty-as-a-Service đa thương hiệu (B2B + B2C).

---

### Slide 10 — Call to Action

**Kết thúc bằng câu hỏi cho giám khảo:**
*"Lần cuối cùng anh/chị để lại phản hồi ở một quán ăn bằng Google Forms là khi nào? Sentrix giúp câu trả lời đó chỉ mất 15 giây — và cứu được 57 khách hàng để hoà vốn."*

**QR code demo trực tiếp** trên slide (link đến web-client đã deploy).
> **[TODO — Thêm QR code khi có URL deploy thật]**

---

## Ghi Chú Cho Người Thuyết Trình (Việt)

### Chuẩn bị
- [ ] Laptop sạc đầy + sạc dự phòng
- [ ] Hotspot 4G backup (theo kế hoạch demo pilot)
- [ ] Dashboard mở sẵn trên tab riêng
- [ ] QR standee đặt sẵn trên bàn giám khảo
- [ ] Video demo backup phòng lỗi mạng

### Câu hỏi giám khảo dự kiến & cách trả lời
1. **"Biên lợi nhuận 88,9% có thực tế không?"**
   → "Con số này dựa trên giá API niêm yết hiện hành, chưa tính chi phí ẩn. Chúng em ghi rõ đây là giả định và sẽ hiệu chỉnh qua pilot."

2. **"Nếu API Whisper/Gemini tăng giá thì sao?"**
   → "Kiến trúc modular cho phép thay thế — có thể chuyển sang các LLM mã nguồn mở hoặc self-host."

3. **"57 khách hàng để hoà vốn — làm sao đạt được?"**
   → "Bắt đầu từ Làng ĐH Quốc gia (~40-50 quán cà phê/tiệm ăn trong bán kính 2km), rồi mở rộng ra."

4. **"Dữ liệu được bảo mật như thế nào trên Firestore?"**
   → "Mỗi quán ăn (tenant) có ID riêng và được phân tách qua Security Rules. Chỉ chủ quán mới xem được data của quán mình."

### Số liệu nhớ thuộc lòng (khớp cheat-sheet giám khảo)
- Thị trường F&B: 760.000 tỷ₫, 333.600 điểm bán
- CAC gấp 5–25x chi phí giữ chân
- 50.000+ cửa hàng đóng cửa nửa đầu 2025
- Gói Pro: 299K₫/tháng, biên LN ~88,9%, BEP ~57 KH
