import { useState, useRef, useEffect, useCallback } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { submitFeedback } from '../api/feedback.js'

const MAX_DURATION_SEC = 15

/**
 * RecordingPage — Bước 3 trong user-flow.md
 *
 * UX Requirements:
 * - Bấm nút → bắt đầu ghi âm ngay (không phải "giữ" — dễ hơn trên mobile)
 * - Hiệu ứng sóng âm 7 bars phản hồi tức thời khi đang ghi
 * - Đồng hồ đếm ngược 15 giây, tự dừng khi hết giờ
 * - Cảnh báo màu vàng khi còn ≤ 5 giây
 * - Nút phụ "gõ văn bản" thay thế cho người không muốn nói
 * - Optimistic UI: navigate ngay, gửi API ngầm (không chờ server)
 *
 * Rủi ro (user-flow.md): Khách không biết mic có đang thu hay không
 * Giải pháp: Waveform animation + text trạng thái rõ ràng + đếm ngược
 */
function RecordingPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const tenantId = searchParams.get('tenant_id') || 'demo_tenant'
  const location = searchParams.get('location') || 'Bàn 1'
  const mode = searchParams.get('mode') || 'audio'

  // === State ===
  const [isRecording, setIsRecording] = useState(false)
  const [timeLeft, setTimeLeft] = useState(MAX_DURATION_SEC)
  const [audioBlob, setAudioBlob] = useState(null)
  const [audioDurationSec, setAudioDurationSec] = useState(0)
  const [error, setError] = useState(null)
  const [textContent, setTextContent] = useState('')
  const [showText, setShowText] = useState(mode === 'text')
  const [recordStartTime, setRecordStartTime] = useState(null)
  // Giai đoạn 7: SĐT tùy chọn để backend tính RFMS
  const [customerPhone, setCustomerPhone] = useState('')
  const [showPhoneInput, setShowPhoneInput] = useState(false)

  // === Refs ===
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const timerRef = useRef(null)
  const streamRef = useRef(null)

  // Cleanup khi unmount
  useEffect(() => {
    return () => {
      clearInterval(timerRef.current)
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop())
      }
    }
  }, [])

  // Countdown timer khi đang ghi
  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            handleStopRecording()
            return 0
          }
          return prev - 1
        })
      }, 1000)
    }
    return () => clearInterval(timerRef.current)
  }, [isRecording]) // eslint-disable-line

  const handleStartRecording = useCallback(async () => {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
          ? 'audio/webm'
          : 'audio/ogg'

      const recorder = new MediaRecorder(stream, { mimeType })
      mediaRecorderRef.current = recorder
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType })
        setAudioBlob(blob)
        stream.getTracks().forEach(t => t.stop())
        const elapsed = MAX_DURATION_SEC - timeLeft + 1
        setAudioDurationSec(Math.min(elapsed, MAX_DURATION_SEC))
      }

      recorder.start(200)
      setIsRecording(true)
      setRecordStartTime(Date.now())
      setTimeLeft(MAX_DURATION_SEC)
    } catch (err) {
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setError('Trình duyệt cần quyền truy cập microphone. Bấm vào biểu tượng 🔒 trên thanh địa chỉ để cho phép.')
      } else if (err.name === 'NotFoundError') {
        setError('Không tìm thấy microphone. Thử gõ văn bản nhé!')
      } else {
        setError('Không thể khởi động microphone. Thử chuyển sang gõ văn bản.')
      }
    }
  }, [timeLeft])

  const handleStopRecording = useCallback(() => {
    clearInterval(timerRef.current)
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    setIsRecording(false)
  }, [])

  const handleToggleRecord = () => {
    if (isRecording) {
      handleStopRecording()
    } else if (!audioBlob) {
      handleStartRecording()
    }
  }

  const handleSubmit = () => {
    if (!audioBlob && !textContent.trim()) {
      setError('Vui lòng ghi âm hoặc gõ phản hồi trước khi gửi.')
      return
    }

    // Optimistic UI: chuyển sang màn hình xác nhận NGAY — đúng user-flow.md Bước 4
    navigate(`/done?tenant_id=${tenantId}&location=${encodeURIComponent(location)}`)

    // Gửi API ngầm (fire-and-forget) — Giai đoạn 7: thêm customerPhone + totalSpending
    submitFeedback({
      tenantId,
      location: decodeURIComponent(location),
      audioBlob: audioBlob || null,
      textContent: textContent.trim() || null,
      customerPhone: customerPhone.trim() || null,
      totalSpending: 0, // Giai đoạn tương lai: lấy từ POS/input
    }).then(result => {
      // Lưu kết quả AI vào sessionStorage để ConfirmationPage hiển thị insight
      try {
        sessionStorage.setItem('sentrix_api_result', JSON.stringify(result))
      } catch { /* ignore */ }
    }).catch(err => {
      console.error('[Sentrix] Feedback submit failed silently:', err)
    })
  }

  const handleRetry = () => {
    setAudioBlob(null)
    setAudioDurationSec(0)
    setTimeLeft(MAX_DURATION_SEC)
    setError(null)
    setRecordStartTime(null)
  }

  const isWarning = timeLeft <= 5 && isRecording
  const waveformBars = [1, 2, 3, 4, 5, 6, 7]

  return (
    <div className="page">
      <div className="bg-glow bg-glow--primary" />
      <div className="bg-glow bg-glow--accent" />

      <div className="page-content">

        {/* Header */}
        <div style={{ textAlign: 'center' }} className="fade-up">
          <h1 style={{ fontSize: 'var(--font-size-xl)' }}>
            {showText ? '✍️ Gõ phản hồi' : '🎙️ Ghi âm phản hồi'}
          </h1>
          <div style={{ marginTop: 8 }}>
            <span className="chip chip--location">📍 {decodeURIComponent(location)}</span>
          </div>
        </div>

        {/* === CHẾ ĐỘ GHI ÂM === */}
        {!showText && (
          <div className="card fade-up fade-up--delay-1" style={{ width: '100%', textAlign: 'center' }}>

            {/* Waveform animation */}
            <div style={{ display: 'flex', justifyContent: 'center', height: 48, marginBottom: 'var(--spacing-md)' }}>
              <div className={`waveform ${isRecording ? 'waveform--active' : ''}`}>
                {waveformBars.map(i => (
                  <div key={i} className="waveform-bar" style={{
                    height: audioBlob ? '30%' : isRecording ? undefined : '20%',
                    background: audioBlob
                      ? 'linear-gradient(to top, #10B981, #34D399)'
                      : 'linear-gradient(to top, var(--color-primary), var(--color-accent))'
                  }} />
                ))}
              </div>
            </div>

            {/* Trạng thái + Countdown */}
            <div style={{ minHeight: 40, marginBottom: 'var(--spacing-md)' }}>
              {audioBlob ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                  <span style={{ fontSize: 32 }}>✅</span>
                  <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-success)', fontWeight: 600 }}>
                    Ghi âm xong · {audioDurationSec}s
                  </p>
                </div>
              ) : isRecording ? (
                <div>
                  <div className={`countdown ${isWarning ? 'countdown--warning' : ''}`}
                       aria-live="polite" aria-label={`Còn ${timeLeft} giây`}>
                    {timeLeft}s
                  </div>
                  <p style={{ fontSize: 'var(--font-size-xs)', color: isWarning ? 'var(--color-warning)' : 'var(--color-text-muted)', marginTop: 4 }}>
                    {isWarning ? '⚡ Gần xong rồi!' : 'Đang ghi... Bấm lại để dừng'}
                  </p>
                </div>
              ) : (
                <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
                  Bấm nút để bắt đầu ghi âm
                </p>
              )}
            </div>

            {/* Nút ghi âm tròn lớn */}
            {!audioBlob && (
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 'var(--spacing-md)' }}>
                <button
                  id="btn-toggle-record"
                  className={`btn-record ${isRecording ? 'btn-record--recording' : ''}`}
                  onClick={handleToggleRecord}
                  aria-label={isRecording ? 'Đang ghi âm, bấm để dừng' : 'Bấm để ghi âm'}
                >
                  {isRecording ? (
                    /* Icon Stop */
                    <svg width="30" height="30" viewBox="0 0 24 24" fill="white">
                      <rect x="6" y="6" width="12" height="12" rx="2"/>
                    </svg>
                  ) : (
                    /* Icon Mic */
                    <svg width="38" height="38" viewBox="0 0 24 24" fill="none"
                         stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                      <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                      <line x1="12" y1="19" x2="12" y2="23"/>
                      <line x1="8" y1="23" x2="16" y2="23"/>
                    </svg>
                  )}
                </button>
              </div>
            )}

            {/* Sau khi có audio blob */}
            {audioBlob && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
                {/* Input SĐT tùy chọn */}
                <PhoneInputSection
                  customerPhone={customerPhone}
                  setCustomerPhone={setCustomerPhone}
                  showPhoneInput={showPhoneInput}
                  setShowPhoneInput={setShowPhoneInput}
                />
                <button id="btn-submit-audio" className="btn btn--primary" onClick={handleSubmit}>
                  🚀 Gửi phản hồi
                </button>
                <button id="btn-retry-record" className="btn btn--secondary" onClick={handleRetry}>
                  🔄 Ghi lại
                </button>
              </div>
            )}

            {/* Error */}
            {error && (
              <p style={{
                color: 'var(--color-danger)',
                fontSize: 'var(--font-size-sm)',
                marginTop: 'var(--spacing-md)',
                lineHeight: 1.5
              }}>
                ⚠️ {error}
              </p>
            )}
          </div>
        )}

        {/* === CHẾ ĐỘ GÕ TEXT === */}
        {showText && (
          <div className="card fade-up fade-up--delay-1" style={{ width: '100%' }}>
            <div className="input-group">
              <label className="input-label" htmlFor="text-feedback">
                Cảm nhận của bạn
              </label>
              <textarea
                id="text-feedback"
                className="textarea"
                placeholder="Ví dụ: Đồ ăn ngon, nhân viên thân thiện. Nhưng hơi chờ lâu..."
                value={textContent}
                onChange={(e) => { setTextContent(e.target.value); setError(null) }}
                maxLength={2000}
                rows={5}
                autoFocus
              />
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textAlign: 'right' }}>
                {textContent.length} / 2000
              </p>
            </div>

            {error && (
              <p style={{ color: 'var(--color-danger)', fontSize: 'var(--font-size-sm)', margin: 'var(--spacing-sm) 0' }}>
                ⚠️ {error}
              </p>
            )}

            {/* Input SĐT tùy chọn — Giai đoạn 7: để backend tính RFMS personalized */}
            <PhoneInputSection
              customerPhone={customerPhone}
              setCustomerPhone={setCustomerPhone}
              showPhoneInput={showPhoneInput}
              setShowPhoneInput={setShowPhoneInput}
            />

            <button
              id="btn-submit-text"
              className="btn btn--primary"
              onClick={handleSubmit}
              disabled={textContent.trim().length < 2}
              style={{ marginTop: 'var(--spacing-md)' }}
            >
              🚀 Gửi phản hồi
            </button>
          </div>
        )}

        {/* Toggle giữa audio / text */}
        <button
          id="btn-toggle-mode"
          className="btn btn--ghost"
          onClick={() => { setShowText(!showText); setError(null); handleRetry() }}
        >
          {showText ? '🎙️ Chuyển sang ghi âm' : '✍️ Thích gõ hơn?'}
        </button>

      </div>
    </div>
  )
}

export default RecordingPage

/**
 * PhoneInputSection — Input SĐT tùy chọn (Giai đoạn 7)
 *
 * Mục đích: để backend hash SĐT và tính RFMS cá nhân hóa.
 * Hiển thị dạng collapsible — không bắt buộc, không gây friction.
 * Backend sẽ hash SĐT (SHA-256 + salt) trước khi lưu Firestore.
 */
function PhoneInputSection({ customerPhone, setCustomerPhone, showPhoneInput, setShowPhoneInput }) {
  const validatePhone = (val) => /^(0|\+84)[0-9]{8,10}$/.test(val.replace(/\s/g, ''))

  return (
    <div style={{ marginBottom: 'var(--spacing-sm)' }}>
      {!showPhoneInput ? (
        <button
          type="button"
          onClick={() => setShowPhoneInput(true)}
          style={{
            background: 'none', border: 'none',
            color: 'var(--color-text-muted)',
            fontSize: 'var(--font-size-xs)',
            cursor: 'pointer', textDecoration: 'underline',
            padding: '4px 0', fontFamily: 'var(--font-family)',
          }}
        >
          📱 Nhận ưu đãi cá nhân? Thêm số điện thoại (tùy chọn)
        </button>
      ) : (
        <div style={{
          padding: 'var(--spacing-md)',
          background: 'rgba(0,194,255,0.04)',
          border: '1px solid rgba(0,194,255,0.12)',
          borderRadius: 'var(--radius-md)',
        }}>
          <label style={{
            display: 'block', fontSize: 'var(--font-size-xs)',
            color: 'var(--color-text-secondary)', marginBottom: 6, fontWeight: 600
          }}>
            📱 Số điện thoại (tùy chọn)
          </label>
          <input
            type="tel"
            inputMode="numeric"
            placeholder="0901 234 567"
            value={customerPhone}
            onChange={e => setCustomerPhone(e.target.value)}
            maxLength={15}
            style={{
              width: '100%', padding: '10px 12px',
              background: 'rgba(255,255,255,0.06)',
              border: `1px solid ${customerPhone && !validatePhone(customerPhone) ? 'rgba(239,68,68,0.5)' : 'rgba(255,255,255,0.1)'}`,
              borderRadius: 'var(--radius-sm)',
              color: 'var(--color-text-primary)',
              fontSize: 'var(--font-size-sm)', fontFamily: 'var(--font-family)',
              boxSizing: 'border-box',
            }}
          />
          {customerPhone && !validatePhone(customerPhone) && (
            <p style={{ fontSize: '0.68rem', color: 'var(--color-danger)', marginTop: 4 }}>
              SĐT không hợp lệ (ví dụ đúng: 0901234567)
            </p>
          )}
          <p style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)', marginTop: 6, lineHeight: 1.5 }}>
            🔒 SĐT được mã hóa (hash) trước khi lưu. Không chia sẻ với bên thứ ba.
          </p>
          <button
            type="button"
            onClick={() => { setShowPhoneInput(false); setCustomerPhone('') }}
            style={{
              background: 'none', border: 'none',
              color: 'var(--color-text-muted)', fontSize: '0.68rem',
              cursor: 'pointer', padding: '2px 0', fontFamily: 'var(--font-family)',
            }}
          >
            ✕ Bỏ qua
          </button>
        </div>
      )}
    </div>
  )
}
