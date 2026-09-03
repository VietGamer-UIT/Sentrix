import { useState, useEffect } from 'react'
import { useReducedMotion } from '../hooks/useReducedMotion'

/*
  Hero — single cinematic product story
  Visual: one phone showing the feedback pipeline
  Animation: calm 5-stage sequence, loops slowly
*/

const STAGES = [
  'idle',       // 0 — empty phone
  'speaking',   // 1 — customer voices feedback
  'analyzing',  // 2 — waveform + "Đang phân tích..."
  'understood', // 3 — aspect breakdown appears
  'notified',   // 4 — staff notification
]

const STAGE_MS = 2600

export function Hero() {
  const reduced = useReducedMotion()
  const [stage, setStage] = useState(0)

  useEffect(() => {
    if (reduced) { setStage(4); return }
    const t = setInterval(() => setStage(s => (s + 1) % STAGES.length), STAGE_MS)
    return () => clearInterval(t)
  }, [reduced])

  const goTo = (href) => (e) => {
    e.preventDefault()
    document.querySelector(href)?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <section
      aria-label="Giới thiệu Sentrix"
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        paddingTop: 'var(--navbar-h)',
        background: 'var(--white)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Subtle teal tint — top-right */}
      <div aria-hidden="true" style={{
        position: 'absolute',
        width: 560,
        height: 560,
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(6,136,166,0.055) 0%, transparent 70%)',
        top: '-80px',
        right: '-80px',
        pointerEvents: 'none',
      }} />

      <div className="container">
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 'var(--s-16)',
          alignItems: 'center',
          minHeight: 'calc(100vh - var(--navbar-h))',
          paddingBottom: 'var(--s-16)',
        }} className="hero-grid">

          {/* LEFT — copy */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--s-6)' }}>

            <div style={{ animation: reduced ? 'none' : 'fadeIn 0.6s ease both' }}>
              <span className="tag tag-teal">
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--teal)', display: 'inline-block' }} />
                Nền tảng phản hồi & hành động tức thì cho F&B
              </span>
            </div>

            <h1 className="h1" style={{
              color: 'var(--grey-900)',
              animation: reduced ? 'none' : 'fadeIn 0.65s 0.08s ease both',
            }}>
              Khách im lặng<br />
              <span style={{ color: 'var(--teal)' }}>không có nghĩa</span><br />
              là họ hài lòng.
            </h1>

            <p className="body-xl" style={{
              maxWidth: 480,
              animation: reduced ? 'none' : 'fadeIn 0.65s 0.16s ease both',
            }}>
              Sentrix lắng nghe phản hồi ngay tại bàn, phân tích vấn đề theo từng khía cạnh và báo nhân viên trong vài giây — để bạn xử lý khi khách vẫn còn ở đây.
            </p>

            <div style={{
              display: 'flex',
              gap: 'var(--s-3)',
              flexWrap: 'wrap',
              animation: reduced ? 'none' : 'fadeIn 0.65s 0.24s ease both',
            }}>
              <a
                href="#dung-thu"
                id="hero-cta-main"
                className="btn btn-primary-lg"
                onClick={goTo('#dung-thu')}
              >
                Đăng ký dùng thử
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
                </svg>
              </a>
              <a
                href="#cach-hoat-dong"
                id="hero-cta-secondary"
                className="btn btn-secondary"
                onClick={goTo('#cach-hoat-dong')}
              >
                Xem cách Sentrix hoạt động
              </a>
            </div>

            {/* Trust line */}
            <p style={{
              fontSize: 'var(--t-sm)',
              color: 'var(--grey-300)',
              marginTop: 'var(--s-2)',
              animation: reduced ? 'none' : 'fadeIn 0.65s 0.32s ease both',
            }}>
              Không cần cài ứng dụng · Không cần tích hợp POS · Không thay đổi quy trình hiện tại
            </p>
          </div>

          {/* RIGHT — phone visual */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            animation: reduced ? 'none' : 'fadeInScale 0.8s 0.2s ease both',
          }}
            aria-label="Minh họa sản phẩm Sentrix"
          >
            <HeroPhone stage={stage} reduced={reduced} />
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 900px) {
          .hero-grid {
            grid-template-columns: 1fr !important;
            min-height: auto !important;
            padding-top: var(--s-10) !important;
            gap: var(--s-12) !important;
          }
        }
      `}</style>
    </section>
  )
}

/* ——— Phone product story ——— */
function HeroPhone({ stage, reduced }) {
  return (
    <div className="phone-shell" style={{ width: 280, position: 'relative' }}>
      <div className="phone-screen" style={{ minHeight: 520, display: 'flex', flexDirection: 'column' }}>
        {/* Status bar */}
        <div style={{
          background: 'var(--teal)',
          padding: '12px 16px 10px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <img src="/sentrix-logo.png" alt="" style={{ width: 20, height: 20, objectFit: 'contain', opacity: 0.9 }} />
            <span style={{ color: 'rgba(255,255,255,0.92)', fontSize: 'var(--t-xs)', fontWeight: 700, letterSpacing: '-0.01em' }}>
              SENTRIX
            </span>
          </div>
          <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.6)', fontWeight: 500 }}>Bàn 08</span>
        </div>

        {/* Screen content */}
        <div style={{
          flex: 1,
          padding: 'var(--s-5)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--s-4)',
          background: 'var(--off-white)',
        }}>

          {/* Stage 0 + 1: Customer input */}
          <div>
            <p style={{ fontSize: 'var(--t-xs)', fontWeight: 600, color: 'var(--grey-300)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--s-2)' }}>
              Phản hồi của khách
            </p>

            <div style={{
              background: 'var(--white)',
              border: '1px solid var(--grey-100)',
              borderRadius: 'var(--r-md)',
              padding: 'var(--s-4)',
            }}>
              {/* Quote bubble */}
              <div style={{
                fontStyle: 'italic',
                fontSize: 'var(--t-sm)',
                color: 'var(--grey-700)',
                fontWeight: 500,
                lineHeight: 1.55,
                marginBottom: 'var(--s-3)',
                opacity: stage >= 1 || reduced ? 1 : 0.3,
                transition: 'opacity 0.5s ease',
              }}>
                "Món ngon nhưng chờ hơi lâu."
              </div>

              {/* Waveform */}
              <div className={`waveform ${stage === 1 && !reduced ? 'active' : ''}`}>
                {[...Array(6)].map((_, i) => <div key={i} className="wave-bar" />)}
              </div>
            </div>
          </div>

          {/* Stage 2: Analyzing */}
          <div style={{
            opacity: stage >= 2 || reduced ? 1 : 0,
            transform: stage >= 2 || reduced ? 'none' : 'translateY(8px)',
            transition: 'opacity 0.5s ease, transform 0.5s ease',
          }}>
            <p style={{ fontSize: 'var(--t-xs)', fontWeight: 600, color: 'var(--grey-300)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--s-2)' }}>
              Sentrix hiểu
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--s-2)' }}>
              {/* Aspect: Food */}
              <div style={{
                background: 'var(--green-bg)',
                border: '1px solid rgba(16,185,129,0.15)',
                borderRadius: 'var(--r-sm)',
                padding: '8px 12px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                opacity: stage >= 3 || reduced ? 1 : 0,
                transform: stage >= 3 || reduced ? 'none' : 'translateY(6px)',
                transition: 'all 0.4s ease',
              }}>
                <span style={{ fontSize: 'var(--t-xs)', fontWeight: 600, color: 'var(--grey-700)' }}>Chất lượng món</span>
                <span style={{ fontSize: 'var(--t-xs)', fontWeight: 700, color: 'var(--green)' }}>Tốt</span>
              </div>

              {/* Aspect: Speed */}
              <div style={{
                background: 'var(--red-bg)',
                border: '1px solid rgba(239,68,68,0.15)',
                borderRadius: 'var(--r-sm)',
                padding: '8px 12px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                opacity: stage >= 3 || reduced ? 1 : 0,
                transform: stage >= 3 || reduced ? 'none' : 'translateY(6px)',
                transition: 'all 0.4s 0.1s ease',
              }}>
                <span style={{ fontSize: 'var(--t-xs)', fontWeight: 600, color: 'var(--grey-700)' }}>Tốc độ phục vụ</span>
                <span style={{ fontSize: 'var(--t-xs)', fontWeight: 700, color: 'var(--red)' }}>Cần cải thiện</span>
              </div>
            </div>
          </div>

          {/* Stage 4: Notification */}
          <div style={{
            opacity: stage >= 4 || reduced ? 1 : 0,
            transform: stage >= 4 || reduced ? 'none' : 'translateY(8px)',
            transition: 'opacity 0.5s ease, transform 0.5s ease',
          }}>
            <div style={{
              background: 'var(--amber-bg)',
              border: '1px solid rgba(245,158,11,0.2)',
              borderRadius: 'var(--r-md)',
              padding: 'var(--s-4)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--s-2)', marginBottom: 6 }}>
                <span style={{ fontSize: 12 }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#B45309" strokeWidth="2.5" strokeLinecap="round" aria-hidden="true">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                  </svg>
                </span>
                <span style={{ fontSize: 'var(--t-xs)', fontWeight: 700, color: '#B45309' }}>
                  Nhân viên đã được báo
                </span>
              </div>
              <p style={{ fontSize: 'var(--t-xs)', color: 'var(--grey-500)', lineHeight: 1.5 }}>
                Bàn 08 cần được hỗ trợ
              </p>
            </div>
          </div>

          {/* Stage indicator */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: 5,
            marginTop: 'auto',
            paddingTop: 'var(--s-3)',
          }}>
            {STAGES.map((_, i) => (
              <div key={i} style={{
                width: i === stage ? 16 : 5,
                height: 5,
                borderRadius: 3,
                background: i === stage ? 'var(--teal)' : 'var(--grey-200)',
                transition: 'all 0.4s ease',
              }} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
