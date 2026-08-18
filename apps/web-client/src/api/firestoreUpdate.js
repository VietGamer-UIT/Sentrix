/**
 * firestoreUpdate.js — Cập nhật Firestore trực tiếp từ web-client
 *
 * Dùng để patch feedback document sau khi khách:
 *   1. Nhập SĐT ở SpinPage
 *   2. Quay và trúng voucher
 *
 * Tại sao cần file này:
 *   - POST /api/gamification/spin chưa có trên backend (Tuyền chưa implement)
 *   - Cần lưu phone_masked + voucher_code vào Firestore để Dashboard thấy
 *
 * Fields được cập nhật trên feedback document (theo schema.md):
 *   phone_masked     string    — SĐT ẩn danh hóa (ví dụ "090****567")
 *   voucher_code     string    — Mã voucher trúng (ví dụ "SENTRIX-20-5678")
 *   spin_prize       string    — ID phần thưởng (ví dụ "giam_20")
 *   spin_prize_label string    — Nhãn hiển thị (ví dụ "Giảm 20%")
 *   spin_at          timestamp — Thời điểm quay
 */

import { doc, updateDoc, serverTimestamp } from 'firebase/firestore'
import { db } from '../firebase.js'

/**
 * Mask số điện thoại: "0901234567" → "090****567"
 * @param {string} phone
 * @returns {string}
 */
function maskPhone(phone) {
  const digits = phone.replace(/\D/g, '')
  if (digits.length < 7) return digits
  const prefix = digits.slice(0, 3)
  const suffix = digits.slice(-3)
  const stars  = '*'.repeat(Math.max(digits.length - 6, 4))
  return `${prefix}${stars}${suffix}`
}

/**
 * Cập nhật feedback document với thông tin spin (SĐT + voucher).
 *
 * @param {Object} params
 * @param {string}      params.tenantId     — ID tenant (từ QR code)
 * @param {string}      params.feedbackId   — ID document Firestore (từ sessionStorage)
 * @param {string}      params.phone        — SĐT gốc của khách (sẽ được mask)
 * @param {string}      params.prize        — Prize ID, ví dụ "giam_20"
 * @param {string}      params.prizeLabel   — Prize label, ví dụ "Giảm 20%"
 * @param {string|null} params.voucherCode  — Voucher code, null nếu không trúng
 * @returns {Promise<boolean>} true nếu update thành công
 */
export async function updateFeedbackWithSpin({
  tenantId,
  feedbackId,
  phone,
  prize,
  prizeLabel,
  voucherCode,
}) {
  if (!db) {
    console.warn('[Sentrix] Firestore chưa khởi tạo (thiếu env vars) — bỏ qua update spin')
    return false
  }
  if (!tenantId || !feedbackId) {
    console.warn('[Sentrix] updateFeedbackWithSpin: thiếu tenantId hoặc feedbackId — bỏ qua')
    return false
  }

  const updateData = {
    phone_masked:     maskPhone(phone),
    spin_prize:       prize,
    spin_prize_label: prizeLabel,
    spin_at:          serverTimestamp(),
  }

  if (voucherCode) {
    updateData.voucher_code = voucherCode
  }

  try {
    const feedbackRef = doc(db, `tenants/${tenantId}/feedbacks/${feedbackId}`)
    await updateDoc(feedbackRef, updateData)
    console.info(`[Sentrix] Đã lưu spin data vào feedback ${feedbackId}:`, updateData)
    return true
  } catch (err) {
    // Không crash app — chỉ log. Có thể do Security Rules chưa cho phép.
    console.error('[Sentrix] updateFeedbackWithSpin thất bại (Firestore rules?):', err.message)
    return false
  }
}
