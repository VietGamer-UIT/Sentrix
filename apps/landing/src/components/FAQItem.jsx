import { useState } from 'react'

/**
 * FAQItem — accessible accordion
 * Uses new CSS system (--grey-*, --teal, --r-md)
 */
export function FAQItem({ index, question, answer }) {
  const [open, setOpen] = useState(false)

  return (
    <div style={{
      borderBottom: '1px solid var(--grey-100)',
    }}>
      <button
        id={`faq-btn-${index}`}
        type="button"
        aria-expanded={open}
        aria-controls={`faq-panel-${index}`}
        onClick={() => setOpen(!open)}
        style={{
          width: '100%',
          background: 'none',
          border: 'none',
          padding: 'var(--s-5) 0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 'var(--s-4)',
          cursor: 'pointer',
          textAlign: 'left',
        }}
      >
        <span style={{
          fontSize: 'var(--t-base)',
          fontWeight: 600,
          color: 'var(--grey-900)',
          lineHeight: 1.5,
        }}>
          {question}
        </span>
        <span style={{
          flexShrink: 0,
          color: open ? 'var(--teal)' : 'var(--grey-300)',
          transform: open ? 'rotate(45deg)' : 'none',
          transition: 'transform 0.25s ease, color 0.2s ease',
        }} aria-hidden="true">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
        </span>
      </button>

      <div
        id={`faq-panel-${index}`}
        role="region"
        aria-labelledby={`faq-btn-${index}`}
        hidden={!open}
        style={{
          paddingBottom: 'var(--s-5)',
          animation: 'fadeIn 0.2s ease',
        }}
      >
        <p style={{
          fontSize: 'var(--t-base)',
          color: 'var(--grey-500)',
          lineHeight: 1.75,
        }}>
          {answer}
        </p>
      </div>
    </div>
  )
}
