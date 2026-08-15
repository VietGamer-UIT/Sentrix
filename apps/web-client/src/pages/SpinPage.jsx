import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { submitSpinAPI, SPIN_PRIZES } from '../api/gamification.js'

/**
 * SpinPage — Bước 5 trong user-flow.md
 *
 * Bug fixes (Giai đoạn BUG FIX):
 * - Fix tính góc vòng quay: pointer ở TOP (12 giờ) → segment 0 bắt đầu từ top
 * - Anti-spam: đọc sessionStorage 'sentrix_is_suspicious' → block quay nếu true
 * - Label phần thưởng: "Uống miễn phí" → "Voucher uống lần sau"
 * - Bỏ bớt icon emoji thừa
 *
 * ⚠️ MOCK — /api/gamification/spin chưa có (xem docs/api-contract.md mục 4)
 */
function SpinPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const tenantId = searchParams.get('tenant_id') || 'pho-ba-lan_1722500000000'
  const location  = searchParams.get('location') || 'Bàn 1'

  const [phone, setPhone]             = useState('')
  const [phoneError, setPhoneError]   = useState(null)
  const [isSpinning, setIsSpinning]   = useState(false)
  const [rotation, setRotation]       = useState(0)
  const [isSuspicious, setIsSuspicious] = useState(false)

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

    // === Lấy feedback_id từ sessionStorage
    let feedbackId = null
    try {
      const stored = sessionStorage.getItem('sentrix_api_result')
      if (stored) {
        const parsed = JSON.parse(stored)
        feedbackId = parsed.feedback_id
      }
    } catch (err) {
      console.error('Failed to parse sentrix_api_result', err)
    }

    try {
      const result = await submitSpinAPI(tenantId, phone, feedbackId)
      const prizeIndex = SPIN_PRIZES.findIndex(p => p.id === result.prize)

      /**
       * Fix góc quay: Pointer ở TOP (12 giờ = -90° trong toán học)
     * Segment i chiếm góc [i * segmentAngle, (i+1) * segmentAngle]
     * Tâm segment i (tính từ top) = (i + 0.5) * segmentAngle
     * Để pointer (top) trỏ vào tâm segment i, wheel phải xoay sao cho
     * điểm đó lên top: rotationNeeded = 360 - (i + 0.5) * segmentAngle
     */
    const targetDeg = 360 - ((prizeIndex + 0.5) * segmentAngle)
    const totalRotation = rotation + 360 * 8 + targetDeg
    setRotation(totalRotation)

    setTimeout(() => {
      const prizeObj = SPIN_PRIZES[prizeIndex]
      navigate(
        `/voucher?tenant_id=${tenantId}` +
        `&location=${encodeURIComponent(location)}` +
        `&prize=${result.prize}` +
        `&prize_label=${encodeURIComponent(prizeObj.prizeLabel || prizeObj.label || result.prize_label)}` +
        `&voucher_code=${encodeURIComponent(result.voucher_code || '')}` +
        `&message=${encodeURIComponent(result.message)}`
      )
    }, 4500)
    } catch (err) {
      setIsSpinning(false)
      setPhoneError(err.message || 'Có lỗi xảy ra, vui lòng thử lại')
    }
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
          // Bắt đầu từ TOP (-π/2), đi theo chiều kim đồng hồ
          const startAngleDeg = i * segmentAngle - 90
          const endAngleDeg   = (i + 1) * segmentAngle - 90
          const startRad = startAngleDeg * (Math.PI / 180)
          const endRad   = endAngleDeg   * (Math.PI / 180)

          const x1 = cx + r * Math.cos(startRad)
          const y1 = cy + r * Math.sin(startRad)
          const x2 = cx + r * Math.cos(endRad)
          const y2 = cy + r * Math.sin(endRad)

          // Text ở tâm segment, 65% bán kính
          const midAngleDeg = (i + 0.5) * segmentAngle - 90
          const midRad = midAngleDeg * (Math.PI / 180)
          const textX = cx + (r * 0.63) * Math.cos(midRad)
          const textY = cy + (r * 0.63) * Math.sin(midRad)

          // Label text ngắn (max 8 char) — xuống dòng nếu cần
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
            Nhập SĐT để quay thưởng ngay!
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

        {/* Form nhập SĐT */}
        {!isSpinning && (
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
