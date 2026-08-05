import { useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { mockSpinAPI, SPIN_PRIZES } from '../mocks/gamification.js'

/**
 * SpinPage — Bước 5 trong user-flow.md
 *
 * UX Requirements (từ user-flow.md):
 * - Vòng quay may mắn xuất hiện ngay sau màn hình cảm ơn
 * - Khách nhập SĐT → bấm "Quay ngay" → vòng quay chạy
 * - Giải thích rõ SĐT chỉ dùng để gửi voucher qua Zalo
 * - Chỉ 1 ô nhập SĐT và 1 nút — tối giản
 *
 * ⚠️ MOCK — Backend /api/gamification/spin chưa có
 *   Thay mockSpinAPI(...) bằng fetch thật khi Tuyền báo xong
 *   Xem: docs/api-contract.md mục 4
 *   Cờ môi trường: VITE_USE_MOCK_GAMIFICATION
 */
function SpinPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const tenantId = searchParams.get('tenant_id') || 'demo_tenant'
  const location = searchParams.get('location') || 'Bàn 1'

  const [phone, setPhone] = useState('')
  const [isSpinning, setIsSpinning] = useState(false)
  const [spinDeg, setSpinDeg] = useState(0)
  const [error, setError] = useState(null)

  // Tính góc mỗi ô của vòng quay
  const segmentDeg = 360 / SPIN_PRIZES.length

  const validatePhone = (p) => /^(0[3|5|7|8|9])[0-9]{8}$/.test(p.trim())

  const handleSpin = async () => {
    if (!validatePhone(phone)) {
      setError('Vui lòng nhập số điện thoại Việt Nam hợp lệ (10 số)')
      return
    }
    setError(null)
    setIsSpinning(true)

    // ⚠️ MOCK — Thay bằng API thật khi Tuyền implement /api/gamification/spin
    const result = await mockSpinAPI(tenantId, phone)

    // Tính góc quay để vòng quay dừng đúng ô prize
    const prizeIndex = SPIN_PRIZES.findIndex(p => p.id === result.prize)
    const targetSegmentCenter = prizeIndex * segmentDeg + segmentDeg / 2
    const extraSpins = 360 * 5 // quay thêm 5 vòng cho đẹp
    const finalDeg = spinDeg + extraSpins + (360 - targetSegmentCenter)

    setSpinDeg(finalDeg)

    // Chờ animation xong (3s theo CSS transition) rồi chuyển màn hình
    setTimeout(() => {
      navigate(`/voucher?tenant_id=${tenantId}&location=${encodeURIComponent(location)}&prize=${result.prize}&prize_label=${encodeURIComponent(result.prize_label)}&voucher_code=${encodeURIComponent(result.voucher_code || '')}&message=${encodeURIComponent(result.message)}`)
    }, 3500)
  }

  return (
    <div className="page">
      <div className="bg-glow bg-glow--primary" style={{ background: 'rgba(124, 58, 237, 0.15)' }} />
      <div className="bg-glow bg-glow--accent" />

      <div className="page-content" style={{ textAlign: 'center' }}>
        {/* Header */}
        <div className="fade-up">
          <h1 style={{ fontSize: 'var(--font-size-2xl)' }}>🎡 Vòng quay may mắn</h1>
          <p style={{ marginTop: 8 }}>Nhập SĐT để quay và nhận quà!</p>
        </div>

        {/* Spin Wheel */}
        <div className="spin-wheel-container fade-up fade-up--delay-1">
          <div className="spin-pointer">▼</div>
          <div
            className="spin-wheel"
            style={{ transform: `rotate(${spinDeg}deg)` }}
          >
            <svg viewBox="0 0 200 200" width="100%" height="100%">
              {SPIN_PRIZES.map((prize, i) => {
                const startAngle = (i * segmentDeg - 90) * (Math.PI / 180)
                const endAngle = ((i + 1) * segmentDeg - 90) * (Math.PI / 180)
                const x1 = 100 + 95 * Math.cos(startAngle)
                const y1 = 100 + 95 * Math.sin(startAngle)
                const x2 = 100 + 95 * Math.cos(endAngle)
                const y2 = 100 + 95 * Math.sin(endAngle)
                const midAngle = ((i + 0.5) * segmentDeg - 90) * (Math.PI / 180)
                const textX = 100 + 65 * Math.cos(midAngle)
                const textY = 100 + 65 * Math.sin(midAngle)

                return (
                  <g key={prize.id}>
                    <path
                      d={`M100,100 L${x1},${y1} A95,95 0 0,1 ${x2},${y2} Z`}
                      fill={prize.color}
                      opacity="0.85"
                    />
                    <text
                      x={textX}
                      y={textY}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fill="white"
                      fontSize="9"
                      fontWeight="700"
                      fontFamily="Be Vietnam Pro, sans-serif"
                      transform={`rotate(${(i + 0.5) * segmentDeg}, ${textX}, ${textY})`}
                    >
                      {prize.label}
                    </text>
                  </g>
                )
              })}
              <circle cx="100" cy="100" r="12" fill="#13131A" />
            </svg>
          </div>
        </div>

        {/* Input SĐT */}
        <div className="card fade-up fade-up--delay-2" style={{ width: '100%' }}>
          <div className="input-group">
            <label className="input-label" htmlFor="phone-input">Số điện thoại</label>
            <input
              id="phone-input"
              className="input"
              type="tel"
              placeholder="0901234567"
              value={phone}
              onChange={(e) => { setPhone(e.target.value); setError(null) }}
              maxLength={10}
              disabled={isSpinning}
              inputMode="numeric"
            />
          </div>

          <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', margin: 'var(--spacing-sm) 0 var(--spacing-md)' }}>
            🔒 SĐT chỉ dùng để gửi voucher qua Zalo, không lưu trữ mục đích khác
          </p>

          {error && (
            <p style={{ color: 'var(--color-danger)', fontSize: 'var(--font-size-sm)', marginBottom: 'var(--spacing-sm)' }}>
              ⚠️ {error}
            </p>
          )}

          <button
            id="btn-spin"
            className="btn btn--primary"
            onClick={handleSpin}
            disabled={isSpinning || phone.length < 10}
          >
            {isSpinning ? '🎡 Đang quay...' : '🎯 Quay ngay!'}
          </button>
        </div>

        {/* Skip */}
        {!isSpinning && (
          <button
            className="btn btn--ghost"
            onClick={() => navigate(`/voucher?tenant_id=${tenantId}&location=${encodeURIComponent(location)}&skipped=true`)}
          >
            Bỏ qua
          </button>
        )}
      </div>
    </div>
  )
}

export default SpinPage
