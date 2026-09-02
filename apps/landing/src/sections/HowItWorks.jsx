/*
  Sentrix hoạt động thế nào — 4 bước pipeline thực tế từ thuyết minh AISC'26
  QR Code → Voice/Text → NLP phân tích khía cạnh → Real-time alert → Dashboard xu hướng
*/

const STEPS = [
  {
    n: '01',
    title: 'Khách quét mã',
    body: 'Mỗi bàn có một mã QR riêng. Khách quét, không cần tải app, không cần đăng nhập. Nói vài câu hoặc gõ — xong trong 30 giây.',
    color: 'var(--teal)',
    Icon: () => (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true">
        <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
        <rect x="3" y="14" width="7" height="7"/>
        <path d="M14 14h.01M14 17h.01M17 14h.01M17 17h.01M20 14h.01M20 17h.01M20 20h.01"/>
      </svg>
    ),
  },
  {
    n: '02',
    title: 'AI phân tích',
    body: 'Phản hồi được xử lý tự động — phân loại cảm xúc, xác định khía cạnh (món ăn, phục vụ, thời gian chờ, không gian) và mức độ ưu tiên cần xử lý.',
    color: '#7C3AED',
    Icon: () => (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true">
        <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
      </svg>
    ),
  },
  {
    n: '03',
    title: 'Nhân viên được báo ngay',
    body: 'Nếu có vấn đề cần xử lý, nhân viên nhận thông báo tức thì — trong khi khách vẫn còn tại quán. Đây là cơ hội duy nhất để cứu vãn trải nghiệm.',
    color: '#D97706',
    Icon: () => (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
      </svg>
    ),
  },
  {
    n: '04',
    title: 'Chủ quán thấy xu hướng',
    body: 'Dashboard tổng hợp phản hồi theo ngày, ca, bàn và từng khía cạnh. Vấn đề lặp đi lặp lại hiện rõ — để bạn biết cần cải thiện gì, không phải đoán.',
    color: 'var(--green)',
    Icon: () => (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true">
        <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/>
        <line x1="6" y1="20" x2="6" y2="14"/>
      </svg>
    ),
  },
]

export function HowItWorks() {
  return (
    <section id="cach-hoat-dong" className="section" style={{ background: 'var(--white)' }}>
      <div className="container">

        {/* Heading */}
        <div className="reveal" style={{ marginBottom: 'var(--s-16)' }}>
          <span className="eyebrow" style={{ display: 'block', marginBottom: 'var(--s-4)' }}>
            Cách hoạt động
          </span>
          <h2 className="h3" style={{ color: 'var(--grey-900)', maxWidth: 560 }}>
            Từ phản hồi đến hành động —<br />trong vòng vài giây.
          </h2>
          <p style={{ fontSize: 'var(--t-base)', color: 'var(--grey-400)', maxWidth: 520, marginTop: 'var(--s-4)', lineHeight: 1.7 }}>
            Không cần nhân viên nhắc khách điền form. Không cần chủ quán tổng hợp thủ công.<br />
            Toàn bộ pipeline diễn ra tự động.
          </p>
        </div>

        {/* Steps */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 'var(--s-5)',
        }} className="steps-grid">

          {STEPS.map((step, i) => (
            <div
              key={step.n}
              className={`reveal d-${i + 1}`}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--s-4)',
                padding: 'var(--s-6)',
                borderLeft: `2px solid ${step.color}`,
                position: 'relative',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--s-3)' }}>
                <span style={{
                  fontSize: 'var(--t-xs)',
                  fontWeight: 700,
                  letterSpacing: '0.1em',
                  color: 'var(--grey-300)',
                }}>
                  {step.n}
                </span>
                <div style={{ color: step.color }}>
                  <step.Icon />
                </div>
              </div>

              <h3 style={{
                fontSize: 'var(--t-xl)',
                fontWeight: 700,
                color: 'var(--grey-900)',
                letterSpacing: '-0.015em',
              }}>
                {step.title}
              </h3>

              <p style={{
                fontSize: 'var(--t-sm)',
                color: 'var(--grey-400)',
                lineHeight: 1.7,
              }}>
                {step.body}
              </p>
            </div>
          ))}
        </div>

        {/* Real-scenario flow example */}
        <div className="reveal" style={{
          marginTop: 'var(--s-16)',
          background: 'var(--off-white)',
          border: '1px solid var(--grey-100)',
          borderRadius: 'var(--r-xl)',
          padding: 'var(--s-8)',
        }}>
          <p style={{
            fontSize: 'var(--t-xs)',
            fontWeight: 600,
            color: 'var(--grey-300)',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            marginBottom: 'var(--s-6)',
          }}>
            Ví dụ thực tế — một câu phản hồi trở thành hành động
          </p>

          <div style={{
            display: 'grid',
            gridTemplateColumns: '1fr auto 1fr auto 1fr auto 1fr',
            gap: 'var(--s-3)',
            alignItems: 'center',
            overflowX: 'auto',
          }} className="flow-grid">
            <FlowBox label="Khách nói (Bàn 08)" content={'"Chờ lâu quá, hơi thất vọng."'} italic />
            <Arrow />
            <FlowBox label="AI phân tích" content={<>
              <span style={{ color: 'var(--red)', fontWeight: 600 }}>Tốc độ phục vụ — Tiêu cực</span>
              <br/>
              <span style={{ color: 'var(--grey-400)', fontSize: '0.85em' }}>Mức độ: Cần xử lý ngay</span>
            </>} />
            <Arrow />
            <FlowBox label="Nhân viên nhận" content="🔔 Bàn 08 — Tốc độ phục vụ. Khách đang chờ." bold />
            <Arrow />
            <FlowBox label="Chủ quán thấy" content='"Tốc độ phục vụ" xuất hiện 14 lần trong tuần này — ca chiều tệ hơn.' />
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 900px) {
          .steps-grid { grid-template-columns: repeat(2, 1fr) !important; }
          .flow-grid { grid-template-columns: 1fr !important; }
          .flow-grid > div[aria-hidden] { display: none; }
        }
        @media (max-width: 540px) {
          .steps-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </section>
  )
}

function FlowBox({ label, content, italic, bold }) {
  return (
    <div style={{
      background: 'var(--white)',
      border: '1px solid var(--grey-100)',
      borderRadius: 'var(--r-md)',
      padding: 'var(--s-4)',
      minWidth: 140,
    }}>
      <p style={{
        fontSize: 'var(--t-xs)',
        fontWeight: 600,
        color: 'var(--teal)',
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
        marginBottom: 'var(--s-2)',
      }}>{label}</p>
      <p style={{
        fontSize: 'var(--t-sm)',
        color: 'var(--grey-600)',
        lineHeight: 1.55,
        fontStyle: italic ? 'italic' : 'normal',
        fontWeight: bold ? 600 : 400,
      }}>{content}</p>
    </div>
  )
}

function Arrow() {
  return (
    <div aria-hidden="true" style={{ color: 'var(--grey-200)', display: 'flex', alignItems: 'center' }}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="9 18 15 12 9 6"/>
      </svg>
    </div>
  )
}
