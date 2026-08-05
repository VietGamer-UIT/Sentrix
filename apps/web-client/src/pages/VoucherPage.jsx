import { useSearchParams } from 'react-router-dom'

/**
 * VoucherPage — Bước 6 trong user-flow.md
 *
 * UX Requirements (từ user-flow.md):
 * - Hiển thị rõ mã voucher (để khách chụp màn hình)
 * - Nút "Mở Zalo kiểm tra ngay"
 * - Rủi ro: không biết cách nhận hay dùng voucher → hiện hướng dẫn rõ
 *
 * TODO: Link Zalo ZNS thật (deep link Zalo với OA ID) khi team có tài khoản Zalo OA
 */
function VoucherPage() {
  const [searchParams] = useSearchParams()

  const prizeLabel = searchParams.get('prize_label') || 'Giảm 10%'
  const voucherCode = searchParams.get('voucher_code') || ''
  const message = searchParams.get('message') || ''
  const skipped = searchParams.get('skipped') === 'true'

  const hasVoucher = voucherCode && voucherCode.length > 0

  // TODO: Thay bằng Zalo OA deep link thật khi có ZNS account
  const zaloLink = `https://zalo.me` // Placeholder — ghi TODO

  return (
    <div className="page">
      <div className="bg-glow bg-glow--primary" />
      <div className="bg-glow bg-glow--accent" />

      <div className="page-content" style={{ textAlign: 'center' }}>

        {skipped ? (
          /* Bỏ qua vòng quay */
          <>
            <div className="fade-up" style={{ fontSize: 64 }}>🙏</div>
            <h1 className="fade-up fade-up--delay-1" style={{ fontSize: 'var(--font-size-2xl)' }}>
              Cảm ơn bạn!
            </h1>
            <p className="fade-up fade-up--delay-2">
              Hẹn gặp lại bạn tại {' '}
              <strong style={{ color: 'var(--color-primary)' }}>Phở Bà Lan</strong> nhé! 🍜
            </p>
          </>
        ) : (
          /* Có voucher */
          <>
            <div className="fade-up" style={{ fontSize: 64 }}>🎊</div>

            <div className="fade-up fade-up--delay-1">
              <h1 style={{ fontSize: 'var(--font-size-2xl)', marginBottom: 8 }}>
                Chúc mừng bạn!
              </h1>
              <p style={{ fontSize: 'var(--font-size-lg)', color: 'var(--color-primary)', fontWeight: 700 }}>
                {prizeLabel}
              </p>
            </div>

            {hasVoucher && (
              <div className="voucher-card fade-up fade-up--delay-2" style={{ width: '100%' }}>
                <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
                  Mã voucher của bạn
                </p>
                <div className="voucher-code" id="voucher-code-display">
                  {voucherCode}
                </div>
                <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                  Chụp màn hình để lưu · Đưa cho nhân viên khi thanh toán
                </p>
              </div>
            )}

            {!hasVoucher && (
              <div className="card fade-up fade-up--delay-2">
                <p>{message}</p>
              </div>
            )}

            <div className="fade-up fade-up--delay-3" style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
              {/* TODO: Thay href bằng Zalo OA deep link thật */}
              <a
                id="btn-open-zalo"
                href={zaloLink}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn--primary"
                style={{ textDecoration: 'none' }}
              >
                💬 Mở Zalo kiểm tra
              </a>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                Voucher cũng đã được gửi vào Zalo của bạn
              </p>
            </div>
          </>
        )}

        {/* Footer */}
        <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: 'var(--spacing-lg)' }}
           className="fade-up">
          Powered by{' '}
          <span style={{ color: 'var(--color-primary)', fontWeight: 700 }}>Sentrix</span>
        </p>
      </div>
    </div>
  )
}

export default VoucherPage
