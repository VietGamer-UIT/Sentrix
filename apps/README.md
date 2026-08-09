# 👑 LÃNH ĐỊA FRONTEND & DASHBOARD

> **📝 Cập nhật 2026-08-05:** Theo quyết định của trưởng nhóm **Việt**, frontend (`apps/`) hiện do **Tuấn** đảm nhận code trong giai đoạn này.
> Việt sẽ tiếp quản lại sau khi backend (Tuyền) và frontend (Tuấn) đã có hình hài hoàn chỉnh.

**Người code hiện tại:** Nguyễn Quốc Tuấn (`nguyenquoctuangm-code`)
**Người cai quản gốc:** Đoàn Hoàng Việt (Trưởng nhóm) — sẽ tiếp quản lại sau giai đoạn này.

---

## 📌 QUY TẮC CỦA LÃNH ĐỊA NÀY

1. **Chỉ Tuấn (tạm thời) và Việt (sau này) được sửa code ở đây.** Tuyền nếu cần thay đổi gì liên quan đến frontend thì nhắn Zalo cho Tuấn.
2. Code Frontend phải chia Component rõ ràng, không viết nguyên 1 file 1000 dòng.
3. Tuân thủ tuyệt đối thiết kế Figma và tài liệu UX/UI mà Tuấn đã chốt trong `design/ux-ui/`. Nếu thấy thiết kế vô lý, cập nhật `design/ux-ui/` trước, code theo sau.
4. **KHÔNG được đụng vào `backend/`** dù chỉ để "tiện tay sửa" — chỉ được đọc để lấy thông tin API/schema.

---

## 🎯 NỘI DUNG 2 ỨNG DỤNG

- `web-client/`: Giao diện cho **khách hàng** (Quét QR → Ghi âm phản hồi → Vòng quay may mắn).
- `dashboard/`: Bảng điều khiển cho **chủ quán** (Xem KPI, sentiment, danh sách khách rủi ro Churn).

---

## 📚 NGUỒN THAM KHẢO BẮT BUỘC KHI CODE

Không tự sáng tác thêm tính năng. Đây là nguồn sự thật duy nhất:

| Tài liệu | Mục đích |
|---|---|
| `design/ux-ui/01-customer-flow/user-flow.md` | Luồng UX từng bước cho `web-client/` (6 bước, kèm rủi ro drop-off) |
| `design/ux-ui/03-dashboard-reference/de-xuat-ux.md` | Layout và widget cụ thể cho `dashboard/` |
| `design/ux-ui/figma-link.md` | Link Figma tham khảo phong cách UI (DashStack) |
| `backend/db/schema.md` | Tên field Firestore chính xác — mock data PHẢI khớp field này |

---

## ⚡ TRẠNG THÁI API BACKEND (quan trọng — đọc trước khi code)

| Endpoint | Trạng thái | Ghi chú |
|---|---|---|
| `GET /health` | ✅ **Có thật, hoạt động** | Kiểm tra server sống |
| `POST /api/v1/feedback` | ✅ **Có thật, hoạt động** | Nhận audio/text từ khách, trả về `request_id` + `status`. Dùng multipart/form-data |
| `POST /api/gamification/spin` | ❌ **CHƯA CÓ — dùng MOCK** | Chưa implement. Comment rõ `// MOCK` trong code, thay thật khi Tuyền báo xong |
| Firestore KPI / customers | ❌ **CHƯA CÓ — dùng MOCK** | Dùng mock data khớp với `backend/db/schema.md` để build Dashboard trước |

> **Quy tắc mock:** Mọi mock data phải dùng **đúng tên field** từ `backend/db/schema.md`. Không tự đặt tên field khác, tránh phải refactor lại khi nối thật.

---

## ✅ CHECKLIST CÔNG VIỆC (Tuấn)

- [x] Giai đoạn 1: Cập nhật tài liệu minh bạch về thay đổi phân công
- [x] Giai đoạn 2: Dựng khung React (Vite) cho `web-client/`
- [x] Giai đoạn 3: Build đủ 5 màn hình `web-client/` theo `user-flow.md`
- [x] Giai đoạn 4: Nối `web-client/` với `POST /api/v1/feedback` thật
- [x] Giai đoạn 5: Build `dashboard/` với mock data khớp schema Firestore
- [x] Giai đoạn 6: Kết nối `dashboard/` Firebase thật — onSnapshot Firestore, Google Sign-In, `sentrix-demo-164`
