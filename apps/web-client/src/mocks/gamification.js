/**
 * MOCK DATA — Gamification (Vòng quay may mắn)
 *
 * ⚠️ MOCK — Thay bằng API thật khi Tuyền implement:
 *   POST /api/gamification/spin
 *   Request: { tenant_id, customer_phone, feedback_id }
 *   Response: { prize, voucher_code, message }
 *   Xem docs/api-contract.md mục 4 để biết format thật.
 *
 * Điều kiện để bỏ mock:
 * 1. Tuyền báo endpoint đã live trên Render
 * 2. Việt cập nhật docs/api-contract.md từ 🔴 sang 🟢
 * 3. Đổi VITE_USE_MOCK_GAMIFICATION=false trong .env
 */

export const SPIN_PRIZES = [
  {
    id: 'giam_10',
    label: 'Giảm 10%',
    color: '#00C2FF',
    probability: 0.35,
    voucherTemplate: (phone) => `SENTRIX-10-${phone.slice(-4).toUpperCase()}`
  },
  {
    id: 'giam_20',
    label: 'Giảm 20%',
    color: '#7C3AED',
    probability: 0.20,
    voucherTemplate: (phone) => `SENTRIX-20-${phone.slice(-4).toUpperCase()}`
  },
  {
    id: 'tang_banh',
    label: 'Tặng bánh',
    color: '#F59E0B',
    probability: 0.15,
    voucherTemplate: (phone) => `SENTRIX-BANH-${phone.slice(-4).toUpperCase()}`
  },
  {
    id: 'giam_5',
    label: 'Giảm 5%',
    color: '#10B981',
    probability: 0.20,
    voucherTemplate: (phone) => `SENTRIX-5-${phone.slice(-4).toUpperCase()}`
  },
  {
    id: 'uong_mien_phi',
    label: 'Voucher\nuống', // Hiện trên wheel: 2 dòng
    prizeLabel: 'Voucher uống miễn phí lần sau',
    color: '#EF4444',
    probability: 0.05,
    voucherTemplate: (phone) => `SENTRIX-FREE-${phone.slice(-4).toUpperCase()}`
  },
  {
    id: 'chuc_may_man',
    label: 'Chúc may mắn',
    color: '#6B7280',
    probability: 0.05,
    voucherTemplate: () => null // Không có voucher
  }
]

/**
 * Giả lập spin API — trả về prize ngẫu nhiên theo xác suất
 * Delay 2.5s để giả lập network latency
 */
export function mockSpinAPI(tenantId, customerPhone) {
  return new Promise((resolve) => {
    setTimeout(() => {
      // Chọn prize theo xác suất
      const rand = Math.random()
      let cumulative = 0
      let selectedPrize = SPIN_PRIZES[SPIN_PRIZES.length - 1] // fallback

      for (const prize of SPIN_PRIZES) {
        cumulative += prize.probability
        if (rand < cumulative) {
          selectedPrize = prize
          break
        }
      }

      const voucherCode = selectedPrize.voucherTemplate(customerPhone || '0000')
      resolve({
        prize: selectedPrize.id,
        prize_label: selectedPrize.label,
        voucher_code: voucherCode,
        message: voucherCode
          ? `Chúc mừng bạn nhận được: ${selectedPrize.label}!`
          : 'Cảm ơn bạn đã tham gia! Chúc bạn may mắn lần sau.'
      })
    }, 2500)
  })
}
