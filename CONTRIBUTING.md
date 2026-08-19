# Git Workflow — Sentrix

Quy trình làm việc với Git để đảm bảo `main` luôn ổn định và dễ rollback khi cần.

---

## Nguyên tắc cốt lõi

1. **`main` là nhánh production** — không commit thẳng vào `main`
2. **Mỗi nhóm việc = 1 nhánh** — tạo nhánh mới khi bắt đầu fix/feature
3. **Commit thường xuyên** — mỗi đơn vị nhỏ hoàn chỉnh là 1 commit
4. **Merge vào `main` qua PR** — để có lịch sử rõ ràng, dễ revert

---

## Quy trình hằng ngày

### 1. Sync code mới nhất

```bash
git checkout main
git pull origin main
```

### 2. Tạo nhánh làm việc

**Quy tắc đặt tên:**

| Loại việc | Prefix | Ví dụ |
|---|---|---|
| Tính năng mới | `feature/` | `feature/dashboard-churn-chart` |
| Sửa bug | `fix/` | `fix/absa-timeout-rfms-input` |
| Tài liệu | `docs/` | `docs/update-api-contract` |
| Cải thiện hiệu suất | `perf/` | `perf/parallel-stt-librosa` |

```bash
git checkout -b fix/ten-nhanh-mo-ta-ngan
```

### 3. Code & Commit

```bash
git add .
git commit -m "fix: tang ABSA timeout 10s len 25s tranh fallback gia"
```

**Cấu trúc commit message:**
```
<type>(<scope>): <mô tả ngắn gọn tiếng Việt hoặc tiếng Anh>

[body tùy chọn — giải thích lý do nếu phức tạp]
```

**Các `type` hợp lệ:**

| Type | Dùng khi |
|---|---|
| `feat` | Thêm tính năng mới |
| `fix` | Sửa bug |
| `refactor` | Tái cấu trúc không thay đổi behavior |
| `docs` | Chỉ sửa tài liệu |
| `perf` | Cải thiện hiệu suất |
| `test` | Thêm/sửa test |
| `chore` | Cập nhật config, dependencies |

**Ví dụ commit tốt:**
```bash
git commit -m "fix(rfms): lay frequency va recency_days that tu Firestore thay vi hardcode"
git commit -m "fix(security): xoa allow update unauthenticated trong firestore.rules"
git commit -m "feat(spin): goi API backend thay vi mock random o client"
```

**Tránh:**
```bash
git commit -m "update"      # ❌ không rõ làm gì
git commit -m "fix bug"     # ❌ bug nào?
git commit -m "WIP"         # ❌ chỉ dùng khi tạm lưu, không push lên main
```

### 4. Push nhánh lên GitHub

```bash
git push origin fix/ten-nhanh-mo-ta-ngan
```

### 5. Tạo Pull Request (PR)

1. Vào GitHub → bấm **"Compare & pull request"**
2. Tiêu đề PR: ngắn gọn, mô tả nhóm changes
3. Mô tả PR: liệt kê các file đã sửa và lý do
4. Merge vào `main` khi PR sẵn sàng

---

## Xử lý conflict

Conflict xảy ra khi cùng 1 dòng bị sửa ở 2 nơi. Cách xử lý:

```bash
# Đang ở nhánh fix/ten-nhanh, bị conflict với main
git checkout main
git pull origin main
git checkout fix/ten-nhanh
git merge main          # merge main vào nhánh của mình để resolve

# Mở file bị conflict, tìm marker <<<<<<< HEAD
# Giữ code đúng, xóa markers
git add .
git commit -m "chore: resolve merge conflict with main"
git push origin fix/ten-nhanh
```

---

## Commit khẩn cấp (hotfix)

Khi cần sửa lỗi nghiêm trọng trực tiếp trên production:

```bash
git checkout main
git pull origin main
git checkout -b hotfix/mo-ta-loi-cap-bach
# ... sửa code ...
git add .
git commit -m "fix: [HOTFIX] mo ta loi cap bach"
git push origin hotfix/mo-ta-loi-cap-bach
# Tạo PR → merge ngay vào main
```

---

## Lịch sử nhánh hiện tại

| Nhánh | Mục đích |
|---|---|
| `main` | Production code — luôn chạy được |
| `fix/optimize-ai-pipeline-and-firestore` | Fix 11 bugs (BUG-01 → E3) — 2026-08-19 |

---

## Checklist trước khi tạo PR

- [ ] Code chạy được local (không lỗi import, không crash)
- [ ] Đã test tay case chính
- [ ] Commit message rõ ràng
- [ ] Không commit file `.env`, `serviceAccountKey.json`, `node_modules/`
- [ ] Firestore Rules đã update (nếu có): nhớ `firebase deploy --only firestore:rules`
