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
 * SentrixOwlSVG — Logo cú Sentrix dạng SVG inline
 * Không cần file ảnh, scale mọi kích thước, không bị méo/mờ
 */
export function SentrixOwlSVG({ size = 32 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="owl-body-grad" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#4880FF"/>
          <stop offset="100%" stopColor="#7C3AED"/>
        </linearGradient>
        <linearGradient id="owl-eye-l" x1="16" y1="22" x2="28" y2="34" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#FFFFFF"/>
          <stop offset="100%" stopColor="#E0E8FF"/>
        </linearGradient>
        <linearGradient id="owl-eye-r" x1="36" y1="22" x2="48" y2="34" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#FFFFFF"/>
          <stop offset="100%" stopColor="#E0E8FF"/>
        </linearGradient>
      </defs>

      {/* Body tròn nền gradient */}
      <circle cx="32" cy="36" r="22" fill="url(#owl-body-grad)" />

      {/* Tai (ear tufts) */}
      <path d="M20 18 L16 8 L26 16 Z" fill="url(#owl-body-grad)" />
      <path d="M44 18 L48 8 L38 16 Z" fill="url(#owl-body-grad)" />

      {/* Mặt trắng (facial disc) */}
      <ellipse cx="32" cy="34" rx="16" ry="14" fill="rgba(255,255,255,0.15)" />

      {/* Mắt trái — vòng ngoài */}
      <circle cx="23" cy="29" r="8" fill="url(#owl-eye-l)" />
      <circle cx="23" cy="29" r="8" fill="none" stroke="rgba(72,128,255,0.3)" strokeWidth="1" />
      {/* Đồng tử trái */}
      <circle cx="23" cy="29" r="4.5" fill="#1E3A8A" />
      <circle cx="23" cy="29" r="2.5" fill="#000D1F" />
      {/* Ánh sáng mắt */}
      <circle cx="25" cy="27" r="1.2" fill="rgba(255,255,255,0.9)" />

      {/* Mắt phải — vòng ngoài */}
      <circle cx="41" cy="29" r="8" fill="url(#owl-eye-r)" />
      <circle cx="41" cy="29" r="8" fill="none" stroke="rgba(72,128,255,0.3)" strokeWidth="1" />
      {/* Đồng tử phải */}
      <circle cx="41" cy="29" r="4.5" fill="#1E3A8A" />
      <circle cx="41" cy="29" r="2.5" fill="#000D1F" />
      {/* Ánh sáng mắt */}
      <circle cx="43" cy="27" r="1.2" fill="rgba(255,255,255,0.9)" />

      {/* Mỏ */}
      <path d="M29 36 L32 40 L35 36 Z" fill="#FFA412" />

      {/* Ngực — lông vũ nhẹ */}
      <ellipse cx="32" cy="44" rx="10" ry="7" fill="rgba(255,255,255,0.12)" />

      {/* Chân */}
      <path d="M25 56 L22 52 L27 52 Z" fill="#FFA412" />
      <path d="M39 56 L36 52 L41 52 Z" fill="#FFA412" />

      {/* Vòng ngoài mạng lưới (network dots — đặc trưng Sentrix AI) */}
      <circle cx="6" cy="12" r="2" fill="rgba(255,255,255,0.5)" />
      <circle cx="58" cy="12" r="2" fill="rgba(255,255,255,0.5)" />
      <circle cx="6" cy="52" r="2" fill="rgba(255,255,255,0.5)" />
      <circle cx="58" cy="52" r="2" fill="rgba(255,255,255,0.5)" />
      <line x1="6" y1="12" x2="14" y2="18" stroke="rgba(255,255,255,0.3)" strokeWidth="1" />
      <line x1="58" y1="12" x2="50" y2="18" stroke="rgba(255,255,255,0.3)" strokeWidth="1" />
    </svg>
  )
}

/**
 * Layout — App shell: sidebar trái + header + <Outlet>
 * Light Theme: sidebar trắng, accent #4880FF, font Nunito Sans
 */
function Layout() {
  const location   = useLocation()
  const { user, logout } = useAuth()
  const { tenant }       = useTenant()

  const tenantName = tenant?.business_name ?? 'Đang tải...'

  const currentPage = navItems.find(n =>
    n.end ? location.pathname === '/' : location.pathname.startsWith('/' + n.to.slice(1))
  )

  return (
    <div className="app-shell">
      {/* === Sidebar === */}
      <aside className="sidebar">
        {/* Logo */}
        <div className="sidebar-logo">
          <SentrixOwlSVG size={32} />
          <span className="sidebar-logo-text">Sentrix</span>
        </div>

        {/* Tên quán */}
        <div style={{
          padding: '0 var(--spacing-lg) var(--spacing-md)',
          fontSize: 'var(--font-size-xs)',
        }}>
          <div style={{
            fontWeight: 600,
            color: 'var(--color-text-muted)',
            fontSize: 'var(--font-size-xs)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}>
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
          {/* Mock data warning */}
          {IS_MOCK && (
            <div style={{
              fontSize: 'var(--font-size-xs)', color: 'var(--color-warning)',
              lineHeight: 1.8, marginBottom: 'var(--spacing-md)',
              padding: '8px 10px',
              background: 'rgba(255, 164, 18, 0.08)',
              border: '1px solid rgba(255, 164, 18, 0.2)',
              borderRadius: 'var(--radius-sm)',
            }}>
              <div style={{ fontWeight: 700 }}>⚠️ Mock Data</div>
              <div style={{ color: 'var(--color-text-muted)' }}>Đặt VITE_USE_MOCK_FIRESTORE=false để kết nối thật</div>
            </div>
          )}

          {/* User info + logout */}
          {user && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
              <img
                src={user.photoURL || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.displayName || user.email)}&background=4880FF&color=FFFFFF`}
                alt={user.displayName}
                style={{ width: 34, height: 34, borderRadius: '50%', border: '2px solid var(--color-border)', flexShrink: 0, objectFit: 'cover' }}
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 'var(--font-size-xs)', fontWeight: 700, color: 'var(--color-text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
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
              padding: '4px 10px',
              borderRadius: 20,
              background: IS_MOCK ? 'rgba(255,164,18,0.08)' : 'rgba(0,182,155,0.08)',
              border: IS_MOCK ? '1px solid rgba(255,164,18,0.25)' : '1px solid rgba(0,182,155,0.25)',
              color: IS_MOCK ? 'var(--color-warning)' : 'var(--color-success)',
            }}>
              <span style={{
                width: 7, height: 7, borderRadius: '50%',
                background: IS_MOCK ? 'var(--color-warning)' : 'var(--color-success)',
                animation: IS_MOCK ? 'none' : 'pulse 2s infinite',
              }} />
              {IS_MOCK ? 'Mock Data' : 'Firestore Live'}
            </span>
            <span style={{
              fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)',
              fontWeight: 600,
            }}>
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
