import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import OverviewPage from './pages/OverviewPage.jsx'
import FeedbacksPage from './pages/FeedbacksPage.jsx'
import CustomersPage from './pages/CustomersPage.jsx'

/**
 * App.jsx — Routing dashboard
 *
 * Routes:
 *   /          → Tổng quan (KPI + biểu đồ cảm xúc + feed feedback mới)
 *   /feedbacks → Toàn bộ phản hồi (có lọc theo sentiment, location, thời gian)
 *   /customers → Danh sách khách hàng + P_churn risk level
 *
 * Tất cả routes đều wrap trong <Layout> để có sidebar + header chung.
 */
function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<OverviewPage />} />
        <Route path="feedbacks" element={<FeedbacksPage />} />
        <Route path="customers" element={<CustomersPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default App
