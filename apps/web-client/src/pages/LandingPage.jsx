import { useSearchParams, useNavigate } from 'react-router-dom'

/**
 * LandingPage — Bước 2 trong user-flow.md
 *
 * UX Requirements (từ user-flow.md):
 * - Hiển thị tên quán (đọc từ tenant_id trong QR params)
 * - Single primary action: NÚT GHI ÂM lớn ở trung tâm
 * - Nút gõ text là secondary action (nhỏ hơn)
 * - Không yêu cầu đăng nhập, không cần tải app
 *
 * TODO: Khi Tuyền có endpoint GET /api/tenants/{tenant_id}/info
 *       thì fetch tên quán thật. Hiện tại fallback về "Phở Bà Lan" (demo)
 */
function LandingPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  // Đọc params từ QR code URL (ví dụ: /?tenant_id=pho-ba-lan_xxx&location=Ban+5)
  const tenantId = searchParams.get('tenant_id') || 'demo_tenant'
  const location = searchParams.get('location') || 'Bàn 1'

  // TODO: Fetch tên quán từ API khi Tuyền implement endpoint
  const businessName = 'Phở Bà Lan' // Hard-code demo — thay bằng API thật sau

  const goToRecord = (mode) => {
    navigate(`/record?tenant_id=${tenantId}&location=${encodeURIComponent(location)}&mode=${mode}`)
  }

  return (
    <div className="page">
      {/* Background decorative glows */}
      <div className="bg-glow bg-glow--primary" />
      <div className="bg-glow bg-glow--accent" />

      <div className="page-content">
        {/* Logo */}
        <div className="brand-logo fade-up">
          <div className="brand-logo-text">Sentrix</div>
        </div>

        {/* Tên quán + vị trí */}
        <div style={{ textAlign: 'center' }} className="fade-up fade-up--delay-1">
          <h1 style={{ fontSize: 'var(--font-size-2xl)', marginBottom: 8 }}>
            {businessName}
          </h1>
          <span className="chip chip--location">
            📍 {location}
          </span>
        </div>

        {/* CTA chính */}
        <div className="card fade-up fade-up--delay-2" style={{ textAlign: 'center' }}>
          <p style={{ fontSize: 'var(--font-size-sm)', marginBottom: 'var(--spacing-lg)' }}>
            Chia sẻ trải nghiệm của bạn — chỉ mất <strong style={{ color: 'var(--color-primary)' }}>10 giây</strong> 🎁
          </p>

          {/* Nút ghi âm — Primary Action */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-md)' }}>
            <button
              id="btn-record-voice"
              className="btn-record"
              onClick={() => goToRecord('audio')}
              aria-label="Ghi âm phản hồi"
            >
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
            </button>
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
              Giữ để nói (tối đa 15 giây)
            </p>
          </div>

          {/* Divider */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 'var(--spacing-md)',
            margin: 'var(--spacing-lg) 0', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)'
          }}>
            <div style={{ flex: 1, height: 1, background: 'var(--color-border)' }} />
            HOẶC
            <div style={{ flex: 1, height: 1, background: 'var(--color-border)' }} />
          </div>

          {/* Nút gõ text — Secondary Action */}
          <button
            id="btn-input-text"
            className="btn btn--secondary"
            onClick={() => goToRecord('text')}
          >
            ✍️ Gõ phản hồi bằng văn bản
          </button>
        </div>

        {/* Cam kết bảo mật */}
        <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textAlign: 'center' }}
           className="fade-up fade-up--delay-3">
          🔒 Không cần đăng nhập · Phản hồi hoàn toàn ẩn danh
        </p>
      </div>
    </div>
  )
}

export default LandingPage
