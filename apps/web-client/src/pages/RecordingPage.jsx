import { useState, useRef, useEffect, useCallback } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { submitFeedback } from '../api/feedback.js'

const MAX_DURATION_SEC = 15

/**
 * RecordingPage — Bước 3 trong user-flow.md
 *
 * UX Requirements (từ user-flow.md):
 * - Giữ nút để ghi âm, thả để dừng
 * - Hiệu ứng sóng âm visual phản hồi tức thời
 * - Đồng hồ đếm ngược 15 giây, tự dừng khi hết giờ
 * - Nút phụ "gõ văn bản" thay thế
 * - Rủi ro: khách không biết mic có đang thu không → Visual rõ ràng
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
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [textContent, setTextContent] = useState('')
  const [showText, setShowText] = useState(mode === 'text')

  // === Refs ===
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])
  const timerRef = useRef(null)
  const streamRef = useRef(null)

  // Cleanup khi unmount
  useEffect(() => {
    return () => {
      stopRecording()
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop())
      }
    }
  }, [])

  // Countdown timer
  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            stopRecording()
            return 0
          }
          return prev - 1
        })
      }, 1000)
    }
    return () => clearInterval(timerRef.current)
  }, [isRecording])

  const startRecording = useCallback(async () => {
    setError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const recorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/ogg'
      })
      mediaRecorderRef.current = recorder
      chunksRef.current = []

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType })
        setAudioBlob(blob)
        // Dừng mic
        stream.getTracks().forEach(t => t.stop())
      }

      recorder.start(100) // chunk mỗi 100ms để waveform mượt
      setIsRecording(true)
      setTimeLeft(MAX_DURATION_SEC)
    } catch (err) {
      if (err.name === 'NotAllowedError') {
        setError('Bạn cần cho phép truy cập microphone. Vui lòng thử lại.')
      } else {
        setError('Không thể khởi động microphone. Thử gõ văn bản nhé.')
      }
    }
  }, [])

  const stopRecording = useCallback(() => {
    clearInterval(timerRef.current)
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    setIsRecording(false)
  }, [])

  const handleRecordButton = () => {
    if (isRecording) {
      stopRecording()
    } else if (!audioBlob) {
      startRecording()
    }
  }

  const handleSubmit = async () => {
    if (!audioBlob && !textContent.trim()) {
      setError('Vui lòng ghi âm hoặc gõ phản hồi trước.')
      return
    }

    setIsSubmitting(true)
    setError(null)

    // Optimistic UI: chuyển sang màn hình xác nhận NGAY (không chờ API)
    // Gửi API chạy ngầm ở background — đúng theo user-flow.md Bước 4
    navigate(`/done?tenant_id=${tenantId}&location=${encodeURIComponent(location)}`)

    // Gửi API ngầm sau khi đã navigate
    submitFeedback({
      tenantId,
      location,
      audioBlob,
      textContent: textContent.trim() || null
    }).catch(err => {
      // Lỗi gửi ngầm — log để debug, không hiện cho user vì đã optimistic
      console.error('[Feedback submit error]', err)
    })
  }

  const handleRetry = () => {
    setAudioBlob(null)
    setTimeLeft(MAX_DURATION_SEC)
    setError(null)
  }

  // Waveform bars (7 bars)
  const waveformBars = Array.from({ length: 7 })

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
          <span className="chip chip--location" style={{ marginTop: 8 }}>
            📍 {decodeURIComponent(location)}
          </span>
        </div>

        <div className="card fade-up fade-up--delay-1" style={{ textAlign: 'center' }}>

          {!showText ? (
            /* === CHẾ ĐỘ GHI ÂM === */
            <>
              {/* Waveform visual */}
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 'var(--spacing-lg)' }}>
                <div className={`waveform ${isRecording ? 'waveform--active' : ''}`}>
                  {waveformBars.map((_, i) => (
                    <div key={i} className="waveform-bar" />
                  ))}
                </div>
              </div>

              {/* Countdown */}
              <div className={`countdown ${timeLeft <= 5 ? 'countdown--warning' : ''}`}
                   aria-live="polite" aria-label={`Còn ${timeLeft} giây`}>
                {audioBlob ? '✅' : `${timeLeft}s`}
              </div>

              <p style={{ fontSize: 'var(--font-size-sm)', margin: 'var(--spacing-md) 0' }}>
                {isRecording
                  ? 'Đang ghi... Nhả nút để dừng'
                  : audioBlob
                    ? 'Ghi âm xong! Bấm gửi hoặc ghi lại'
                    : 'Giữ nút để bắt đầu ghi'}
              </p>

              {/* Nút ghi âm tròn lớn */}
              {!audioBlob && (
                <div style={{ display: 'flex', justifyContent: 'center', margin: 'var(--spacing-md) 0' }}>
                  <button
                    id="btn-hold-record"
                    className={`btn-record ${isRecording ? 'btn-record--recording' : ''}`}
                    onMouseDown={handleRecordButton}
                    onTouchStart={(e) => { e.preventDefault(); if (!isRecording) startRecording() }}
                    onMouseUp={() => { if (isRecording) stopRecording() }}
                    onTouchEnd={(e) => { e.preventDefault(); if (isRecording) stopRecording() }}
                    aria-label={isRecording ? 'Đang ghi âm, nhả để dừng' : 'Giữ để ghi âm'}
                  >
                    {isRecording ? (
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="white">
                        <rect x="6" y="6" width="12" height="12" rx="2" />
                      </svg>
                    ) : (
                      <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                        <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                        <line x1="12" y1="19" x2="12" y2="23" />
                        <line x1="8" y1="23" x2="16" y2="23" />
                      </svg>
                    )}
                  </button>
                </div>
              )}

              {/* Sau khi có audio blob */}
              {audioBlob && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)', marginTop: 'var(--spacing-md)' }}>
                  <button id="btn-submit-audio" className="btn btn--primary" onClick={handleSubmit} disabled={isSubmitting}>
                    {isSubmitting ? 'Đang gửi...' : '🚀 Gửi phản hồi'}
                  </button>
                  <button id="btn-retry-record" className="btn btn--secondary" onClick={handleRetry}>
                    🔄 Ghi lại
                  </button>
                </div>
              )}
            </>
          ) : (
            /* === CHẾ ĐỘ GÕ TEXT === */
            <>
              <div className="input-group" style={{ textAlign: 'left' }}>
                <label className="input-label" htmlFor="text-feedback">
                  Phản hồi của bạn
                </label>
                <textarea
                  id="text-feedback"
                  className="textarea"
                  placeholder="Nhập cảm nhận của bạn về dịch vụ hôm nay..."
                  value={textContent}
                  onChange={(e) => setTextContent(e.target.value)}
                  maxLength={2000}
                  rows={4}
                />
                <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', textAlign: 'right' }}>
                  {textContent.length}/2000
                </p>
              </div>
              <button
                id="btn-submit-text"
                className="btn btn--primary"
                onClick={handleSubmit}
                disabled={isSubmitting || textContent.trim().length === 0}
                style={{ marginTop: 'var(--spacing-md)' }}
              >
                {isSubmitting ? 'Đang gửi...' : '🚀 Gửi phản hồi'}
              </button>
            </>
          )}

          {/* Error message */}
          {error && (
            <p style={{ color: 'var(--color-danger)', fontSize: 'var(--font-size-sm)', marginTop: 'var(--spacing-md)' }}>
              ⚠️ {error}
            </p>
          )}
        </div>

        {/* Toggle giữa audio và text */}
        <button
          className="btn btn--ghost"
          onClick={() => { setShowText(!showText); setError(null); setAudioBlob(null) }}
        >
          {showText ? '🎙️ Chuyển sang ghi âm' : '✍️ Thích gõ hơn?'}
        </button>
      </div>
    </div>
  )
}

export default RecordingPage
