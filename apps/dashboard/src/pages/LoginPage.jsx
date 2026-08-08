/**
 * LoginPage.jsx — Màn hình đăng nhập Dashboard Sentrix
 *
 * Giai đoạn 6: Demo Google Sign-In để bảo vệ dashboard
 * Sau khi đăng nhập, user sẽ được redirect về / (OverviewPage)
 *
 * Design: Dark mode, glassmorphism — khớp với index.css
 */

import { useState } from 'react'
import { useAuth } from '../context/AuthContext.jsx'

export default function LoginPage() {
  const { loginWithGoogle } = useAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  const handleLogin = async () => {
    setLoading(true)
    setError(null)
    try {
      await loginWithGoogle()
      // onAuthStateChanged trong AuthContext sẽ tự cập nhật user → App.jsx redirect
    } catch (err) {
      console.error('[Login] Lỗi đăng nhập:', err)
      if (err.code === 'auth/popup-closed-by-user') {
        setError('Bạn đã đóng cửa sổ đăng nhập. Thử lại.')
      } else if (err.code === 'auth/unauthorized-domain') {
        setError('Domain chưa được phép. Kiểm tra Firebase Console → Authentication → Authorized domains.')
      } else {
        setError(`Đăng nhập thất bại: ${err.message}`)
      }
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--color-bg-main)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Background glow decorations */}
      <div style={{
        position: 'absolute', top: '15%', left: '20%',
        width: 400, height: 400,
        background: 'radial-gradient(circle, rgba(0,194,255,0.08) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute', bottom: '20%', right: '15%',
        width: 300, height: 300,
        background: 'radial-gradient(circle, rgba(124,58,237,0.1) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      {/* Login Card */}
      <div style={{
        width: '100%',
        maxWidth: 420,
        margin: '0 var(--spacing-lg)',
        padding: 'var(--spacing-2xl)',
        background: 'var(--color-bg-card)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: '0 32px 80px rgba(0,0,0,0.4)',
        textAlign: 'center',
      }}>
        {/* Logo */}
        <div style={{ marginBottom: 'var(--spacing-xl)' }}>
          <svg width="56" height="56" viewBox="0 0 64 64" fill="none" style={{ marginBottom: 'var(--spacing-md)' }}>
            <defs>
              <linearGradient id="lg-login" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#00C2FF"/>
                <stop offset="100%" stopColor="#7C3AED"/>
              </linearGradient>
            </defs>
            <rect width="64" height="64" rx="16" fill="url(#lg-login)"/>
            <rect x="26" y="14" width="12" height="20" rx="6" fill="white"/>
            <path d="M18 32c0 7.7 6.3 14 14 14s14-6.3 14-14" stroke="white" strokeWidth="2.5" fill="none" strokeLinecap="round"/>
            <line x1="32" y1="46" x2="32" y2="52" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
            <line x1="26" y1="52" x2="38" y2="52" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
          </svg>

          <h1 style={{
            fontSize: '1.75rem',
            fontWeight: 800,
            background: 'linear-gradient(135deg, #00C2FF 0%, #7C3AED 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            margin: 0,
          }}>
            Sentrix Dashboard
          </h1>
          <p style={{
            marginTop: 'var(--spacing-sm)',
            color: 'var(--color-text-muted)',
            fontSize: 'var(--font-size-sm)',
          }}>
            Phân tích phản hồi khách hàng · AI-powered
          </p>
        </div>

        {/* Divider */}
        <div style={{
          height: 1,
          background: 'var(--color-border)',
          margin: 'var(--spacing-xl) 0',
        }} />

        <p style={{
          fontSize: 'var(--font-size-sm)',
          color: 'var(--color-text-secondary)',
          marginBottom: 'var(--spacing-lg)',
        }}>
          Đăng nhập để xem báo cáo và quản lý phản hồi
        </p>

        {/* Error message */}
        {error && (
          <div style={{
            padding: 'var(--spacing-md)',
            marginBottom: 'var(--spacing-md)',
            background: 'rgba(239,68,68,0.1)',
            border: '1px solid rgba(239,68,68,0.3)',
            borderRadius: 'var(--radius-md)',
            fontSize: 'var(--font-size-xs)',
            color: 'var(--color-danger)',
            textAlign: 'left',
          }}>
            ⚠️ {error}
          </div>
        )}

        {/* Google Sign-In Button */}
        <button
          onClick={handleLogin}
          disabled={loading}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 'var(--spacing-md)',
            padding: '14px var(--spacing-lg)',
            background: loading ? 'rgba(255,255,255,0.05)' : 'rgba(255,255,255,0.08)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            color: loading ? 'var(--color-text-muted)' : 'var(--color-text-primary)',
            fontSize: 'var(--font-size-sm)',
            fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--font-family)',
            transition: 'all 0.2s ease',
          }}
          onMouseOver={e => { if (!loading) e.currentTarget.style.background = 'rgba(255,255,255,0.12)' }}
          onMouseOut={e => { if (!loading) e.currentTarget.style.background = 'rgba(255,255,255,0.08)' }}
        >
          {loading ? (
            <>
              <span style={{
                width: 18, height: 18,
                border: '2px solid rgba(255,255,255,0.2)',
                borderTopColor: 'var(--color-primary)',
                borderRadius: '50%',
                animation: 'spin 0.8s linear infinite',
                display: 'inline-block',
              }} />
              Đang đăng nhập...
            </>
          ) : (
            <>
              {/* Google SVG icon */}
              <svg width="20" height="20" viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              Đăng nhập với Google
            </>
          )}
        </button>

        {/* Footer note */}
        <p style={{
          marginTop: 'var(--spacing-xl)',
          fontSize: '0.7rem',
          color: 'var(--color-text-muted)',
          lineHeight: 1.6,
        }}>
          🔒 Dữ liệu được bảo mật bởi Firebase Authentication.<br/>
          Chỉ tài khoản được cấp phép mới xem được dashboard.
        </p>

        {/* AISC badge */}
        <div style={{
          marginTop: 'var(--spacing-lg)',
          padding: '6px 12px',
          display: 'inline-block',
          background: 'linear-gradient(135deg, rgba(0,194,255,0.1), rgba(124,58,237,0.1))',
          border: '1px solid rgba(0,194,255,0.2)',
          borderRadius: 20,
          fontSize: '0.65rem',
          color: 'var(--color-primary)',
          fontWeight: 700,
          letterSpacing: '0.05em',
        }}>
          ✦ AISC '26 · Sentrix Team
        </div>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}
