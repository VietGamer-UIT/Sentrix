import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { submitFeedback } from '../api/feedback.js'

const MAX_DURATION_SEC = 15

/**
 * RecordingOverlay — Overlay thu âm đè lên LandingPage
 *
 * Không redirect URL. Hiện dạng modal full-screen với blur backdrop.
 * Tích hợp Web Speech API (SpeechRecognition) để hiện transcript realtime mờ.
 *
 * Module 2 (PDPA) — thêm:
 *   - Toggle "Phản hồi ẩn danh" (Điều 5 NĐ 356/2025: quyền từ chối)
 *   - Khi KHÔNG ẩn danh: ô nhập SĐT + mini OTP flow (Lớp 1 Module 1)
 *   - voucher_eligible = false khi ẩn danh (không gọi OTP, không phát voucher)
 *
 * Props:
 *   tenantId      string  — từ QR code
 *   location      string  — encoded location từ QR
 *   initialMode   string  — 'audio' | 'text'
 *   onClose       fn      — callback khi đóng overlay (bấm X)
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Chế độ thử nghiệm: bỏ qua OTP (set VITE_SKIP_OTP=true trong .env)
// Khi deploy production, xóa biến này hoặc để false
const SKIP_OTP = import.meta.env.VITE_SKIP_OTP === 'true'

function RecordingOverlay({ tenantId, location, initialMode = 'audio', onClose }) {
  const navigate = useNavigate()

  const [mode, setMode]                       = useState(initialMode)
  const [isRecording, setIsRecording]         = useState(false)
  const [timeLeft, setTimeLeft]               = useState(MAX_DURATION_SEC)
  const [audioBlob, setAudioBlob]             = useState(null)
  const [audioDurationSec, setAudioDurationSec] = useState(0)
  const [error, setError]                     = useState(null)
  const [textContent, setTextContent]         = useState('')
  // Fix bug double-click: chặn submit 2 lần → duplicate Firestore document
  const [isSubmitting, setIsSubmitting]       = useState(false)

  // SpeechRecognition realtime transcript
  const [liveTranscript, setLiveTranscript]   = useState('')
  const [speechSupported, setSpeechSupported] = useState(false)

  // ── Module 2: Anonymous Toggle + OTP ─────────────────────────────────────
  // Mặc định isAnonymous=false: không ẩn danh → hiển thị form nhập SĐT để nhận voucher.
  // Khi user BẬT toggle → isAnonymous=true → ẩn form SĐT, voucher_eligible=false.
  const [isAnonymous, setIsAnonymous]         = useState(false)
  const [phone, setPhone]                     = useState('')
  const [otpCode, setOtpCode]                 = useState('')
  const [otpSent, setOtpSent]                 = useState(false)
  // SKIP_OTP=true: tự coi như đã verified (chế độ thử nghiệm)
  const [otpVerified, setOtpVerified]         = useState(SKIP_OTP)
  const [otpLoading, setOtpLoading]           = useState(false)
  const [otpError, setOtpError]               = useState(null)
  // ─────────────────────────────────────────────────────────────────────────

  const mediaRecorderRef  = useRef(null)
  const chunksRef         = useRef([])
  const timerRef          = useRef(null)
  const streamRef         = useRef(null)
  const recognitionRef    = useRef(null)

  // Kiểm tra SpeechRecognition support
  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    setSpeechSupported(!!SR)
  }, [])

  // Cleanup khi unmount hoặc close
  useEffect(() => {
    return () => {
      clearInterval(timerRef.current)
      if (streamRef.current) streamRef.current.getTracks().forEach(t => t.stop())
      if (recognitionRef.current) { try { recognitionRef.current.stop() } catch {} }
    }
  }, [])

  // Countdown khi đang ghi
  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) { handleStopRecording(); return 0 }
          return prev - 1
        })
      }, 1000)
    }
    return () => clearInterval(timerRef.current)
  }, [isRecording]) // eslint-disable-line

  const startSpeechRecognition = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) return
    const rec = new SR()
    rec.lang = 'vi-VN'
    rec.continuous = true
    rec.interimResults = true
    rec.onresult = (e) => {
      let transcript = ''
      for (let i = e.resultIndex; i < e.results.length; i++) {
        transcript += e.results[i][0].transcript
      }
      setLiveTranscript(transcript)
    }
    rec.onerror = () => { /* silent */ }
    try { rec.start() } catch {}
    recognitionRef.current = rec
  }

  const stopSpeechRecognition = () => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop() } catch {}
      recognitionRef.current = null
    }
  }

  const handleStartRecording = useCallback(async () => {
    setError('Tính năng ghi âm tạm thời bảo trì. Vui lòng sử dụng tính năng gõ văn bản!')
    return
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/ogg'

      const recorder = new MediaRecorder(stream, { mimeType })
      mediaRecorderRef.current = recorder
      chunksRef.current = []

      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: mimeType })
        setAudioBlob(blob)
        stream.getTracks().forEach(t => t.stop())
        setAudioDurationSec(Math.min(MAX_DURATION_SEC - timeLeft + 1, MAX_DURATION_SEC))
      }

      recorder.start(200)
      setIsRecording(true)
      setTimeLeft(MAX_DURATION_SEC)
      if (speechSupported) startSpeechRecognition()

    } catch (err) {
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setError('Cần quyền truy cập microphone. Bấm vào biểu tượng khóa trên thanh địa chỉ để cho phép.')
      } else if (err.name === 'NotFoundError') {
        setError('Không tìm thấy microphone. Thử chuyển sang gõ văn bản.')
      } else {
        setError('Không thể khởi động microphone. Hãy thử gõ văn bản.')
      }
    }
  }, [timeLeft, speechSupported]) // eslint-disable-line

  const handleStopRecording = useCallback(() => {
    clearInterval(timerRef.current)
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    stopSpeechRecognition()
    setIsRecording(false)
  }, [])

  const handleRetry = () => {
    setAudioBlob(null)
    setAudioDurationSec(0)
    setTimeLeft(MAX_DURATION_SEC)
    setError(null)
    setLiveTranscript('')
  }

  // ── Module 2: OTP handlers ────────────────────────────────────────────────

  /** Validate SĐT Việt Nam đơn giản (10 số, bắt đầu 0) */
  const isValidPhone = (p) => /^0[0-9]{9}$/.test(p.replace(/[\s-]/g, ''))

  /** Gửi OTP qua backend POST /api/v1/otp/send */
  const handleSendOtp = async () => {
    if (!isValidPhone(phone)) {
      setOtpError('Số điện thoại không hợp lệ. Vui lòng nhập đúng 10 số (VD: 0901234567).')
      return
    }
    setOtpLoading(true)
    setOtpError(null)
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/otp/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: phone.trim(), tenant_id: tenantId }),
      })
      if (res.ok) {
        setOtpSent(true)
      } else {
        const body = await res.json().catch(() => ({}))
        setOtpError(body.detail || 'Gửi mã OTP thất bại. Vui lòng thử lại.')
      }
    } catch {
      setOtpError('Không kết nối được server. Vui lòng thử lại.')
    } finally {
      setOtpLoading(false)
    }
  }

  /** Xác thực OTP qua backend POST /api/v1/otp/verify */
  const handleVerifyOtp = async () => {
    if (otpCode.length < 4) {
      setOtpError('Vui lòng nhập mã OTP (6 chữ số).')
      return
    }
    setOtpLoading(true)
    setOtpError(null)
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/otp/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: phone.trim(), otp_code: otpCode.trim() }),
      })
      if (res.ok) {
        setOtpVerified(true)
        setOtpError(null)
        // Lưu SĐT vào sessionStorage để SpinPage dùng lại, không hỏi lần 2
        try { sessionStorage.setItem('sentrix_customer_phone', phone.trim()) } catch {}
      } else {
        const body = await res.json().catch(() => ({}))
        setOtpError(body.detail || 'Mã OTP không đúng. Vui lòng thử lại.')
      }
    } catch {
      setOtpError('Không kết nối được server. Vui lòng thử lại.')
    } finally {
      setOtpLoading(false)
    }
  }


  // ─────────────────────────────────────────────────────────────────────────

  const handleSubmit = async () => {
    if (isSubmitting) return  // chặn double-click
    if (!audioBlob && !textContent.trim()) {
      setError('Vui lòng ghi âm hoặc gõ phản hồi trước khi gửi.')
      return
    }

    // Kiểm tra OTP nếu không ẩn danh, có nhập SĐT, và chưa verify (chỉ khi không phải test mode)
    if (!isAnonymous && phone.trim() && !otpVerified && !SKIP_OTP) {
      setError('Vui lòng xác thực số điện thoại qua OTP trước khi gửi.')
      return
    }

    setIsSubmitting(true)
    const decodedLocation = decodeURIComponent(location)

    // Khi ghi âm: dùng liveTranscript (SpeechRecognition trình duyệt) làm text_content
    // để backend có fallback nếu Whisper không chạy được — cả hai field sẽ được gửi cùng.
    // Backend ưu tiên Whisper; nếu Whisper fail → dùng text_content (= liveTranscript) này.
    const textFallback = mode === 'audio'
      ? (liveTranscript.trim() || null)
      : (textContent.trim() || null)

    // voucher_eligible: chỉ true khi KHÔNG ẩn danh + có SĐT + (OTP verified hoặc skip mode)
    const effectiveVoucherEligible = !isAnonymous && (otpVerified || SKIP_OTP) && !!phone.trim()

    try {
      const result = await submitFeedback({
        tenantId,
        location: decodedLocation,
        audioBlob: audioBlob || null,
        textContent: textFallback,
        customerPhone: effectiveVoucherEligible ? phone.trim() : null,
        totalSpending: 0,
        voucherEligible: effectiveVoucherEligible,
      })
      // Lưu kết quả + feedback_id vào sessionStorage trước khi navigate
      try {
        sessionStorage.setItem('sentrix_api_result', JSON.stringify(result))
        if (result.feedback_id) {
          sessionStorage.setItem('sentrix_feedback_id', result.feedback_id)
        }
        if (result.is_suspicious) {
          sessionStorage.setItem('sentrix_is_suspicious', 'true')
        }
      } catch { /* ignore storage errors */ }
    } catch (err) {
      // Lỗi API không block navigate — vẫn cho user đi tiếp (UX frictionless)
      console.error('[Sentrix] Feedback submit failed:', err)
    }

    // Navigate SAU khi đã có kết quả (hoặc fail) — đảm bảo feedback_id đã được lưu
    navigate(`/done?tenant_id=${tenantId}&location=${encodeURIComponent(decodedLocation)}`)
  }

  const isWarning   = timeLeft <= 5 && isRecording
  const waveformBars = [1, 2, 3, 4, 5, 6, 7]

  return (
    /* Backdrop blur full-screen */
    <div
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: 'rgba(0,0,0,0.15)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px 16px',
        animation: 'overlay-in 0.25s ease forwards',
      }}
    >
      {/* Modal card */}
      <div style={{
        width: '100%',
        maxWidth: 420,
        background: '#FFFFFF',
        borderRadius: 28,
        boxShadow: '0 24px 80px rgba(0,0,0,0.18)',
        padding: '28px 24px 24px',
        position: 'relative',
        animation: 'card-up 0.3s cubic-bezier(0.34,1.56,0.64,1) forwards',
        maxHeight: '90dvh',
        overflowY: 'auto',
      }}>

        {/* Close button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute', top: 16, right: 16,
            width: 32, height: 32, borderRadius: '50%',
            background: '#F3F4F6', border: 'none', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 16, color: '#6B7280', fontFamily: 'var(--font-family)',
          }}
          aria-label="Đóng"
        >×</button>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <h2 style={{ fontSize: 20, fontWeight: 800, color: '#111827', marginBottom: 4 }}>
            {mode === 'text' ? 'Gõ phản hồi' : 'Ghi âm phản hồi'}
          </h2>
          <span style={{
            display: 'inline-block', padding: '3px 10px', borderRadius: 20,
            background: 'rgba(0,122,255,0.08)', color: '#007AFF',
            fontSize: 12, fontWeight: 600
          }}>
            {decodeURIComponent(location)}
          </span>
        </div>

        {/* === MODE: AUDIO === */}
        {mode === 'audio' && (
          <div style={{ textAlign: 'center' }}>
            {/* Waveform */}
            <div style={{ display: 'flex', justifyContent: 'center', height: 48, marginBottom: 16 }}>
              <div className={`waveform ${isRecording ? 'waveform--active' : ''}`}>
                {waveformBars.map(i => (
                  <div key={i} className="waveform-bar" style={{
                    height: audioBlob ? '30%' : isRecording ? undefined : '20%',
                    background: isRecording
                      ? 'linear-gradient(to top, #007AFF, #7C3AED)'
                      : audioBlob
                        ? 'linear-gradient(to top, #10B981, #34D399)'
                        : 'linear-gradient(to top, #D1D5DB, #9CA3AF)',
                  }} />
                ))}
              </div>
            </div>

            {/* Live transcript realtime — mờ, font italic */}
            {isRecording && liveTranscript && (
              <div style={{
                minHeight: 36, marginBottom: 8,
                padding: '8px 12px',
                background: 'rgba(0,122,255,0.05)',
                borderRadius: 12,
                fontSize: 13, color: '#6B7280', fontStyle: 'italic',
                textAlign: 'left', lineHeight: 1.5,
                transition: 'all 0.2s',
              }}>
                "{liveTranscript}"
              </div>
            )}

            {/* Status */}
            <div style={{ minHeight: 48, marginBottom: 16 }}>
              {audioBlob ? (
                <div>
                  <div style={{ fontSize: 32, marginBottom: 4 }}>✅</div>
                  <p style={{ fontSize: 14, color: '#10B981', fontWeight: 600 }}>
                    Ghi âm xong · {audioDurationSec}s
                  </p>
                </div>
              ) : isRecording ? (
                <div>
                  <div style={{
                    fontSize: 36, fontWeight: 800,
                    color: isWarning ? '#F59E0B' : '#007AFF',
                    animation: isWarning ? 'blink 0.5s step-end infinite' : 'none',
                  }}>
                    {timeLeft}s
                  </div>
                  <p style={{ fontSize: 12, color: isWarning ? '#F59E0B' : '#9CA3AF', marginTop: 4 }}>
                    {isWarning ? 'Gần xong rồi!' : 'Đang ghi — nhấn lại để dừng'}
                  </p>
                </div>
              ) : (
                <p style={{ fontSize: 14, color: '#6B7280', marginTop: 8 }}>
                  Nhấn nút để bắt đầu ghi âm
                </p>
              )}
            </div>

            {/* Nút ghi âm */}
            {!audioBlob && (
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 16 }}>
                <button
                  id="btn-toggle-record"
                  className={`btn-record ${isRecording ? 'btn-record--recording' : ''}`}
                  onClick={isRecording ? handleStopRecording : handleStartRecording}
                  aria-label={isRecording ? 'Dừng ghi âm' : 'Bắt đầu ghi âm'}
                >
                  {isRecording ? (
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="white">
                      <rect x="6" y="6" width="12" height="12" rx="2"/>
                    </svg>
                  ) : (
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none"
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

            {/* Sau khi có audio */}
            {audioBlob && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 8 }}>
                <button
                  id="btn-submit-audio"
                  className="btn btn--primary"
                  onClick={handleSubmit}
                  disabled={isSubmitting}
                  style={{ opacity: isSubmitting ? 0.7 : 1, cursor: isSubmitting ? 'not-allowed' : 'pointer' }}
                >
                  {isSubmitting ? 'Đang gửi...' : 'Gửi phản hồi'}
                </button>
                {!isSubmitting && (
                  <button id="btn-retry-record" className="btn btn--secondary" onClick={handleRetry}>
                    Ghi lại
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* === MODE: TEXT === */}
        {mode === 'text' && (
          <div>
            <textarea
              id="text-feedback"
              className="textarea"
              placeholder="Ví dụ: Đồ ăn ngon, nhân viên thân thiện. Hơi chờ lâu..."
              value={textContent}
              onChange={(e) => { setTextContent(e.target.value); setError(null) }}
              maxLength={2000}
              rows={5}
              autoFocus
              spellCheck={false}
              lang="vi"
              style={{ marginBottom: 8 }}
            />
            <p style={{ fontSize: 11, color: '#9CA3AF', textAlign: 'right', marginBottom: 16 }}>
              {textContent.length} / 2000
            </p>
            <button
              id="btn-submit-text"
              className="btn btn--primary"
              onClick={handleSubmit}
              disabled={textContent.trim().length < 2 || isSubmitting}
              style={{ opacity: isSubmitting ? 0.7 : 1, cursor: isSubmitting ? 'not-allowed' : 'pointer' }}
            >
              {isSubmitting ? 'Đang gửi...' : 'Gửi phản hồi'}
            </button>
          </div>
        )}

        {/* ════════════════════════════════════════════════════════════════
            MODULE 2: Anonymous Toggle + OTP flow
            Căn cứ: Điều 5 NĐ 356/2025/NĐ-CP (quyền từ chối xử lý dữ liệu)
            ════════════════════════════════════════════════════════════════ */}
        <div style={{
          marginTop: 20,
          padding: '14px 16px',
          // Khi ẩn danh (BẬT): nền xám. Khi không ẩn danh (TẮT): nền xanh accent
          background: isAnonymous ? 'rgba(107,114,128,0.06)' : 'rgba(6,136,166,0.05)',
          borderRadius: 16,
          border: `1.5px solid ${isAnonymous ? 'rgba(107,114,128,0.2)' : 'rgba(6,136,166,0.2)'}`,
          transition: 'all 0.2s',
        }}>
          {/* Toggle ẩn danh */}
          <label
            id="anonymous-toggle-label"
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              cursor: 'pointer', gap: 10,
            }}
          >
            <div style={{ flex: 1 }}>
              <p style={{ fontSize: 13, fontWeight: 700, color: '#111827', margin: 0 }}>
                Phản hồi ẩn danh
              </p>
              <p style={{ fontSize: 11, color: '#6B7280', margin: '2px 0 0', lineHeight: 1.5 }}>
                {isAnonymous
                  ? '🔒 Ẩn danh — không thể gửi voucher qua Zalo'
                  : '🎁 Để lại SĐT → nhận voucher qua Zalo'}
              </p>
            </div>
            {/* Toggle switch
                BẬT (isAnonymous=true):  knob PHẢI + màu xanh = ẩn danh đang bật
                TẮT (isAnonymous=false): knob TRÁI + màu xám  = không ẩn danh
            */}
            <div
              id="btn-anonymous-toggle"
              onClick={() => {
                setIsAnonymous(a => !a)
                // Reset OTP state khi đổi mode
                setPhone(''); setOtpCode(''); setOtpSent(false)
                setOtpVerified(SKIP_OTP); setOtpError(null)
              }}
              role="switch"
              aria-checked={isAnonymous}
              style={{
                width: 48, height: 28, borderRadius: 14, flexShrink: 0,
                // BẬT ẩn danh = xanh teal | TẮT = xám
                background: isAnonymous ? '#0688A6' : '#D1D5DB',
                position: 'relative', cursor: 'pointer',
                transition: 'background 0.2s',
              }}
            >
              <div style={{
                position: 'absolute', top: 3,
                // BẬT: knob phải (23) | TẮT: knob trái (3)
                left: isAnonymous ? 23 : 3,
                width: 22, height: 22, borderRadius: '50%',
                background: '#FFFFFF',
                boxShadow: '0 1px 4px rgba(0,0,0,0.2)',
                transition: 'left 0.2s',
              }} />
            </div>
          </label>

          {/* OTP form — chỉ hiện khi KHÔNG ẩn danh */}
          {!isAnonymous && (
            <div style={{ marginTop: 14 }}>
              {!otpVerified ? (
                <>
                  {/* Ô nhập SĐT */}
                  <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                    <input
                      id="input-phone"
                      type="tel"
                      inputMode="numeric"
                      placeholder="Số điện thoại (VD: 0901234567)"
                      value={phone}
                      onChange={e => {
                        setPhone(e.target.value)
                        setOtpError(null)
                        setOtpSent(false)
                        // Khi user đổi SĐT: reset verified (trừ SKIP_OTP mode)
                        if (!SKIP_OTP) setOtpVerified(false)
                      }}
                      maxLength={11}
                      disabled={otpSent && !otpVerified && !SKIP_OTP}
                      spellCheck={false}
                      style={{
                        flex: 1, padding: '10px 12px', borderRadius: 10,
                        border: '1.5px solid #E5E7EB', fontFamily: 'inherit',
                        fontSize: 14, outline: 'none', background: '#FAFAFA',
                        opacity: (otpSent && !otpVerified && !SKIP_OTP) ? 0.6 : 1,
                      }}
                    />
                    {/* Nút gửi OTP — ẩn đi nếu SKIP_OTP mode */}
                    {!SKIP_OTP && (
                      <button
                        id="btn-send-otp"
                        onClick={handleSendOtp}
                        disabled={otpLoading || (otpSent && !otpVerified)}
                        style={{
                          padding: '10px 14px', borderRadius: 10, border: 'none',
                          background: '#0688A6', color: '#fff', fontSize: 13,
                          fontWeight: 600, fontFamily: 'inherit', cursor: 'pointer',
                          whiteSpace: 'nowrap', flexShrink: 0,
                          opacity: (otpLoading || (otpSent && !otpVerified)) ? 0.6 : 1,
                        }}
                      >
                        {otpLoading && !otpSent ? '...' : otpSent ? 'Gửi lại' : 'Gửi mã'}
                      </button>
                    )}
                  </div>

                  {/* Ô nhập mã OTP — ẩn khi SKIP_OTP hoặc chưa gửi */}
                  {!SKIP_OTP && otpSent && (
                    <div style={{ display: 'flex', gap: 8, marginBottom: 4 }}>
                      <input
                        id="input-otp-code"
                        type="text"
                        inputMode="numeric"
                        placeholder="Nhập mã OTP (6 chữ số)"
                        value={otpCode}
                        onChange={e => { setOtpCode(e.target.value.replace(/\D/g, '')); setOtpError(null) }}
                        maxLength={6}
                        spellCheck={false}
                        style={{
                          flex: 1, padding: '10px 12px', borderRadius: 10,
                          border: '1.5px solid #E5E7EB', fontFamily: 'inherit',
                          fontSize: 14, letterSpacing: '0.15em', outline: 'none',
                          background: '#FAFAFA', textAlign: 'center',
                        }}
                      />
                      <button
                        id="btn-verify-otp"
                        onClick={handleVerifyOtp}
                        disabled={otpLoading || otpCode.length < 4}
                        style={{
                          padding: '10px 14px', borderRadius: 10, border: 'none',
                          background: '#10B981', color: '#fff', fontSize: 13,
                          fontWeight: 600, fontFamily: 'inherit', cursor: 'pointer',
                          whiteSpace: 'nowrap', flexShrink: 0,
                          opacity: (otpLoading || otpCode.length < 4) ? 0.6 : 1,
                        }}
                      >
                        {otpLoading ? '...' : 'Xác nhận'}
                      </button>
                    </div>
                  )}

                  {!SKIP_OTP && otpSent && (
                    <p style={{ fontSize: 11, color: '#9CA3AF', marginTop: 4 }}>
                      Mã OTP đã gửi tới {phone} · Có hiệu lực 5 phút
                    </p>
                  )}

                  {/* Thông báo chế độ thử nghiệm */}
                  {SKIP_OTP && (
                    <p style={{ fontSize: 11, color: '#D97706', marginTop: 4 }}>
                      ⚙️ Chế độ thử nghiệm — OTP đang được bỏ qua
                    </p>
                  )}
                </>
              ) : (
                /* Đã verified thành công */
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  padding: '8px 12px', borderRadius: 10,
                  background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.25)',
                }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                    stroke="#10B981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                  <p style={{ fontSize: 13, color: '#065F46', fontWeight: 600, margin: 0 }}>
                    SĐT đã xác thực — bạn sẽ nhận voucher qua Zalo!
                  </p>
                </div>
              )}

              {/* OTP Error */}
              {otpError && (
                <p style={{
                  color: '#EF4444', fontSize: 12, marginTop: 6,
                  padding: '6px 10px', background: 'rgba(239,68,68,0.06)',
                  borderRadius: 8, lineHeight: 1.5,
                }}>
                  {otpError}
                </p>
              )}
            </div>
          )}
        </div>
        {/* ════════════════ END Module 2 ════════════════ */}

        {/* Error */}
        {error && (
          <p style={{
            color: '#EF4444', fontSize: 13, marginTop: 12,
            padding: '8px 12px', background: 'rgba(239,68,68,0.06)',
            borderRadius: 8, lineHeight: 1.5
          }}>
            {error}
          </p>
        )}

        {/* Toggle mode */}
        <button
          id="btn-toggle-mode"
          className="btn btn--ghost"
          onClick={() => { setMode(mode === 'audio' ? 'text' : 'audio'); setError(null); handleRetry() }}
          style={{ marginTop: 12, color: '#6B7280' }}
        >
          {mode === 'audio' ? 'Thích gõ hơn?' : 'Chuyển sang ghi âm'}
        </button>
      </div>

      <style>{`
        @keyframes overlay-in {
          from { opacity: 0; }
          to   { opacity: 1; }
        }
        @keyframes card-up {
          from { transform: translateY(24px) scale(0.97); opacity: 0; }
          to   { transform: translateY(0) scale(1); opacity: 1; }
        }
      `}</style>
    </div>
  )
}

export default RecordingOverlay
