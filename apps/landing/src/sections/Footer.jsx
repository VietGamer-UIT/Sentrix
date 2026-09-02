/*
  Footer — dark final CTA + minimal footer
  No decorative blobs, no gradient text.
  Clean, editorial, premium.
*/

export function Footer() {
  const go = (e, href) => {
    e.preventDefault()
    document.querySelector(href)?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <>
      {/* Final CTA — dark */}
      <section
        id="cta-cuoi"
        style={{
          background: 'var(--ink)',
          padding: 'var(--s-24) 0',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Subtle teal glow — very restrained */}
        <div aria-hidden="true" style={{
          position: 'absolute',
          width: 480,
          height: 480,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(6,136,166,0.10) 0%, transparent 70%)',
          top: '-20%', right: '-5%',
          pointerEvents: 'none',
        }} />

        <div className="container" style={{ position: 'relative', zIndex: 1, textAlign: 'center' }}>

          <span className="eyebrow reveal" style={{
            display: 'block',
            marginBottom: 'var(--s-6)',
            color: 'var(--teal)',
          }}>
            Bắt đầu ngay hôm nay
          </span>

          <h2
            className="reveal h2 d-1"
            style={{
              color: '#F1F5F9',
              maxWidth: 680,
              margin: '0 auto var(--s-5)',
            }}
          >
            Biết khách đang cần gì, khi bạn vẫn còn kịp xử lý.
          </h2>

          <p
            className="reveal d-2 body-xl"
            style={{
              maxWidth: 440,
              margin: '0 auto var(--s-10)',
              color: 'rgba(241,245,249,0.55)',
            }}
          >
            Bắt đầu với một Pilot nhỏ tại cửa hàng của bạn.
          </p>

          <div
            className="reveal d-3"
            style={{
              display: 'flex',
              justifyContent: 'center',
              gap: 'var(--s-3)',
              flexWrap: 'wrap',
            }}
          >
            <a
              href="#dung-thu"
              id="cta-final-primary"
              className="btn btn-primary-lg"
              onClick={(e) => go(e, '#dung-thu')}
            >
              Đăng ký dùng thử
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
              </svg>
            </a>
            <a
              href="#cach-hoat-dong"
              className="btn btn-ghost-dark"
              onClick={(e) => go(e, '#cach-hoat-dong')}
            >
              Xem cách hoạt động
            </a>
          </div>

          {/* Dashboard hint — blurred preview */}
          <div aria-hidden="true" style={{
            marginTop: 'var(--s-16)',
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: 'var(--r-xl)',
            padding: 'var(--s-5) var(--s-6)',
            maxWidth: 380,
            margin: 'var(--s-16) auto 0',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--s-3)',
            filter: 'blur(2px)',
            opacity: 0.45,
            pointerEvents: 'none',
          }}>
            <p style={{ fontSize: 'var(--t-xs)', fontWeight: 700, color: 'rgba(255,255,255,0.4)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Tổng quan hôm nay
            </p>
            {[
              { label: 'Phản hồi', value: '128', color: 'var(--teal)' },
              { label: 'Cần xử lý', value: '7', color: 'var(--amber)' },
              { label: 'Đã xử lý', value: '6', color: 'var(--green)' },
            ].map(item => (
              <div key={item.label} style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 'var(--t-sm)', color: 'rgba(255,255,255,0.4)' }}>{item.label}</span>
                <span style={{ fontSize: 'var(--t-lg)', fontWeight: 800, color: item.color }}>{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer
        role="contentinfo"
        style={{
          background: 'var(--ink)',
          borderTop: '1px solid rgba(255,255,255,0.06)',
          padding: 'var(--s-8) 0',
        }}
      >
        <div className="container">
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 'var(--s-5)',
          }}>
            {/* Logo + tagline */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                <img src="/sentrix-logo.png" alt="Sentrix" style={{ width: 26, height: 26, objectFit: 'contain' }} />
                <span style={{
                  fontWeight: 800,
                  fontSize: 'var(--t-base)',
                  letterSpacing: '-0.03em',
                  color: 'var(--teal)',
                }}>
                  SENTRIX
                </span>
              </div>
              <p style={{
                fontSize: 'var(--t-xs)',
                color: 'rgba(241,245,249,0.35)',
                maxWidth: 260,
                lineHeight: 1.55,
              }}>
                Giúp cửa hàng nghe khách, hiểu vấn đề và xử lý kịp lúc.
              </p>
            </div>

            {/* Nav */}
            <nav aria-label="Điều hướng footer" style={{ display: 'flex', gap: 'var(--s-6)', flexWrap: 'wrap' }}>
              {[
                { label: 'Sản phẩm', href: '#san-pham' },
                { label: 'Cách hoạt động', href: '#cach-hoat-dong' },
                { label: 'Dùng thử', href: '#dung-thu' },
                { label: 'FAQ', href: '#faq' },
              ].map(l => (
                <a
                  key={l.label}
                  href={l.href}
                  onClick={(e) => go(e, l.href)}
                  style={{
                    fontSize: 'var(--t-sm)',
                    color: 'rgba(241,245,249,0.4)',
                    transition: 'color var(--ease-fast)',
                  }}
                  onMouseEnter={e => { e.target.style.color = 'rgba(241,245,249,0.85)' }}
                  onMouseLeave={e => { e.target.style.color = 'rgba(241,245,249,0.4)' }}
                >
                  {l.label}
                </a>
              ))}
            </nav>

            {/* Copyright */}
            <p style={{ fontSize: 'var(--t-xs)', color: 'rgba(241,245,249,0.25)' }}>
              © {new Date().getFullYear()} Sentrix
            </p>
          </div>
        </div>
      </footer>
    </>
  )
}
