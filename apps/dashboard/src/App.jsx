import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext.jsx'
import Layout from './components/Layout.jsx'
import LoginPage from './pages/LoginPage.jsx'
import OverviewPage from './pages/OverviewPage.jsx'
import FeedbacksPage from './pages/FeedbacksPage.jsx'
import CustomersPage from './pages/CustomersPage.jsx'
import FraudMonitorPage from './pages/FraudMonitorPage.jsx'
import VoucherConfigPage from './pages/VoucherConfigPage.jsx'
import OperatingCostPage from './pages/OperatingCostPage.jsx'

/**
 * App.jsx — Routing dashboard với Auth Guard
 *
 * Routes:
 *   /login      → LoginPage (Google Sign-In)
 *   /           → OverviewPage — KPI tổng quan + charts
 *   /feedbacks  → FeedbacksPage — bảng phản hồi + filter
 *   /customers  → CustomersPage — danh sách khách + p_churn
 *
 * Guard: Chưa đăng nhập → redirect về /login
 */
function App() {
  const { user, loading } = useAuth()

  // Đang kiểm tra auth state (Firebase cần 1 tick)
  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--color-bg-main)',
        flexDirection: 'column',
        gap: '16px',
      }}>
        <div style={{
          width: 40, height: 40,
          border: '3px solid rgba(255,255,255,0.1)',
          borderTopColor: '#00C2FF',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }} />
        <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: '0.875rem' }}>
          Đang kiểm tra phiên đăng nhập...
        </span>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    )
  }

  return (
    <Routes>
      {/* Route đăng nhập — public */}
      <Route
        path="/login"
        element={user ? <Navigate to="/" replace /> : <LoginPage />}
      />

      {/* Routes bảo vệ bởi auth */}
      <Route
        path="/"
        element={user ? <Layout /> : <Navigate to="/login" replace />}
      >
        <Route index element={<OverviewPage />} />
        <Route path="feedbacks" element={<FeedbacksPage />} />
        <Route path="customers" element={<CustomersPage />} />
        {/* Module 4 — 3 Panel mới */}
        <Route path="fraud" element={<FraudMonitorPage />} />
        <Route path="voucher-config" element={<VoucherConfigPage />} />
        <Route path="operating-cost" element={<OperatingCostPage />} />
      </Route>

      {/* Catch-all */}
      <Route path="*" element={<Navigate to={user ? '/' : '/login'} replace />} />
    </Routes>
  )
}

export default App
