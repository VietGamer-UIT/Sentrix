# Frontend Apps Architecture

Tài liệu mô tả kiến trúc và quy định phát triển của các ứng dụng Frontend trong hệ thống Sentrix.

---

## QUY TẮC PHÁT TRIỂN FRONTEND

1. Code Frontend phải chia Component rõ ràng, module hóa cao.
2. Tuân thủ thiết kế Figma và tài liệu UX/UI.
3. Tách biệt hoàn toàn với Backend, chỉ giao tiếp thông qua API đã thống nhất. Tránh thay đổi trực tiếp `backend/` từ phía frontend.

---

## NỘI DUNG 2 ỨNG DỤNG

- `web-client/`: Giao diện cho khách hàng (Quét QR -> Ghi âm/Gõ text phản hồi -> Vòng quay may mắn).
- `dashboard/`: Bảng điều khiển cho chủ quán (Xem thống kê, cảnh báo nhân viên, danh sách khách rủi ro Churn).

---

## NGUỒN THAM KHẢO BẮT BUỘC KHI CODE

Không tự sáng tác thêm tính năng. Đây là nguồn sự thật duy nhất:

| Tài liệu | Mục đích |
|---|---|
| `docs/user-flow.md` | Luồng UX từng bước cho `web-client/` |
| `docs/dashboard-ux.md` | Layout và widget cụ thể cho `dashboard/` |
| `docs/figma-link.md` | Link Figma tham khảo phong cách UI |
| `docs/database-schema.md` | Tên field Firestore chính xác |

---

## TRẠNG THÁI TÍCH HỢP

| Endpoint/Dữ liệu | Trạng thái | Ghi chú |
|---|---|---|
| `GET /health` | Hoạt động | Kiểm tra server sống |
| `POST /api/v1/feedback` | Hoạt động | Nhận audio/text từ khách, trả về `request_id` và trạng thái |
| Dữ liệu Dashboard (Firestore) | Hoạt động (Realtime) | Sử dụng onSnapshot để nhận dữ liệu thời gian thực. Cần đặt `VITE_USE_MOCK_FIRESTORE=false` để dùng dữ liệu thật. |
| Firebase Google Sign-In | Hoạt động | Đăng nhập an toàn cho chủ quán |

---

## TIẾN ĐỘ FRONTEND

- [x] Giai đoạn 1: Cập nhật tài liệu minh bạch về thay đổi phân công
- [x] Giai đoạn 2: Dựng khung React cho `web-client/`
- [x] Giai đoạn 3: Build đủ màn hình `web-client/` theo `user-flow.md`
- [x] Giai đoạn 4: Nối `web-client/` với `POST /api/v1/feedback` thật
- [x] Giai đoạn 5: Build `dashboard/`
- [x] Giai đoạn 6: Kết nối `dashboard/` Firebase thật qua onSnapshot và Google Sign-In
