# LUẬT CHƠI GIT & GITHUB CỦA TEAM SENTRIX (DÀNH CHO NGƯỜI MỚI TỪ CON SỐ 0)

Để làm việc nhóm không bị "giẫm chân" lên nhau, mất code của nhau hay lỗi tùm lum, cả team **BẮT BUỘC** phải tuân thủ nghiêm ngặt quy trình dưới đây. Không có ngoại lệ!

## 🔴 3 NGUYÊN TẮC TỬ TỬ QUYẾT 🔴
1. **CẤM ĐỤNG VÀO NHÁNH `main`**: Nhánh `main` là code "sạch" và "chạy được". Cấm tuyệt đối việc bạn code trực tiếp và push thẳng lên `main`.
2. **MỖI VIỆC MỘT NHÁNH**: Khi bắt đầu làm một tính năng mới (ví dụ: làm trang đăng nhập), BẮT BUỘC phải tạo một nhánh (branch) mới để làm.
3. **REVIEW QUA PULL REQUEST (PR)**: Code xong ở nhánh của mình, phải đẩy lên GitHub và bấm nút "Tạo Pull Request". Việt (Trưởng nhóm) sẽ xem code, nếu OK mới được gộp (Merge) vào `main`.

---

## 🛠️ HƯỚNG DẪN TỪNG BƯỚC (CỨ LÀM THEO LÀ SỐNG)

Mỗi ngày mở máy tính lên làm việc, hãy làm ĐÚNG thứ tự sau:

### Bước 1: Cập nhật code mới nhất từ team về máy
Trước khi làm gì, phải chắc chắn máy bạn đang có bản code mới nhất từ nhánh `main`.
```bash
git checkout main
git pull origin main
```
*Giải thích: Đứng ở nhánh main, kéo (pull) toàn bộ code mới nhất từ trên mạng (origin) về máy.*

### Bước 2: Tạo nhánh riêng cho công việc của bạn
**QUY TẮC ĐẶT TÊN NHÁNH:** `feature/<tên-bạn>-<việc-đang-làm>` (Viết thường, không dấu, dùng gạch ngang).
*Ví dụ: `feature/tuyen-viet-api-login`, `feature/viet-giao-dien-home`, `feature/tuan-tai-lieu-ui`*
```bash
git checkout -b feature/ten-cua-ban-viec-se-lam
```
*Giải thích: Lệnh này giúp bạn tạo ra một nhánh mới từ `main` và nhảy sang đó luôn. Từ giờ bạn sửa code thì chỉ ảnh hưởng trên nhánh này, `main` vẫn an toàn.*

### Bước 3: Làm việc trong LÃNH ĐỊA của bạn
Hãy nhớ: Tuyền chỉ code trong `backend/`, Tuấn code trong `apps/` và `design/`, Việt quản lý cấu hình `deploy/` và bao quát toàn hệ thống.
Code xong một đoạn nhỏ (ví dụ: xong cái nút bấm, xong 1 hàm API), hãy lưu lại (Commit).
```bash
git add .
git commit -m "feat: <mô tả bạn vừa làm gì>"
```
**Quy tắc viết Message Commit:** Rõ ràng, dễ hiểu. Ví dụ: `git commit -m "feat: tao giao dien quet QR"` hoặc `git commit -m "fix: sua loi api dang nhap"`. Đừng viết "update", "asdasd" - Việt sẽ không duyệt!

### Bước 4: Đẩy code của bạn lên GitHub
Xong việc của ngày hôm đó, hãy đẩy nhánh của bạn lên GitHub.
```bash
git push origin feature/ten-cua-ban-viec-se-lam
```

### Bước 5: Yêu cầu gộp code (Pull Request - PR)
1. Lên trang GitHub `Sentrix`.
2. Bạn sẽ thấy một thông báo màu vàng hiện ra ghi là "Compare & pull request". Bấm vào đó!
3. Ở phần mô tả, viết ngắn gọn: "Tôi đã làm tính năng X, nhờ Việt review". 
4. Bấm **Create pull request**.
5. Nhắn tin vào Zalo nhóm: "Việt ơi, duyệt PR cho tui nha!".

### Bước 6: Review & Merge (Chỉ dành cho Việt)
Việt vào xem PR. Nếu code tốt, Việt bấm **Merge pull request**. Lúc này code của bạn chính thức được đưa vào `main`! Sau đó xóa cái nhánh `feature/...` đó đi cho sạch.

---

## 💥 NẾU BỊ CONFLICT (XUNG ĐỘT) THÌ SAO?
Conflict xảy ra khi **2 người cùng sửa 1 dòng code trong cùng 1 file**. 
*Nếu mọi người tuân thủ đúng luật "Lãnh địa" thì tỉ lệ bị conflict là 0%.*

Nhưng nếu lỡ bị, Git sẽ báo lỗi `Can't automatically merge` khi tạo PR.
**Cách giải quyết cực nhanh:**
1. Hú lên trong Zalo: "Ê tao với mày bị conflict file README kìa!".
2. Gọi Việt vào xem. Trên GitHub nó sẽ bôi đỏ bôi xanh chỗ khác nhau.
3. Cả 3 cùng thống nhất xem lấy code của ai (hoặc gộp cả 2). Việt sẽ nhấn nút Resolve Conflict trên GitHub, sửa lại cho đúng ý, rồi Merge. 
4. Bình tĩnh, không được tự ý xóa code của người khác!
