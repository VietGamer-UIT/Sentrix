/**
 * SectionHeading.jsx — Consistent section header block
 * label → heading → subheading with optional divider
 */
export function SectionHeading({
  label,
  heading,
  subheading,
  align = 'left',
  dark = false,
  maxWidth,
  className = ''
}) {
  const textAlign = align === 'center' ? 'center' : 'left'
  const alignItems = align === 'center' ? 'center' : 'flex-start'

  return (
    <div
      className={`section-heading reveal ${className}`}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems,
        textAlign,
        maxWidth: maxWidth || 'none'
      }}
    >
      {label && (
        <span className="label" style={{ marginBottom: 'var(--space-3)' }}>
          {label}
        </span>
      )}
      <h2
        className="heading-1"
        style={{
          color: dark ? 'var(--color-text-dark)' : 'var(--color-text)',
          marginBottom: subheading ? 'var(--space-4)' : 0
        }}
      >
        {heading}
      </h2>
      {subheading && (
        <p
          className="body-lg"
          style={{
            color: dark ? 'var(--color-text-dark-2)' : 'var(--color-text-secondary)',
            maxWidth: '580px'
          }}
        >
          {subheading}
        </p>
      )}
    </div>
  )
}
