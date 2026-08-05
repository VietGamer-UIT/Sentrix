# Business Model Canvas — Sentrix

**Người soạn:** Đoàn Hoàng Việt (Trưởng nhóm)
**Ngày tạo:** 2026-08-05
**Nguồn dữ liệu chính:**
- `design/market-research/input-cho-bmc.md` (Tuấn)
- `design/market-research/doi-thu-canh-tranh.md` (Tuấn)
- `design/market-research/mo-hinh-tai-chinh-sme.md` (Tuấn)
- `docs/thuyet-minh-du-an/AISC26_Mau_Thuyet_Minh_Sentrix.md`

> **Kỷ luật dữ liệu:** Mỗi số liệu trong tài liệu này đều trích rõ nguồn. Chỗ nào là giả định sẽ ghi rõ "*giả định, chưa xác minh*" — nhất quán với phong cách minh bạch dữ liệu của cả nhóm.

---

## 1. Customer Segments — Phân Khúc Khách Hàng

### Khách hàng trả phí (B2B SaaS)
- **Trọng tâm ban đầu:** Doanh nghiệp SME ngành F&B (quán cà phê, tiệm ăn) tại khu vực Làng Đại học Quốc gia TP.HCM.
  *(Nguồn: input-cho-bmc.md §1)*
- **Mở rộng giai đoạn sau:** Spa, Nha khoa, Phòng khám quy mô nhỏ đến chuỗi vừa (5–15 chi nhánh).
  *(Nguồn: input-cho-bmc.md §1; Thuyết minh §II.2.c)*
- **Đặc điểm chung:** Các doanh nghiệp dịch vụ đang chuyển từ mở rộng quy mô sang phát triển chiều sâu, cần khai thác giá trị vòng đời khách hàng (CLV) trong bối cảnh hơn 50.000 cơ sở kinh doanh F&B phải đóng cửa chỉ trong nửa đầu năm 2025.
  *(Nguồn: Thuyết minh §II.2.a, tham khảo [2])*

### Người dùng cuối (nguồn dữ liệu, không trả phí)
- Khách hàng trải nghiệm dịch vụ tại điểm bán, phản hồi qua giọng nói/văn bản sau khi quét QR.
  *(Nguồn: Thuyết minh §II.2.c)*

---

## 2. Value Propositions — Giải Pháp Giá Trị

### Cho doanh nghiệp (B2B)
1. **Thu thập Voice-first 15 giây** qua Web Audio API — thao tác một chạm, giải quyết "nghịch lý của sự lịch sự" trong văn hoá Á Đông (khách hàng ngại phản hồi qua form dài dòng).
   *(Nguồn: doi-thu-canh-tranh.md §2.1)*
2. **Phân tích cảm xúc ABSA** bóc tách nguyên nhân gốc rễ theo từng khía cạnh dịch vụ (nhân viên, món ăn, không gian, giá cả, tốc độ phục vụ, vệ sinh) — thay vì điểm số chung chung không actionable.
   *(Nguồn: doi-thu-canh-tranh.md §1; Thuyết minh §II.6)*
3. **Tự động gửi voucher cứu vãn qua Zalo ZNS** ngay tại "thời điểm vàng" khi phát hiện khách hàng có trải nghiệm tệ — chặn đứng nguy cơ bóc phốt trên mạng xã hội.
   *(Nguồn: doi-thu-canh-tranh.md §2.2)*
4. **Gamification ("Vòng quay may mắn")** tăng vọt tỷ lệ phản hồi, đồng thời thu thập zero-party data (SĐT) hợp lệ làm tiền đề remarketing.
   *(Nguồn: doi-thu-canh-tranh.md §2.3)*
5. **Dự báo rủi ro rời bỏ (Churn Probability)** qua mô hình RFMS + hồi quy logistic — chủ động thay vì chờ mất khách.
   *(Nguồn: Thuyết minh §II.3, PHỤ LỤC)*

### So sánh USP với đối thủ

| Tính năng cốt lõi | Google Forms | Đánh giá sao (Google Maps) | **Sentrix** |
|---|---|---|---|
| Trải nghiệm một chạm (Ghi âm) | ❌ | ❌ | ✅ |
| Phân tích cảm xúc từ giọng nói | ❌ | ❌ | ✅ |
| Bóc tách nguyên nhân gốc rễ | ❌ | ❌ | ✅ |
| Dự báo rủi ro rời bỏ (Churn) | ❌ | ❌ | ✅ |
| Tự động gửi voucher cứu vãn | ❌ | ❌ | ✅ (Zalo ZNS) |

*(Nguồn: Thuyết minh §II.5)*

---

## 3. Channels — Kênh Phân Phối

| Kênh | Mô tả | Giai đoạn |
|---|---|---|
| **QR Code tại điểm bán** | Standee mini để bàn + thẻ đeo nhỏ gọn, khách quét bằng Camera/Zalo → mở Web Client | Pilot + Thương mại hoá |
| **Web Client (Vercel)** | Giao diện thu thập phản hồi responsive, truy cập qua URL từ QR | Pilot |
| **Dashboard quản trị (Vercel)** | Giao diện React cho chủ doanh nghiệp xem KPI, cảnh báo churn real-time | Pilot |
| **Zalo ZNS** | Kênh gửi voucher cứu vãn tự động đến khách hàng có rủi ro rời bỏ cao | Thương mại hoá |
| **Demo trực tiếp tại UIT** | Triển khai pilot tại thư viện trung tâm và sảnh tòa nhà giảng đường | Cuộc thi AISC'26 |

*(Nguồn: Thuyết minh §II.6, §II.8; design/logistics/ke-hoach-demo-pilot.md)*

---

## 4. Customer Relationships — Quan Hệ Khách Hàng

| Loại quan hệ | Cách thức | Đối tượng |
|---|---|---|
| **Self-service SaaS** | Chủ doanh nghiệp tự đăng ký, truy cập Dashboard, xem báo cáo | B2B (chủ quán) |
| **Gamification tương tác** | Vòng quay may mắn sau khi gửi phản hồi → trúng mã giảm giá | B2C (khách hàng cuối) |
| **Tự động hoá chăm sóc** | Hệ thống tự gửi voucher Zalo ZNS khi P_churn > ngưỡng (mặc định 85%) | B2C (giữ chân) |
| **Loyalty-as-a-Service** *(dài hạn)* | Mạng lưới ưu đãi liên kết đa thương hiệu, tích điểm đổi voucher qua Mobile App | B2C (hệ sinh thái) |

*(Nguồn: Thuyết minh §II.6; input-cho-bmc.md §2)*

---

## 5. Revenue Streams — Dòng Doanh Thu

| Gói | Giá | Nội dung chính | Đối tượng |
|---|---|---|---|
| **Starter** | 99.000 VNĐ/tháng | Nhập văn bản thuần tuý, không AI voice, thống kê tĩnh cơ bản. Sản phẩm "chim mồi" | Quán nhỏ, mới thử nghiệm |
| **Pro** (Chủ lực) | 299.000 VNĐ/tháng | Toàn bộ AI đa phương thức, ABSA real-time, "bơm sao Google Maps" | SME F&B, Spa, Nha khoa đơn lẻ |
| **Enterprise** | 1.000.000 – 2.000.000 VNĐ/tháng (thương lượng) | Liên kết dữ liệu chéo, KPI so sánh, RFMS + ZNS tự động | Chuỗi 5–15 chi nhánh |

*(Nguồn: input-cho-bmc.md §1; Thuyết minh §II.6)*

> *Ghi chú: Cấu trúc giá mang tính chất tham khảo dựa trên mặt bằng chung của thị trường SaaS tại Việt Nam. Các mức giá dự kiến sẽ được hiệu chỉnh qua dữ liệu thu thập thực tế trong giai đoạn Pilot.* *(Nguồn: Thuyết minh §II.6)*

---

## 6. Key Resources — Tài Nguyên Cốt Lõi

| Tài nguyên | Chi tiết |
|---|---|
| **AI Pipeline** | Whisper API (STT), Librosa (audio features), Gemini Flash-Lite (ABSA), Dynamic Weighted Fusion |
| **Cơ sở dữ liệu** | Firebase Firestore (multi-tenant, Security Rules theo Tenant ID) |
| **Hạ tầng hosting** | Vercel (frontend — miễn phí), Render.com (backend — serverless) |
| **Bộ dữ liệu benchmark** | UIT-ViSD4SA (35.396 nhãn, 11.122 bình luận), UIT-ABSA Restaurant7 (12 khía cạnh, lĩnh vực nhà hàng) |
| **Đội ngũ** | 3 sinh viên năm nhất UIT — Việt (PM/Frontend), Tuyền (AI/Backend), Tuấn (UX/UI/Research) |
| **Kênh truyền thông** | Zalo ZNS (gửi tin nhắn tự động), QR Code in ấn |

*(Nguồn: Thuyết minh PHỤ LỤC — Bảng công nghệ cốt lõi; §II.3)*

---

## 7. Key Activities — Hoạt Động Cốt Lõi

| Hoạt động | Mô tả |
|---|---|
| **Phát triển & duy trì nền tảng SaaS** | Xây dựng và vận hành Web Client, Dashboard, Backend API |
| **Pipeline AI 4 giai đoạn** | ① Tiếp nhận phản hồi (QR + Web Audio) → ② STT + Audio features + ABSA → ③ Lưu trữ multi-tenant Firestore → ④ Dashboard real-time + ZNS trigger |
| **Thu thập & gán nhãn dữ liệu** | Pilot tại UIT để có dữ liệu thật, bổ sung từ Kaggle (Foody, ShopeeFood) để làm giàu từ vựng tiếng lóng |
| **Tối ưu mô hình ABSA tiếng Việt** | Benchmark trên UIT-ViSD4SA và UIT-ABSA Restaurant7, tinh chỉnh Prompt Engineering |
| **Tính toán RFMS & P_churn** | Huấn luyện hệ số α, β, γ, δ trên dữ liệu lịch sử từng doanh nghiệp |
| **Bán hàng & onboarding khách B2B** | Tiếp cận SME, hỗ trợ cài đặt QR, hướng dẫn Dashboard |

*(Nguồn: Thuyết minh §II.6, PHỤ LỤC)*

---

## 8. Key Partnerships — Đối Tác Chiến Lược

| Đối tác | Vai trò | Ghi chú |
|---|---|---|
| **OpenAI (Whisper API)** | Speech-to-Text | ~0.006 USD/phút *(giả định, chưa xác minh chiết khấu — mo-hinh-tai-chinh-sme.md §1)* |
| **Google (Gemini Flash-Lite)** | ABSA / NLP core | ~0.25 USD/1M token đầu vào *(Nguồn: Thuyết minh [9])* |
| **Zalo (ZNS)** | Kênh gửi voucher cứu vãn | ~200 VNĐ/tin nhắn *(giả định, chưa xác minh chiết khấu sản lượng — mo-hinh-tai-chinh-sme.md §1)* |
| **Firebase (Google)** | Firestore + Auth + Storage | Miễn phí ở quy mô MVP (Spark Plan) |
| **Vercel** | Hosting frontend | Miễn phí (hobby tier) |
| **Render.com** | Hosting backend | Serverless / Free tier |
| **UIT (Trường ĐH CNTT)** | Địa điểm pilot, nguồn dữ liệu thử nghiệm | Pilot tại thư viện + sảnh giảng đường |

---

## 9. Cost Structure — Cấu Trúc Chi Phí

### Chi phí biến đổi (COGS) — trên mỗi khách hàng B2B/tháng

| Khoản mục | Giả định sử dụng | Chi phí ước tính |
|---|---|---|
| Whisper API | 500 lượt × 10s = 83.3 phút | ~12.500 VNĐ (0.5 USD) |
| Gemini API | 500 lượt × 200 token = 100K token | ~625 VNĐ (0.025 USD) |
| Zalo ZNS | 10% trigger = 50 tin nhắn | ~10.000 VNĐ |
| Hosting/Firestore (khấu hao) | — | ~10.000 VNĐ |
| **Tổng COGS** | | **~33.125 VNĐ/KH/tháng** |

*(Nguồn: mo-hinh-tai-chinh-sme.md §1 — toàn bộ là dữ liệu giả định)*

### Chi phí cố định

- **Ước tính:** 15.000.000 VNĐ/tháng (bao gồm vận hành nền tảng, máy chủ, marketing, nhân sự quản trị)
  *(giả định, chưa xác minh chi tiết các khoản mục — mo-hinh-tai-chinh-sme.md §3)*

### Chỉ số sinh lời (Gói Pro)

| Chỉ số | Giá trị |
|---|---|
| Doanh thu / KH | 299.000 VNĐ |
| COGS / KH | ~33.125 VNĐ |
| Lợi nhuận gộp / KH | ~265.875 VNĐ |
| **Biên lợi nhuận gộp** | **~88,9%** |
| **Điểm hoà vốn** | **~57 khách hàng gói Pro** |

*(Nguồn: mo-hinh-tai-chinh-sme.md §2-3 — dữ liệu giả định)*

---

## Sơ Đồ Tổng Hợp BMC

```
┌─────────────────┬──────────────────┬──────────────────┬──────────────────┬─────────────────┐
│  8. KEY          │  7. KEY           │  2. VALUE        │  4. CUSTOMER     │  1. CUSTOMER    │
│  PARTNERSHIPS    │  ACTIVITIES       │  PROPOSITIONS    │  RELATIONSHIPS   │  SEGMENTS       │
│                  │                   │                  │                  │                 │
│ • OpenAI Whisper │ • Pipeline AI     │ • Voice-first    │ • Self-service   │ • SME F&B       │
│ • Google Gemini  │   4 giai đoạn     │   15s            │   SaaS           │   (Làng ĐH)     │
│ • Zalo ZNS      │ • Thu thập data   │ • ABSA bóc tách  │ • Gamification   │ • Spa, Nha khoa │
│ • Firebase      │ • Tối ưu ABSA     │   gốc rễ         │ • ZNS tự động    │   Phòng khám    │
│ • Vercel/Render │ • RFMS + P_churn  │ • ZNS cứu vãn    │ • Loyalty-as-    │ • Chuỗi 5-15    │
│ • UIT (pilot)   │ • Bán hàng/       │ • Gamification    │   a-Service      │   chi nhánh     │
│                  │   onboarding      │ • Dự báo churn   │   (dài hạn)      │                 │
│                  │                   │                  │                  │ (End-user: KH   │
│                  │                   │                  │                  │  tại điểm bán)  │
├─────────────────┴──────────────────┼──────────────────┴──────────────────┤                 │
│                                     │                                     │                 │
│  6. KEY RESOURCES                   │  3. CHANNELS                        │                 │
│                                     │                                     │                 │
│ • AI Pipeline (Whisper + Librosa    │ • QR Code tại điểm bán              │                 │
│   + Gemini + Fusion)                │ • Web Client (Vercel)               │                 │
│ • Firebase Firestore (multi-tenant) │ • Dashboard React (Vercel)          │                 │
│ • Bộ dữ liệu UIT-ViSD4SA,          │ • Zalo ZNS                          │                 │
│   UIT-ABSA Restaurant7              │ • Demo trực tiếp tại UIT            │                 │
│ • Đội ngũ 3 SV UIT                  │                                     │                 │
│                                     │                                     │                 │
├─────────────────────────────────────┴─────────────────────────────────────┤                 │
│                                                                           │                 │
│  9. COST STRUCTURE                                     5. REVENUE STREAMS │                 │
│                                                                           │                 │
│ • COGS ~33.125₫/KH/tháng (Whisper + Gemini + ZNS)     • Starter: 99K₫   │                 │
│ • Chi phí cố định ~15M₫/tháng (giả định)              • Pro: 299K₫      │                 │
│ • Biên LN gộp ~88,9% (gói Pro)                        • Enterprise:     │                 │
│ • Điểm hoà vốn ~57 KH gói Pro                           1M–2M₫          │                 │
│                                                                           │                 │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Lưu Ý & Rủi Ro

1. **Phụ thuộc API bên thứ ba:** Chi phí Whisper và Gemini có thể thay đổi. Biên lợi nhuận 88,9% chỉ đúng ở mức giá niêm yết hiện hành (7/2026). *(Nguồn: Thuyết minh §II.6 — Hạn chế)*
2. **Mô hình RFMS cần dữ liệu lịch sử:** Hệ số α, β, γ, δ cần huấn luyện trên dữ liệu đủ lớn của từng doanh nghiệp. Giai đoạn pilot sẽ dùng hệ số mặc định. *(Nguồn: Thuyết minh §II.6 — Hạn chế)*
3. **Chi phí cố định 15M₫/tháng là giả định:** Chưa khảo sát chi tiết — cần nhóm bổ sung trước khi thuyết trình. *(Nguồn: mo-hinh-tai-chinh-sme.md §3)*
4. **Gói Enterprise chưa có khách mục tiêu cụ thể:** Cần pilot thành công ở gói Pro trước rồi mới tiếp cận chuỗi.
