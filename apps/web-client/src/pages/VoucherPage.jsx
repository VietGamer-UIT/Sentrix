import { useSearchParams } from 'react-router-dom'

/**
 * VoucherPage — Bước 6 trong user-flow.md
 *
 * UX Requirements:
 * - Hiển thị rõ mã voucher (to, nổi bật — để khách chụp màn hình)
 * - Nút "Mở Zalo kiểm tra ngay" — hành động chính
 * - Hiện hướng dẫn sử dụng rõ ràng
 * - Xử lý cả 3 trường hợp:
 *   (a) Có voucher thật (giảm %, tặng bánh...)
 *   (b) Trúng "Chúc may mắn" (không có voucher code)
 *   (c) Bỏ qua vòng quay
 *
 * Rủi ro (user-flow.md): Không biết cách nhận hay cách dùng voucher
 * Giải pháp: Hướng dẫn 3 bước ngắn + nút Mở Zalo nổi bật
 *
 * TODO: Thay href zaloLink bằng Zalo OA deep link thật khi có ZNS account
 *       Format: https://zalo.me/oa/{OA_ID}?msg=...
 */
function VoucherPage() {
  const [searchParams] = useSearchParams()

  const prizeLabel = searchParams.get('prize_label') || ''
  const voucherCode = searchParams.get('voucher_code') || ''
  const message = searchParams.get('message') || ''
  const skipped = searchParams.get('skipped') === 'true'
  const prizeId = searchParams.get('prize')

  const hasVoucher = voucherCode.length > 0
  const isConsolationPrize = prizeId === 'chuc_may_man'

  // TODO: Thay bằng Zalo OA deep link thật khi team có tài khoản Zalo OA
  // Format đúng: https://zalo.me/oa/{OA_ID}
  const zaloLink = 'https://zalo.me' // Placeholder

  // Emoji theo loại prize
  const getPrizeEmoji = () => {
    if (!prizeLabel) return '🎊'
    if (prizeLabel.includes('miễn phí')) return '🆓'
    if (prizeLabel.includes('bánh')) return '🎂'
    if (prizeLabel.includes('%')) return '💸'
    return '🎁'
  }

  return (
    <div className="page">
      <div className="bg-glow bg-glow--primary"/>
      <div className="bg-glow bg-glow--accent"/>

      <div className="page-content" style={{ textAlign: 'center' }}>

        {/* === TRƯỜNG HỢP: BỎ QUA === */}
        {skipped && (
          <>
            <div className="fade-up" style={{ fontSize: 72 }}>🙏</div>
            <div className="fade-up fade-up--delay-1">
              <h1 style={{ fontSize: 'var(--font-size-2xl)', marginBottom: 'var(--spacing-sm)' }}>
                Cảm ơn bạn!
              </h1>
              <p style={{ lineHeight: 1.7 }}>
                Hẹn gặp lại bạn tại{' '}
                <strong style={{ color: 'var(--color-primary)' }}>Phở Bà Lan</strong>{' '}
                lần sau nhé! 🍜
              </p>
            </div>
          </>
        )}

        {/* === TRƯỜNG HỢP: CHÚC MAY MẮN (không có voucher) === */}
        {!skipped && isConsolationPrize && (
          <>
            <div className="fade-up" style={{ fontSize: 72 }}>🍀</div>
            <div className="card fade-up fade-up--delay-1" style={{ width: '100%' }}>
              <h1 style={{ fontSize: 'var(--font-size-xl)', marginBottom: 'var(--spacing-sm)' }}>
                Cảm ơn bạn đã tham gia!
              </h1>
              <p style={{ lineHeight: 1.7 }}>
                {message || 'Lần này chưa trúng thưởng, nhưng cảm ơn vì đã chia sẻ. Hẹn gặp lại! 💪'}
              </p>
            </div>
          </>
        )}

        {/* === TRƯỜNG HỢP: CÓ VOUCHER === */}
        {!skipped && !isConsolationPrize && hasVoucher && (
          <>
            {/* Confetti emoji */}
            <div className="fade-up" style={{ fontSize: 64 }}>
              {getPrizeEmoji()}
            </div>

            {/* Tiêu đề */}
            <div className="fade-up fade-up--delay-1">
              <h1 style={{ fontSize: 'var(--font-size-2xl)', marginBottom: 6 }}>
                Chúc mừng!
              </h1>
              <p style={{
                fontSize: 'var(--font-size-lg)',
                fontWeight: 700,
                color: 'var(--color-primary)'
              }}>
                Bạn nhận được: {prizeLabel}
              </p>
            </div>

            {/* Voucher Card — to, nổi bật để chụp màn hình */}
            <div className="voucher-card fade-up fade-up--delay-2" style={{ width: '100%' }}>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginBottom: 4 }}>
                MÃ VOUCHER CỦA BẠN
              </p>
              <div className="voucher-code" id="voucher-code-display">
                {voucherCode}
              </div>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
                📸 Chụp màn hình để lưu lại
                <br />
                Đưa cho nhân viên khi thanh toán lần sau
              </p>
            </div>

            {/* Nút CTA chính — Mở Zalo */}
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
                💬 Mở Zalo kiểm tra ngay
              </a>
              <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                Voucher cũng đã được gửi vào Zalo của bạn
              </p>
            </div>

            {/* Hướng dẫn sử dụng */}
            <div className="card fade-up" style={{
              width: '100%',
              background: 'rgba(0,194,255,0.05)',
              border: '1px solid rgba(0,194,255,0.15)'
            }}>
              <p style={{ fontSize: 'var(--font-size-sm)', fontWeight: 700, marginBottom: 'var(--spacing-sm)', textAlign: 'left' }}>
                📋 Cách sử dụng voucher:
              </p>
              <ol style={{
                fontSize: 'var(--font-size-xs)',
                color: 'var(--color-text-secondary)',
                lineHeight: 2,
                paddingLeft: 'var(--spacing-md)',
                textAlign: 'left'
              }}>
                <li>Chụp màn hình hoặc kiểm tra Zalo để lưu mã</li>
                <li>Đến quán lần sau, đưa mã cho nhân viên khi tính tiền</li>
                <li>Nhân viên sẽ áp dụng ưu đãi cho bạn ngay lập tức</li>
              </ol>
            </div>
          </>
        )}

        {/* Footer Sentrix */}
        <p className="fade-up" style={{
          fontSize: 'var(--font-size-xs)',
          color: 'var(--color-text-muted)',
          marginTop: 'var(--spacing-md)'
        }}>
          Powered by{' '}
          <span style={{ color: 'var(--color-primary)', fontWeight: 700 }}>Sentrix</span>
          {' '}· AI Customer Experience
        </p>

      </div>
    </div>
  )
}

export default VoucherPage
