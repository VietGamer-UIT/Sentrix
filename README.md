# Sentrix - AI-Powered Multimodal Customer Experience Analytics Platform

Chào mừng team Sentrix! Đây là dự án của 3 thành viên: **Việt**, **Tuyền**, và **Tuấn**.
Để đảm bảo tiến độ và không bị xung đột code (conflict), repository này được thiết kế với **CÁC NGUYÊN TẮC CHỐT CỨNG** theo đúng thế mạnh của từng người.

## 🚨 PHÂN CÔNG VÀ "LÃNH ĐỊA" (CẤM VI PHẠM)

Hệ thống được chia thành các "lãnh địa" rõ ràng. **Nguyên tắc tối thượng:** Ai phụ trách mảng nào thì chỉ được sửa code ở mảng đó. CẤM TUYỆT ĐỐI việc sửa code trong thư mục của người khác nếu chưa được sự đồng ý.

- 👑 **ĐOÀN HOÀNG VIỆT (Trưởng nhóm / DevOps / Full-stack Support)**
  - Phụ trách chính: Khởi xướng ý tưởng, Quản trị mô hình kinh doanh (BMC), Thuyết trình (Pitching).
  - Kỹ thuật: Quản lý API Keys, chịu trách nhiệm Deploy toàn bộ hệ thống lên Vercel & Render, hỗ trợ xử lý lỗi khó cho cả Frontend lẫn Backend.
  - Lãnh địa: `deploy/`, các file cấu hình gốc như `.env.example`, `firestore.rules`, `.gitignore`, `render.yaml`.
  
- 🎨 **NGUYỄN QUỐC TUẤN (Frontend Developer & UX/UI Designer)**
  - Phụ trách chính: Toàn bộ giao diện người dùng (Web-Client cho khách và Dashboard cho chủ quán). Thiết kế UI/UX trên Figma và code React.
  - Lãnh địa: `apps/` (React, Vite, Tailwind) và `design/`.

- 🧠 **NGUYỄN THANH TUYỀN (Backend Developer & AI Engineer)**
  - Phụ trách chính: Kiến trúc hệ thống API, xây dựng Data Pipeline, phát triển lõi AI đa phương thức (Whisper, Gemini ABSA, Librosa) và thiết kế Database (Firestore Multi-tenant).
  - Lãnh địa: `backend/` (Python, FastAPI).

- 📚 `docs/`: Tài liệu chung (ai phụ trách mảng nào thì viết mảng đó).

> **Tips:** Nhờ việc chia "lãnh địa" này, khi các bạn làm việc và đẩy code lên, sẽ GẦN NHƯ KHÔNG BAO GIỜ bị conflict code với nhau!

## 🚀 Hướng dẫn cài đặt cho từng người

Mọi người sau khi clone code về (`git clone https://github.com/VietGamer-UIT/Sentrix.git`), hãy đi vào thư mục của mình và đọc file `README.md` trong đó để biết phải làm gì tiếp theo.

1. **Tuấn:** Đọc file `apps/README.md` để xem cách chạy Frontend.
2. **Tuyền:** Đọc file `backend/README.md` để xem cấu trúc API và cách chạy Backend.
3. **Việt:** Theo dõi các file trong `deploy/` và cấu hình server, Database.

## 📚 Mới dùng Git? Đọc ngay CONTRIBUTING.md
Nếu bạn chưa biết cách tạo nhánh (branch), lưu code (commit), và đẩy code (push) qua Pull Request, HÃY ĐỌC NGAY file `CONTRIBUTING.md`. Đó là luật chơi của team mình!
