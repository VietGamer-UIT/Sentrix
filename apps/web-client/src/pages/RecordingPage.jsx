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

    // Gửi API ngầm sau khi đã navigate (fire-and-forget)
    submitFeedback({
      tenantId,
      location: decodeURIComponent(location),
      audioBlob: audioBlob || null,
      textContent: textContent.trim() || null
    }).catch(err => {
      // Lỗi ngầm — log để debug, không ảnh hưởng UX
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
