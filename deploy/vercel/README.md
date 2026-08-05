# Deploy Hướng Dẫn — Vercel (Frontend)

> **Người soạn:** Đoàn Hoàng Việt (Trưởng nhóm)
> **Cập nhật:** 2026-08-05
> **Trạng thái:** Chuẩn bị sẵn — chưa deploy thật (chờ Tuấn code xong `apps/`)

---

## Tổng Quan Kiến Trúc Deploy

```
┌──────────────┐     HTTPS      ┌──────────────┐
│  web-client  │ ──────────────▶│   Backend    │
│  (Vercel)    │     API calls  │  (Render.com)│
├──────────────┤                ├──────────────┤
│  dashboard   │ ──────────────▶│  Firestore   │
│  (Vercel)    │  Direct SDK    │  (Firebase)  │
└──────────────┘                └──────────────┘
```

- **`apps/web-client`** → Deploy lên Vercel (project riêng hoặc cùng project, tùy cấu hình)
- **`apps/dashboard`** → Deploy lên Vercel (React app, KHÔNG phải Streamlit)
- **`backend/`** → Deploy lên Render.com (Tuyền phụ trách — xem `deploy/render/`)

---

## 1. Chuẩn Bị Trước Khi Deploy

### 1.1 Yêu cầu
- Tài khoản Vercel (đăng nhập bằng GitHub)
- Repo GitHub đã public hoặc Vercel có quyền truy cập repo private
- `apps/web-client/` và `apps/dashboard/` có code chạy được (build thành công ở local)

### 1.2 Kiểm tra local trước
```bash
# Web Client
cd apps/web-client
npm install
npm run build    # Phải thành công, không lỗi
npm run dev      # Kiểm tra chạy local OK

# Dashboard
cd apps/dashboard
npm install
npm run build
npm run dev
```

---

## 2. Biến Môi Trường (Environment Variables)

Khai báo trên Vercel Dashboard → Project Settings → Environment Variables.

### 2.1 Cho `apps/web-client`

| Biến | Giá trị | Ghi chú |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` (dev) → `https://<render-app>.onrender.com` (prod) | Đổi sang URL Render thật khi Tuyền deploy xong |
| `VITE_FIREBASE_PROJECT_ID` | `<firebase-project-id>` | Lấy từ Firebase Console |
| `VITE_FIREBASE_API_KEY` | `<firebase-web-api-key>` | Firebase Web API Key (public, OK để expose) |
| `VITE_FIREBASE_AUTH_DOMAIN` | `<project-id>.firebaseapp.com` | |
| `VITE_FIREBASE_STORAGE_BUCKET` | `<project-id>.appspot.com` | |

> ⚠️ Prefix `VITE_` bắt buộc nếu dùng Vite — nếu Tuấn dùng framework khác (Next.js → `NEXT_PUBLIC_`), cần điều chỉnh.

### 2.2 Cho `apps/dashboard`

| Biến | Giá trị | Ghi chú |
|---|---|---|
| `VITE_FIREBASE_PROJECT_ID` | `<firebase-project-id>` | Dashboard đọc trực tiếp Firestore, không qua backend API |
| `VITE_FIREBASE_API_KEY` | `<firebase-web-api-key>` | |
| `VITE_FIREBASE_AUTH_DOMAIN` | `<project-id>.firebaseapp.com` | |
| `VITE_DEFAULT_TENANT_ID` | `pho-ba-lan_1722500000000` | Tenant mặc định cho demo — đổi theo tenant pilot |

---

## 3. Cấu Hình Vercel

### 3.1 Tạo Project trên Vercel

**Cách 1 — 2 project riêng biệt (khuyến nghị cho demo):**
1. Vào [vercel.com/new](https://vercel.com/new) → Import Git Repository → chọn `VietGamer-UIT/Sentrix`
2. **Project 1 — Web Client:**
   - Root Directory: `apps/web-client`
   - Framework Preset: Vite (hoặc tự động detect)
   - Build Command: `npm run build`
   - Output Directory: `dist`
3. **Project 2 — Dashboard:**
   - Root Directory: `apps/dashboard`
   - Framework Preset: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`

**Cách 2 — Monorepo (nếu cần 1 domain):**
Dùng `vercel.json` với routing config — xem file `vercel.json` bên dưới.

### 3.2 Domain
- Web Client: `sentrix-client.vercel.app` (hoặc custom domain nếu có)
- Dashboard: `sentrix-dashboard.vercel.app`

---

## 4. File `vercel.json` (Tham Khảo)

> File này **chưa cần tạo** nếu dùng Cách 1 (2 project riêng). Chỉ cần nếu dùng Cách 2 monorepo hoặc cần rewrite rules cho SPA.

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

> Dùng rewrite rule trên nếu app dùng client-side routing (React Router) — đảm bảo mọi path đều trả `index.html` thay vì 404.

---

## 5. Checklist Deploy

### Trước khi deploy
- [ ] `apps/web-client` build thành công ở local (`npm run build`)
- [ ] `apps/dashboard` build thành công ở local
- [ ] Tuyền đã deploy backend lên Render.com và cho biết URL
- [ ] Đã tạo Firebase project và lấy config keys
- [ ] Đã khai báo env vars trên Vercel Dashboard

### Sau khi deploy
- [ ] Truy cập URL Vercel → web-client load được
- [ ] Truy cập URL Vercel → dashboard load được
- [ ] Web Client gọi `GET /health` đến backend Render → trả `200 OK`
- [ ] Web Client gửi feedback (text) → nhận `202 Accepted`
- [ ] Dashboard đọc được data từ Firestore (real-time listener hoạt động)
- [ ] Test trên điện thoại (quét QR → mở web-client → ghi âm)

---

## 6. Phối Hợp Với Tuyền (Backend Deploy — Render.com)

| Mốc | Hành động | Ai |
|---|---|---|
| Tuyền deploy backend thành công | Gửi URL Render cho Việt | Tuyền |
| Nhận URL Render | Cập nhật `VITE_API_BASE_URL` trên Vercel | Việt |
| Xác nhận frontend gọi được backend | Test `GET /health` + `POST /feedback` | Việt |
| Tất cả OK | Gửi URL cuối cho cả nhóm + chuẩn bị demo | Việt |

> **Ghi chú:** File `deploy/render/` do Tuyền phụ trách. Việt chỉ đọc, không tự sửa. Nếu cần thêm config render, nhắn Zalo nhóm.

---

## 7. Troubleshooting

| Vấn đề | Nguyên nhân thường gặp | Cách xử lý |
|---|---|---|
| Build fail trên Vercel | Thiếu env vars hoặc dependency | Kiểm tra Build Logs, thêm env vars |
| CORS error khi gọi API | Backend chưa cho phép domain Vercel | Tuyền thêm domain vào `allow_origins` trong `main.py` |
| Firestore permission denied | Security Rules chặn | Kiểm tra Rules trong Firebase Console, đảm bảo auth đúng |
| 404 khi refresh trang | Client-side routing không có rewrite | Thêm `vercel.json` với rewrite rule |
| API timeout | Render free tier cold start (~30s) | Chờ lần đầu, hoặc nâng lên paid tier |
