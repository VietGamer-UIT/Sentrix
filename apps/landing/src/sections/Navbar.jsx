import { useState, useEffect } from 'react'

const NAV = [
  { label: 'Vấn đề', href: '#van-de' },
  { label: 'Cách hoạt động', href: '#cach-hoat-dong' },
  { label: 'Dành cho quản lý', href: '#cho-quan' },
  { label: 'FAQ', href: '#faq' },
]

export function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  const go = (e, href) => {
    e.preventDefault()
    setOpen(false)
    document.querySelector(href)?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <>
      <header style={{
        position: 'fixed',
        top: 0, left: 0, right: 0,
        zIndex: 100,
        height: scrolled ? '56px' : '66px',
        transition: 'height 0.3s ease, background 0.3s ease, box-shadow 0.3s ease',
        background: scrolled ? 'rgba(255,255,255,0.93)' : 'transparent',
        backdropFilter: scrolled ? 'blur(18px)' : 'none',
        WebkitBackdropFilter: scrolled ? 'blur(18px)' : 'none',
        boxShadow: scrolled ? '0 1px 0 rgba(0,0,0,0.06)' : 'none',
      }}>
        <div className="container" style={{
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          {/* Logo */}
          <a href="#" onClick={(e) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }) }}
            style={{ display: 'flex', alignItems: 'center', gap: 10, textDecoration: 'none' }}
            aria-label="Sentrix — về đầu trang"
          >
            <img src="/sentrix-logo.png" alt="Sentrix" style={{ width: 32, height: 32, objectFit: 'contain' }} />
            <span style={{
              fontWeight: 800,
              fontSize: 'var(--t-lg)',
              letterSpacing: '-0.035em',
              color: 'var(--teal)',
            }}>SENTRIX</span>
          </a>

          {/* Desktop nav */}
          <nav aria-label="Điều hướng chính" className="nav-desktop" style={{
            display: 'flex', alignItems: 'center', gap: 'var(--s-1)',
          }}>
            {NAV.map(l => (
              <a key={l.href} href={l.href} onClick={(e) => go(e, l.href)}
                style={{
                  fontSize: 'var(--t-sm)',
                  fontWeight: 500,
                  color: 'var(--grey-500)',
                  padding: '6px 12px',
                  borderRadius: 'var(--r-sm)',
                  transition: 'color var(--ease-fast), background var(--ease-fast)',
                  textDecoration: 'none',
                }}
                onMouseEnter={e => { e.target.style.color = 'var(--grey-900)'; e.target.style.background = 'var(--grey-50)' }}
                onMouseLeave={e => { e.target.style.color = 'var(--grey-500)'; e.target.style.background = 'transparent' }}
              >
                {l.label}
            </a>
            ))}
            <a href="#dung-thu" onClick={(e) => go(e, '#dung-thu')}
              className="btn btn-primary"
              style={{ marginLeft: 'var(--s-3)', fontSize: 'var(--t-sm)', padding: '9px 20px' }}
            >
              Đăng ký dùng thử
            </a>
          </nav>

          {/* Hamburger */}
          <button
            id="hamburger-btn"
            onClick={() => setOpen(!open)}
            aria-label={open ? 'Đóng menu' : 'Mở menu'}
            aria-expanded={open}
            className="nav-hamburger"
            style={{
              display: 'none',
              background: 'none',
              border: 'none',
              padding: 'var(--s-2)',
              color: 'var(--grey-700)',
              borderRadius: 'var(--r-sm)',
            }}
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              {open
                ? <><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></>
                : <><line x1="3" y1="8" x2="21" y2="8"/><line x1="3" y1="16" x2="21" y2="16"/></>
              }
            </svg>
          </button>
        </div>
      </header>

      {/* Mobile menu */}
      {open && (
        <div style={{
          position: 'fixed', inset: 0,
          zIndex: 99,
          background: 'rgba(255,255,255,0.97)',
          backdropFilter: 'blur(16px)',
          display: 'flex',
          flexDirection: 'column',
          padding: '80px var(--s-6) var(--s-8)',
          gap: 'var(--s-1)',
          animation: 'fadeIn 0.2s ease',
        }}>
          {NAV.map(l => (
            <a key={l.href} href={l.href} onClick={(e) => go(e, l.href)}
              style={{
                fontSize: 'var(--t-3xl)',
                fontWeight: 700,
                color: 'var(--grey-900)',
                padding: 'var(--s-3) 0',
                borderBottom: '1px solid var(--grey-100)',
                letterSpacing: '-0.02em',
              }}
            >
              {l.label}
            </a>
          ))}
          <a href="#dung-thu" onClick={(e) => go(e, '#dung-thu')}
            className="btn btn-primary-lg"
            style={{ marginTop: 'var(--s-6)', width: '100%', textAlign: 'center' }}
          >
            Đăng ký dùng thử
          </a>
        </div>
      )}

      <style>{`
        @media (max-width: 768px) {
          .nav-desktop { display: none !important; }
          .nav-hamburger { display: flex !important; }
        }
      `}</style>
    </>
  )
}
