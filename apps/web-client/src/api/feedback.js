/**
 * feedback.js — Hàm gọi API POST /api/v1/feedback
 *
 * 🟢 API này CÓ THẬT — xem docs/api-contract.md mục 2
 * Format: multipart/form-data
 * Fields: tenant_id (string), location (string), audio_file? (file), text_content? (string)
 *
 * Lưu ý: Field names phải khớp CHÍNH XÁC với backend/api/routes/feedback.py
 * KHÔNG được đổi tên field dù chỉ 1 ký tự — sẽ gây lỗi 422 validation
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Gửi phản hồi khách hàng lên backend
 *
 * @param {Object} params
 * @param {string} params.tenantId - ID doanh nghiệp từ QR code
 * @param {string} params.location - Vị trí quét QR (tên bàn/khu vực)
 * @param {Blob|null} params.audioBlob - File ghi âm từ MediaRecorder (null nếu chỉ dùng text)
 * @param {string|null} params.textContent - Văn bản gõ tay (null nếu chỉ dùng audio)
 * @returns {Promise<Object>} Response từ backend: { request_id, status, transcript, is_suspicious, ... }
 * @throws {Error} với property .statusCode khi lỗi từ backend
 */
export async function submitFeedback({ tenantId, location, audioBlob, textContent }) {
  const formData = new FormData()

  // Fields bắt buộc — khớp CHÍNH XÁC với backend/api/routes/feedback.py
  formData.append('tenant_id', tenantId)
  formData.append('location', location)

  // Fields tùy chọn (ít nhất 1 trong 2 phải có)
  if (audioBlob) {
    // Đặt tên file .webm hoặc .ogg tùy browser hỗ trợ
    const ext = audioBlob.type.includes('ogg') ? 'ogg' : 'webm'
    formData.append('audio_file', audioBlob, `recording.${ext}`)
  }
  if (textContent) {
    formData.append('text_content', textContent)
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/feedback`, {
    method: 'POST',
    body: formData
    // KHÔNG set Content-Type header — browser tự set boundary cho multipart/form-data
  })

  // Xử lý các mã lỗi đã ghi trong docs/api-contract.md
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Lỗi không xác định' }))

    const error = new Error(getFriendlyErrorMessage(response.status, errorData.detail))
    error.statusCode = response.status
    error.rawDetail = errorData.detail
    throw error
  }

  return response.json()
}

/**
 * Chuyển lỗi kỹ thuật thành thông báo thân thiện cho user
 * Danh sách mã lỗi từ docs/api-contract.md mục 2
 */
function getFriendlyErrorMessage(statusCode, detail) {
  switch (statusCode) {
    case 400:
      // Có thể là fraud filter hoặc thiếu input
      if (detail && detail.includes('fraud')) {
        return 'Phản hồi của bạn không thể xử lý lúc này. Vui lòng thử lại sau.'
      }
      return 'Vui lòng thêm nội dung phản hồi (ghi âm hoặc văn bản).'
    case 413:
      return 'File ghi âm quá lớn. Vui lòng ghi âm ngắn hơn (tối đa 15 giây).'
    case 503:
      return 'Dịch vụ tạm thời không khả dụng. Vui lòng thử lại sau.'
    case 504:
      return 'Hệ thống đang bận. Vui lòng thử lại sau ít phút.'
    default:
      return 'Đã xảy ra lỗi. Vui lòng thử lại.'
  }
}

/**
 * Kiểm tra backend đang chạy không
 * Dùng khi cần debug kết nối
 */
export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/health`)
  return response.json()
}
