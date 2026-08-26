/**
 * feedback.js — API client cho POST /api/v1/feedback
 *
 * 🟢 ENDPOINT CÓ THẬT — xem docs/api-contract.md mục 2
 *
 * Giai đoạn 7: Cập nhật request fields mới từ backend/api/routes/feedback.py:
 *   customer_phone  (Form, string, optional — hash trong backend trước khi lưu)
 *   total_spending  (Form, float, default 0.0 — chi tiêu lần này tính RFMS M)
 *
 * Response 202 giờ trả thêm:
 *   sentiment_score       float   — điểm cảm xúc tổng hợp (0.0–1.0, backend dùng thang -1~1)
 *   overall_sentiment     string  — "Tích cực" | "Tiêu cực" | "Trung lập"
 *   is_sarcasm_suspected  bool    — AI phát hiện mỉa mai
 *   p_churn               float   — xác suất rời bỏ
 *   churn_risk_level      string  — "low" | "medium" | "high"
 *   should_alert          bool    — có trigger Zalo ZNS không
 *   feedback_id           string  — Firestore document ID
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Gửi phản hồi khách hàng lên backend (Giai đoạn 7 — đầy đủ fields).
 *
 * @param {Object} params
 * @param {string}       params.tenantId       - ID doanh nghiệp từ QR code
 * @param {string}       params.location       - Vị trí quét QR (bàn/khu vực)
 * @param {Blob|null}    params.audioBlob      - File ghi âm (null nếu chỉ dùng text)
 * @param {string|null}  params.textContent    - Văn bản gõ tay (null nếu chỉ audio)
 * @param {string|null}  params.customerPhone  - SĐT khách (optional, backend sẽ hash)
 * @param {number}       params.totalSpending  - Chi tiêu lần này (VND, default 0)
 *
 * @returns {Promise<Object>} Response 202 với đầy đủ AI analysis results
 * @throws {FeedbackError}
 */
export async function submitFeedback({
  tenantId,
  location,
  audioBlob,
  textContent,
  customerPhone = null,
  totalSpending = 0,
  feedbackId = null,
  voucherEligible = false,   // Module 2: false = ẩn danh, true = có SĐT + OTP verified
}) {
  const formData = new FormData()

  // === Fields bắt buộc ===
  formData.append('tenant_id', tenantId)
  formData.append('location', location)

  if (feedbackId) {
    formData.append('feedback_id', feedbackId)
  }

  // === Fields tùy chọn — audio hoặc text (cần ít nhất 1) ===
  if (audioBlob && audioBlob.size > 0) {
    const mimeType = audioBlob.type || 'audio/webm'
    const ext = mimeType.includes('ogg') ? '.ogg'
      : mimeType.includes('mp4') || mimeType.includes('m4a') ? '.m4a'
      : mimeType.includes('mpeg') || mimeType.includes('mp3') ? '.mp3'
      : mimeType.includes('wav') ? '.wav'
      : '.webm'
    formData.append('audio_file', audioBlob, `recording${ext}`)
  }

  if (textContent && textContent.trim().length > 0) {
    formData.append('text_content', textContent.trim())
  }

  // === Fields tùy chọn mới — Giai đoạn 7 (backend/api/routes/feedback.py dòng 224-232) ===
  if (customerPhone && customerPhone.trim().length > 0) {
    // Backend sẽ hash SĐT trước khi lưu — an toàn gửi thô
    formData.append('customer_phone', customerPhone.trim())
  }

  // Module 2: voucher_eligible — backend dùng để biết có áp dụng OTP check không
  // false = ẩn danh → bỏ qua Lớp 1 (OTP/rate-limit), không phát voucher
  // true = đã qua OTP verified ở frontend → backend double-check OTP session
  formData.append('voucher_eligible', String(voucherEligible))

  // total_spending: 0 là mặc định hợp lệ cho backend
  formData.append('total_spending', String(totalSpending))

  let response
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/feedback`, {
      method: 'POST',
      body: formData,
      // KHÔNG set Content-Type — browser tự set multipart/form-data với boundary
    })
  } catch (networkErr) {
    throw new FeedbackError(
      'Không kết nối được tới server. Vui lòng thử lại sau.',
      0,
      'NETWORK_ERROR'
    )
  }

  if (response.ok) {
    return response.json()
  }

  // Xử lý lỗi từ backend
  let errorDetail = 'Lỗi không xác định'
  try {
    const errorBody = await response.json()
    errorDetail = errorBody.detail || errorBody.error || JSON.stringify(errorBody)
  } catch {
    errorDetail = response.statusText
  }

  throw new FeedbackError(
    getFriendlyMessage(response.status, errorDetail),
    response.status,
    errorDetail
  )
}

/**
 * Chuyển lỗi kỹ thuật → thông báo tiếng Việt thân thiện
 */
function getFriendlyMessage(statusCode, rawDetail) {
  switch (statusCode) {
    case 400:
      if (rawDetail && rawDetail.includes('fraud'))
        return 'Phản hồi của bạn có dấu hiệu bất thường. Vui lòng thử lại.'
      if (rawDetail && rawDetail.includes('Thieu noi dung'))
        return 'Vui lòng ghi âm hoặc gõ phản hồi trước khi gửi.'
      if (rawDetail && rawDetail.includes('Dinh dang audio'))
        return 'Định dạng ghi âm không được hỗ trợ. Thử gõ văn bản nhé.'
      return 'Phản hồi không hợp lệ. Vui lòng thử lại.'
    case 413:
      return 'File ghi âm quá lớn (tối đa 5MB ~15 giây). Vui lòng ghi lại ngắn hơn.'
    case 422:
      return 'Dữ liệu gửi lên không đúng định dạng. Vui lòng thử lại.'
    case 503:
      return 'Dịch vụ phân tích giọng nói tạm thời không khả dụng. Thử gõ văn bản nhé!'
    case 504:
      return 'Hệ thống đang bận. Vui lòng thử lại sau ít giây.'
    case 500:
      return 'Lỗi server. Vui lòng thử lại sau.'
    default:
      return 'Đã xảy ra lỗi không mong muốn. Vui lòng thử lại.'
  }
}

/**
 * Custom error class
 */
export class FeedbackError extends Error {
  constructor(friendlyMessage, statusCode, rawDetail) {
    super(friendlyMessage)
    this.name = 'FeedbackError'
    this.statusCode = statusCode
    this.rawDetail = rawDetail
  }
}

/**
 * Health check — GET /health
 */
export async function checkBackendHealth() {
  const response = await fetch(`${API_BASE_URL}/health`)
  if (!response.ok) throw new Error(`Backend health check failed: ${response.status}`)
  return response.json()
}
