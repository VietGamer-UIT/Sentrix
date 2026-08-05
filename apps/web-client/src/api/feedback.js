/**
 * feedback.js — API client cho POST /api/v1/feedback
 *
 * 🟢 ENDPOINT CÓ THẬT — xem docs/api-contract.md mục 2
 *
 * Field names KHỚP CHÍNH XÁC với backend/api/routes/feedback.py:
 *   tenant_id    (Form, string, required)
 *   location     (Form, string, required, max 100 ký tự)
 *   audio_file   (File, optional — WebM/MP3/WAV/OGG, max 5MB)
 *   text_content (Form, optional — max 2000 ký tự)
 *
 * ⚠️ KHÔNG đổi tên bất kỳ field nào — sẽ gây lỗi 422 validation từ FastAPI
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Gửi phản hồi khách hàng lên backend.
 *
 * @param {Object} params
 * @param {string}   params.tenantId    - ID doanh nghiệp từ QR code
 * @param {string}   params.location    - Vị trí quét QR (bàn/khu vực)
 * @param {Blob|null} params.audioBlob  - File ghi âm từ MediaRecorder (null nếu chỉ dùng text)
 * @param {string|null} params.textContent - Văn bản gõ tay (null nếu chỉ dùng audio)
 * @returns {Promise<Object>} Response 202: { request_id, status, transcript, is_suspicious, ... }
 * @throws {FeedbackError} khi backend trả lỗi
 */
export async function submitFeedback({ tenantId, location, audioBlob, textContent }) {
  const formData = new FormData()

  // === Fields bắt buộc ===
  // Tên field PHẢI khớp tuyệt đối với backend/api/routes/feedback.py dòng 163-183
  formData.append('tenant_id', tenantId)
  formData.append('location', location)

  // === Fields tùy chọn (ít nhất 1 trong 2 phải có) ===
  if (audioBlob && audioBlob.size > 0) {
    // Detect đúng extension từ MIME type của blob
    const mimeType = audioBlob.type || 'audio/webm'
    const ext = mimeType.includes('ogg') ? '.ogg'
      : mimeType.includes('mp4') || mimeType.includes('m4a') ? '.m4a'
      : mimeType.includes('mpeg') || mimeType.includes('mp3') ? '.mp3'
      : mimeType.includes('wav') ? '.wav'
      : '.webm' // default — Chrome/Firefox
    formData.append('audio_file', audioBlob, `recording${ext}`)
  }

  if (textContent && textContent.trim().length > 0) {
    formData.append('text_content', textContent.trim())
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/feedback`, {
      method: 'POST',
      body: formData,
      // KHÔNG set Content-Type — browser tự set multipart/form-data với boundary
    })
  } catch (networkErr) {
    // Lỗi mạng (backend không chạy, CORS block, v.v.)
    throw new FeedbackError(
      'Không kết nối được tới server. Vui lòng thử lại sau.',
      0,
      'NETWORK_ERROR'
    )
  }

  if (response.ok) {
    // 202 Accepted — thành công
    return response.json()
  }

  // Xử lý các mã lỗi từ backend/api/routes/feedback.py
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
 * Chuyển lỗi kỹ thuật → thông báo tiếng Việt thân thiện cho user
 * Danh sách mã lỗi từ backend/api/routes/feedback.py + docs/api-contract.md
 */
function getFriendlyMessage(statusCode, rawDetail) {
  switch (statusCode) {
    case 400:
      if (rawDetail && rawDetail.includes('fraud')) {
        return 'Phản hồi của bạn có dấu hiệu bất thường. Vui lòng thử lại.'
      }
      if (rawDetail && rawDetail.includes('Thiếu nội dung')) {
        return 'Vui lòng ghi âm hoặc gõ phản hồi trước khi gửi.'
      }
      if (rawDetail && rawDetail.includes('Định dạng audio')) {
        return 'Định dạng ghi âm không được hỗ trợ. Thử gõ văn bản nhé.'
      }
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
 * Custom error class cho feedback API
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
 * Kiểm tra backend có đang chạy không — dùng để debug local
 * Gọi GET /health (🟢 endpoint cam kết — docs/api-contract.md mục 1)
 *
 * @returns {Promise<{status: string, version: string, message: string}>}
 */
export async function checkBackendHealth() {
  const response = await fetch(`${API_BASE_URL}/health`)
  if (!response.ok) throw new Error(`Backend health check failed: ${response.status}`)
  return response.json()
}
