# Hướng dẫn làm việc nhóm trên GitHub (Dành cho người mới)

Chào mừng team Sentrix! Vì chúng ta làm việc theo nhóm 3 người, việc tuân thủ quy trình Git là **BẮT BUỘC** để tránh mất code hoặc xung đột (conflict).

## 1. Quy tắc bắt buộc
- **KHÔNG BAO GIỜ** code và push trực tiếp lên nhánh `main`.
- Mỗi tính năng/công việc phải làm trên một nhánh riêng.
- Code xong phải mở Pull Request (PR) để Trưởng nhóm (Việt) review và merge.

## 2. Quy ước đặt tên nhánh
Tên nhánh phải viết thường, không dấu, dùng dấu gạch ngang `-`, theo cấu trúc:
`feature/<ten-nguoi>-<mo-ta-ngan>`

**Ví dụ:**
- `feature/tuyen-absa-pipeline`
- `feature/tuan-uiux-mockup`
- `feature/viet-dashboard-ui`

## 3. Quy trình chuẩn từng bước (Cực kỳ quan trọng)

Mỗi khi bắt đầu một việc mới, hãy làm theo đúng thứ tự này:

**Bước 1: Lấy code mới nhất từ nhánh main về máy**
```bash
git checkout main
git pull origin main
```

**Bước 2: Tạo nhánh mới cho công việc của bạn**
```bash
git checkout -b feature/ten-cua-ban-ten-cong-viec
```
*(Lưu ý: Bạn chỉ làm việc trong thư mục mà mình phụ trách)*

**Bước 3: Code và Lưu lại (Commit)**
Ghi lại những thay đổi thường xuyên. Message phải rõ ràng:
```bash
git add .
git commit -m "feat: viet giao dien dang nhap"
```

**Bước 4: Đẩy nhánh của bạn lên GitHub**
```bash
git push origin feature/ten-cua-ban-ten-cong-viec
```

**Bước 5: Tạo Pull Request (PR)**
Lên trang GitHub.com, bạn sẽ thấy nút "Compare & pull request". Bấm vào đó, viết mô tả những gì bạn đã làm, và yêu cầu **Việt** vào review. 

**Bước 6: Gộp code (Merge)**
Việt sẽ xem code, nếu OK sẽ bấm "Merge pull request" để đưa code vào nhánh `main`.

## 4. Xử lý Xung đột (Merge Conflict) cơ bản
Conflict xảy ra khi **2 người cùng sửa 1 dòng code trong cùng 1 file**. Git không biết nên lấy của ai.

**Ví dụ:**
Việt và Tuyền cùng sửa file `README.md` ở dòng số 5. Khi tạo PR, GitHub sẽ báo "Can't automatically merge".

**Cách xử lý:**
1. Việt (người duyệt PR) sẽ mở file bị conflict trên GitHub hoặc trên máy.
2. File sẽ trông như thế này:
   ```text
   <<<<<<< HEAD
   Dòng code của Việt viết
   =======
   Dòng code của Tuyền viết
   >>>>>>> feature/tuyen-lam-gi-do
   ```
3. Việt quyết định giữ dòng nào (hoặc gộp cả 2), xóa các dấu `<<<<`, `====`, `>>>>` đi.
4. Lưu lại, commit và merge.

*Lời khuyên: Để hạn chế conflict, hãy **chỉ làm việc trong thư mục của mình**.*
