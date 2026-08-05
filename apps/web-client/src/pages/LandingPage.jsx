import { useSearchParams, useNavigate } from 'react-router-dom'

/**
 * LandingPage — Bước 2 trong user-flow.md
 *
 * UX Requirements (từ user-flow.md):
 * - Hiển thị tên quán + vị trí (đọc từ QR query params)
 * - Single primary action: NÚT GHI ÂM lớn ở trung tâm
 * - Nút gõ text là secondary action (nhỏ hơn)
 * - Không yêu cầu đăng nhập, không cần tải app
 * - Tải dưới 2 giây, giao diện tối giản
 *
 * Rủi ro (user-flow.md): QR không nổi bật, không có CTA đủ hấp dẫn
 * Giải pháp: Thông điệp kích thích "10 giây", gamification hint
 *
 * TODO: Khi Tuyền implement GET /api/tenants/{tenant_id}/info
 *       → fetch businessName thật thay vì fallback hard-code
 */
function LandingPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const tenantId = searchParams.get('tenant_id') || 'demo_tenant'
  const location = searchParams.get('location') || 'Bàn 1'

  // TODO: Fetch từ API khi có endpoint. Hiện tại hard-code tên demo.
  const businessName = 'Phở Bà Lan'

  const goToRecord = (mode) => {
    navigate(`/record?tenant_id=${tenantId}&location=${encodeURIComponent(location)}&mode=${mode}`)
  }

  return (
    <div className="page">
      <div className="bg-glow bg-glow--primary" />
      <div className="bg-glow bg-glow--accent" />

      <div className="page-content">

        {/* Logo Sentrix nhỏ phía trên */}
        <div className="fade-up" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <svg width="28" height="28" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="lg1" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#00C2FF"/>
                <stop offset="100%" stopColor="#7C3AED"/>
              </linearGradient>
            </defs>
            <rect width="64" height="64" rx="16" fill="url(#lg1)"/>
            <rect x="26" y="14" width="12" height="20" rx="6" fill="white"/>
            <path d="M18 32c0 7.7 6.3 14 14 14s14-6.3 14-14" stroke="white" strokeWidth="2.5" fill="none" strokeLinecap="round"/>
            <line x1="32" y1="46" x2="32" y2="52" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
            <line x1="26" y1="52" x2="38" y2="52" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
          </svg>
          <span style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)', fontWeight: 600 }}>
            Sentrix
          </span>
        </div>

        {/* Tên quán + Vị trí */}
        <div style={{ textAlign: 'center' }} className="fade-up fade-up--delay-1">
          <h1 style={{ fontSize: 'var(--font-size-2xl)', marginBottom: 10 }}>
            {businessName}
          </h1>
          <span className="chip chip--location">📍 {decodeURIComponent(location)}</span>
        </div>

        {/* Card CTA chính */}
        <div className="card fade-up fade-up--delay-2" style={{ width: '100%' }}>

          {/* Headline kích thích */}
          <div style={{ textAlign: 'center', marginBottom: 'var(--spacing-lg)' }}>
            <p style={{
              fontSize: 'var(--font-size-lg)',
              fontWeight: 700,
              color: 'var(--color-text-primary)',
              lineHeight: 1.4,
              marginBottom: 6
            }}>
              Cảm nhận của bạn hôm nay? 😊
            </p>
            <p style={{ fontSize: 'var(--font-size-sm)' }}>
              Chỉ <strong style={{ color: 'var(--color-primary)' }}>10 giây</strong>{' '}
              — có cơ hội nhận{' '}
              <strong style={{ color: '#F59E0B' }}>voucher miễn phí</strong> ngay!
            </p>
          </div>

          {/* Nút ghi âm — Primary Action lớn ở trung tâm */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-sm)' }}>
            <button
              id="btn-record-voice"
              className="btn-record"
              onClick={() => goToRecord('audio')}
              aria-label="Bấm để ghi âm phản hồi"
            >
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none"
                   stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
              </svg>
            </button>
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
              Bấm và nói (tối đa 15 giây)
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

          {/* Nút gõ text — Secondary Action */}
          <button
            id="btn-input-text"
            className="btn btn--secondary"
            onClick={() => goToRecord('text')}
          >
            ✍️&nbsp; Thích gõ hơn? Gõ tại đây
          </button>
        </div>

        {/* Cam kết bảo mật — giải tỏa lo ngại về privacy */}
        <p className="fade-up fade-up--delay-3" style={{
          fontSize: 'var(--font-size-xs)',
          color: 'var(--color-text-muted)',
          textAlign: 'center',
          lineHeight: 1.8
        }}>
          🔒 Không cần đăng nhập · Không cần tải app
          <br/>Phản hồi hoàn toàn ẩn danh
        </p>

      </div>
    </div>
  )
}

export default LandingPage
