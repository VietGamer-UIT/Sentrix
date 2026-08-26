/**
 * consent.js — API client cho POST /api/v1/consent/record
 * =========================================================
 * Module 2 — Tuân thủ Nghị định 356/2025/NĐ-CP
 *
 * Gọi backend để lưu bằng chứng đồng ý xử lý dữ liệu cá nhân.
 * Căn cứ: Điều 6.2 Nghị định 356/2025/NĐ-CP.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Gửi bằng chứng đồng ý lên backend để lưu vào Firestore.
 *
 * @param {Object} params
 * @param {string}       params.tenantId        — ID tenant
 * @param {string}       params.consentVersion  — phiên bản điều khoản (vd "v1.0-356-2025")
 * @param {string}       params.consentGivenAt  — ISO 8601 UTC timestamp
 * @param {string|null}  params.phoneHash       — SHA-256 hex của SĐT (hoặc null nếu ẩn danh)
 * @param {boolean}      params.anonymous       — true nếu user chọn ẩn danh
 *
 * @returns {Promise<{success: boolean, record_id: string, message: string}>}
 * @throws {Error} nếu server trả lỗi HTTP
 */
export async function recordConsent({
  tenantId,
  consentVersion,
  consentGivenAt,
  phoneHash = null,
  anonymous = false,
}) {
  const payload = {
    tenant_id:        tenantId,
    consent_version:  consentVersion,
    consent_given_at: consentGivenAt,
    phone_hash:       phoneHash,
    anonymous:        anonymous,
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/consent/record`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
  } catch (networkErr) {
    throw new Error(`[PDPA] Không kết nối được server để lưu consent: ${networkErr.message}`)
  }

  if (response.ok) {
    return response.json()
  }

  let detail = 'Lỗi server không xác định'
  try {
    const body = await response.json()
    detail = body.detail || JSON.stringify(body)
  } catch { /* ignore */ }

  throw new Error(`[PDPA] Server trả lỗi ${response.status}: ${detail}`)
}
