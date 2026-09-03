const TRUST_POINTS = [
  {
    icon: '🎙️',
    title: 'Audio processed and cleared',
    body: 'Voice input is converted to text immediately. Audio is not retained beyond what is needed for processing.',
  },
  {
    icon: '🔒',
    title: 'Anonymous-friendly',
    body: 'Customers can submit feedback without identifying themselves. Personal data is not required.',
  },
  {
    icon: '✅',
    title: 'Consent-first',
    body: 'Data collection requires explicit customer consent before any recording or processing begins.',
  },
  {
    icon: '📊',
    title: 'Data minimization',
    body: 'Only data necessary for operational purposes is collected and retained. Dashboard does not expose unnecessary personal details.',
  },
]

const TECH_STACK = [
  { label: 'Frontend', value: 'React' },
  { label: 'Backend', value: 'FastAPI' },
  { label: 'Speech', value: 'Whisper STT' },
  { label: 'Analysis', value: 'Gemini AI' },
  { label: 'Database', value: 'Firebase' },
]

export function WhySentrix() {
  return (
    <section id="why-sentrix" className="section" style={{
      background: 'var(--color-bg)',
    }}>
      <div className="container">

        {/* Positioning */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 'var(--space-16)',
          alignItems: 'start',
          marginBottom: 'var(--space-20)',
        }}
        className="why-grid"
        >
          <div className="reveal">
            <span className="label" style={{ display: 'block', marginBottom: 'var(--space-3)' }}>
              Positioning
            </span>
            <h2 className="heading-1" style={{ marginBottom: 'var(--space-5)' }}>
              Less complexity.
              <br />
              More action at the
              <br />
              point of experience.
            </h2>
            <p className="body-lg">
              Sentrix không cố cạnh tranh bằng số lượng tính năng. Sentrix tập trung vào một bài toán hẹp và giải nó thật tốt: biến phản hồi tại điểm bán thành hành động ngay lập tức.
            </p>
          </div>

          <div className="reveal reveal-delay-2">
            <ComparisonTable />
          </div>
        </div>

        {/* Customer experience */}
        <CustomerSection />

        {/* Trust */}
        <TrustSection />

        {/* Tech */}
        <TechSection techStack={TECH_STACK} />
      </div>

      <style>{`
        @media (max-width: 900px) {
          .why-grid { grid-template-columns: 1fr !important; gap: var(--space-10) !important; }
        }
      `}</style>
    </section>
  )
}

function ComparisonTable() {
  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius-lg)',
      overflow: 'hidden',
      boxShadow: 'var(--shadow-sm)',
    }}>
      {/* Header */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        background: 'var(--color-bg)',
        borderBottom: '1px solid var(--color-border)',
      }}>
        <div style={{ padding: 'var(--space-4) var(--space-5)', borderRight: '1px solid var(--color-border)' }}>
          <p style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Traditional feedback
          </p>
        </div>
        <div style={{ padding: 'var(--space-4) var(--space-5)' }}>
          <p style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--color-primary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Sentrix
          </p>
        </div>
      </div>

      {/* Rows */}
      {[
        ['Collect', 'Listen'],
        ['Store', 'Understand'],
        ['Report', 'Act'],
        ['—', 'Learn'],
      ].map(([left, right], i) => (
        <div key={i} style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          borderBottom: i < 3 ? '1px solid var(--color-border)' : 'none',
        }}>
          <div style={{
            padding: 'var(--space-4) var(--space-5)',
            borderRight: '1px solid var(--color-border)',
            color: left === '—' ? 'var(--color-text-muted)' : 'var(--color-text-secondary)',
            fontSize: 'var(--text-sm)',
          }}>
            {left}
          </div>
          <div style={{
            padding: 'var(--space-4) var(--space-5)',
            fontWeight: 600,
            color: 'var(--color-primary)',
            fontSize: 'var(--text-sm)',
            background: 'var(--color-primary-light)',
          }}>
            {right}
          </div>
        </div>
      ))}

      {/* Footer note */}
      <div style={{
        padding: 'var(--space-4) var(--space-5)',
        background: 'var(--color-primary)',
        textAlign: 'center',
      }}>
        <p style={{ fontSize: 'var(--text-sm)', fontWeight: 700, color: '#fff' }}>
          Sentrix is not another survey form.
        </p>
      </div>
    </div>
  )
}

function CustomerSection() {
  return (
    <div
      className="reveal customer-section-grid"
      style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 'var(--space-10)',
        alignItems: 'center',
        marginBottom: 'var(--space-20)',
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-xl)',
        padding: 'var(--space-10)',
      }}
    >
      <div>
        <span className="label" style={{ display: 'block', marginBottom: 'var(--space-3)' }}>
          Customer experience
        </span>
        <h2 className="heading-2" style={{ marginBottom: 'var(--space-4)' }}>
          For your customers,
          <br />
          it feels simple.
        </h2>
        <p className="body-base" style={{ marginBottom: 'var(--space-6)' }}>
          Khách của bạn không cần học Sentrix. Không cần app. Không cần account. Không form dài.
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          {[
            { step: '1', label: 'Scan', desc: 'Quét QR tại bàn' },
            { step: '2', label: 'Speak or Type', desc: 'Nói hoặc gõ — xong trong 15 giây' },
            { step: '3', label: 'Done', desc: 'Không cần làm thêm gì' },
          ].map(item => (
            <div key={item.step} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <div className="step-number" style={{ width: 32, height: 32, fontSize: 'var(--text-xs)' }}>
                {item.step}
              </div>
              <div>
                <span style={{ fontWeight: 600, fontSize: 'var(--text-sm)', color: 'var(--color-text)' }}>{item.label}</span>
                <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)', marginLeft: 6 }}>— {item.desc}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Phone mockup */}
      <div style={{ display: 'flex', justifyContent: 'center' }}>
        <PhoneMockup />
      </div>

      <style>{`
        @media (max-width: 768px) {
          .customer-section-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  )
}

function PhoneMockup() {
  return (
    <div style={{
      width: 220,
      height: 400,
      background: 'var(--color-text)',
      borderRadius: 32,
      padding: 12,
      boxShadow: 'var(--shadow-xl)',
      position: 'relative',
    }}>
      {/* Notch */}
      <div style={{
        width: 70,
        height: 20,
        background: 'var(--color-text)',
        borderRadius: 10,
        margin: '0 auto 8px',
        position: 'relative',
        zIndex: 2,
      }} />

      {/* Screen */}
      <div style={{
        width: '100%',
        height: 'calc(100% - 32px)',
        background: '#F8FAFB',
        borderRadius: 22,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 16,
        padding: 16,
      }}>
        <img src="/sentrix-logo.png" alt="" style={{ width: 48, height: 48, objectFit: 'contain' }} />
        <p style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: 14, color: 'var(--color-primary)', letterSpacing: '-0.02em' }}>
          SENTRIX
        </p>
        <div style={{
          width: '100%',
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 16,
          padding: 16,
          textAlign: 'center',
        }}>
          <p style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-secondary)', marginBottom: 12 }}>
            Cảm nhận của bạn?
          </p>
          {/* Record button */}
          <div style={{
            width: 60,
            height: 60,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, var(--color-primary), var(--color-accent))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 8px',
            boxShadow: '0 4px 16px rgba(6,136,166,0.4)',
          }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            </svg>
          </div>
          <p style={{ fontSize: 9, color: 'var(--color-text-muted)' }}>Tap to speak · 15 sec</p>
        </div>
        <p style={{ fontSize: 9, color: 'var(--color-text-muted)', textAlign: 'center', lineHeight: 1.4 }}>
          No app · No login · No long form
        </p>
      </div>
    </div>
  )
}

function TrustSection() {
  return (
    <div style={{ marginBottom: 'var(--space-20)' }}>
      <div className="reveal" style={{ marginBottom: 'var(--space-8)' }}>
        <span className="label" style={{ display: 'block', marginBottom: 'var(--space-3)' }}>
          Data & privacy
        </span>
        <h2 className="heading-2" style={{ marginBottom: 'var(--space-4)' }}>
          Designed with data minimization in mind.
        </h2>
        <p className="body-base" style={{ maxWidth: 520 }}>
          Sentrix thu thập chỉ những gì cần thiết — và giữ tối thiểu. Không claim compliance chưa có. Chỉ minh bạch về những gì đang làm.
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: 'var(--space-4)',
      }}
      className="trust-grid"
      >
        {TRUST_POINTS.map((point, i) => (
          <div
            key={point.title}
            className={`reveal reveal-delay-${i + 1}`}
            style={{
              background: 'var(--color-surface)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-5)',
              display: 'flex',
              gap: 'var(--space-4)',
            }}
          >
            <span style={{ fontSize: 24, flexShrink: 0 }}>{point.icon}</span>
            <div>
              <p style={{ fontWeight: 600, fontSize: 'var(--text-sm)', color: 'var(--color-text)', marginBottom: 4 }}>{point.title}</p>
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>{point.body}</p>
            </div>
          </div>
        ))}
      </div>

      <style>{`
        @media (max-width: 640px) {
          .trust-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  )
}

function TechSection({ techStack }) {
  return (
    <div
      className="reveal"
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-8)',
      }}
    >
      <p style={{
        fontSize: 'var(--text-xs)',
        fontWeight: 700,
        textTransform: 'uppercase',
        letterSpacing: '0.08em',
        color: 'var(--color-text-muted)',
        marginBottom: 'var(--space-6)',
      }}>
        Simple experience. Serious infrastructure.
      </p>
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 'var(--space-3)',
      }}>
        {techStack.map(t => (
          <div key={t.label} style={{
            background: 'var(--color-bg)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-3) var(--space-4)',
            display: 'flex',
            flexDirection: 'column',
            gap: 4,
            minWidth: 120,
          }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{t.label}</span>
            <span style={{ fontSize: 'var(--text-sm)', fontWeight: 700, color: 'var(--color-text)' }}>{t.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
