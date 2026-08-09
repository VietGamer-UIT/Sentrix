import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { useTenant } from '../mocks/useFirestore.js'
import { IS_MOCK } from '../mocks/useFirestore.js'

const navItems = [
  { to: '/', icon: '📊', label: 'Tổng quan', end: true },
  { to: '/feedbacks', icon: '💬', label: 'Phản hồi' },
  { to: '/customers', icon: '👥', label: 'Khách hàng' },
]

/**
 * Layout — App shell: sidebar trái + header + <Outlet>
 * Giai đoạn 6: dùng useTenant() thay vì import MOCK_TENANT trực tiếp
 *              Banner "Mock Data" chỉ hiện khi IS_MOCK = true
 */
function Layout() {
  const location   = useLocation()
  const { user, logout } = useAuth()
  const { tenant }       = useTenant()

  const tenantName = tenant?.business_name ?? '...'
  const tenantPlan = tenant?.plan ?? '...'

  const currentPage = navItems.find(n =>
    n.end ? location.pathname === '/' : location.pathname.startsWith('/' + n.to.slice(1))
  )

  return (
    <div className="app-shell">
      {/* === Sidebar === */}
      <aside className="sidebar">
        {/* Logo */}
        <div className="sidebar-logo">
          <img src="/sentrix-logo.png" alt="Sentrix Logo" width="28" height="28" style={{ borderRadius: '8px' }} />
          <span className="sidebar-logo-text">Sentrix</span>
        </div>

        {/* Tên quán */}
        <div style={{ padding: '0 var(--spacing-lg) var(--spacing-md)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
          <div style={{ fontWeight: 700, color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
            {tenantName}
          </div>
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
          {/* Mock data warning — chỉ hiện khi IS_MOCK = true */}
          {IS_MOCK && (
            <div style={{
              fontSize: 'var(--font-size-xs)', color: 'var(--color-warning)',
              lineHeight: 1.8, marginBottom: 'var(--spacing-md)',
              padding: '8px 10px',
              background: 'rgba(251,191,36,0.08)',
              border: '1px solid rgba(251,191,36,0.2)',
              borderRadius: 'var(--radius-sm)',
            }}>
              <div style={{ fontWeight: 700 }}>⚠️ Mock Data</div>
              <div>Đặt VITE_USE_MOCK_FIRESTORE=false để kết nối thật</div>
            </div>
          )}

          {/* User info + logout */}
          {user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
              <img
                src={user.photoURL || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.displayName || user.email)}&background=0d1117&color=00c2ff`}
                alt={user.displayName}
                style={{ width: 32, height: 32, borderRadius: '50%', border: '2px solid var(--color-border)', flexShrink: 0 }}
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {user.displayName || user.email}
                </div>
                <button
                  onClick={logout}
                  style={{
                    background: 'none', border: 'none', padding: 0,
                    fontSize: '0.65rem', color: 'var(--color-text-muted)',
                    cursor: 'pointer', fontFamily: 'var(--font-family)',
                  }}
                  onMouseOver={e => e.target.style.color = 'var(--color-danger)'}
                  onMouseOut={e => e.target.style.color = 'var(--color-text-muted)'}
                >
                  Đăng xuất →
                </button>
              </div>
            </div>
          )}
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
            {/* Trạng thái kết nối */}
            <span style={{
              display: 'flex', alignItems: 'center', gap: 5,
              fontSize: 'var(--font-size-xs)',
              color: IS_MOCK ? 'var(--color-warning)' : 'var(--color-positive)',
            }}>
              <span style={{
                width: 7, height: 7, borderRadius: '50%',
                background: IS_MOCK ? 'var(--color-warning)' : 'var(--color-positive)',
                animation: IS_MOCK ? 'none' : 'pulse 2s infinite',
              }} />
              {IS_MOCK ? 'Mock Data' : 'Firestore Live'}
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
