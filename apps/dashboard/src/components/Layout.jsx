import { useState } from 'react'
import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'
import { useTenant } from '../mocks/useFirestore.js'
import { IS_MOCK } from '../mocks/useFirestore.js'

const navItems = [
  { to: '/', label: 'Tổng quan', end: true },
  { to: '/feedbacks', label: 'Phản hồi' },
  { to: '/customers', label: 'Khách hàng' },
]

const navItemsOps = [
  { to: '/fraud',          label: 'Chống gian lận' },
  { to: '/voucher-config', label: 'Cấu hình voucher' },
  { to: '/operating-cost', label: 'Chi phí vận hành' },
]

function Layout() {
  const location         = useLocation()
  const { user, logout } = useAuth()
  const { tenant }       = useTenant()
  const [collapsed, setCollapsed] = useState(false)

  const tenantName = tenant?.business_name ?? null

  const allNavItems = [...navItems, ...navItemsOps]
  const currentPage = allNavItems.find(n =>
    n.end ? location.pathname === '/' : location.pathname.startsWith('/' + n.to.slice(1))
  )

  const sidebarWidth = collapsed ? 0 : 240

  return (
    <div className="app-shell">

      {/* === Sidebar === */}
      <aside
        className="sidebar"
        style={{
          width: sidebarWidth,
          minWidth: sidebarWidth,
          overflow: 'hidden',
          transition: 'width 0.28s cubic-bezier(0.4,0,0.2,1), min-width 0.28s cubic-bezier(0.4,0,0.2,1)',
        }}
      >
        <div style={{ width: 240, height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

          {/* Logo */}
          <div className="sidebar-logo" style={{ flexShrink: 0 }}>
            <img
              src="/sentrix-logo.png"
              alt="Sentrix"
              style={{ width: 160, height: 'auto', objectFit: 'contain', display: 'block' }}
            />
          </div>

          {/* Tên quán — nổi bật hơn logo */}
          {tenantName && (
            <div style={{ padding: '0 var(--spacing-lg) var(--spacing-sm)', flexShrink: 0 }}>
              <div style={{
                fontWeight: 800,
                color: 'var(--color-text-primary)',
                fontSize: 'var(--font-size-base)',
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {tenantName}
              </div>
            </div>
          )}

          {/* Phân cách dưới logo + tên */}
          <div style={{ margin: '0 var(--spacing-lg) 4px', height: 1, background: 'var(--color-border)', flexShrink: 0 }} />

          {/* Nav chính — nhóm chức năng cốt lõi */}
          <nav className="sidebar-nav" style={{ flexShrink: 0 }}>
            {navItems.map(({ to, label, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
              >
                {label}
              </NavLink>
            ))}
          </nav>

          {/* Phân cách trước nhóm vận hành */}
          <div style={{ margin: '8px var(--spacing-lg) 0', height: 1, background: 'var(--color-border)', flexShrink: 0 }} />

          {/* Nhóm Vận hành — nhãn mục */}
          <div style={{
            padding: '10px var(--spacing-lg) 4px',
            fontSize: '0.65rem', fontWeight: 700,
            color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em',
            flexShrink: 0,
          }}>
            Vận hành
          </div>
          <nav className="sidebar-nav" style={{ paddingTop: 0, flexShrink: 0 }}>
            {navItemsOps.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
              >
                {label}
              </NavLink>
            ))}
          </nav>

          {/* Spacer — đẩy footer xuống đáy */}
          <div style={{ flex: 1 }} />

          {/* Footer sidebar — không bao giờ bị ẩn */}
          <div style={{ borderTop: '1px solid var(--color-border)', padding: 'var(--spacing-md) var(--spacing-lg)', flexShrink: 0 }}>
            {IS_MOCK && (
              <div style={{
                fontSize: 'var(--font-size-xs)', color: 'var(--color-warning)',
                lineHeight: 1.7, marginBottom: 10,
                padding: '6px 8px',
                background: 'rgba(255, 164, 18, 0.08)',
                border: '1px solid rgba(255, 164, 18, 0.2)',
                borderRadius: 'var(--radius-sm)',
              }}>
                <div style={{ fontWeight: 700 }}>Đang dùng dữ liệu mẫu</div>
                <div style={{ color: 'var(--color-text-muted)', marginTop: 2 }}>
                  Đặt VITE_USE_MOCK_FIRESTORE=false để kết nối Firestore thật
                </div>
              </div>
            )}

            {user && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <img
                  src={user.photoURL || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.displayName || user.email)}&background=0688A6&color=FFFFFF`}
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
                    Đăng xuất
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* === Main Content === */}
      <div
        className="main-content"
        style={{
          marginLeft: sidebarWidth,
          transition: 'margin-left 0.28s cubic-bezier(0.4,0,0.2,1)',
        }}
      >
        {/* Top Header — hamburger luôn ở đây */}
        <header className="top-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
            <button
              id="btn-toggle-sidebar"
              onClick={() => setCollapsed(c => !c)}
              title={collapsed ? 'Mở thanh điều hướng' : 'Thu thanh điều hướng'}
              style={{
                width: 34, height: 34,
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-border)',
                background: 'var(--color-bg)',
                cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: 'var(--color-text-secondary)',
                transition: 'all 0.18s ease',
                flexShrink: 0,
              }}
              onMouseOver={e => { e.currentTarget.style.borderColor = 'var(--color-primary)'; e.currentTarget.style.color = 'var(--color-primary)' }}
              onMouseOut={e => { e.currentTarget.style.borderColor = 'var(--color-border)'; e.currentTarget.style.color = 'var(--color-text-secondary)' }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
            <h1 className="header-title">
              {currentPage?.label ?? 'Tổng quan'}
            </h1>
          </div>

          <div className="header-meta">
            <span style={{
              display: 'flex', alignItems: 'center', gap: 5,
              fontSize: 'var(--font-size-xs)',
              padding: '4px 10px', borderRadius: 20,
              background: IS_MOCK ? 'rgba(255,164,18,0.08)' : 'rgba(0,182,155,0.08)',
              border: IS_MOCK ? '1px solid rgba(255,164,18,0.25)' : '1px solid rgba(0,182,155,0.25)',
              color: IS_MOCK ? 'var(--color-warning)' : 'var(--color-success)',
            }}>
              <span style={{
                width: 7, height: 7, borderRadius: '50%',
                background: IS_MOCK ? 'var(--color-warning)' : 'var(--color-success)',
                animation: IS_MOCK ? 'none' : 'pulse 2s infinite',
              }} />
              {IS_MOCK ? 'Dữ liệu mẫu' : 'Firestore Live'}
            </span>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', fontWeight: 600 }}>
              {new Date().toLocaleDateString('vi-VN', { weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric' })}
            </span>
          </div>
        </header>

        {/* Page outlet */}
        <main className="page-content fade-in" style={{ display: 'flex', flexDirection: 'column', minHeight: 'calc(100vh - 64px)' }}>
          <div style={{ flex: 1 }}>
            <Outlet />
          </div>
          <footer style={{
            textAlign: 'center',
            marginTop: 'var(--spacing-xl)',
            paddingBottom: 'var(--spacing-md)',
            color: 'var(--color-text-muted)',
            fontSize: 'var(--font-size-xs)',
          }}>
            Sentrix: AI-Powered Customer Experience Platform<br/>
            © Copyright 2026 Prep. All rights reserved.
          </footer>
        </main>
      </div>
    </div>
  )
}

export default Layout
