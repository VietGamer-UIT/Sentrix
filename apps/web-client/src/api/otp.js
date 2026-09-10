/**
 * otp.js — API client cho OTP endpoints
 *
 * POST /api/v1/otp/send   — Gửi mã OTP đến SĐT hoặc Email
 * POST /api/v1/otp/verify — Xác thực mã OTP
 *
 * Hỗ trợ cả 2 loại contact:
 *   - SĐT: 0901234567 → gửi qua Zalo/SMS (hoặc mock)
 *   - Email: user@gmail.com → gửi qua Gmail SMTP (miễn phí)
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Gửi mã OTP đến SĐT hoặc Email
 * @param {string} contact - SĐT (0901...) hoặc Email (user@gmail.com)
 * @param {string} tenantId
 * @returns {Promise<{success: boolean, message: string, contact_type: string}>}
 */
export async function sendOtp(contact, tenantId) {
  const res = await fetch(`${API_BASE_URL}/api/v1/otp/send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ contact, tenant_id: tenantId }),
  })
  const data = await res.json()
  if (!res.ok) {
    throw new Error(data.detail || 'Không thể gửi mã OTP. Vui lòng thử lại.')
  }
  return data
}

/**
 * Xác thực mã OTP
 * @param {string} contact - SĐT hoặc Email (phải khớp với lúc gửi)
 * @param {string} otpCode - Mã 6 chữ số
 * @param {string} tenantId
 * @returns {Promise<{success: boolean, otp_verified: boolean, message: string}>}
 */
export async function verifyOtp(contact, otpCode, tenantId) {
  const res = await fetch(`${API_BASE_URL}/api/v1/otp/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ contact, otp_code: otpCode, tenant_id: tenantId }),
  })
  const data = await res.json()
  if (!res.ok) {
    throw new Error(data.detail || 'Mã OTP không đúng hoặc đã hết hạn.')
  }
  return data
}
