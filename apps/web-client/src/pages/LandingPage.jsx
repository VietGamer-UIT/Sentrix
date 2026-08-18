import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import RecordingOverlay from '../components/RecordingOverlay.jsx'

/**
 * LandingPage — Bước 2 trong user-flow.md
 *
 * Giai đoạn BUG FIX:
 * - KHÔNG redirect sang /record — mở overlay thu âm ngay tại trang này
 * - Copywriting chuẩn: "Nhấn để nói", "15 giây", ngắt dòng đúng
 * - Logo SVG inline chất lượng cao
 * - Bỏ bớt icon thừa
 * - Anti-spam: đọc sessionStorage để block spin nếu is_suspicious
 */
function LandingPage() {
  const [searchParams] = useSearchParams()
  const [showOverlay, setShowOverlay] = useState(false)
  const [overlayMode, setOverlayMode] = useState('audio')

  const tenantId  = searchParams.get('tenant_id') || 'pho-ba-lan_1722500000000'
  const location  = searchParams.get('location') || 'Bàn 1'
  const businessName = 'Phở Bà Lan'

  // Xóa kết quả API cũ khi vào trang mới (session mới bắt đầu)
  useEffect(() => {
    sessionStorage.removeItem('sentrix_api_result')
    sessionStorage.removeItem('sentrix_feedback_id')
    sessionStorage.removeItem('sentrix_is_suspicious')
  }, [])

  const openOverlay = (mode) => {
    setOverlayMode(mode)
    setShowOverlay(true)
  }

  return (
    <>
      <div className="page">
        <div className="bg-glow bg-glow--primary" />
        <div className="bg-glow bg-glow--accent" />

        <div className="page-content">

          {/* Logo Sentrix */}
          <div className="fade-up" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <img
              src="/sentrix-logo.png"
              alt="Sentrix"
              style={{ width: 140, height: 'auto', objectFit: 'contain', flexShrink: 0 }}
            />
          </div>

          {/* Tên quán + Vị trí */}
          <div style={{ textAlign: 'center' }} className="fade-up fade-up--delay-1">
            <h1 style={{ fontSize: 'var(--font-size-2xl)', marginBottom: 10, color: 'var(--color-text-primary)' }}>
              {businessName}
            </h1>
            <span className="chip chip--location">{decodeURIComponent(location)}</span>
          </div>

          {/* Card CTA chính */}
          <div className="card fade-up fade-up--delay-2" style={{ width: '100%' }}>

            {/* Headline — ngắt dòng đúng theo UX spec */}
            <div style={{ textAlign: 'center', marginBottom: 'var(--spacing-lg)' }}>
              <p style={{
                fontSize: 'var(--font-size-lg)',
                fontWeight: 700,
                color: 'var(--color-text-primary)',
                lineHeight: 1.4,
                marginBottom: 8
              }}>
                Cảm nhận của bạn hôm nay?
              </p>
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.7 }}>
                Chỉ <strong style={{ color: 'var(--color-primary)' }}>15 giây</strong> — có cơ hội nhận ngay<br />
                <strong style={{ color: '#F59E0B', fontSize: 'var(--font-size-base)' }}>VOUCHER MIỄN PHÍ!</strong>
              </p>
            </div>

            {/* Nút ghi âm — Primary Action */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
              <button
                id="btn-record-voice"
                className="btn-record"
                onClick={() => openOverlay('audio')}
                aria-label="Nhấn để ghi âm phản hồi"
              >
                <svg width="38" height="38" viewBox="0 0 24 24" fill="none"
                  stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                  <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                  <line x1="12" y1="19" x2="12" y2="23"/>
                  <line x1="8" y1="23" x2="16" y2="23"/>
                </svg>
              </button>
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginTop: 4 }}>
                Nhấn để nói — tối đa 15 giây
              </p>
            </div>

            {/* Divider */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)',
              margin: 'var(--spacing-lg) 0'
            }}>
              <div style={{ flex: 1, height: 1, background: 'var(--color-border)' }} />
              <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>HOẶC</span>
              <div style={{ flex: 1, height: 1, background: 'var(--color-border)' }} />
            </div>

            {/* Nút gõ text — Secondary */}
            <button
              id="btn-input-text"
              className="btn btn--secondary"
              onClick={() => openOverlay('text')}
            >
              Thích gõ hơn? Gõ tại đây
            </button>
          </div>

          {/* Cam kết bảo mật — tách dòng rõ */}
          <p className="fade-up fade-up--delay-3" style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--color-text-muted)',
            textAlign: 'center',
            lineHeight: 2,
          }}>
            Sentrix: AI-Powered Customer Experience Platform<br/>
            © Copyright 2026 Sentrix. All rights reserved.
          </p>

        </div>
      </div>

      {/* Recording Overlay — hiển thị đè lên trang, không redirect */}
      {showOverlay && (
        <RecordingOverlay
          tenantId={tenantId}
          location={location}
          initialMode={overlayMode}
          onClose={() => setShowOverlay(false)}
        />
      )}
    </>
  )
}


export default LandingPage
