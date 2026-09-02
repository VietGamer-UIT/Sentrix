import { useState, useEffect } from 'react'
import { useReducedMotion } from '../hooks/useReducedMotion'

/*
  Dành cho quán — replaces ProductExperience + WhySentrix
  Three sub-sections:
  1. Chủ quán nhìn thấy gì (dashboard)
  2. Với khách — mọi thứ chỉ mất vài giây (phone)
  3. Before / after — khác biệt nằm ở thời điểm
*/

export function ForOwners() {
  return (
    <section id="cho-quan" className="section" style={{ background: 'var(--white)' }}>
      <div className="container">

        <div className="reveal" style={{ marginBottom: 'var(--s-20)' }}>
          <span className="eyebrow" style={{ display: 'block', marginBottom: 'var(--s-4)' }}>
            Dành cho quản lý
          </span>
          <h2 className="h3" style={{ color: 'var(--grey-900)', maxWidth: 560 }}>
            Chủ quán cần biết gì — Sentrix hiển thị được điều đó.
          </h2>
        </div>

        {/* Dashboard preview + owner questions */}
        <OwnerDashboard />

        {/* Divider */}
        <hr className="hr" style={{ margin: 'var(--s-20) 0' }} />

        {/* Customer side */}
        <CustomerSide />

        {/* Divider */}
        <hr className="hr" style={{ margin: 'var(--s-20) 0' }} />

        {/* Before / After */}
        <BeforeAfter />

        {/* Divider */}
        <hr className="hr" style={{ margin: 'var(--s-20) 0' }} />

        {/* Positioning */}
        <Positioning />
      </div>
    </section>
  )
}

/* ——— Owner Dashboard ——— */
function OwnerDashboard() {
  const reduced = useReducedMotion()
  const [liveIssue, setLiveIssue] = useState(null)
  const [issueState, setIssueState] = useState('open')
  const [resolved, setResolved] = useState(6)

  useEffect(() => {
    if (reduced) return
    const seq = [
      () => setLiveIssue({ table: 12, issue: 'Tốc độ phục vụ', time: '19:42' }),
      () => setIssueState('handling'),
      () => { setIssueState('resolved'); setResolved(7) },
      () => { setLiveIssue(null); setIssueState('open'); setResolved(6) },
    ]
    let i = 0
    const t = setInterval(() => { seq[i % seq.length](); i++ }, 2000)
    return () => clearInterval(t)
  }, [reduced])

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 'var(--s-16)',
      alignItems: 'start',
    }} className="owner-grid">

      {/* Left — questions */}
      <div className="reveal">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--s-5)' }}>
          {[
            'Khách đang phàn nàn điều gì? Khía cạnh nào?',
            'Vấn đề nào lặp lại nhiều lần trong tuần?',
            'Ca làm nào có nhiều phản hồi tiêu cực nhất?',
            'Vấn đề nào cần xử lý ngay hôm nay?',
            'Đội ngũ đã phản hồi và xử lý bao nhiêu trường hợp?',
          ].map((q, i) => (
            <div key={i} style={{ display: 'flex', gap: 'var(--s-4)', alignItems: 'flex-start' }}>
              <span style={{
                width: 6,
                height: 6,
                borderRadius: '50%',
                background: 'var(--teal)',
                flexShrink: 0,
                marginTop: 8,
              }} />
              <p style={{ fontSize: 'var(--t-lg)', color: 'var(--grey-700)', lineHeight: 1.55, fontWeight: 500 }}>
                {q}
              </p>
            </div>
          ))}
        </div>

        <p style={{
          marginTop: 'var(--s-8)',
          fontSize: 'var(--t-base)',
          color: 'var(--grey-400)',
          lineHeight: 1.7,
          borderLeft: '2px solid var(--grey-100)',
          paddingLeft: 'var(--s-5)',
        }}>
          Sentrix hiển thị xu hướng, vấn đề phổ biến và những trường hợp cần xử lý — không hiển thị thông tin cá nhân của khách.
        </p>
      </div>

      {/* Right — dashboard preview */}
      <div className="reveal d-2">
        <div style={{
          background: 'var(--off-white)',
          border: '1px solid var(--grey-100)',
          borderRadius: 'var(--r-xl)',
          padding: 'var(--s-6)',
        }}>
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--s-6)' }}>
            <div>
              <p style={{ fontWeight: 700, fontSize: 'var(--t-base)', color: 'var(--grey-900)' }}>
                Tổng quan hôm nay
              </p>
              <p style={{ fontSize: 'var(--t-xs)', color: 'var(--grey-300)' }}>Dữ liệu minh họa</p>
            </div>
            <span style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontSize: 'var(--t-xs)',
              color: 'var(--green)',
              fontWeight: 600,
            }}>
              <span className="dot-live" />
              Đang hoạt động
            </span>
          </div>

          {/* KPIs */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--s-3)', marginBottom: 'var(--s-4)' }}>
            <KPI label="Phản hồi" value="128" color="var(--teal)" />
            <KPI label="Cần xử lý" value="7" color="var(--amber)" />
            <KPI label="Đã xử lý" value={resolved} color="var(--green)" />
          </div>

          {/* Top issue */}
          <div style={{
            background: 'var(--white)',
            border: '1px solid var(--grey-100)',
            borderRadius: 'var(--r-md)',
            padding: 'var(--s-4)',
            marginBottom: 'var(--s-3)',
          }}>
            <p style={{ fontSize: 'var(--t-xs)', color: 'var(--grey-300)', marginBottom: 6, fontWeight: 500 }}>
              Vấn đề phổ biến nhất
            </p>
            <p style={{ fontWeight: 700, fontSize: 'var(--t-base)', color: 'var(--grey-900)' }}>
              Tốc độ phục vụ
            </p>
            <span className="tag tag-amber" style={{ marginTop: 8, display: 'inline-flex' }}>Xu hướng tăng</span>
          </div>

          {/* Live feed */}
          {liveIssue && (
            <div style={{
              background: 'var(--white)',
              border: '1px solid rgba(245,158,11,0.2)',
              borderRadius: 'var(--r-md)',
              padding: 'var(--s-4)',
              animation: reduced ? 'none' : 'slideDown 0.35s ease',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: 'var(--s-3)',
            }}>
              <div>
                <p style={{ fontWeight: 600, fontSize: 'var(--t-sm)', color: 'var(--grey-900)' }}>
                  {liveIssue.issue} · Bàn {liveIssue.table}
                </p>
                <p style={{ fontSize: 'var(--t-xs)', color: 'var(--grey-300)' }}>{liveIssue.time}</p>
              </div>
              <IssueStatusTag state={issueState} />
            </div>
          )}
        </div>
      </div>

      <style>{`
        @media (max-width: 900px) {
          .owner-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  )
}

function KPI({ label, value, color }) {
  return (
    <div style={{
      background: 'var(--white)',
      border: '1px solid var(--grey-100)',
      borderRadius: 'var(--r-md)',
      padding: 'var(--s-4)',
    }}>
      <p style={{ fontSize: 'var(--t-xs)', color: 'var(--grey-300)', marginBottom: 6, fontWeight: 500 }}>{label}</p>
      <p style={{ fontWeight: 800, fontSize: 'var(--t-3xl)', color, lineHeight: 1 }}>{value}</p>
    </div>
  )
}

function IssueStatusTag({ state }) {
  const map = {
    open:     { label: 'Chờ xử lý',  color: 'var(--amber)', bg: 'var(--amber-bg)' },
    handling: { label: 'Đang xử lý', color: 'var(--teal)',  bg: 'var(--teal-light)' },
    resolved: { label: 'Đã xử lý',   color: 'var(--green)', bg: 'var(--green-bg)' },
  }
  const s = map[state] || map.open
  return (
    <span style={{
      padding: '4px 10px',
      borderRadius: 'var(--r-pill)',
      fontSize: 'var(--t-xs)',
      fontWeight: 700,
      background: s.bg,
      color: s.color,
      whiteSpace: 'nowrap',
      transition: 'all 0.3s ease',
    }}>
      {s.label}
    </span>
  )
}

/* ——— Customer Side ——— */
function CustomerSide() {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 'var(--s-16)',
      alignItems: 'center',
    }} className="customer-grid">

      {/* Left — phone */}
      <div className="reveal" style={{ display: 'flex', justifyContent: 'center' }}>
        <CustomerPhone />
      </div>

      {/* Right — copy */}
      <div className="reveal d-2">
        <span className="eyebrow" style={{ display: 'block', marginBottom: 'var(--s-4)' }}>
          Với khách hàng
        </span>
        <h2 className="h4" style={{ color: 'var(--grey-900)', marginBottom: 'var(--s-5)' }}>
          Mọi thứ chỉ mất vài giây.
        </h2>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--s-4)', marginBottom: 'var(--s-8)' }}>
          {[
            { step: '1', label: 'Quét mã QR tại bàn' },
            { step: '2', label: 'Nói hoặc gõ phản hồi' },
            { step: '3', label: 'Gửi — xong trong 15 giây' },
          ].map(item => (
            <div key={item.step} style={{ display: 'flex', gap: 'var(--s-4)', alignItems: 'center' }}>
              <span style={{
                width: 32, height: 32,
                borderRadius: '50%',
                background: 'var(--teal-light)',
                border: '1px solid rgba(6,136,166,0.12)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 'var(--t-xs)',
                fontWeight: 700,
                color: 'var(--teal)',
                flexShrink: 0,
              }}>{item.step}</span>
              <p style={{ fontSize: 'var(--t-base)', color: 'var(--grey-700)', fontWeight: 500 }}>{item.label}</p>
            </div>
          ))}
        </div>

        <p style={{
          fontSize: 'var(--t-base)',
          color: 'var(--grey-400)',
          lineHeight: 1.7,
          borderLeft: '2px solid var(--teal-light)',
          paddingLeft: 'var(--s-5)',
        }}>
          Không cần tải ứng dụng. Không cần đăng nhập. Không điền biểu mẫu dài.
        </p>
      </div>

      <style>{`
        @media (max-width: 900px) {
          .customer-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  )
}

function CustomerPhone() {
  return (
    <div className="phone-shell" style={{ width: 220 }}>
      <div className="phone-screen" style={{ minHeight: 380, display: 'flex', flexDirection: 'column' }}>
        {/* App bar */}
        <div style={{
          background: 'var(--teal)',
          padding: '10px 14px 8px',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}>
          <img src="/sentrix-logo.png" alt="" style={{ width: 18, height: 18, objectFit: 'contain', opacity: 0.9 }} />
          <span style={{ color: 'rgba(255,255,255,0.9)', fontSize: 11, fontWeight: 800, letterSpacing: '-0.01em' }}>
            SENTRIX
          </span>
        </div>

        <div style={{ flex: 1, padding: 'var(--s-4)', background: 'var(--off-white)', display: 'flex', flexDirection: 'column', gap: 'var(--s-3)' }}>
          <p style={{ fontSize: 11, color: 'var(--grey-400)', fontWeight: 600 }}>
            Cảm nhận của bạn về lần này?
          </p>

          {/* Record button */}
          <div style={{
            background: 'var(--white)',
            border: '1px solid var(--grey-100)',
            borderRadius: 'var(--r-md)',
            padding: 'var(--s-5)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 'var(--s-3)',
          }}>
            <div style={{
              width: 52,
              height: 52,
              borderRadius: '50%',
              background: 'var(--teal)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 16px rgba(6,136,166,0.35)',
            }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" aria-label="Ghi âm">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
              </svg>
            </div>
            <p style={{ fontSize: 10, color: 'var(--grey-400)', textAlign: 'center', lineHeight: 1.4 }}>
              Nhấn để nói · hoặc gõ bên dưới
            </p>
          </div>

          <div style={{
            background: 'var(--white)',
            border: '1px solid var(--grey-200)',
            borderRadius: 'var(--r-sm)',
            padding: '8px 10px',
            fontSize: 11,
            color: 'var(--grey-300)',
          }}>
            Nhập phản hồi...
          </div>

          <p style={{ fontSize: 9, color: 'var(--grey-300)', textAlign: 'center', lineHeight: 1.5 }}>
            Không cần tải ứng dụng · Không cần đăng nhập
          </p>
        </div>
      </div>
    </div>
  )
}

/* ——— Before / After ——— */
function BeforeAfter() {
  return (
    <div className="reveal">
      <div style={{ textAlign: 'center', marginBottom: 'var(--s-12)' }}>
        <h2 className="h4" style={{ color: 'var(--grey-900)' }}>
          Khác biệt nằm ở thời điểm.
        </h2>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 'var(--s-4)',
      }} className="ba-grid">
        {/* Before */}
        <div style={{
          background: 'var(--off-white)',
          border: '1px solid var(--grey-100)',
          borderRadius: 'var(--r-xl)',
          padding: 'var(--s-8)',
        }}>
          <p style={{ fontSize: 'var(--t-xs)', fontWeight: 700, color: 'var(--grey-300)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--s-6)' }}>
            Không có Sentrix
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--s-4)' }}>
            {[
              { t: 'Khách gặp vấn đề', c: 'var(--grey-700)' },
              { t: 'Không nói với nhân viên', c: 'var(--grey-400)' },
              { t: 'Rời quán', c: 'var(--grey-400)' },
              { t: 'Review xuất hiện sau đó', c: 'var(--red)' },
              { t: 'Chủ quán mới biết — đã muộn', c: 'var(--red)', bold: true },
            ].map((item, i) => (
              <div key={i} style={{ display: 'flex', gap: 'var(--s-3)', alignItems: 'flex-start' }}>
                <span style={{ color: 'var(--grey-200)', fontSize: 'var(--t-sm)', flexShrink: 0, paddingTop: 2 }}>→</span>
                <p style={{ fontSize: 'var(--t-base)', color: item.c, fontWeight: item.bold ? 600 : 400 }}>{item.t}</p>
              </div>
            ))}
          </div>
        </div>

        {/* After */}
        <div style={{
          background: 'linear-gradient(145deg, rgba(6,136,166,0.04), rgba(44,217,229,0.04))',
          border: '1px solid rgba(6,136,166,0.12)',
          borderRadius: 'var(--r-xl)',
          padding: 'var(--s-8)',
        }}>
          <p style={{ fontSize: 'var(--t-xs)', fontWeight: 700, color: 'var(--teal)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--s-6)' }}>
            Có Sentrix
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--s-4)' }}>
            {[
              { t: 'Khách gặp vấn đề', c: 'var(--grey-700)' },
              { t: 'Nói hoặc gõ vài câu', c: 'var(--grey-700)' },
              { t: 'Sentrix hiểu và phân loại', c: 'var(--grey-700)' },
              { t: 'Nhân viên được báo ngay', c: 'var(--teal)' },
              { t: 'Xử lý khi khách còn ở đây', c: 'var(--teal)', bold: true },
            ].map((item, i) => (
              <div key={i} style={{ display: 'flex', gap: 'var(--s-3)', alignItems: 'flex-start' }}>
                <span style={{ color: 'var(--teal)', fontSize: 'var(--t-sm)', flexShrink: 0, paddingTop: 2, fontWeight: 700 }}>✓</span>
                <p style={{ fontSize: 'var(--t-base)', color: item.c, fontWeight: item.bold ? 600 : 400 }}>{item.t}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .ba-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  )
}

/* ——— Positioning ——— */
function Positioning() {
  const TECH = [
    { label: 'Giao diện khách', value: 'React (Vite)' },
    { label: 'Backend', value: 'FastAPI (Python)' },
    { label: 'Giọng nói → Văn bản', value: 'Whisper STT' },
    { label: 'Phân tích NLP', value: 'Gemini 2.0 Flash' },
    { label: 'Cơ sở dữ liệu', value: 'Firestore' },
    { label: 'Hạ tầng', value: 'Firebase + Render' },
  ]

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 'var(--s-16)',
      alignItems: 'start',
    }} className="pos-grid">

      {/* Left */}
      <div className="reveal">
        <span className="eyebrow" style={{ display: 'block', marginBottom: 'var(--s-4)' }}>
          Định vị sản phẩm
        </span>
        <h2 className="h4" style={{ color: 'var(--grey-900)', marginBottom: 'var(--s-5)' }}>
          Sentrix không cố trở thành một hệ thống quản trị khổng lồ.
        </h2>
        <p className="body-lg" style={{ marginBottom: 'var(--s-6)' }}>
          Sentrix tập trung vào một việc: giúp cửa hàng nghe khách, hiểu vấn đề và xử lý kịp lúc.
        </p>

        <div style={{
          background: 'var(--off-white)',
          border: '1px solid var(--grey-100)',
          borderRadius: 'var(--r-lg)',
          overflow: 'hidden',
        }}>
          {[
            ['Công cụ khảo sát thông thường', 'Thu thập → Lưu trữ → Báo cáo định kỳ'],
            ['Sentrix', 'Lắng nghe → Hiểu → Hành động → Học'],
          ].map(([label, value], i) => (
            <div key={i} style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              borderBottom: i === 0 ? '1px solid var(--grey-100)' : 'none',
            }}>
              <div style={{ padding: 'var(--s-4) var(--s-5)', borderRight: '1px solid var(--grey-100)' }}>
                <p style={{ fontSize: 'var(--t-sm)', color: i === 0 ? 'var(--grey-400)' : 'var(--teal)', fontWeight: i === 1 ? 700 : 400 }}>{label}</p>
              </div>
              <div style={{ padding: 'var(--s-4) var(--s-5)', background: i === 1 ? 'var(--teal-light)' : 'transparent' }}>
                <p style={{ fontSize: 'var(--t-sm)', color: i === 0 ? 'var(--grey-400)' : 'var(--teal)', fontWeight: i === 1 ? 700 : 400 }}>{value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right — tech + trust */}
      <div className="reveal d-2">
        {/* Trust */}
        <div style={{ marginBottom: 'var(--s-8)' }}>
          <p style={{ fontSize: 'var(--t-sm)', fontWeight: 600, color: 'var(--grey-700)', marginBottom: 'var(--s-4)' }}>
            Dữ liệu & bảo mật
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--s-3)' }}>
            {[
              'Phản hồi ẩn danh — khách có thể chọn không để lại thông tin cá nhân',
              'Audio được xử lý và không lưu giữ lâu dài',
              'Chỉ thu thập dữ liệu cần thiết cho mục đích vận hành',
              'Có cơ chế xin phép trước khi ghi âm',
            ].map((item, i) => (
              <div key={i} style={{ display: 'flex', gap: 'var(--s-3)', alignItems: 'flex-start' }}>
                <span style={{ color: 'var(--teal)', flexShrink: 0, paddingTop: 3 }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" aria-hidden="true">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </span>
                <p style={{ fontSize: 'var(--t-sm)', color: 'var(--grey-500)', lineHeight: 1.6 }}>{item}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Tech */}
        <div>
          <p style={{ fontSize: 'var(--t-xs)', fontWeight: 700, color: 'var(--grey-300)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--s-4)' }}>
            Công nghệ đứng phía sau Sentrix
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--s-2)' }}>
            {TECH.map(t => (
              <div key={t.label} style={{
                background: 'var(--off-white)',
                border: '1px solid var(--grey-100)',
                borderRadius: 'var(--r-md)',
                padding: '8px 14px',
              }}>
                <p style={{ fontSize: 'var(--t-xs)', color: 'var(--grey-300)', marginBottom: 2 }}>{t.label}</p>
                <p style={{ fontSize: 'var(--t-sm)', fontWeight: 700, color: 'var(--grey-700)' }}>{t.value}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 900px) {
          .pos-grid { grid-template-columns: 1fr !important; gap: var(--s-10) !important; }
        }
      `}</style>
    </div>
  )
}
