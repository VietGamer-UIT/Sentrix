import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { SPIN_PRIZES, submitSpinAPI } from '../api/gamification.js'

/**
 * SpinPage — Bước 5 trong user-flow.md
 *
 * FIX B1+C1 (2026-08-19):
 * - Gọi POST /api/v1/gamification/spin thay vì mock random ở client
 *   (bảo mật: prize được quyết định ở server, không thể hack JS)
 * - SĐT: ưu tiên lấy từ sessionStorage (nhập ở RecordingPage), chỉ hiện input
 *   nếu chưa có → tránh nhập 2 lần, tránh 2 SĐT khác nhau cho cùng 1 feedback
 * - Bỏ hoàn toàn firestoreUpdate.js — mọi ghi DB qua backend
 * - handleSkip: navigate bình thường, không gọi spin API
 */
function SpinPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const tenantId = searchParams.get('tenant_id') || 'pho-ba-lan_1722500000000'
  const location  = searchParams.get('location') || 'Bàn 1'

  // C1 FIX: Lấy SĐT từ sessionStorage (đã nhập ở RecordingPage)
  // Chỉ hiện input nhập nếu sessionStorage trống (khách bỏ qua ở RecordingPage)
  const storedPhone = sessionStorage.getItem('sentrix_customer_phone') || ''
  const [phone, setPhone]             = useState(storedPhone)
  const [phoneError, setPhoneError]   = useState(null)
  const [isSpinning, setIsSpinning]   = useState(false)
  const [rotation, setRotation]       = useState(0)
  const [isSuspicious, setIsSuspicious] = useState(false)
  const [apiError, setApiError]       = useState(null)
  // Hiện input SĐT chỉ khi sessionStorage không có SĐT
  const [showPhoneInput, setShowPhoneInput] = useState(!storedPhone)

  const segmentAngle = 360 / SPIN_PRIZES.length

  // Anti-spam: kiểm tra sessionStorage
  useEffect(() => {
    const flag = sessionStorage.getItem('sentrix_is_suspicious')
    if (flag === 'true') setIsSuspicious(true)
  }, [])

  const validatePhone = (p) => /^(0[3|5|7|8|9])[0-9]{8}$/.test(p.trim())

  const handlePhoneChange = (e) => {
    const val = e.target.value.replace(/\D/g, '')
    setPhone(val)
    setPhoneError(null)
  }

  const handleSpin = async () => {
    if (!validatePhone(phone)) {
      setPhoneError('Số điện thoại không hợp lệ (ví dụ: 0912345678)')
      return
    }
    setIsSpinning(true)
    setPhoneError(null)
    setApiError(null)

    // Lưu SĐT vào sessionStorage để đồng bộ (phòng trường hợp nhập lần đầu tại đây)
    sessionStorage.setItem('sentrix_customer_phone', phone)

    // Lấy feedback_id từ sessionStorage (được lưu bởi RecordingPage)
    let feedbackId = null
    try {
      feedbackId = sessionStorage.getItem('sentrix_feedback_id')
      if (!feedbackId) {
        const stored = sessionStorage.getItem('sentrix_api_result')
        if (stored) feedbackId = JSON.parse(stored).feedback_id
      }
    } catch (err) {
      console.error('[Sentrix] Không đọc được feedback_id từ sessionStorage', err)
    }

    // === B1 FIX: Gọi backend API thật, không mock random ở client ===
    let prizeId = 'chuc_may_man'
    let prizeLabel = 'Chúc may mắn'
    let voucherCode = ''

    try {
      const spinResult = await submitSpinAPI(tenantId, phone, feedbackId)
      // Backend đã lưu phone + voucher vào Firestore — client chỉ nhận kết quả
      prizeId     = spinResult.prize        || 'chuc_may_man'
      prizeLabel  = spinResult.prize_label  || 'Chúc may mắn'
      voucherCode = spinResult.voucher_code || ''
    } catch (err) {
      console.error('[Sentrix] Spin API thất bại:', err)
      setApiError('Không kết nối được máy chủ. Vui lòng thử lại.')
      setIsSpinning(false)
      return
    }

    // Tìm prizeIndex trong SPIN_PRIZES để animate đúng ô
    const prizeIndex = SPIN_PRIZES.findIndex(p => p.id === prizeId)
    const safeIndex  = prizeIndex >= 0 ? prizeIndex : 0

    // Fix góc quay: Pointer ở TOP (12 giờ)
    // Segment i chiếm góc [i * segmentAngle, (i+1) * segmentAngle]
    const targetDeg    = 360 - ((safeIndex + 0.5) * segmentAngle)
    const totalRotation = rotation + 360 * 8 + targetDeg
    setRotation(totalRotation)

    // Navigate sang VoucherPage sau animation
    setTimeout(() => {
      navigate(
        `/voucher?tenant_id=${tenantId}` +
        `&location=${encodeURIComponent(location)}` +
        `&prize=${prizeId}` +
        `&prize_label=${encodeURIComponent(prizeLabel)}` +
        `&voucher_code=${encodeURIComponent(voucherCode)}` +
        `&message=${encodeURIComponent(voucherCode ? 'Chúc mừng bạn đã trúng thưởng!' : 'Cảm ơn bạn đã tham gia!')}`
      )
    }, 4500)
  }

  const handleSkip = () => {
    navigate(`/voucher?tenant_id=${tenantId}&location=${encodeURIComponent(location)}&skipped=true`)
  }

  // SVG Vòng quay — pointer ở TOP, segment 0 bắt đầu từ TOP
  const renderWheel = () => {
    const cx = 130, cy = 130, r = 118
    return (
      <svg width="260" height="260" viewBox="0 0 260 260">
        {/* Outer ring */}
        <circle cx={cx} cy={cy} r={r + 6} fill="none"
          stroke="rgba(0,122,255,0.12)" strokeWidth="10"/>

        {SPIN_PRIZES.map((prize, i) => {
          const startAngleDeg = i * segmentAngle - 90
          const endAngleDeg   = (i + 1) * segmentAngle - 90
          const startRad = startAngleDeg * (Math.PI / 180)
          const endRad   = endAngleDeg   * (Math.PI / 180)

          const x1 = cx + r * Math.cos(startRad)
          const y1 = cy + r * Math.sin(startRad)
          const x2 = cx + r * Math.cos(endRad)
          const y2 = cy + r * Math.sin(endRad)

          const midAngleDeg = (i + 0.5) * segmentAngle - 90
          const midRad = midAngleDeg * (Math.PI / 180)
          const textX = cx + (r * 0.63) * Math.cos(midRad)
          const textY = cy + (r * 0.63) * Math.sin(midRad)

          const labelLines = prize.label.split('\n')

          return (
            <g key={prize.id}>
              <path
                d={`M${cx},${cy} L${x1},${y1} A${r},${r} 0 0,1 ${x2},${y2} Z`}
                fill={prize.color}
                stroke="rgba(255,255,255,0.8)"
                strokeWidth="1.5"
              />
              <g transform={`rotate(${(i + 0.5) * segmentAngle}, ${textX}, ${textY})`}>
                {labelLines.map((line, li) => (
                  <text
                    key={li}
                    x={textX}
                    y={textY + (li - (labelLines.length - 1) / 2) * 13}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fill="white"
                    fontSize="9.5"
                    fontWeight="800"
                    fontFamily="'Be Vietnam Pro', sans-serif"
                    style={{ pointerEvents: 'none', userSelect: 'none' }}
                  >
                    {line}
                  </text>
                ))}
              </g>
            </g>
          )
        })}

        {/* Center cap */}
        <circle cx={cx} cy={cy} r="20" fill="#FFFFFF" stroke="rgba(0,122,255,0.3)" strokeWidth="2"/>
        <circle cx={cx} cy={cy} r="7" fill="#007AFF"/>
      </svg>
    )
  }

  // === BLOCKED: is_suspicious ===
  if (isSuspicious) {
    return (
      <div className="page">
        <div className="bg-glow bg-glow--primary"/>
        <div className="page-content" style={{ textAlign: 'center', gap: 'var(--spacing-xl)' }}>
          <div style={{ fontSize: 56 }}>🚫</div>
          <div className="card" style={{ width: '100%' }}>
            <h1 style={{ fontSize: 'var(--font-size-xl)', marginBottom: 12, color: 'var(--color-text-primary)' }}>
              Phản hồi chưa hợp lệ
            </h1>
            <p style={{ color: 'var(--color-text-secondary)', lineHeight: 1.7, marginBottom: 16 }}>
              Hệ thống phát hiện phản hồi của bạn có dấu hiệu bất thường.<br/>
              Vui lòng gửi lại phản hồi trung thực để nhận phần thưởng.
            </p>
            <button className="btn btn--secondary" onClick={() => navigate('/')}>
              Quay lại trang chủ
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="bg-glow bg-glow--primary" style={{ background: 'rgba(124,58,237,0.08)', top: -100, right: -100 }}/>
      <div className="bg-glow bg-glow--accent"/>

      <div className="page-content" style={{ textAlign: 'center' }}>

        {/* Header */}
        <div className="fade-up">
          <h1 style={{ fontSize: 'var(--font-size-xl)', color: 'var(--color-text-primary)' }}>
            Vòng quay may mắn
          </h1>
          <p style={{ marginTop: 6, color: 'var(--color-text-secondary)' }}>
            {storedPhone
              ? `Quay thưởng cho SĐT ${storedPhone.slice(0, 3)}****${storedPhone.slice(-3)}`
              : 'Nhập SĐT để quay thưởng ngay!'}
          </p>
        </div>

        {/* Vòng quay */}
        <div className="fade-up fade-up--delay-1" style={{ position: 'relative', display: 'inline-block' }}>
          {/* Con trỏ ▼ ở TOP */}
          <div style={{
            position: 'absolute', top: -10, left: '50%',
            transform: 'translateX(-50%)',
            width: 0, height: 0,
            borderLeft: '10px solid transparent',
            borderRight: '10px solid transparent',
            borderTop: '20px solid #007AFF',
            zIndex: 2,
            filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))',
          }} />

          <div style={{
            transform: `rotate(${rotation}deg)`,
            transition: isSpinning ? 'transform 4.5s cubic-bezier(0.17, 0.67, 0.12, 0.99)' : 'none',
            borderRadius: '50%',
            boxShadow: '0 4px 24px rgba(0,0,0,0.1)',
            display: 'inline-block',
          }}>
            {renderWheel()}
          </div>
        </div>

        {/* Form nhập SĐT — chỉ hiện nếu chưa có SĐT từ RecordingPage */}
        {!isSpinning && showPhoneInput && (
          <div className="card fade-up fade-up--delay-2" style={{ width: '100%' }}>
            <div className="input-group">
              <label className="input-label" htmlFor="phone-input">
                Số điện thoại nhận quà
              </label>
              <input
                id="phone-input"
                className="input"
                type="tel"
                inputMode="numeric"
                placeholder="0912 345 678"
                value={phone}
                onChange={handlePhoneChange}
                maxLength={10}
                autoComplete="tel"
              />
            </div>

            <p style={{
              fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)',
              margin: '8px 0 var(--spacing-md)', lineHeight: 1.6
            }}>
              SĐT chỉ dùng để gửi voucher qua Zalo<br/>
              Không chia sẻ cho bên thứ ba
            </p>

            {phoneError && (
              <p style={{ color: 'var(--color-danger)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--spacing-sm)' }}>
                {phoneError}
              </p>
            )}

            {apiError && (
              <p style={{ color: 'var(--color-danger)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--spacing-sm)' }}>
                ⚠️ {apiError}
              </p>
            )}

            <button
              id="btn-spin"
              className="btn btn--primary"
              onClick={handleSpin}
              disabled={phone.length < 10}
            >
              Quay ngay!
            </button>
          </div>
        )}

        {/* Có SĐT sẵn — hiện nút quay ngay không cần nhập lại */}
        {!isSpinning && !showPhoneInput && (
          <div className="card fade-up fade-up--delay-2" style={{ width: '100%' }}>
            {apiError && (
              <p style={{ color: 'var(--color-danger)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--spacing-sm)' }}>
                ⚠️ {apiError}
              </p>
            )}
            <button
              id="btn-spin"
              className="btn btn--primary"
              onClick={handleSpin}
            >
              🎰 Quay ngay!
            </button>
            <button
              type="button"
              style={{
                background: 'none', border: 'none',
                color: 'var(--color-text-muted)',
                fontSize: 'var(--font-size-xs)',
                cursor: 'pointer', textDecoration: 'underline',
                padding: '8px 0', fontFamily: 'var(--font-family)',
                marginTop: 8,
              }}
              onClick={() => setShowPhoneInput(true)}
            >
              Dùng số điện thoại khác
            </button>
          </div>
        )}

        {isSpinning && (
          <div className="fade-up" style={{ textAlign: 'center' }}>
            <p style={{ color: 'var(--color-primary)', fontWeight: 600 }}>
              Đang quay... Chúc may mắn!
            </p>
          </div>
        )}

        {!isSpinning && (
          <button id="btn-skip-spin" className="btn btn--ghost" onClick={handleSkip}>
            Bỏ qua
          </button>
        )}

      </div>
    </div>
  )
}

export default SpinPage
