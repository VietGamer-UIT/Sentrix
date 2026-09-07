/**
 * pilotService.js — Pilot form submission using FormSubmit API
 */

export async function submitPilotLead(formData) {
  // We send to the specific email the user provided. 
  // Uses formsubmit.co's AJAX API for headless submission.
  const response = await fetch("https://formsubmit.co/ajax/skyvdygaming@gmail.com", {
    method: "POST",
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    },
    body: JSON.stringify({
      _subject: "[SENTRIX] Đăng ký dùng thử mới",
      _captcha: "false", // Đang tắt CAPTCHA để UX mượt
      "Tên cửa hàng": formData.storeName,
      "Người liên hệ": formData.contactName,
      "Thông tin liên hệ": formData.contactInfo,
      "Loại hình": formData.storeType,
      "Quy mô": formData.storeSize,
      "Mục tiêu": formData.goal,
      "Thời gian đăng ký": new Date().toLocaleString('vi-VN')
    })
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();
  if (data.success === 'true' || data.success === true || data.success === 'success') {
    return { success: true };
  } else {
    console.error("[Sentrix Pilot] FormSubmit error:", data);
    throw new Error('Provider returned error.');
  }
}
