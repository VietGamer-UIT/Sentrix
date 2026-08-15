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

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Gọi spin API — nhận prize, voucher và backend tự cập nhật feedback
 */
export async function submitSpinAPI(tenantId, customerPhone, feedbackId) {
  const formData = new FormData()
  formData.append('tenant_id', tenantId)
  formData.append('customer_phone', customerPhone)
  if (feedbackId) {
    formData.append('feedback_id', feedbackId)
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/gamification/spin`, {
      method: 'POST',
      body: formData,
    })
  } catch (networkErr) {
    throw new Error('Không kết nối được tới server. Vui lòng thử lại sau.')
  }

  if (response.ok) {
    return response.json()
  }

  let detail = ''
  try {
    const errObj = await response.json()
    detail = errObj.detail ? JSON.stringify(errObj.detail) : JSON.stringify(errObj)
  } catch {
    detail = response.statusText
  }

  console.error('[Gamification API Error]', response.status, detail)
  throw new Error(`Lỗi từ server khi quay thưởng (${response.status}: ${detail})`)
}
