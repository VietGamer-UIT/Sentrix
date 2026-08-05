# Kịch Bản Demo — Sentrix (AISC'26)

> **Người soạn:** Đoàn Hoàng Việt (Trưởng nhóm & Thuyết trình viên)
> **Cập nhật:** 2026-08-05
> **Tham chiếu:** `design/logistics/cheat-sheet-giam-khao.md`, `design/logistics/ke-hoach-demo-pilot.md`

---

## Tổng Quan Luồng Demo

```
Giám khảo quét QR ──▶ Web Client mở ──▶ Nhấn ghi âm ──▶ Nói 15s
                                                              │
        Dashboard cập nhật ◀── Backend xử lý ◀── Nhấn "Gửi" ◀┘
              │
              ▼
     Xem ABSA + Churn ──▶ (Tuỳ chọn) ZNS trigger demo
```

**Thời lượng dự kiến:** 3–5 phút demo live + 2 phút hỏi đáp

---

## Kịch Bản Chi Tiết (5 Bước)

### Bước 1 — Quét QR (30 giây)

**Việt nói:**
> *"Em mời anh/chị mở Camera hoặc Zalo và quét mã QR trên bàn. Đây chính xác là trải nghiệm một khách hàng khi ngồi tại quán."*

**Trên màn hình giám khảo:**
- Mở Camera/Zalo → quét QR → trình duyệt mở Web Client
- Web Client load ngay, không yêu cầu đăng nhập/đăng ký

**Backup:** Nếu QR không quét được (ánh sáng, camera lỗi) → có sẵn link ngắn ghi trên standee.

> **[TODO — Cần URL deploy thật từ Vercel để in QR]**

---

### Bước 2 — Ghi Âm Phản Hồi (45 giây)

**Việt nói:**
> *"Bây giờ anh/chị nhấn nút micro và nói một câu nhận xét bất kỳ. Em gợi ý vài câu mẫu."*

**Câu mẫu gợi ý (chọn 1, tùy tình huống):**

| # | Câu mẫu | Mục đích demo |
|---|---|---|
| 1 | *"Đồ uống ở đây pha hơi nhạt và nhân viên phục vụ hơi chậm"* | Demo phát hiện **2 khía cạnh** (món ăn + tốc độ phục vụ), cả hai tiêu cực |
| 2 | *"Không gian quán đẹp lắm, nhưng giá hơi chát so với chất lượng"* | Demo **tích cực + tiêu cực** cùng lúc (không gian vs giá cả) |
| 3 | *"Phục vụ tốt quá ha, đợi có 20 phút mà"* | Demo **mỉa mai** — giọng khen nhưng ý chê → `is_sarcasm: true` |
| 4 | *"Nhân viên cười tươi, món ăn ngon, sẽ quay lại"* | Demo phản hồi **hoàn toàn tích cực** → P_churn thấp |

> **Khuyến nghị:** Dùng câu #3 (mỉa mai) nếu chỉ demo 1 lần — đây là điểm nhấn công nghệ ấn tượng nhất, giám khảo dễ nhớ.

**Trên màn hình giám khảo:**
- Nhấn nút micro → đèn ghi âm sáng
- Nói xong → nhấn dừng
- Nhấn "Gửi" → loading spinner

> **[TODO — Test thử câu mẫu với sản phẩm thật để xác nhận ABSA nhận diện đúng]**

---

### Bước 3 — Vòng Quay May Mắn (30 giây)

**Việt nói:**
> *"Sau khi gửi phản hồi, khách hàng được chơi Vòng quay may mắn. Đây là cơ chế Gamification để tăng tỷ lệ phản hồi và thu thập số điện thoại — zero-party data hợp lệ."*

**Trên màn hình giám khảo:**
- Vòng quay xuất hiện tự động sau khi gửi feedback
- Giám khảo nhấn quay → animation quay → trúng mã giảm giá
- Hiển thị mã voucher (demo/mock)

> ⚠️ **Endpoint `POST /api/gamification/spin` chưa có thật** — hiện dùng mock data phía frontend.

---

### Bước 4 — Dashboard Real-time (60 giây) ⭐ **Phần quan trọng nhất**

**Việt nói:**
> *"Bây giờ em mời anh/chị nhìn sang màn hình laptop. Đây là Dashboard dành cho chủ quán. Phản hồi vừa rồi đã được AI xử lý và hiển thị ngay."*

**Trên laptop (Dashboard đã mở sẵn):**

**Điểm cần chỉ ra cho giám khảo:**
1. **Feedback vừa gửi** xuất hiện ở đầu danh sách (real-time, không cần refresh)
2. **ABSA breakdown:** Phân tích theo từng khía cạnh với sentiment score
   - Ví dụ câu #3: `toc_do_phuc_vu: negative (-0.82)` + `nhan_vien: positive (0.45, confidence thấp)`
3. **Phát hiện mỉa mai:** `is_sarcasm: true` — "Hệ thống nhận ra giọng khen nhưng ý chê"
4. **Churn alert:** Nếu khách hàng này đã có lịch sử, P_churn cập nhật
5. **KPI tổng quan:** Điểm cảm xúc trung bình, số feedback hôm nay

**Việt nói (kết):**
> *"Chủ quán không cần đọc 100 review — hệ thống tự bóc tách vấn đề và cho biết nhân viên nào cần cải thiện, món nào đang bị chê."*

> **[TODO — Cần test E2E toàn luồng với data thật. Dashboard phải đọc được Firestore real-time.]**

---

### Bước 5 — ZNS Auto-Rescue (30 giây, tuỳ chọn)

**Việt nói:**
> *"Khi hệ thống phát hiện khách hàng có rủi ro rời bỏ cao — ví dụ P_churn trên 85% — nó tự động gửi voucher xin lỗi qua Zalo cho khách, ngay lập tức, trước khi họ ra khỏi quán."*

**Demo:**
- Chỉ vào Dashboard nơi hiển thị cảnh báo churn
- Giải thích: "Zalo ZNS sẽ gửi tin nhắn tự động đến SĐT khách đã nhập ở bước Vòng quay"

> ⚠️ **ZNS thật cần Zalo Business account + template đã duyệt.** Trong demo AISC'26, có thể mock bằng screenshot/mockup tin nhắn Zalo nếu chưa có tài khoản ZNS thật.

---

## Phương Án Dự Phòng (Backup Plan)

| Rủi ro | Giải pháp |
|---|---|
| **Wifi hội trường lag** | Phát hotspot 4G từ điện thoại cá nhân (đã đăng ký gói data tốc độ cao) |
| **Backend Render cold start lâu** | Ping `GET /health` trước demo 5 phút để warm up |
| **Whisper/Gemini API lỗi** | Có video demo đã quay sẵn, phát thay demo live |
| **Điện thoại giám khảo không quét được QR** | Chuẩn bị sẵn link ngắn + tab browser đã mở sẵn trên điện thoại dự phòng |
| **Dashboard không load real-time** | Refresh thủ công + giải thích "trong production sẽ tự cập nhật" |

*(Nguồn: design/logistics/ke-hoach-demo-pilot.md §4)*

---

## Checklist Trước Ngày Demo

### Thiết bị
- [ ] Laptop sạc đầy + sạc dự phòng
- [ ] Điện thoại có 4G tốc độ cao
- [ ] QR standee in sẵn (đúng URL deploy)
- [ ] Cáp kết nối laptop ↔ projector (HDMI/USB-C)

### Phần mềm
- [ ] Dashboard mở sẵn trên tab riêng, đã đăng nhập đúng tenant demo
- [ ] Web Client mở sẵn trên tab khác để backup
- [ ] Backend đã warm up (`GET /health` trả `200`)
- [ ] Video demo backup đã quay và lưu offline

### Nội dung
- [ ] Thuộc lòng 4 câu mẫu
- [ ] Thuộc lòng số liệu chính (760K tỷ, 333.600, 5-25x, 88.9%, 57 KH)
- [ ] Đã luyện demo ít nhất 1 lần trước ngày thi
- [ ] Pitch deck số liệu khớp cheat-sheet giám khảo

> **[TODO — Luyện demo thử khi Tuấn + Tuyền xong sản phẩm. Quay video backup.]**
