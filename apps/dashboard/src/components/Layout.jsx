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

// Nav items nhóm "Vận hành" — Module 4
const navItemsOps = [
  { to: '/fraud',           label: '🛡️ Chống Gian Lận' },
  { to: '/voucher-config',  label: '🎫 Cấu hình Voucher' },
  { to: '/operating-cost',  label: '💰 Chi phí Vận hành' },
]

/**
 * Layout — App shell: sidebar trái + header + <Outlet>
 * Light Theme: sidebar trắng, accent #0688A6 (cyan Sentrix)
 * Collapsible sidebar: nút toggle thu/mở, có transition mượt
 */
function Layout() {
  const location   = useLocation()
  const { user, logout } = useAuth()
  const { tenant }       = useTenant()
  const [collapsed, setCollapsed] = useState(false)

  // Chỉ hiện tên quán khi có dữ liệu thật, không hiện "Đang tải..."
  const tenantName = tenant?.business_name ?? null

  const currentPage = navItems.find(n =>
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
        {/* Wrapper chiều rộng cố định để nội dung không bị wrap khi thu */}
        <div style={{ width: 240, display: 'flex', flexDirection: 'column', height: '100%' }}>

          {/* Logo + nút collapse */}
          <div className="sidebar-logo" style={{ position: 'relative' }}>
            <img
              src="/sentrix-logo.png"
              alt="Sentrix"
              style={{
                width: 160,
                height: 'auto',
                objectFit: 'contain',
                imageRendering: '-webkit-optimize-contrast',
                display: 'block',
              }}
            />
            {/* Nút thu sidebar */}
            <button
              id="btn-collapse-sidebar"
              onClick={() => setCollapsed(true)}
              title="Thu sidebar"
              style={{
                position: 'absolute',
                right: 8,
                top: '50%',
                transform: 'translateY(-50%)',
                width: 28, height: 28,
                borderRadius: '50%',
                border: '1px solid var(--color-border)',
                background: 'var(--color-bg)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--color-text-muted)',
                transition: 'all 0.18s ease',
                flexShrink: 0,
              }}
              onMouseOver={e => { e.currentTarget.style.borderColor = 'var(--color-primary)'; e.currentTarget.style.color = 'var(--color-primary)' }}
              onMouseOut={e => { e.currentTarget.style.borderColor = 'var(--color-border)'; e.currentTarget.style.color = 'var(--color-text-muted)' }}
            >
              {/* ← icon */}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="15 18 9 12 15 6" />
              </svg>
            </button>
          </div>

          {/* Tên quán — chỉ hiện khi có dữ liệu thật */}
          {tenantName && (
            <div style={{ padding: '0 var(--spacing-lg) var(--spacing-md)' }}>
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
          )}

          <div className="nav-separator" />

          {/* Nav Items */}
          <nav className="sidebar-nav">
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

          {/* Nhóm Vận hành — Module 4 */}
          <div className="nav-separator" style={{ margin: '8px 0 0' }} />
          <div style={{
            padding: '8px var(--spacing-lg) 4px',
            fontSize: 'var(--font-size-xs)', fontWeight: 700,
            color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em',
          }}>
            Vận hành
          </div>
          <nav className="sidebar-nav" style={{ paddingTop: 0 }}>
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

          {/* Footer sidebar */}
          <div style={{ padding: 'var(--spacing-lg)', marginTop: 'auto', borderTop: '1px solid var(--color-border)' }}>
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

            {user && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
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
                    Đăng xuất →
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
        {/* Top Header */}
        <header className="top-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
            {/* Nút mở sidebar khi đã thu */}
            {collapsed && (
              <button
                id="btn-expand-sidebar"
                onClick={() => setCollapsed(false)}
                title="Mở sidebar"
                style={{
                  width: 34, height: 34,
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid var(--color-border)',
                  background: 'var(--color-bg)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--color-text-secondary)',
                  transition: 'all 0.18s ease',
                  flexShrink: 0,
                }}
                onMouseOver={e => { e.currentTarget.style.borderColor = 'var(--color-primary)'; e.currentTarget.style.color = 'var(--color-primary)' }}
                onMouseOut={e => { e.currentTarget.style.borderColor = 'var(--color-border)'; e.currentTarget.style.color = 'var(--color-text-secondary)' }}
              >
                {/* ☰ hamburger */}
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                  <line x1="3" y1="6" x2="21" y2="6" />
                  <line x1="3" y1="12" x2="21" y2="12" />
                  <line x1="3" y1="18" x2="21" y2="18" />
                </svg>
              </button>
            )}
            <h1 className="header-title">
              {currentPage?.label ?? 'Dashboard'}
            </h1>
          </div>

          <div className="header-meta">
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
        <main className="page-content fade-in" style={{ display: 'flex', flexDirection: 'column', minHeight: 'calc(100vh - 64px)' }}>
          <div style={{ flex: 1 }}>
            <Outlet />
          </div>
          <footer style={{ 
            textAlign: "center", 
            marginTop: "var(--spacing-xl)", 
            paddingBottom: "var(--spacing-md)", 
            color: "var(--color-text-muted)",
            fontSize: "var(--font-size-xs)"
          }}>
            Sentrix: AI-Powered Customer Experience Platform <br/>
            © Copyright 2026 Sentrix. All rights reserved.
          </footer>
        </main>
      </div>
    </div>
  )
}

export default Layout
