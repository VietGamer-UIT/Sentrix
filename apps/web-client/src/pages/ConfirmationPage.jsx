import { useEffect, useRef } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'

/**
 * ConfirmationPage — Bước 4 trong user-flow.md
 *
 * UX Requirements:
 * - Optimistic UI: hiện NGAY thành công, không chờ server phân tích xong
 * - Hiệu ứng mượt mà — tuyệt đối KHÔNG dùng loading spinner quay đều
 * - Cảm giác "nhanh và xong" cho khách
 * - Tự động chuyển sang Gamification sau 2.5 giây
 *
 * Rủi ro (user-flow.md): Loading chậm khiến khách tưởng lỗi và đóng tab
 * Giải pháp: Hiện màn hình thành công ngay lập tức (processing ngầm)
 */
function ConfirmationPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const hasNavigated = useRef(false)

  const tenantId = searchParams.get('tenant_id') || 'demo_tenant'
  const location = searchParams.get('location') || 'Bàn 1'

  // Tự chuyển sang SpinPage sau 2.5 giây — đủ để khách đọc thông báo
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!hasNavigated.current) {
        hasNavigated.current = true
        navigate(`/spin?tenant_id=${tenantId}&location=${encodeURIComponent(location)}`)
      }
    }, 2500)
    return () => clearTimeout(timer)
  }, [navigate, tenantId, location])

  return (
    <div className="page">
      {/* Màu xanh lá thay vì màu primary để thể hiện thành công */}
      <div className="bg-glow" style={{
        width: 350, height: 350,
        background: 'rgba(16, 185, 129, 0.12)',
        top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        borderRadius: '50%',
        filter: 'blur(80px)',
        position: 'absolute',
        zIndex: 0
      }} />

      <div className="page-content" style={{ textAlign: 'center', gap: 'var(--spacing-xl)' }}>

        {/* Animated checkmark SVG */}
        <div className="fade-up" style={{ position: 'relative' }}>
          <svg
            width="110" height="110" viewBox="0 0 110 110" fill="none"
            style={{ filter: 'drop-shadow(0 0 24px rgba(16, 185, 129, 0.45))' }}
          >
            {/* Circle */}
            <circle
              cx="55" cy="55" r="50"
              stroke="#10B981"
              strokeWidth="4"
              fill="rgba(16, 185, 129, 0.08)"
              strokeDasharray="314"
              strokeDashoffset="314"
              style={{
                animation: 'circle-draw 0.6s ease forwards',
                transformOrigin: '55px 55px',
                transform: 'rotate(-90deg)'
              }}
            />
            {/* Checkmark */}
            <path
              d="M32 55 L48 71 L78 40"
              stroke="#10B981"
              strokeWidth="5"
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
              strokeDasharray="80"
              strokeDashoffset="80"
              style={{ animation: 'check-draw 0.5s ease 0.5s forwards' }}
            />
          </svg>
        </div>

        {/* Thông điệp */}
        <div className="fade-up fade-up--delay-1">
          <h1 style={{ fontSize: 'var(--font-size-2xl)', marginBottom: 'var(--spacing-sm)' }}>
            Cảm ơn bạn! 🎉
          </h1>
          <p style={{ lineHeight: 1.7 }}>
            Phản hồi đã được ghi nhận thành công.
            <br />
            <span style={{ color: 'var(--color-text-secondary)' }}>
              Ý kiến của bạn giúp chúng mình phục vụ tốt hơn!
            </span>
          </p>
        </div>

        {/* Indicator chuyển màn hình — dạng 3 chấm nhấp nhô, không phải spinner */}
        <div className="fade-up fade-up--delay-2" style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12
        }}>
          <div style={{ display: 'flex', gap: 8 }}>
            {[0, 0.2, 0.4].map((delay, i) => (
              <div key={i} style={{
                width: 8, height: 8, borderRadius: '50%',
                background: 'var(--color-primary)',
                animation: `pulse-ring 1.2s ease-in-out ${delay}s infinite`
              }} />
            ))}
          </div>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
            🎡 Đang chuẩn bị vòng quay may mắn...
          </p>
        </div>

      </div>
    </div>
  )
}

export default ConfirmationPage
