import { useState } from 'react'
import { useReducedMotion } from '../hooks/useReducedMotion'

/*
  WOW Demo — cinematic product story
  ONE sentence → 4 transforming stages
  Sticky scroll feel with manual navigation
*/

const STAGES = [
  {
    id: 'raw',
    title: 'Phản hồi gốc',
    desc: 'Khách nói hoặc gõ',
  },
  {
    id: 'understand',
    title: 'Sentrix hiểu',
    desc: 'Phân tích từng khía cạnh',
  },
  {
    id: 'act',
    title: 'Sentrix xử lý',
    desc: 'Chuyển thành thông báo',
  },
  {
    id: 'learn',
    title: 'Cửa hàng nhìn thấy',
    desc: 'Xu hướng & dữ liệu',
  },
]

export function ProductDemo() {
  const [active, setActive] = useState(0)
  const reduced = useReducedMotion()

  return (
    <section id="san-pham" className="section" style={{
      background: 'var(--off-white)',
      borderTop: '1px solid var(--grey-100)',
    }}>
      <div className="container">
        {/* Heading */}
        <div className="reveal" style={{ marginBottom: 'var(--s-12)' }}>
          <span className="eyebrow" style={{ display: 'block', marginBottom: 'var(--s-4)' }}>
            Demo thực tế
          </span>
          <h2 className="h3" style={{ color: 'var(--grey-900)', marginBottom: 'var(--s-4)', maxWidth: 580 }}>
            Xem Sentrix làm gì với một câu phản hồi.
          </h2>
          <p className="body-lg" style={{ maxWidth: 480 }}>
            Từ lời nói của khách đến hành động của nhân viên — dưới đây là toàn bộ quá trình.
          </p>
        </div>

        {/* Demo panel */}
        <div className="reveal" style={{
          background: 'var(--white)',
          border: '1px solid var(--grey-100)',
          borderRadius: 'var(--r-2xl)',
          overflow: 'hidden',
          boxShadow: 'var(--shadow-md)',
        }}>
          {/* Tab row */}
          <div style={{
            display: 'flex',
            borderBottom: '1px solid var(--grey-100)',
            overflowX: 'auto',
          }} role="tablist" aria-label="Các bước xử lý phản hồi">
            {STAGES.map((s, i) => (
              <button
                key={s.id}
                id={`demo-tab-${s.id}`}
                role="tab"
                aria-selected={active === i}
                aria-controls={`demo-panel-${s.id}`}
                onClick={() => setActive(i)}
                style={{
                  flex: 1,
                  minWidth: 120,
                  background: 'none',
                  border: 'none',
                  borderBottom: `2px solid ${active === i ? 'var(--teal)' : 'transparent'}`,
                  padding: 'var(--s-4) var(--s-5)',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'border-color var(--ease-fast)',
                }}
              >
                <span style={{
                  display: 'block',
                  fontSize: 10,
                  fontWeight: 700,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  color: active === i ? 'var(--teal)' : 'var(--grey-300)',
                  marginBottom: 4,
                }}>
                  {String(i + 1).padStart(2, '0')}
                </span>
                <span style={{
                  fontSize: 'var(--t-sm)',
                  fontWeight: 600,
                  color: active === i ? 'var(--grey-900)' : 'var(--grey-400)',
                  whiteSpace: 'nowrap',
                }}>
                  {s.title}
                </span>
              </button>
            ))}
          </div>

          {/* Content */}
          <div
            id={`demo-panel-${STAGES[active].id}`}
            role="tabpanel"
            aria-labelledby={`demo-tab-${STAGES[active].id}`}
            style={{ padding: 'var(--s-8)' }}
          >
            <p style={{
              fontSize: 'var(--t-xs)',
              fontWeight: 600,
              color: 'var(--grey-300)',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              marginBottom: 'var(--s-6)',
            }}>
              {STAGES[active].desc}
            </p>

            <div
              key={active}
              style={{ animation: reduced ? 'none' : 'fadeIn 0.3s ease' }}
            >
              <DemoContent stage={active} />
            </div>

            {/* Nav */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: 'var(--s-8)',
              paddingTop: 'var(--s-6)',
              borderTop: '1px solid var(--grey-100)',
            }}>
              <button
                onClick={() => setActive(a => Math.max(0, a - 1))}
                disabled={active === 0}
                style={{
                  background: 'none',
                  border: '1px solid var(--grey-200)',
                  borderRadius: 'var(--r-pill)',
                  padding: '8px 18px',
                  fontSize: 'var(--t-sm)',
                  fontWeight: 500,
                  color: 'var(--grey-400)',
                  cursor: active === 0 ? 'not-allowed' : 'pointer',
                  opacity: active === 0 ? 0.35 : 1,
                  transition: 'opacity var(--ease-fast)',
                }}
              >
                ← Trước
              </button>

              <div style={{ display: 'flex', gap: 6 }}>
                {STAGES.map((_, i) => (
                  <button
                    key={i}
                    onClick={() => setActive(i)}
                    aria-label={`Bước ${i + 1}`}
                    style={{
                      width: active === i ? 22 : 8,
                      height: 8,
                      borderRadius: 4,
                      background: active === i ? 'var(--teal)' : 'var(--grey-200)',
                      border: 'none',
                      cursor: 'pointer',
                      padding: 0,
                      transition: 'all var(--ease)',
                    }}
                  />
                ))}
              </div>

              <button
                onClick={() => setActive(a => Math.min(STAGES.length - 1, a + 1))}
                disabled={active === STAGES.length - 1}
                style={{
                  background: active < STAGES.length - 1 ? 'var(--teal)' : 'none',
                  border: active < STAGES.length - 1 ? 'none' : '1px solid var(--grey-200)',
                  borderRadius: 'var(--r-pill)',
                  padding: '8px 18px',
                  fontSize: 'var(--t-sm)',
                  fontWeight: 600,
                  color: active < STAGES.length - 1 ? '#fff' : 'var(--grey-400)',
                  cursor: active === STAGES.length - 1 ? 'not-allowed' : 'pointer',
                  opacity: active === STAGES.length - 1 ? 0.35 : 1,
                  transition: 'all var(--ease-fast)',
                }}
              >
                Tiếp →
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

function DemoContent({ stage }) {
  switch (stage) {
    case 0: return <StageRaw />
    case 1: return <StageUnderstand />
    case 2: return <StageAct />
    case 3: return <StageLearn />
    default: return null
  }
}

function StageRaw() {
  return (
    <div style={{
      background: 'var(--off-white)',
      border: '1px solid var(--grey-100)',
      borderRadius: 'var(--r-lg)',
      padding: 'var(--s-6) var(--s-8)',
      maxWidth: 560,
    }}>
      <p style={{
        fontSize: 'var(--t-xs)',
        fontWeight: 600,
        color: 'var(--grey-300)',
        textTransform: 'uppercase',
        letterSpacing: '0.08em',
        marginBottom: 'var(--s-3)',
      }}>
        Bàn 08 · 19:24
      </p>
      <p style={{
        fontSize: 'var(--t-3xl)',
        fontWeight: 700,
        color: 'var(--grey-900)',
        lineHeight: 1.3,
        letterSpacing: '-0.02em',
        fontStyle: 'italic',
      }}>
        "Món ngon nhưng chờ hơi lâu."
      </p>
      <div style={{ marginTop: 'var(--s-5)' }}>
        <div className="waveform active" style={{ height: 28 }}>
          {[...Array(6)].map((_, i) => <div key={i} className="wave-bar" />)}
        </div>
        <p style={{ fontSize: 'var(--t-xs)', color: 'var(--grey-300)', marginTop: 'var(--s-2)' }}>
          Phản hồi bằng giọng nói
        </p>
      </div>
    </div>
  )
}

function StageUnderstand() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--s-4)', maxWidth: 480 }}>
      <AspectCard
        aspect="Chất lượng món"
        verdict="Tốt"
        detail="Khách hài lòng với thức ăn"
        positive
      />
      <AspectCard
        aspect="Tốc độ phục vụ"
        verdict="Cần cải thiện"
        detail="Thời gian chờ quá dài so với mong đợi"
        positive={false}
      />
    </div>
  )
}

function StageAct() {
  return (
    <div style={{ maxWidth: 480 }}>
      <div style={{
        background: 'rgba(245,158,11,0.05)',
        border: '1.5px solid rgba(245,158,11,0.2)',
        borderRadius: 'var(--r-lg)',
        padding: 'var(--s-6)',
        marginBottom: 'var(--s-4)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--s-3)', marginBottom: 'var(--s-4)' }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#D97706" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          <span style={{ fontSize: 'var(--t-sm)', fontWeight: 700, color: '#B45309' }}>
            Nhân viên đã được thông báo
          </span>
        </div>
        <p style={{
          fontSize: 'var(--t-xl)',
          fontWeight: 700,
          color: 'var(--grey-900)',
          letterSpacing: '-0.01em',
          marginBottom: 'var(--s-3)',
        }}>
          Bàn 08 cần được hỗ trợ
        </p>
        <p style={{ fontSize: 'var(--t-sm)', color: 'var(--grey-400)' }}>Tốc độ phục vụ · 19:24</p>
      </div>
      <div style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 'var(--s-2)',
        background: 'var(--green-bg)',
        border: '1px solid rgba(16,185,129,0.12)',
        borderRadius: 'var(--r-pill)',
        padding: '6px 14px',
        fontSize: 'var(--t-xs)',
        fontWeight: 600,
        color: 'var(--green)',
      }}>
        <span className="dot-live" />
        Đang chờ nhân viên xử lý
      </div>
    </div>
  )
}

function StageLearn() {
  return (
    <div style={{ maxWidth: 520 }}>
      <div style={{
        background: 'var(--white)',
        border: '1px solid var(--grey-100)',
        borderRadius: 'var(--r-lg)',
        padding: 'var(--s-6)',
        marginBottom: 'var(--s-4)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--s-5)' }}>
          <div>
            <p style={{ fontSize: 'var(--t-base)', fontWeight: 700, color: 'var(--grey-900)', marginBottom: 4 }}>
              Tốc độ phục vụ
            </p>
            <p style={{ fontSize: 'var(--t-sm)', color: 'var(--grey-400)' }}>7 ngày qua</p>
          </div>
          <span className="tag tag-amber">Xu hướng tăng</span>
        </div>

        <MiniBar label="Tuần này" pct={72} color="var(--red)" />
        <MiniBar label="Tuần trước" pct={44} color="var(--amber)" />
      </div>

      <p style={{
        fontSize: 'var(--t-sm)',
        color: 'var(--grey-700)',
        fontWeight: 600,
        lineHeight: 1.6,
        padding: 'var(--s-4)',
        background: 'var(--teal-light)',
        borderRadius: 'var(--r-md)',
        borderLeft: '3px solid var(--teal)',
      }}>
        Tốc độ phục vụ là vấn đề xuất hiện nhiều nhất trong tuần — có thể xem xét phân công thêm nhân sự vào giờ cao điểm.
      </p>

      <p style={{
        fontSize: 'var(--t-xs)',
        color: 'var(--grey-300)',
        marginTop: 'var(--s-3)',
        fontStyle: 'italic',
      }}>
        Dữ liệu minh họa
      </p>
    </div>
  )
}

function AspectCard({ aspect, verdict, detail, positive }) {
  return (
    <div style={{
      background: positive ? 'var(--green-bg)' : 'var(--red-bg)',
      border: `1px solid ${positive ? 'rgba(16,185,129,0.14)' : 'rgba(239,68,68,0.14)'}`,
      borderRadius: 'var(--r-lg)',
      padding: 'var(--s-5)',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      gap: 'var(--s-4)',
    }}>
      <div>
        <p style={{ fontWeight: 700, fontSize: 'var(--t-base)', color: 'var(--grey-900)', marginBottom: 4 }}>
          {aspect}
        </p>
        <p style={{ fontSize: 'var(--t-sm)', color: 'var(--grey-500)' }}>{detail}</p>
      </div>
      <span style={{
        fontSize: 'var(--t-sm)',
        fontWeight: 700,
        color: positive ? 'var(--green)' : 'var(--red)',
        whiteSpace: 'nowrap',
      }}>
        {verdict}
      </span>
    </div>
  )
}

function MiniBar({ label, pct, color }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--s-3)',
      marginBottom: 'var(--s-3)',
    }}>
      <span style={{ width: 80, fontSize: 'var(--t-xs)', color: 'var(--grey-400)', flexShrink: 0 }}>{label}</span>
      <div style={{ flex: 1, height: 6, background: 'var(--grey-100)', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 3 }} />
      </div>
      <span style={{ width: 32, fontSize: 'var(--t-xs)', color: 'var(--grey-400)', textAlign: 'right' }}>{pct}%</span>
    </div>
  )
}
