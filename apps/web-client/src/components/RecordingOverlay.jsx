import { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { submitFeedback } from '../api/feedback.js'
import { auth, googleProvider } from '../firebase.js'
import { signInWithPopup, signOut } from 'firebase/auth'

const MAX_DURATION_SEC = 15

/**
 * RecordingOverlay — Overlay thu âm đè lên LandingPage
 *
 * Không redirect URL. Hiện dạng modal full-screen với blur backdrop.
 * Tích hợp Web Speech API (SpeechRecognition) để hiện transcript realtime mờ.
 *
 * Module 2 (PDPA) — thêm:
 *   - Toggle "Phản hồi ẩn danh" (Điều 5 NĐ 356/2025: quyền từ chối)
 *   - Khi KHÔNG ẩn danh: Google Sign-In hoặc Email OTP
 *   - voucher_eligible = false khi ẩn danh (không gọi OTP, không phát voucher)
 *
 * Props:
 *   tenantId      string  — từ QR code
 *   location      string  — encoded location từ QR
 *   initialMode   string  — 'audio' | 'text'
 *   onClose       fn      — callback khi đóng overlay (bấm X)
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

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
  const [isLiveTranscriptFinal, setIsLiveTranscriptFinal] = useState(false)
  const [speechSupported, setSpeechSupported] = useState(false)

  // ── Module 2: Anonymous Toggle + Auth / OTP ─────────────────────────────
  // Mặc định isAnonymous=false: không ẩn danh → yêu cầu xác thực Google / Email để nhận voucher.
  // Khi user BẬT toggle → isAnonymous=true → ẩn xác thực, voucher_eligible=false.
  const [isAnonymous, setIsAnonymous]         = useState(false)
  const [contactType, setContactType]         = useState('email') // 'google' | 'email' | 'phone'
  const [contact, setContact]                 = useState('')
  const [otpCode, setOtpCode]                 = useState('')
  const [otpSent, setOtpSent]                 = useState(false)
  const [otpVerified, setOtpVerified]         = useState(false)
  const [otpLoading, setOtpLoading]           = useState(false)
  const [otpError, setOtpError]               = useState(null)
  const [googleLoading, setGoogleLoading]     = useState(false)
  
  // stage: 'auth' | 'feedback'
  const [stage, setStage]                     = useState('auth')
  // ─────────────────────────────────────────────────────────────────────────

  const mediaRecorderRef  = useRef(null)
  const chunksRef         = useRef([])
  const timerRef          = useRef(null)
  const streamRef         = useRef(null)
  const recognitionRef    = useRef(null)
  const recognitionTimerRef = useRef(null)

  // Kiểm tra SpeechRecognition support
  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    setSpeechSupported(!!SR)
  }, [])

  // Cleanup khi unmount hoặc close
  useEffect(() => {
    return () => {
      clearInterval(timerRef.current)
      clearTimeout(recognitionTimerRef.current)
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

  const startSpeechRecognition = (audioTrack) => {
    if (import.meta.env.DEV) {
      console.log('[VOICE DEBUG] speech.start(audioTrack)')
      console.log(`[VOICE DEBUG] speechSupported=${speechSupported}`)
    }
    
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) return
    if (import.meta.env.DEV) {
      console.log(`[VOICE DEBUG] speech-api=${window.SpeechRecognition ? 'SpeechRecognition' : 'webkitSpeechRecognition'}`)
    }
    
    const rec = new SR()
    rec.lang = 'vi-VN'
    rec.continuous = true
    rec.interimResults = true
    
    // Add detailed lifecycle events
    if (import.meta.env.DEV) {
      rec.onstart = () => { console.log('[VOICE DEBUG] speech.started-from-track') }
      rec.onaudiostart = () => console.log('[VOICE DEBUG] speech.audiostart')
      rec.onsoundstart = () => console.log('[VOICE DEBUG] speech.soundstart')
      rec.onspeechstart = () => console.log('[VOICE DEBUG] speech.speechstart')
      rec.onsoundend = () => console.log('[VOICE DEBUG] speech.soundend')
      rec.onspeechend = () => console.log('[VOICE DEBUG] speech.speechend')
      rec.onnomatch = () => console.log('[VOICE DEBUG] speech.nomatch')
      rec.onend = () => { console.log('[VOICE DEBUG] speech.onend') }
    }
    
    rec.onresult = (e) => {
      if (import.meta.env.DEV) {
        console.log(`[VOICE DEBUG] speech.onresult (results.length=${e.results.length}, resultIndex=${e.resultIndex})`)
      }
      let transcript = ''
      let isFinal = false
      for (let i = 0; i < e.results.length; i++) {
        transcript += e.results[i][0].transcript
        if (i === e.results.length - 1) {
          isFinal = e.results[i].isFinal
          if (import.meta.env.DEV) {
            console.log(`[VOICE DEBUG] result[${i}] transcript="${e.results[i][0].transcript}" confidence=${e.results[i][0].confidence} isFinal=${e.results[i].isFinal}`)
          }
        }
      }
      setLiveTranscript(transcript)
      setIsLiveTranscriptFinal(isFinal)
    }
    
    rec.onerror = (err) => { 
      if (import.meta.env.DEV) {
        console.error(`[VOICE DEBUG] speech.onerror error=${err.error} message=${err.message || ''}`) 
      }
    }
    
    if (!audioTrack || audioTrack.kind !== 'audio' || audioTrack.readyState !== 'live') {
      if (import.meta.env.DEV) {
        console.log('[VOICE DEBUG] realtime-preview.disabled reason=invalid-track')
      }
      return
    }

    if (import.meta.env.DEV) {
      console.log('[VOICE DEBUG] track state', {
        kind: audioTrack.kind,
        readyState: audioTrack.readyState,
        enabled: audioTrack.enabled,
        muted: audioTrack.muted,
        contentHint: audioTrack.contentHint
      })
    }

    try { 
      try {
        audioTrack.contentHint = 'speech-recognition'
      } catch (e) {
        if (import.meta.env.DEV) {
          console.warn('[VOICE DEBUG] Could not set contentHint:', e)
        }
      }

      if (import.meta.env.DEV) {
        console.log('[VOICE DEBUG] speech.start(original-track)')
        console.log(`[VOICE DEBUG] speech.original-track.contentHint=${audioTrack.contentHint}`)
      }

      rec.start(audioTrack) 
    } catch (err) { 
      if (import.meta.env.DEV) {
        console.error(`[VOICE DEBUG] speech.start.error name=${err.name} message=${err.message}`) 
        console.log('[VOICE DEBUG] realtime-preview.disabled reason=start_exception')
      }
      setLiveTranscript('Realtime preview unavailable.')
    }
    recognitionRef.current = rec
  }

  const stopSpeechRecognition = () => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop() } catch {}
      recognitionRef.current = null
    }
  }

  const handleStartRecording = useCallback(async () => {
    if (import.meta.env.DEV) {
      console.log('[VOICE DEBUG] getUserMedia.start')
    }
    setError(null) // Clear any previous errors

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      if (import.meta.env.DEV) {
        console.log('[VOICE DEBUG] getUserMedia.success')
      }
      streamRef.current = stream
      
      // Log devices for Phase 9
      try {
        const devices = await navigator.mediaDevices.enumerateDevices()
        const audioInputs = devices.filter(d => d.kind === 'audioinput')
        if (import.meta.env.DEV) {
          console.log('[Voice E2E] Available microphones:', audioInputs.map(d => d.label || 'Unknown mic'))
        }
        const activeTrack = stream.getAudioTracks()[0]
        if (import.meta.env.DEV) {
          console.log('[Voice E2E] Selected microphone track:', activeTrack ? activeTrack.label : 'None')
        }
      } catch (e) {
        if (import.meta.env.DEV) {
          console.warn('[Voice E2E] Cannot enumerate devices:', e)
        }
      }

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/ogg'

      const recorder = new MediaRecorder(stream, { mimeType })
      mediaRecorderRef.current = recorder
      chunksRef.current = []
      
      const startTime = Date.now()
      if (import.meta.env.DEV) {
        console.log(`[Voice E2E] recording started at ${startTime}`)
      }

      recorder.ondataavailable = (e) => { 
        if (import.meta.env.DEV) {
          console.log(`[VOICE DEBUG] recorder.dataavailable size=${e.data.size}`)
        }
        if (e.data.size > 0) chunksRef.current.push(e.data) 
      }
      recorder.onstop = () => {
        const stopTime = Date.now()
        const durationMs = stopTime - startTime
        
        if (import.meta.env.DEV) {
          console.log('[VOICE DEBUG] recorder.stop')
          console.log(`[Voice E2E] recording stopped at ${stopTime}`)
          console.log(`[Voice E2E] duration_ms = ${durationMs}`)
          console.log(`[Voice E2E] chunks = ${chunksRef.current.length}`)
        }
        
        const blob = new Blob(chunksRef.current, { type: mimeType })
        if (import.meta.env.DEV) {
          console.log(`[Voice E2E] blob_size = ${blob.size}`)
          console.log(`[Voice E2E] blob_type = ${blob.type}`)
        }
        
        setAudioBlob(blob)
        stream.getTracks().forEach(t => t.stop())
        setAudioDurationSec(Math.max(1, Math.round(durationMs / 1000)))
        if (import.meta.env.DEV) {
          console.log(`[VOICE DEBUG] final state: blob_size=${blob.size}, duration=${durationMs}ms`)
        }
      }

      if (import.meta.env.DEV) {
        console.log('[VOICE DEBUG] mediaRecorder.start')
      }
      recorder.start(200)
      if (import.meta.env.DEV) {
        console.log(`[VOICE DEBUG] recorder.state=${recorder.state}`)
      }
      setIsRecording(true)
      setTimeLeft(MAX_DURATION_SEC)
      
      const activeTrack = stream.getAudioTracks()[0]
      if (speechSupported && activeTrack) {
        recognitionTimerRef.current = setTimeout(() => {
          startSpeechRecognition(activeTrack)
        }, 1500)
      }

    } catch (err) {
      if (import.meta.env.DEV) {
        console.error(`[VOICE DEBUG] handleStartRecording.error name=${err.name} message=${err.message}`)
      }
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
    if (import.meta.env.DEV) {
      console.log('[VOICE DEBUG] handleStopRecording')
    }
    clearInterval(timerRef.current)
    clearTimeout(recognitionTimerRef.current)
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
    setIsLiveTranscriptFinal(false)
  }

  // ── Module 2: Auth & OTP handlers ────────────────────────────────────────

  /** Reset identity / sign out for shared devices */
  const handleResetAuth = async () => {
    if (auth && auth.currentUser) {
      try { await signOut(auth) } catch {}
    }
    try {
      sessionStorage.removeItem('sentrix_customer_phone')
      sessionStorage.removeItem('sentrix_customer_contact')
      sessionStorage.removeItem('sentrix_customer_contact_type')
    } catch {}
    setContact('')
    setOtpCode('')
    setOtpSent(false)
    setOtpVerified(false)
    setOtpError(null)
    setContactType('email')
    setStage('auth')
  }

  /** Close overlay and clean up shared session if unsubmitted */
  const handleOverlayClose = async () => {
    if (auth && auth.currentUser) {
      try { await signOut(auth) } catch {}
    }
    try {
      sessionStorage.removeItem('sentrix_customer_phone')
      sessionStorage.removeItem('sentrix_customer_contact')
      sessionStorage.removeItem('sentrix_customer_contact_type')
    } catch {}
    onClose()
  }

  /** Google Sign-In handler qua popup */
  const handleGoogleSignIn = async () => {
    if (googleLoading) return
    if (!auth || !googleProvider) {
      setOtpError('Hệ thống xác thực Google tạm thời chưa được cấu hình. Vui lòng sử dụng Email OTP.')
      return
    }
    setGoogleLoading(true)
    setOtpError(null)
    try {
      const result = await signInWithPopup(auth, googleProvider)
      const user = result.user
      if (!user || !user.email) {
        throw new Error('Không nhận được email từ tài khoản Google.')
      }
      if (!user.emailVerified) {
        throw new Error('Tài khoản Google này chưa được xác minh email.')
      }
      const verifiedEmail = user.email.trim()
      setContact(verifiedEmail)
      setContactType('google')
      setOtpVerified(true)
      setStage('feedback')
      try {
        sessionStorage.setItem('sentrix_customer_contact', verifiedEmail)
        sessionStorage.setItem('sentrix_customer_contact_type', 'google')
      } catch {}
    } catch (err) {
      console.error('[Sentrix] Google Sign-in error:', err)
      if (err.code === 'auth/popup-closed-by-user' || err.code === 'auth/cancelled-popup-request') {
        setOtpError('Cửa sổ đăng nhập Google đã đóng. Vui lòng bấm lại để tiếp tục.')
      } else if (err.code === 'auth/popup-blocked') {
        setOtpError('Trình duyệt đã chặn cửa sổ popup. Vui lòng cấp quyền mở popup.')
      } else if (err.code === 'auth/network-request-failed') {
        setOtpError('Lỗi kết nối mạng khi xác thực Google. Vui lòng kiểm tra lại đường truyền.')
      } else {
        setOtpError(err.message || 'Đăng nhập Google thất bại. Vui lòng thử lại.')
      }
    } finally {
      setGoogleLoading(false)
    }
  }

  /** Validate Contact */
  const isValidContact = (c, type) => {
    if (type === 'phone') return /^0[0-9]{9}$/.test(c.replace(/[\s-]/g, ''))
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(c.trim())
  }

  /** Gửi OTP qua backend POST /api/v1/otp/send */
  const handleSendOtp = async () => {
    if (contactType === 'phone') {
      setOtpError('Phương thức xác thực qua số điện thoại tạm thời chưa khả dụng. Vui lòng tiếp tục với Google hoặc nhập Email.')
      return
    }
    if (!isValidContact(contact, contactType)) {
      setOtpError('Email không hợp lệ. Vui lòng kiểm tra lại.')
      return
    }
    setOtpLoading(true)
    setOtpError(null)
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/otp/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contact: contact.trim(), tenant_id: tenantId }),
      })
      if (res.ok) {
        setOtpSent(true)
      } else {
        const body = await res.json().catch(() => ({}))
        const errorMessage = Array.isArray(body.detail)
          ? 'Dữ liệu không hợp lệ. Vui lòng thử lại.'
          : (body.detail || 'Gửi mã OTP thất bại. Vui lòng thử lại.')
        setOtpError(errorMessage)
      }
    } catch {
      setOtpError('Không kết nối được server. Vui lòng thử lại.')
    } finally {
      setOtpLoading(false)
    }
  }

  /** Xác thực OTP qua backend POST /api/v1/otp/verify */
  const handleVerifyOtp = async () => {
    if (otpCode.length !== 6) {
      setOtpError('Vui lòng nhập mã OTP (6 chữ số).')
      return
    }
    setOtpLoading(true)
    setOtpError(null)
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/otp/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contact: contact.trim(), otp_code: otpCode.trim(), tenant_id: tenantId }),
      })
      if (res.ok) {
        setOtpVerified(true)
        setStage('feedback')
        setOtpError(null)
        // Lưu contact vào sessionStorage để SpinPage dùng lại, không hỏi lần 2
        try { 
          sessionStorage.setItem('sentrix_customer_contact', contact.trim())
          sessionStorage.setItem('sentrix_customer_contact_type', 'email')
        } catch {}
      } else {
        const body = await res.json().catch(() => ({}))
        const errorMessage = Array.isArray(body.detail) ? 'Dữ liệu không hợp lệ. Vui lòng thử lại.' : (body.detail || 'Mã OTP không đúng. Vui lòng thử lại.')
        setOtpError(errorMessage)
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

    // Kiểm tra nếu không ẩn danh thì phải hoàn tất xác thực (Google hoặc Email OTP)
    if (!isAnonymous && !otpVerified) {
      setError('Vui lòng xác thực Google/Email hoặc chọn Phản hồi ẩn danh trước khi gửi.')
      return
    }

    setIsSubmitting(true)
    const decodedLocation = decodeURIComponent(location)

    const textFallback = mode === 'text'
      ? (textContent.trim() || null)
      : null

    let freshGoogleToken = null
    if (!isAnonymous && contactType === 'google') {
      try {
        if (!auth || !auth.currentUser) {
          setError('Phiên đăng nhập Google đã hết hạn. Vui lòng đăng nhập lại.')
          setIsSubmitting(false)
          return
        }
        // Lấy token tươi ngay tại thời điểm submit, không lưu vào storage
        freshGoogleToken = await auth.currentUser.getIdToken(false)
      } catch (tokenErr) {
        console.error('[Sentrix] Lỗi lấy Firebase ID token:', tokenErr)
        setError('Không thể lấy mã xác thực Google. Vui lòng đăng nhập lại.')
        setIsSubmitting(false)
        return
      }
    }

    // voucher_eligible: chỉ true khi KHÔNG ẩn danh + đã xác thực
    const effectiveVoucherEligible = !isAnonymous && otpVerified && (
      contactType === 'google' ? !!freshGoogleToken : !!contact.trim()
    )

    if (import.meta.env.DEV) {
      console.log('[Voice E2E] submit started')
      console.log('[Voice E2E] blob size:', audioBlob ? audioBlob.size : 0)
      console.log('[Voice E2E] blob type:', audioBlob ? audioBlob.type : 'none')
      console.log('[Voice E2E] API URL:', API_BASE_URL)
      console.log('[Voice E2E] request sent')
    }

    try {
      const result = await submitFeedback({
        tenantId,
        location: decodedLocation,
        audioBlob: audioBlob || null,
        textContent: textFallback,
        customerPhone: effectiveVoucherEligible ? contact.trim() : null,
        totalSpending: 0,
        voucherEligible: effectiveVoucherEligible,
        firebaseIdToken: freshGoogleToken,
      })
      if (import.meta.env.DEV) {
        console.log('[Voice E2E] response status: 202 (Accepted)')
      }
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
      if (import.meta.env.DEV) {
        console.log('[Voice E2E] response status:', err.statusCode || 'Unknown Error')
      }
      // Lỗi API không block navigate — vẫn cho user đi tiếp (UX frictionless)
      console.error('[Sentrix] Feedback submit failed:', err)
      setError(err.message || 'Không thể gửi phản hồi. Vui lòng thử lại.')
      setIsSubmitting(false)
      return
    } finally {
      setIsSubmitting(false)
    }

    // Navigate SAU khi đã có kết quả (hoặc fail)
    navigate(`/done?tenant_id=${tenantId}&location=${encodeURIComponent(decodedLocation)}`)
  }

  const isWarning   = timeLeft <= 5 && isRecording
  const waveformBars = [1, 2, 3, 4, 5, 6, 7]

  return (
    /* Backdrop blur full-screen */
    <div
      onClick={(e) => { if (e.target === e.currentTarget) handleOverlayClose() }}
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
          onClick={handleOverlayClose}
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

        {/* ════════════════════════════════════════════════════════════════
            MODULE 2: Anonymous Toggle + Auth / OTP flow (STAGE: AUTH)
            ════════════════════════════════════════════════════════════════ */}
        <div style={{
          padding: '14px 16px', marginBottom: stage === 'auth' ? 0 : 20,
          background: isAnonymous ? 'rgba(107,114,128,0.06)' : 'rgba(6,136,166,0.05)',
          borderRadius: 16, border: `1.5px solid ${isAnonymous ? 'rgba(107,114,128,0.2)' : 'rgba(6,136,166,0.2)'}`,
          transition: 'all 0.2s',
        }}>
          {/* Toggle ẩn danh */}
          <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', gap: 10 }}>
            <div style={{ flex: 1 }}>
              <p style={{ fontSize: 13, fontWeight: 700, color: '#111827', margin: 0 }}>
                Phản hồi ẩn danh
              </p>
              <p style={{ fontSize: 11, color: '#6B7280', margin: '2px 0 0', lineHeight: 1.5 }}>
                {isAnonymous
                  ? '🔒 Ẩn danh — không nhận voucher qua Zalo/Email'
                  : '🎁 Đăng nhập Google / Email → nhận voucher'}
              </p>
            </div>
            <div
              id="btn-anonymous-toggle"
              onClick={() => {
                const newVal = !isAnonymous;
                setIsAnonymous(newVal);
                if (newVal) {
                  if (auth && auth.currentUser) {
                    signOut(auth).catch(() => {});
                  }
                  try {
                    sessionStorage.removeItem('sentrix_customer_contact');
                    sessionStorage.removeItem('sentrix_customer_phone');
                    sessionStorage.removeItem('sentrix_customer_contact_type');
                  } catch {}
                }
                setContact(''); setOtpCode(''); setOtpSent(false); setOtpVerified(false); setOtpError(null);
                setStage(newVal ? 'feedback' : 'auth');
              }}
              role="switch" aria-checked={isAnonymous}
              style={{
                width: 48, height: 28, borderRadius: 14, flexShrink: 0,
                background: isAnonymous ? '#0688A6' : '#D1D5DB',
                position: 'relative', cursor: 'pointer', transition: 'background 0.2s',
              }}
            >
              <div style={{
                position: 'absolute', top: 3, left: isAnonymous ? 23 : 3,
                width: 22, height: 22, borderRadius: '50%', background: '#FFFFFF',
                boxShadow: '0 1px 4px rgba(0,0,0,0.2)', transition: 'left 0.2s',
              }} />
            </div>
          </label>

          {/* Auth form — hiện ở stage auth nếu KHÔNG ẩn danh */}
          {stage === 'auth' && !isAnonymous && (
            <div style={{ marginTop: 14, borderTop: '1px solid rgba(0,0,0,0.05)', paddingTop: 14 }}>
              {!otpVerified ? (
                <>
                  {/* Google Sign-In Button (Nhanh & Tien cho demo) */}
                  <button
                    id="btn-google-signin"
                    type="button"
                    onClick={handleGoogleSignIn}
                    disabled={googleLoading}
                    style={{
                      width: '100%',
                      padding: '11px 16px',
                      borderRadius: 12,
                      border: '1.5px solid #E5E7EB',
                      background: '#FFFFFF',
                      color: '#374151',
                      fontWeight: 600,
                      fontSize: 14,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: 10,
                      cursor: googleLoading ? 'not-allowed' : 'pointer',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
                      transition: 'all 0.15s ease',
                      opacity: googleLoading ? 0.7 : 1,
                    }}
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24">
                      <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.665-5.17 3.665-9.17z"/>
                      <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.33 24 12 24z"/>
                      <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.18 0 10.03 0 12s.45 3.82 1.25 5.42l4.03-3.15z"/>
                      <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
                    </svg>
                    <span>{googleLoading ? 'Đang kết nối Google...' : 'Tiếp tục với Google'}</span>
                  </button>

                  {/* Divider */}
                  <div style={{ display: 'flex', alignItems: 'center', margin: '14px 0', gap: 10 }}>
                    <div style={{ flex: 1, height: 1, background: '#E5E7EB' }} />
                    <span style={{ fontSize: 11, color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      hoặc nhập OTP
                    </span>
                    <div style={{ flex: 1, height: 1, background: '#E5E7EB' }} />
                  </div>

                  {/* Radio tabs */}
                  <div style={{ display: 'flex', gap: 16, marginBottom: 12 }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, cursor: 'pointer', color: '#111827' }}>
                      <input type="radio" name="contactType" checked={contactType === 'email'} onChange={() => { setContactType('email'); setContact(''); setOtpCode(''); setOtpSent(false); setOtpError(null); }} /> Email
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, cursor: 'pointer', color: '#6B7280' }}>
                      <input type="radio" name="contactType" checked={contactType === 'phone'} onChange={() => { setContactType('phone'); setContact(''); setOtpCode(''); setOtpSent(false); setOtpError(null); }} /> Số điện thoại
                    </label>
                  </div>

                  {/* Luồng Phone OTP bị disabled an toàn khi chưa có SMS/ZNS */}
                  {contactType === 'phone' ? (
                    <div style={{
                      padding: '10px 12px',
                      background: '#FEF3C7',
                      border: '1px solid #FCD34D',
                      borderRadius: 10,
                      fontSize: 12,
                      color: '#92400E',
                      lineHeight: 1.45,
                      marginBottom: 8,
                    }}>
                      ⚠️ Phương thức xác thực qua số điện thoại tạm thời chưa khả dụng do đang nâng cấp hạ tầng SMS/ZNS. Vui lòng đăng nhập với <strong>Google</strong> hoặc <strong>Email</strong>.
                    </div>
                  ) : (
                    <>
                      <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                        <input
                          type="email"
                          placeholder="ten@gmail.com"
                          value={contact}
                          onChange={e => { setContact(e.target.value); setOtpError(null); setOtpSent(false); }}
                          disabled={otpSent}
                          style={{ flex: 1, padding: '10px 12px', borderRadius: 10, border: '1.5px solid #E5E7EB', outline: 'none', background: '#FAFAFA' }}
                        />
                        <button
                          onClick={handleSendOtp}
                          disabled={otpLoading || otpSent}
                          style={{ padding: '10px 14px', borderRadius: 10, border: 'none', background: '#0688A6', color: '#fff', fontWeight: 600, cursor: 'pointer', opacity: (otpLoading || otpSent) ? 0.6 : 1 }}
                        >
                          {otpLoading && !otpSent ? '...' : otpSent ? 'Đã gửi' : 'Gửi mã'}
                        </button>
                      </div>
                      {otpSent && (
                        <div style={{ display: 'flex', gap: 8, marginBottom: 4 }}>
                          <input
                            type="text" placeholder="Nhập mã OTP (6 số)"
                            value={otpCode} onChange={e => { setOtpCode(e.target.value.replace(/\D/g, '')); setOtpError(null); }}
                            maxLength={6}
                            style={{ flex: 1, padding: '10px 12px', borderRadius: 10, border: '1.5px solid #E5E7EB', outline: 'none', background: '#FAFAFA', textAlign: 'center', letterSpacing: '2px' }}
                          />
                          <button
                            onClick={handleVerifyOtp}
                            disabled={otpLoading || otpCode.length !== 6}
                            style={{ padding: '10px 14px', borderRadius: 10, border: 'none', background: '#10B981', color: '#fff', fontWeight: 600, cursor: 'pointer', opacity: (otpLoading || otpCode.length !== 6) ? 0.6 : 1 }}
                          >
                            {otpLoading ? '...' : 'Xác nhận'}
                          </button>
                        </div>
                      )}
                      {otpSent && <p style={{ fontSize: 11, color: '#9CA3AF' }}>Mã đã được gửi · Có hiệu lực 5 phút</p>}
                    </>
                  )}
                </>
              ) : null}
              {otpError && <p style={{ color: '#EF4444', fontSize: 12, marginTop: 6 }}>{otpError}</p>}
            </div>
          )}
        </div>

        {/* Badge hiển thị danh tính đã xác thực (khi ở stage feedback) */}
        {stage === 'feedback' && !isAnonymous && otpVerified && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px 12px',
            background: '#ECFDF5',
            border: '1px solid #A7F3D0',
            borderRadius: 12,
            marginBottom: 16,
            fontSize: 12,
            color: '#065F46',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              <span>✅</span>
              <span>
                {contactType === 'google' ? 'Google: ' : 'Email: '}
                <strong>{contact}</strong>
              </span>
            </div>
            <button
              type="button"
              onClick={handleResetAuth}
              style={{
                border: 'none',
                background: 'transparent',
                color: '#047857',
                textDecoration: 'underline',
                fontSize: 12,
                cursor: 'pointer',
                padding: '2px 4px',
              }}
            >
              Đổi
            </button>
          </div>
        )}

        {/* === MODE: AUDIO === */}
        {stage === 'feedback' && mode === 'audio' && (
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
            {isRecording && (
              <div style={{
                minHeight: 36, marginBottom: 8,
                padding: '8px 12px',
                background: 'rgba(0,122,255,0.05)',
                borderRadius: 12,
                fontSize: 13, 
                color: liveTranscript && isLiveTranscriptFinal ? '#374151' : '#6B7280', 
                fontStyle: liveTranscript && isLiveTranscriptFinal ? 'normal' : 'italic',
                fontWeight: liveTranscript && isLiveTranscriptFinal ? 500 : 400,
                textAlign: 'left', lineHeight: 1.5,
                transition: 'all 0.2s',
              }}>
                {!speechSupported 
                  ? 'Live transcript không khả dụng trên browser này.' 
                  : (liveTranscript ? `"${liveTranscript}"` : '🎙 Đang nghe...')}
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
        {stage === 'feedback' && mode === 'text' && (
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
