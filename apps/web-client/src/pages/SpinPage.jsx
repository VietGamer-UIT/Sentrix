import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { SPIN_PRIZES, submitSpinAPI } from '../api/gamification.js'

/**
 * SpinPage — Bước 5 trong user-flow.md
 *
 * FIX B1+C1 (2026-08-19):
 * - Gọi POST /api/v1/gamification/spin thay vì mock random ở client
 * - SĐT: ưu tiên lấy từ sessionStorage (nhập ở RecordingOverlay), chỉ hiện input
 *   nếu chưa có → tránh nhập 2 lần, tránh 2 SĐT khác nhau cho cùng 1 feedback
 * - Bỏ hoàn toàn firestoreUpdate.js — mọi ghi DB qua backend
 * - handleSkip: navigate bình thường, không gọi spin API
 *
 * Module 2 (PDPA):
 * - Nếu voucher_eligible=false (phản hồi ẩn danh) → skip spin ngay, không hỏi SĐT
 * - Nếu đã OTP ở RecordingOverlay → sentrix_customer_phone có sẵn, không hỏi lại
 */
function SpinPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const tenantId = searchParams.get('tenant_id') || 'pho-ba-lan_1722500000000'
  const location  = searchParams.get('location') || 'Bàn 1'

  // Module 2: đọc voucher_eligible từ sessionStorage (set bởi RecordingOverlay)
  // Nếu false (ẩn danh) → không hiện spin, redirect thẳng sang voucher
  const voucherEligible = (() => {
    try {
      const stored = sessionStorage.getItem('sentrix_api_result')
      if (stored) return JSON.parse(stored).voucher_eligible !== false
    } catch { /* ignore */ }
    return true  // Default: cho phép spin nếu không có info
  })()

  // C1 FIX: Lấy Contact từ sessionStorage (đã nhập và OTP ở RecordingOverlay)
  const storedContact = sessionStorage.getItem('sentrix_customer_contact') || sessionStorage.getItem('sentrix_customer_phone') || ''
  const storedContactType = sessionStorage.getItem('sentrix_customer_contact_type') || (storedContact.includes('@') ? 'email' : 'phone')
  
  const [contact, setContact]         = useState(storedContact)
  const [contactType, setContactType] = useState(storedContactType)
  const [contactError, setContactError] = useState(null)
  const [isSpinning, setIsSpinning]   = useState(false)
  const [rotation, setRotation]       = useState(0)
  const [isSuspicious, setIsSuspicious] = useState(false)
  const [apiError, setApiError]       = useState(null)
  
  // Hiện input nếu sessionStorage trống
  const [showContactInput, setShowContactInput] = useState(!storedContact && voucherEligible)

  const segmentAngle = 360 / SPIN_PRIZES.length

  // Anti-spam: kiểm tra sessionStorage
  useEffect(() => {
    const flag = sessionStorage.getItem('sentrix_is_suspicious')
    if (flag === 'true') setIsSuspicious(true)
  }, [])


  // Module 2: Nếu ẩn danh (voucher_eligible=false) → redirect sang voucher ngay
  // Không hiển thị spin vì user đã từ chối nhận voucher (Điều 5 NĐ 356/2025)
  useEffect(() => {
    if (!voucherEligible) {
      navigate(
        `/voucher?tenant_id=${tenantId}` +
        `&location=${encodeURIComponent(location)}` +
        `&skipped=true` +
        `&anonymous=true`
      )
    }
  }, [voucherEligible, navigate, tenantId, location]) // eslint-disable-line

  const validateContact = (c) => {
    if (contactType === 'phone') {
      return /^(0[3|5|7|8|9])[0-9]{8}$/.test(c.trim())
    }
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(c.trim())
  }

  const handleContactChange = (e) => {
    let val = e.target.value
    if (contactType === 'phone') {
      val = val.replace(/\D/g, '')
    }
    setContact(val)
    setContactError(null)
  }

  const handleSpin = async () => {
    if (!validateContact(contact)) {
      setContactError(contactType === 'phone' ? 'Số điện thoại không hợp lệ' : 'Email không hợp lệ')
      return
    }
    setIsSpinning(true)
    setContactError(null)
    setApiError(null)

    // Lưu lại vào sessionStorage
    if (contactType === 'phone') sessionStorage.setItem('sentrix_customer_phone', contact)
    sessionStorage.setItem('sentrix_customer_contact', contact)
    sessionStorage.setItem('sentrix_customer_contact_type', contactType)

    // Lấy feedback_id từ sessionStorage (được lưu bởi RecordingOverlay)
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
      const spinResult = await submitSpinAPI(tenantId, contact, feedbackId)
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
            {storedContact
              ? `Quay thưởng cho ${contactType === 'email' ? storedContact : storedContact.slice(0, 3) + '****' + storedContact.slice(-3)}`
              : 'Nhập thông tin liên hệ để quay thưởng ngay!'}
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

        {/* Form nhập Liên hệ — chỉ hiện nếu chưa có từ RecordingPage */}
        {!isSpinning && showContactInput && (
          <div className="card fade-up fade-up--delay-2" style={{ width: '100%' }}>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'center', marginBottom: 12 }}>
              <label>
                <input type="radio" name="contactType" value="phone" checked={contactType === 'phone'} onChange={() => { setContactType('phone'); setContactError(null) }} />
                <span> Số điện thoại</span>
              </label>
              <label style={{ marginLeft: 16 }}>
                <input type="radio" name="contactType" value="email" checked={contactType === 'email'} onChange={() => { setContactType('email'); setContactError(null) }} />
                <span> Email</span>
              </label>
            </div>
            <div className="input-group">
              <input
                id="contact-input"
                className="input"
                type={contactType === 'email' ? 'email' : 'tel'}
                inputMode={contactType === 'email' ? 'email' : 'numeric'}
                placeholder={contactType === 'email' ? 'Nhập email (vd: abc@gmail.com)' : 'Nhập SĐT (vd: 0912345678)'}
                value={contact}
                onChange={handleContactChange}
                maxLength={contactType === 'email' ? 100 : 10}
                autoComplete={contactType === 'email' ? 'email' : 'tel'}
              />
            </div>

            <p style={{
              fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)',
              margin: '8px 0 var(--spacing-md)', lineHeight: 1.6
            }}>
              Thông tin chỉ dùng để gửi voucher<br/>
              Không chia sẻ cho bên thứ ba
            </p>

            {contactError && (
              <p style={{ color: 'var(--color-danger)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--spacing-sm)' }}>
                {contactError}
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
              disabled={contact.length < 5}
            >
              Quay ngay!
            </button>
          </div>
        )}

        {/* Có SĐT/Email sẵn — hiện nút quay ngay không cần nhập lại */}
        {!isSpinning && !showContactInput && (
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
              onClick={() => setShowContactInput(true)}
            >
              Dùng liên hệ khác
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
