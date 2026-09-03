# Sentrix - Hệ thống thu thập phản hồi và hỗ trợ cải thiện trải nghiệm khách hàng

Sentrix (AI-Powered Customer Feedback and Service Recovery Platform) là hệ thống giúp cửa hàng thu thập phản hồi nhanh, hiểu vấn đề và xử lý ngay trong lúc khách hàng đang trải nghiệm dịch vụ.

Giai đoạn AISC'26 và Pilot tập trung vào quán ăn, quán cà phê tại khu vực Làng Đại học.

Giá trị cốt lõi của Sentrix không nằm ở việc sử dụng AI phức tạp, mà ở khả năng rút ngắn khoảng cách giữa phản hồi và hành động. Hệ thống hỗ trợ nhân viên hành động kịp thời, không thay thế nhân viên.

---

## 🚀 Tính năng hiện tại (MVP)

- **Đa phương thức đầu vào:** Khách hàng quét QR tại bàn, có thể phản hồi bằng giọng nói (Voice) hoặc văn bản (Text) mà không cần tải App.
- **Phân tích âm thanh và ngôn ngữ tự nhiên:**
  - Chuyển đổi giọng nói thành văn bản (Speech-to-Text) bằng Whisper API (Groq).
  - Phân tích cảm xúc theo khía cạnh (ABSA) bằng mô hình Gemini Flash-Lite.
- **Action-oriented (Hướng hành động):** 
  - Phân biệt phản hồi và yêu cầu hỗ trợ. Ví dụ: "Tôi cần một ly trà đá" sẽ tạo ra cảnh báo (alert) ngay cho nhân viên.
- **Feedback Recovery & Review Invitation:** Phân luồng phản hồi. Phản hồi tốt có thể mời đánh giá công khai (kèm voucher), phản hồi chưa tốt được ưu tiên giữ lại để cửa hàng xử lý nội bộ.
- **Cơ chế chống gian lận (Anti-fraud) 4 lớp:** Kiểm soát tần suất (hash số điện thoại), kiểm tra chất lượng dữ liệu (thời lượng, SNR trước khi STT), kiểm tra ngữ nghĩa (bỏ qua nội dung vô nghĩa) và kiểm soát ngân sách voucher.

---

## 🏗️ Kiến trúc hệ thống

```
Sentrix/
├── backend/          - FastAPI backend (AI pipeline, Firestore)
├── apps/
│   ├── web-client/   - React + Web Audio API (Khách hàng quét QR)
│   └── dashboard/    - React (Dashboard thời gian thực cho chủ quán)
├── docs/             - Tài liệu kỹ thuật
├── firestore.rules   - Cấu hình bảo mật Firestore
└── render.yaml       - Cấu hình triển khai Render
```

---

## 🔄 Luồng trải nghiệm khách hàng

1. Quét QR tại bàn/quầy.
2. Nói hoặc nhập text.
3. Hoàn tất phản hồi (dữ liệu được xử lý ngầm: Voice -> STT -> NLP/ABSA).
4. Khách không cần chờ nhân viên tổng hợp, có thể tiếp tục trải nghiệm.
5. Nếu là yêu cầu hỗ trợ, nhân viên nhận alert và xử lý ngay.
6. Khách xem kết quả đánh giá (Feedback Recovery & Review Invitation).
7. Chọn chia sẻ công khai nếu được mời.
8. Nhận voucher nếu đủ điều kiện và hệ thống kiểm tra gian lận thành công.

*Lưu ý bảo mật (Nghị định 356/2025/NĐ-CP): Audio thô được dùng cho STT và ưu tiên xóa ngay sau khi chuyển đổi thành công. Dữ liệu định danh được băm (hash).*

---

## 🚀 Hướng dẫn cài đặt và chạy local

### Backend (Python 3.11+, FastAPI)

```bash
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env   # Cấu hình API key
uvicorn backend.main:app --reload --port 8000
```

### Web Client (Node 18+, React, Vercel)

```bash
cd apps/web-client
npm install
cp .env.example .env         # Cấu hình VITE_API_BASE_URL
npm run dev                  # http://localhost:5173
```

### Dashboard (Node 18+, React, Vercel)

```bash
cd apps/dashboard
npm install
cp .env.example .env
npm run dev                  # http://localhost:5174
```

---

## 🔐 Cấu hình biến môi trường

Vui lòng xem file `.env.example` để biết chi tiết. Các biến môi trường quan trọng:

- `FIREBASE_PROJECT_ID`, `FIREBASE_CLIENT_EMAIL`, `FIREBASE_PRIVATE_KEY`: Cấu hình kết nối Firestore đa khách hàng (Real-time Native NoSQL).
- `WHISPER_API_KEY`: Dành cho Groq Whisper STT (Tối ưu xử lý tạp âm quán ăn).
- `GEMINI_API_KEY`: Dành cho module phân tích NLP/ABSA (Gemini Flash-Lite tốc độ cao).

---

## 🧪 Kiểm thử (Testing)

Hệ thống có bộ unit test tự động (28/28 kịch bản PASS cho chống gian lận, voucher và pipeline).
```bash
pytest backend/tests/ -v
```

---

## 🛠️ Triển khai (Deployment)

- **Backend:** Triển khai qua dịch vụ Web Service của Render (Tối ưu tự động hóa CI/CD với Docker).
- **Frontend:** Tự động triển khai trên Vercel (Edge CDN).
- **Cơ sở dữ liệu:** Firebase Firestore.

---

## 🔮 Định hướng tương lai (Roadmap)

- **RFMS nâng cấp:** Mô hình RFMS hỗ trợ quản trị và dự báo rời bỏ hiện ở mức thử nghiệm. Chỉ nâng cấp chế độ huấn luyện bằng dữ liệu thật sau Pilot.
- **Hoàn thiện Review Invitation:** Hoàn thiện cơ chế kết nối nền tảng đánh giá theo khả năng tích hợp thực tế.
- **Mở rộng đa phương thức:** Nâng cấp phân tích đa phương thức ở mức mô hình chỉ sau khi dữ liệu Pilot đủ lớn.
- **Zalo ZNS:** Gửi tin nhắn cảnh báo/chăm sóc dựa trên ngưỡng rủi ro, dự kiến triển khai thương mại hóa.

---

## 📚 Tài liệu kỹ thuật chi tiết

- [CONTRIBUTING.md](CONTRIBUTING.md) - Quy định làm việc chung.
- [docs/backend-api.md](docs/backend-api.md) - Chi tiết Backend API.
- [docs/ai-pipeline.md](docs/ai-pipeline.md) - Chi tiết AI Pipeline.
- [docs/rfms-model.md](docs/rfms-model.md) - Chi tiết RFMS Model.
- [docs/database-schema.md](docs/database-schema.md) - Cấu trúc dữ liệu Firestore.
- [docs/api-contract.md](docs/api-contract.md) - Đặc tả API kết nối Frontend và Backend.
- [docs/frontend-apps.md](docs/frontend-apps.md) - Giao diện Frontend và Dashboard.
