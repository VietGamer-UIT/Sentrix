import { useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { mockSpinAPI, SPIN_PRIZES } from '../mocks/gamification.js'

/**
 * SpinPage — Bước 5 trong user-flow.md
 *
 * UX Requirements:
 * - Hiện ngay sau màn hình cảm ơn — gamification hook
 * - Khách nhập SĐT → bấm "Quay ngay" → vòng quay chạy
 * - Giải thích rõ: SĐT chỉ để gửi voucher qua Zalo, không mục đích khác
 * - Tối giản: chỉ 1 ô SĐT + 1 nút Quay — đúng user-flow.md
 * - Nút "Bỏ qua" phụ cho người không muốn để lại SĐT
 *
 * Rủi ro (user-flow.md): Khách ngại lộ thông tin cá nhân
 * Giải pháp: Cam kết rõ ràng ngay dưới ô input
 *
 * ⚠️ MOCK — /api/gamification/spin chưa có (xem docs/api-contract.md mục 4)
 *   Khi Tuyền báo endpoint sống:
 *   1. Đổi VITE_USE_MOCK_GAMIFICATION=false trong .env
 *   2. Import spinAPI từ api/gamification.js (tạo file mới)
 *   3. Thay mockSpinAPI(...) bằng spinAPI(...)
 */
function SpinPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const tenantId = searchParams.get('tenant_id') || 'demo_tenant'
  const location = searchParams.get('location') || 'Bàn 1'

  const [phone, setPhone] = useState('')
  const [phoneError, setPhoneError] = useState(null)
  const [isSpinning, setIsSpinning] = useState(false)
  const [rotation, setRotation] = useState(0)

  const segmentAngle = 360 / SPIN_PRIZES.length

  const validatePhone = (p) => /^(0[3|5|7|8|9])[0-9]{8}$/.test(p.trim())

  const handlePhoneChange = (e) => {
    // Chỉ cho nhập số
    const val = e.target.value.replace(/\D/g, '')
    setPhone(val)
    setPhoneError(null)
  }

  const handleSpin = async () => {
    if (!validatePhone(phone)) {
      setPhoneError('Số điện thoại không hợp lệ. Vui lòng nhập đúng 10 chữ số (VD: 0912345678)')
      return
    }

    setIsSpinning(true)
    setPhoneError(null)

    // ⚠️ MOCK — Thay bằng API thật khi Tuyền implement /api/gamification/spin
    const result = await mockSpinAPI(tenantId, phone)

    // Tính góc quay: dừng tại trung tâm segment của prize trúng
    const prizeIndex = SPIN_PRIZES.findIndex(p => p.id === result.prize)
    // Offset để pointer (▼ ở đỉnh) trỏ đúng vào giữa segment
    const targetAngle = prizeIndex * segmentAngle + segmentAngle / 2
    // Quay thêm 8 vòng để thấy rõ animation
    const totalRotation = rotation + 360 * 8 + (360 - targetAngle % 360)
    setRotation(totalRotation)

    // Chờ animation CSS 4s xong mới navigate
    setTimeout(() => {
      navigate(
        `/voucher?tenant_id=${tenantId}` +
        `&location=${encodeURIComponent(location)}` +
        `&prize=${result.prize}` +
        `&prize_label=${encodeURIComponent(result.prize_label)}` +
        `&voucher_code=${encodeURIComponent(result.voucher_code || '')}` +
        `&message=${encodeURIComponent(result.message)}`
      )
    }, 4200)
  }

  const handleSkip = () => {
    navigate(`/voucher?tenant_id=${tenantId}&location=${encodeURIComponent(location)}&skipped=true`)
  }

  // === Render SVG vòng quay ===
  const renderWheel = () => {
    const cx = 130, cy = 130, r = 120
    return (
      <svg width="260" height="260" viewBox="0 0 260 260">
        {/* Shadow / glow ring */}
        <circle cx={cx} cy={cy} r={r + 4} fill="none" stroke="rgba(0,194,255,0.15)" strokeWidth="8"/>

        {SPIN_PRIZES.map((prize, i) => {
          const startRad = ((i * segmentAngle) - 90) * (Math.PI / 180)
          const endRad = (((i + 1) * segmentAngle) - 90) * (Math.PI / 180)
          const x1 = cx + r * Math.cos(startRad)
          const y1 = cy + r * Math.sin(startRad)
          const x2 = cx + r * Math.cos(endRad)
          const y2 = cy + r * Math.sin(endRad)

          // Text position: giữa segment, 70% bán kính
          const midRad = ((i + 0.5) * segmentAngle - 90) * (Math.PI / 180)
          const textX = cx + (r * 0.68) * Math.cos(midRad)
          const textY = cy + (r * 0.68) * Math.sin(midRad)
          const textAngle = (i + 0.5) * segmentAngle

          return (
            <g key={prize.id}>
              {/* Segment */}
              <path
                d={`M${cx},${cy} L${x1},${y1} A${r},${r} 0 0,1 ${x2},${y2} Z`}
                fill={prize.color}
                opacity="0.9"
                stroke="rgba(10,10,15,0.5)"
                strokeWidth="1.5"
              />
              {/* Label */}
              <text
                x={textX}
                y={textY}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="white"
                fontSize="10"
                fontWeight="800"
                fontFamily="'Be Vietnam Pro', sans-serif"
                transform={`rotate(${textAngle}, ${textX}, ${textY})`}
                style={{ pointerEvents: 'none', userSelect: 'none' }}
              >
                {prize.label}
              </text>
            </g>
          )
        })}

        {/* Center cap */}
        <circle cx={cx} cy={cy} r="18" fill="var(--color-bg-card)" stroke="rgba(0,194,255,0.3)" strokeWidth="2"/>
        <circle cx={cx} cy={cy} r="6" fill="var(--color-primary)"/>
      </svg>
    )
  }

  return (
    <div className="page">
      <div className="bg-glow bg-glow--primary" style={{ background: 'rgba(124,58,237,0.15)', top: -100, right: -100 }}/>
      <div className="bg-glow bg-glow--accent"/>

      <div className="page-content" style={{ textAlign: 'center' }}>

        {/* Header */}
        <div className="fade-up">
          <h1 style={{ fontSize: 'var(--font-size-2xl)' }}>🎡 Vòng quay may mắn</h1>
          <p style={{ marginTop: 8 }}>Nhập SĐT để quay thưởng ngay!</p>
        </div>

        {/* Vòng quay */}
        <div className="fade-up fade-up--delay-1" style={{ position: 'relative', display: 'inline-block' }}>
          {/* Con trỏ ▼ */}
          <div style={{
            position: 'absolute',
            top: -8,
            left: '50%',
            transform: 'translateX(-50%)',
            fontSize: 22,
            zIndex: 2,
            filter: 'drop-shadow(0 2px 6px rgba(0,0,0,0.6))',
            color: 'var(--color-primary)'
          }}>
            ▼
          </div>

          {/* Wheel wrapper */}
          <div style={{
            transform: `rotate(${rotation}deg)`,
            transition: isSpinning ? 'transform 4s cubic-bezier(0.17, 0.67, 0.12, 0.99)' : 'none',
            borderRadius: '50%',
            overflow: 'hidden',
            boxShadow: '0 0 30px rgba(0,194,255,0.2), 0 4px 30px rgba(0,0,0,0.5)',
            display: 'inline-block'
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

            {/* Cam kết bảo mật */}
            <p style={{
              fontSize: 'var(--font-size-xs)',
              color: 'var(--color-text-muted)',
              margin: '8px 0 var(--spacing-md)',
              lineHeight: 1.6
            }}>
              🔒 SĐT chỉ dùng để gửi voucher qua Zalo · Không chia sẻ cho bên thứ 3
            </p>

            {phoneError && (
              <p style={{ color: 'var(--color-danger)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--spacing-sm)' }}>
                ⚠️ {phoneError}
              </p>
            )}

            <button
              id="btn-spin"
              className="btn btn--primary"
              onClick={handleSpin}
              disabled={phone.length < 10}
            >
              🎯 Quay ngay!
            </button>
          </div>
        )}

        {/* Loading state khi đang quay */}
        {isSpinning && (
          <div className="fade-up" style={{ textAlign: 'center' }}>
            <p style={{ color: 'var(--color-primary)', fontWeight: 600 }}>
              🎡 Đang quay... Chúc may mắn!
            </p>
          </div>
        )}

        {/* Skip */}
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
