import { useState, useEffect, useRef } from 'react'
import { useCountUp } from '../hooks/useCountUp'
import { useReducedMotion } from '../hooks/useReducedMotion'

const CAPABILITIES = [
  {
    id: 'feedback',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
    title: 'Feedback in seconds',
    body: 'QR tại bàn. Khách nói hoặc gõ — xong trong 15 giây. Không form dài, không app, không đăng nhập.',
    color: 'var(--color-primary)',
    bg: 'var(--color-primary-light)',
  },
  {
    id: 'understand',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
    ),
    title: 'Understand what happened',
    body: 'Sentrix xác định sentiment, aspect, và yêu cầu cụ thể. Không chỉ "positive / negative" — mà là "Chính xác cái gì và ở đâu".',
    color: '#7C3AED',
    bg: 'rgba(124,58,237,0.08)',
    example: {
      text: '"Món ngon nhưng chờ hơi lâu."',
      aspects: [
        { label: 'Food', tag: '↑ Positive', tagColor: 'var(--color-success)' },
        { label: 'Service speed', tag: '↓ Issue', tagColor: 'var(--color-danger)' },
      ],
    },
  },
  {
    id: 'action',
    icon: (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
      </svg>
    ),
    title: 'Turn insight into action',
    body: 'Feedback trở thành cảnh báo. Yêu cầu hỗ trợ được gửi đến đúng người. Vấn đề được xử lý — khi khách vẫn còn ở quán.',
    color: '#F59E0B',
    bg: 'rgba(245,158,11,0.08)',
    highlight: true,
  },
]

export function ProductExperience() {
  const reducedMotion = useReducedMotion()
  const feedbackCount = useCountUp(128, 1600)
  const issueCount = useCountUp(7, 1400)
  const resolvedCount = useCountUp(6, 1500)

  return (
    <section id="product-experience" className="section" style={{ background: 'var(--color-surface)' }}>
      <div className="container">
        {/* Heading */}
        <div className="reveal" style={{ marginBottom: 'var(--space-12)' }}>
          <span className="label" style={{ display: 'block', marginBottom: 'var(--space-3)' }}>
            Core capabilities
          </span>
          <h2 className="heading-1" style={{ marginBottom: 'var(--space-4)', maxWidth: 640 }}>
            Three things Sentrix does really well.
          </h2>
          <p className="body-lg" style={{ maxWidth: 520 }}>
            Không phải 20 tính năng. Chỉ 3 thứ — mỗi thứ đều phục vụ một kết quả rõ ràng.
          </p>
        </div>

        {/* Capabilities */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 'var(--space-5)',
          marginBottom: 'var(--space-16)',
        }}
        className="cap-grid"
        >
          {CAPABILITIES.map((cap, i) => (
            <CapabilityCard key={cap.id} cap={cap} delay={i * 0.1} />
          ))}
        </div>

        {/* Dashboard preview */}
        <DashboardPreview
          feedbackCount={feedbackCount}
          issueCount={issueCount}
          resolvedCount={resolvedCount}
          reducedMotion={reducedMotion}
        />

        {/* Before / After */}
        <BeforeAfter reducedMotion={reducedMotion} />
      </div>

      <style>{`
        @media (max-width: 900px) {
          .cap-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </section>
  )
}

function CapabilityCard({ cap, delay }) {
  const [hovered, setHovered] = useState(false)

  return (
    <div
      className={`reveal reveal-delay-${Math.round(delay * 10) + 1}`}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: cap.highlight
          ? 'linear-gradient(135deg, var(--color-primary) 0%, #056880 100%)'
          : 'var(--color-surface)',
        border: `1px solid ${cap.highlight ? 'transparent' : 'var(--color-border)'}`,
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-8)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-4)',
        transition: 'all var(--ease-base)',
        transform: hovered ? 'translateY(-3px)' : 'none',
        boxShadow: cap.highlight
          ? 'var(--shadow-primary)'
          : hovered ? 'var(--shadow-md)' : 'var(--shadow-sm)',
      }}
    >
      {/* Icon */}
      <div style={{
        width: 48,
        height: 48,
        borderRadius: 'var(--radius-md)',
        background: cap.highlight ? 'rgba(255,255,255,0.15)' : cap.bg,
        color: cap.highlight ? '#fff' : cap.color,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}>
        {cap.icon}
      </div>

      <h3 style={{
        fontFamily: 'var(--font-display)',
        fontSize: 'var(--text-xl)',
        fontWeight: 700,
        color: cap.highlight ? '#fff' : 'var(--color-text)',
        letterSpacing: '-0.02em',
      }}>
        {cap.title}
      </h3>

      <p style={{
        fontSize: 'var(--text-base)',
        color: cap.highlight ? 'rgba(255,255,255,0.80)' : 'var(--color-text-secondary)',
        lineHeight: 1.7,
      }}>
        {cap.body}
      </p>

      {/* Example for understand card */}
      {cap.example && (
        <div style={{
          background: 'var(--color-bg)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)',
          marginTop: 'var(--space-1)',
        }}>
          <p style={{ fontStyle: 'italic', fontSize: 'var(--text-sm)', color: 'var(--color-text)', marginBottom: 'var(--space-3)', fontWeight: 500 }}>
            {cap.example.text}
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            {cap.example.aspects.map(a => (
              <div key={a.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--color-text)' }}>{a.label}</span>
                <span style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: a.tagColor, background: `${a.tagColor}15`, padding: '2px 8px', borderRadius: 'var(--radius-full)' }}>{a.tag}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action card highlight note */}
      {cap.highlight && (
        <div style={{
          background: 'rgba(255,255,255,0.12)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)',
          marginTop: 'var(--space-1)',
        }}>
          <p style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'rgba(255,255,255,0.9)', marginBottom: 6 }}>
            Example:
          </p>
          <p style={{ fontStyle: 'italic', fontSize: 'var(--text-sm)', color: 'rgba(255,255,255,0.75)', marginBottom: 'var(--space-3)' }}>
            "Cho mình thêm một ly trà đá."
          </p>
          <div style={{
            background: 'rgba(255,255,255,0.15)',
            borderRadius: 'var(--radius-sm)',
            padding: '6px 12px',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
          }}>
            <span style={{ fontSize: 14 }}>🔔</span>
            <span style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: '#fff' }}>Staff action required</span>
          </div>
          <p style={{ fontSize: 'var(--text-xs)', color: 'rgba(255,255,255,0.5)', marginTop: 6, fontStyle: 'italic' }}>
            Not just sentiment = neutral.
          </p>
        </div>
      )}
    </div>
  )
}

function DashboardPreview({ feedbackCount, issueCount, resolvedCount, reducedMotion }) {
  const [resolvedCount2, setResolvedCount2] = useState(6)
  const [latestIssue, setLatestIssue] = useState(null)
  const [issueStatus, setIssueStatus] = useState('open') // open | handling | resolved

  useEffect(() => {
    if (reducedMotion) return

    const seq = [
      () => setLatestIssue({ table: 12, time: '19:42', issue: 'Service speed' }),
      () => setIssueStatus('handling'),
      () => { setIssueStatus('resolved'); setResolvedCount2(7) },
      () => { setLatestIssue(null); setIssueStatus('open') },
    ]

    let step = 0
    const interval = setInterval(() => {
      if (step < seq.length) {
        seq[step]()
        step++
      } else {
        step = 0
        setResolvedCount2(6)
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [reducedMotion])

  return (
    <div
      className="reveal"
      style={{
        background: 'var(--color-bg)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-xl)',
        padding: 'var(--space-6)',
        marginBottom: 'var(--space-6)',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-6)' }}>
        <div>
          <p style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 'var(--text-lg)', color: 'var(--color-text)' }}>
            Operational Overview
          </p>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>Today</p>
        </div>
        <span style={{
          fontSize: 'var(--text-xs)',
          fontWeight: 600,
          color: 'var(--color-text-muted)',
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          padding: '4px 10px',
          borderRadius: 'var(--radius-full)',
          fontStyle: 'italic',
        }}>
          Product preview
        </span>
      </div>

      {/* KPI row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 'var(--space-4)',
        marginBottom: 'var(--space-6)',
      }}
      className="kpi-grid"
      >
        <KPICard label="Feedback" value={feedbackCount.value} ref={feedbackCount.ref} color="var(--color-primary)" />
        <KPICard label="Needs attention" value={issueCount.value} ref={issueCount.ref} color="var(--color-warning)" />
        <KPICard label="Resolved" value={resolvedCount2} color="var(--color-success)" />
        <div style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)',
        }}>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginBottom: 6, fontWeight: 500 }}>Top issue</p>
          <p style={{ fontWeight: 700, fontSize: 'var(--text-base)', color: 'var(--color-text)' }}>Service speed</p>
          <span className="chip chip-warning" style={{ marginTop: 8, display: 'inline-flex' }}>Recurring</span>
        </div>
      </div>

      {/* Live feed */}
      {latestIssue && (
        <div style={{
          background: 'var(--color-surface)',
          border: '1px solid rgba(245,158,11,0.25)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--space-4)',
          animation: reducedMotion ? 'none' : 'dropIn 0.4s ease',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 'var(--space-3)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <span style={{ fontSize: 20 }}>⚠️</span>
            <div>
              <p style={{ fontWeight: 600, fontSize: 'var(--text-sm)', color: 'var(--color-text)' }}>
                {latestIssue.issue} · Table {latestIssue.table}
              </p>
              <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>{latestIssue.time}</p>
            </div>
          </div>
          <StatusBadge status={issueStatus} />
        </div>
      )}

      <style>{`
        @media (max-width: 768px) {
          .kpi-grid { grid-template-columns: repeat(2, 1fr) !important; }
        }
      `}</style>
    </div>
  )
}

function KPICard({ label, value, color }) {
  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius-md)',
      padding: 'var(--space-4)',
    }}>
      <p style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginBottom: 6, fontWeight: 500 }}>{label}</p>
      <p style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 'var(--text-2xl)', color, lineHeight: 1 }}>
        {value}
      </p>
    </div>
  )
}

function StatusBadge({ status }) {
  const map = {
    open:     { label: 'Open',     color: 'var(--color-warning)', bg: 'var(--color-warning-light)' },
    handling: { label: 'Handling', color: 'var(--color-primary)', bg: 'var(--color-primary-light)' },
    resolved: { label: 'Resolved', color: 'var(--color-success)', bg: 'var(--color-success-light)' },
  }
  const s = map[status]
  return (
    <span style={{
      padding: '4px 12px',
      borderRadius: 'var(--radius-full)',
      fontSize: 'var(--text-xs)',
      fontWeight: 700,
      background: s.bg,
      color: s.color,
      transition: 'all 0.3s ease',
    }}>
      {s.label}
    </span>
  )
}

function BeforeAfter({ reducedMotion }) {
  return (
    <div className="reveal before-after-grid" style={{
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 'var(--space-4)',
      marginTop: 'var(--space-6)',
    }}
    >
      {/* Without */}
      <div style={{
        background: 'var(--color-bg)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-6)',
      }}>
        <p style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-5)' }}>
          Without Sentrix
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          {['Customer leaves', '⭐️⭐️⭐️ Review appears later', 'Owner sees: "3 stars"', '"What happened? When? Which table?"', 'Too late to act.'].map((step, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-2)' }}>
              <span style={{ color: 'var(--color-danger)', fontWeight: 700, fontSize: 'var(--text-xs)', marginTop: 2, flexShrink: 0 }}>→</span>
              <span style={{ fontSize: 'var(--text-sm)', color: i === 4 ? 'var(--color-danger)' : 'var(--color-text-secondary)', fontWeight: i === 4 ? 600 : 400 }}>
                {step}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* With Sentrix */}
      <div style={{
        background: 'linear-gradient(145deg, var(--color-primary-light), rgba(44,217,229,0.06))',
        border: '1px solid rgba(6,136,166,0.18)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-6)',
      }}>
        <p style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--color-primary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 'var(--space-5)' }}>
          With Sentrix
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          {[
            'Customer gives feedback',
            'Sentrix understands what happened',
            'Staff gets notified immediately',
            'Issue resolved while customer is still here.',
            'Owner sees the pattern — and fixes it.',
          ].map((step, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-2)' }}>
              <span style={{ color: 'var(--color-success)', fontWeight: 700, fontSize: 'var(--text-xs)', marginTop: 2, flexShrink: 0 }}>✓</span>
              <span style={{ fontSize: 'var(--text-sm)', color: i >= 3 ? 'var(--color-primary-dark)' : 'var(--color-text-secondary)', fontWeight: i >= 3 ? 600 : 400 }}>
                {step}
              </span>
            </div>
          ))}
        </div>
        <div style={{
          marginTop: 'var(--space-5)',
          padding: 'var(--space-3) var(--space-4)',
          background: 'var(--color-primary)',
          borderRadius: 'var(--radius-md)',
          textAlign: 'center',
        }}>
          <p style={{ fontSize: 'var(--text-sm)', fontWeight: 700, color: '#fff' }}>
            The difference is timing.
          </p>
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .before-after-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  )
}
