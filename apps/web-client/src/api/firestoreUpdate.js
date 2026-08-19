/**
 * firestoreUpdate.js — DEPRECATED (BUG-03 FIX, 2026-08-19)
 *
 * ⛔ FILE NÀY KHÔNG CÒN ĐƯỢC SỬ DỤNG.
 *
 * Lý do deprecated:
 *   File này cho phép ghi trực tiếp phone_masked + voucher_code vào Firestore
 *   từ phía client (unauthenticated), bypass hoàn toàn backend validation.
 *   Hậu quả:
 *     - Voucher tạo ở client có thể bị giả mạo (chỉ cần biết 4 số cuối SĐT)
 *     - 2 SĐT khác nhau cho cùng 1 feedback (RecordingPage vs SpinPage)
 *     - RFMS customer document không được cập nhật đúng
 *
 * Thay thế:
 *   Gọi POST /api/v1/gamification/spin (qua gamification.js → submitSpinAPI).
 *   Backend tự lưu phone + voucher vào Firestore sau khi xác thực.
 *
 * Nếu bạn thấy file này được import ở đâu đó → hãy xóa import đó
 * và thay bằng submitSpinAPI từ '../api/gamification.js'.
 */

export function updateFeedbackWithSpin() {
  console.error(
    '[Sentrix] updateFeedbackWithSpin() đã bị deprecated (BUG-03 FIX). ' +
    'Dùng submitSpinAPI() từ api/gamification.js thay thế. ' +
    'Mọi ghi dữ liệu phải qua backend — không ghi Firestore trực tiếp từ client.'
  )
  return Promise.resolve(false)
}
