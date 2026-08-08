import { useEffect, useRef, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'

/**
 * ConfirmationPage — Bước 4 trong user-flow.md
 *
 * Giai đoạn 7: Sau khi API trả về kết quả AI (sentiment_score, overall_sentiment,
 * is_sarcasm_suspected, p_churn), hiển thị một phần kết quả nhẹ nhàng để khách
 * thấy AI đang hoạt động — tạo cảm giác "thật" cho sản phẩm.
 *
 * Luồng:
 *   - Navigate ngay (optimistic UI) → hiện màn hình này
 *   - API chạy ngầm → lưu vào sessionStorage('sentrix_api_result')
 *   - Component poll sessionStorage mỗi 500ms tối đa 6 giây
 *   - Nếu có kết quả sớm → hiện AI insight card trước khi chuyển sang Spin
 *   - Sau 2.5s (hoặc khi có kết quả) → tự chuyển sang SpinPage
 *
 * UX: Optimistic — không bao giờ block khách chờ. Insight chỉ là bonus.
 */
function ConfirmationPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const hasNavigated = useRef(false)

  const tenantId = searchParams.get('tenant_id') || 'demo_tenant'
  const location  = searchParams.get('location') || 'Bàn 1'

  const [apiResult, setApiResult] = useState(null)
  const pollRef = useRef(null)

  // Poll sessionStorage để lấy kết quả AI (chạy ngầm từ RecordingPage)
  useEffect(() => {
    // Xóa kết quả cũ trước khi poll
    sessionStorage.removeItem('sentrix_api_result')

    pollRef.current = setInterval(() => {
      const raw = sessionStorage.getItem('sentrix_api_result')
      if (raw) {
        try {
          setApiResult(JSON.parse(raw))
          sessionStorage.removeItem('sentrix_api_result')
        } catch { /* ignore parse error */ }
        clearInterval(pollRef.current)
      }
    }, 500)

    return () => clearInterval(pollRef.current)
  }, [])

  // Tự chuyển sau 3 giây (đủ thời gian đọc thông báo + xem insight nếu có)
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!hasNavigated.current) {
        hasNavigated.current = true
        clearInterval(pollRef.current)
        navigate(`/spin?tenant_id=${tenantId}&location=${encodeURIComponent(location)}`)
      }
    }, 3000)
    return () => clearTimeout(timer)
  }, [navigate, tenantId, location])

  // Helper: sentiment score → emoji + màu
  const getSentimentDisplay = (score, label) => {
    if (label?.includes('Tích cực') || score > 0.3)
      return { emoji: '😊', color: '#10B981', text: label || 'Tích cực' }
    if (label?.includes('Tiêu cực') || score < -0.3)
      return { emoji: '😔', color: '#EF4444', text: label || 'Tiêu cực' }
    return { emoji: '😐', color: '#6B7280', text: label || 'Trung lập' }
  }

  const sentimentDisplay = apiResult
    ? getSentimentDisplay(apiResult.sentiment_score, apiResult.overall_sentiment)
    : null

  return (
    <div className="page">
      {/* Background glow xanh lá = thành công */}
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

        {/* Thông điệp chính */}
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

        {/* AI Insight Card — hiện khi có kết quả từ backend */}
        {apiResult && sentimentDisplay && (
          <div className="fade-up" style={{
            width: '100%',
            padding: 'var(--spacing-md) var(--spacing-lg)',
            background: 'rgba(255,255,255,0.04)',
            border: `1px solid ${sentimentDisplay.color}30`,
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-md)',
          }}>
            <span style={{ fontSize: 32, flexShrink: 0 }}>{sentimentDisplay.emoji}</span>
            <div style={{ textAlign: 'left' }}>
              <p style={{
                fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginBottom: 2
              }}>
                🤖 AI phân tích phản hồi của bạn:
              </p>
              <p style={{
                fontSize: 'var(--font-size-sm)', fontWeight: 700, color: sentimentDisplay.color
              }}>
                {sentimentDisplay.text}
                {apiResult.is_sarcasm_suspected && (
                  <span style={{
                    marginLeft: 8, fontSize: '0.7rem',
                    color: '#F59E0B', fontWeight: 400
                  }}>
                    ⚠️ Phát hiện mỉa mai
                  </span>
                )}
              </p>
              {apiResult.transcript && (
                <p style={{
                  fontSize: '0.7rem', color: 'var(--color-text-muted)',
                  marginTop: 4, fontStyle: 'italic', lineHeight: 1.4
                }}>
                  "{apiResult.transcript.slice(0, 80)}{apiResult.transcript.length > 80 ? '…' : ''}"
                </p>
              )}
            </div>
          </div>
        )}

        {/* Indicator chuyển màn hình — 3 chấm nhấp nhô */}
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
