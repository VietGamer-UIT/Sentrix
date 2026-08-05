import { useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'

/**
 * ConfirmationPage — Bước 4 trong user-flow.md
 *
 * UX Requirements (từ user-flow.md):
 * - Optimistic UI: hiện NGAY thông báo thành công, không chờ server xử lý xong
 * - Hiệu ứng mượt mà (không loading spinner quay đều chậm chạp)
 * - Tự động chuyển sang Gamification sau 2 giây
 */
function ConfirmationPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const tenantId = searchParams.get('tenant_id') || 'demo_tenant'
  const location = searchParams.get('location') || 'Bàn 1'

  // Tự động chuyển sang Spin sau 2.5 giây
  useEffect(() => {
    const timer = setTimeout(() => {
      navigate(`/spin?tenant_id=${tenantId}&location=${encodeURIComponent(location)}`)
    }, 2500)
    return () => clearTimeout(timer)
  }, [navigate, tenantId, location])

  return (
    <div className="page">
      <div className="bg-glow bg-glow--primary" style={{ background: 'rgba(16, 185, 129, 0.15)' }} />

      <div className="page-content" style={{ textAlign: 'center', gap: 'var(--spacing-xl)' }}>
        {/* Success Icon SVG */}
        <svg
          className="success-icon fade-up"
          width="100"
          height="100"
          viewBox="0 0 100 100"
          fill="none"
          style={{ filter: 'drop-shadow(0 0 20px rgba(16, 185, 129, 0.5))' }}
        >
          <circle
            cx="50" cy="50" r="45"
            stroke="#10B981"
            strokeWidth="4"
            fill="rgba(16, 185, 129, 0.1)"
          />
          <path
            d="M30 50 L44 64 L70 38"
            stroke="#10B981"
            strokeWidth="5"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />
        </svg>

        <div className="fade-up fade-up--delay-1">
          <h1 style={{ fontSize: 'var(--font-size-2xl)', marginBottom: 'var(--spacing-md)' }}>
            Cảm ơn bạn! 🎉
          </h1>
          <p>
            Phản hồi của bạn đã được ghi nhận thành công.
            <br />Ý kiến của bạn giúp chúng mình cải thiện dịch vụ tốt hơn!
          </p>
        </div>

        <div className="fade-up fade-up--delay-2" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 8, height: 8, borderRadius: '50%',
            background: 'var(--color-primary)',
            animation: 'pulse-ring 1s ease-out infinite'
          }} />
          <p style={{ fontSize: 'var(--font-size-sm)' }}>
            Đang chuyển đến vòng quay may mắn...
          </p>
        </div>
      </div>
    </div>
  )
}

export default ConfirmationPage
