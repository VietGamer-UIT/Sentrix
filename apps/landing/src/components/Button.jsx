/**
 * Button.jsx — Reusable button component
 * Variants: primary | primary-lg | ghost | outline-light
 */
export function Button({
  children,
  variant = 'primary',
  href,
  onClick,
  type = 'button',
  disabled = false,
  className = '',
  ...props
}) {
  const cls = `btn btn-${variant} ${className}`.trim()

  if (href) {
    return (
      <a href={href} className={cls} {...props}>
        {children}
      </a>
    )
  }

  return (
    <button
      type={type}
      className={cls}
      onClick={onClick}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  )
}
