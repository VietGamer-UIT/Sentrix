import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { MOCK_TENANT } from '../mocks/firestoreMock.js'

const tenantName = MOCK_TENANT.business_name

const navItems = [
  { to: '/', icon: '📊', label: 'Tổng quan', end: true },
  { to: '/feedbacks', icon: '💬', label: 'Phản hồi' },
  { to: '/customers', icon: '👥', label: 'Khách hàng' },
]

/**
 * Layout — App shell chung: sidebar trái + header trên + <Outlet> content
 */
function Layout() {
  const location = useLocation()
  const currentPage = navItems.find(n => n.end ? location.pathname === '/' : location.pathname.startsWith('/' + n.to.slice(1)))

  return (
    <div className="app-shell">
      {/* === Sidebar === */}
      <aside className="sidebar">
        {/* Logo */}
        <div className="sidebar-logo">
          <svg width="28" height="28" viewBox="0 0 64 64" fill="none">
            <defs>
              <linearGradient id="slg" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#00C2FF"/>
                <stop offset="100%" stopColor="#7C3AED"/>
              </linearGradient>
            </defs>
            <rect width="64" height="64" rx="16" fill="url(#slg)"/>
            <rect x="26" y="14" width="12" height="20" rx="6" fill="white"/>
            <path d="M18 32c0 7.7 6.3 14 14 14s14-6.3 14-14" stroke="white" strokeWidth="2.5" fill="none" strokeLinecap="round"/>
            <line x1="32" y1="46" x2="32" y2="52" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
            <line x1="26" y1="52" x2="38" y2="52" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
          </svg>
          <span className="sidebar-logo-text">Sentrix</span>
        </div>

        {/* Tên quán */}
        <div style={{ padding: '0 var(--spacing-lg) var(--spacing-md)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
          <div style={{ fontWeight: 700, color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
            {tenantName}
          </div>
          <div>Gói Pro · Đang hoạt động</div>
        </div>

        <div className="nav-separator" />

        {/* Nav Items */}
        <nav className="sidebar-nav">
          {navItems.map(({ to, icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
            >
              <span className="nav-icon">{icon}</span>
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Footer sidebar */}
        <div style={{ padding: 'var(--spacing-lg)', marginTop: 'auto', borderTop: '1px solid var(--color-border)' }}>
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', lineHeight: 1.8 }}>
            <div style={{ fontWeight: 600, color: 'var(--color-text-secondary)' }}>⚠️ Mock Data</div>
            <div>Kết nối Firestore thật khi Tuyền setup Firebase</div>
          </div>
        </div>
      </aside>

      {/* === Main Content === */}
      <div className="main-content">
        {/* Top Header */}
        <header className="top-header">
          <h1 className="header-title">
            {currentPage?.icon} {currentPage?.label ?? 'Dashboard'}
          </h1>
          <div className="header-meta">
            <span className="live-badge">
              <span className="live-dot" />
              Live
            </span>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              {new Date().toLocaleDateString('vi-VN', { weekday: 'short', day: '2-digit', month: '2-digit', year: 'numeric' })}
            </span>
          </div>
        </header>

        {/* Page outlet */}
        <main className="page-content fade-in">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout
