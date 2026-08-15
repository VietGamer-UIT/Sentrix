import { Routes, Route, Navigate } from 'react-router-dom'
import LandingPage from './pages/LandingPage.jsx'
import RecordingPage from './pages/RecordingPage.jsx'
import ConfirmationPage from './pages/ConfirmationPage.jsx'
import SpinPage from './pages/SpinPage.jsx'
import VoucherPage from './pages/VoucherPage.jsx'

/**
 * App.jsx — Điều phối 5 màn hình theo user-flow.md:
 * Bước 2: / → LandingPage       (hiển thị tên quán, CTA ghi âm)
 * Bước 3: /record → RecordingPage (Web Audio API, 15s max)
 * Bước 4: /done → ConfirmationPage (optimistic UI, gửi ngầm)
 * Bước 5: /spin → SpinPage       (vòng quay may mắn — MOCK)
 * Bước 6: /voucher → VoucherPage  (kết quả + mã voucher)
 *
 * Query params từ QR code: ?tenant_id=...&location=...
 * Các params này được truyền qua từng route bằng URL search params
 */
import DarkModeToggle from './components/DarkModeToggle.jsx'

function App() {
  return (
    <>
      <DarkModeToggle />
      <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/record" element={<RecordingPage />} />
      <Route path="/done" element={<ConfirmationPage />} />
      <Route path="/spin" element={<SpinPage />} />
      <Route path="/voucher" element={<VoucherPage />} />
      {/* Fallback: mọi route lạ đều về trang chủ */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
    </>
  )
}

export default App
