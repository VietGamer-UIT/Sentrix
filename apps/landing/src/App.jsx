import { useScrollReveal } from './hooks/useScrollReveal'
import { Navbar }      from './sections/Navbar'
import { Hero }        from './sections/Hero'
import { Problem }     from './sections/Problem'
import { HowItWorks }  from './sections/HowItWorks'
import { ProductDemo } from './sections/ProductDemo'
import { ForOwners }   from './sections/ForOwners'
import { Pilot }       from './sections/Pilot'
import { FAQ }         from './sections/FAQ'
import { Footer }      from './sections/Footer'

/**
 * App — Sentrix Landing Page v2
 *
 * Scroll narrative:
 *  1. Navbar        — sticky, transparent → frosted glass
 *  2. Hero          — single phone visual, 5-stage pipeline animation
 *  3. Problem       — narrative story, star morphing
 *  4. HowItWorks    — 4 steps + flow example
 *  5. ProductDemo   — 4-tab cinematic WOW demo
 *  6. ForOwners     — dashboard, customer flow, before/after, positioning
 *  7. Pilot         — conversion: steps + validated form
 *  8. FAQ           — 7 natural Vietnamese questions
 *  9. Footer        — dark final CTA + minimal footer
 */
export default function App() {
  useScrollReveal()

  return (
    <>
      <Navbar />

      <main id="main-content">
        <Hero />
        <Problem />
        <HowItWorks />
        <ProductDemo />
        <ForOwners />
        <Pilot />
        <FAQ />
      </main>

      <Footer />

      <MobileStickyPill />
    </>
  )
}

/**
 * MobileStickyPill — small CTA fixed to bottom on mobile.
 * Only visible on screens ≤ 768px.
 */
function MobileStickyPill() {
  return (
    <>
      <div id="mobile-cta" style={{
        position: 'fixed',
        bottom: 'var(--s-5)',
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 90,
        display: 'none',
        pointerEvents: 'auto',
      }}>
        <a
          href="#dung-thu"
          onClick={(e) => { e.preventDefault(); document.querySelector('#dung-thu')?.scrollIntoView({ behavior: 'smooth' }) }}
          className="btn btn-primary"
          style={{
            boxShadow: '0 6px 24px rgba(6,136,166,0.4)',
            padding: '13px 28px',
          }}
        >
          Đăng ký dùng thử
        </a>
      </div>

      <style>{`
        @media (max-width: 768px) {
          #mobile-cta { display: flex !important; }
        }
      `}</style>
    </>
  )
}
