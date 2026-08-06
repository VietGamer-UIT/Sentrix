/**
 * mockFirestore.js — Dữ liệu giả lập Firestore cho Dashboard
 *
 * Field names KHỚP CHÍNH XÁC với backend/db/schema.md
 * KHÔNG được đổi tên field — khi bỏ mock sẽ dùng cùng field names này
 * từ Firestore SDK thật.
 *
 * Điều kiện để bỏ mock:
 * 1. Tuyền tạo Firebase project và báo credentials
 * 2. Việt/Tuyền fill .env với Firebase config thật
 * 3. Đổi VITE_USE_MOCK_FIRESTORE=false trong .env
 * 4. Thay useMockFeedbacks/useMockCustomers bằng useFirestoreFeedbacks/useFirestoreCustomers
 */

const NOW = Date.now()
const DAY = 86400000

// ============================================================
// Mock data: feedbacks — schema từ backend/db/schema.md §feedbacks
// ============================================================
export const MOCK_FEEDBACKS = [
  {
    feedback_id: 'fb_001',
    customer_id: 'cust_a3f8c2d1e4b7f901',
    timestamp: { seconds: Math.floor((NOW - 5 * 60000) / 1000) },   // 5 phút trước
    location: 'Bàn 5',
    input_type: 'audio',
    transcript: 'Phục vụ tốt quá ha, đợi có 20 phút mà. Nước uống ngon!',
    aspects: [
      { aspect: 'toc_do_phuc_vu', sentiment: 'negative', score: -0.82, reason: 'Chờ 20 phút', confidence: 0.91 },
      { aspect: 'nhan_vien', sentiment: 'positive', score: 0.45, reason: 'Nhân viên được khen', confidence: 0.78 },
      { aspect: 'mon_an', sentiment: 'positive', score: 0.62, reason: 'Khen nước uống ngon', confidence: 0.85 }
    ],
    sentiment_score: -0.21,
    is_sarcasm: true,
    processing_status: 'done',
    audio_duration_sec: 8.4
  },
  {
    feedback_id: 'fb_002',
    customer_id: 'cust_b9d4e7f1a2c3e084',
    timestamp: { seconds: Math.floor((NOW - 45 * 60000) / 1000) },  // 45 phút trước
    location: 'Bàn 12',
    input_type: 'text',
    transcript: 'Phở ngon lắm! Nhân viên nhiệt tình. Sẽ quay lại!',
    aspects: [
      { aspect: 'mon_an', sentiment: 'positive', score: 0.91, reason: 'Khen phở ngon', confidence: 0.95 },
      { aspect: 'nhan_vien', sentiment: 'positive', score: 0.84, reason: 'Khen nhiệt tình', confidence: 0.90 }
    ],
    sentiment_score: 0.88,
    is_sarcasm: false,
    processing_status: 'done',
    audio_duration_sec: null
  },
  {
    feedback_id: 'fb_003',
    customer_id: 'cust_c7e2f4a8b1d6e912',
    timestamp: { seconds: Math.floor((NOW - 2 * 3600000) / 1000) }, // 2 giờ trước
    location: 'Khu VIP',
    input_type: 'audio',
    transcript: 'Không gian ồn quá, bàn bẩn, giá hơi cao so với chất lượng.',
    aspects: [
      { aspect: 'khong_gian', sentiment: 'negative', score: -0.75, reason: 'Phàn nàn ồn ào', confidence: 0.88 },
      { aspect: 've_sinh', sentiment: 'negative', score: -0.91, reason: 'Bàn bẩn', confidence: 0.94 },
      { aspect: 'gia_ca', sentiment: 'negative', score: -0.58, reason: 'Giá không tương xứng', confidence: 0.82 }
    ],
    sentiment_score: -0.75,
    is_sarcasm: false,
    processing_status: 'done',
    audio_duration_sec: 12.1
  },
  {
    feedback_id: 'fb_004',
    customer_id: 'cust_d2a9c5f7e3b1d804',
    timestamp: { seconds: Math.floor((NOW - 4 * 3600000) / 1000) }, // 4 giờ trước
    location: 'Bàn 3',
    input_type: 'text',
    transcript: 'Tạm ổn thôi. Bình thường.',
    aspects: [
      { aspect: 'khac', sentiment: 'neutral', score: 0.02, reason: 'Nhận xét trung lập', confidence: 0.61 }
    ],
    sentiment_score: 0.02,
    is_sarcasm: false,
    processing_status: 'done',
    audio_duration_sec: null
  },
  {
    feedback_id: 'fb_005',
    customer_id: 'cust_e4f1b8d6c9a2f713',
    timestamp: { seconds: Math.floor((NOW - DAY + 3600000) / 1000) }, // Hôm qua
    location: 'Bàn 8',
    input_type: 'audio',
    transcript: 'Mỗi lần tới đây mình đều hài lòng. Giữ nguyên chất lượng nha!',
    aspects: [
      { aspect: 'mon_an', sentiment: 'positive', score: 0.78, reason: 'Hài lòng tổng thể', confidence: 0.86 },
      { aspect: 'nhan_vien', sentiment: 'positive', score: 0.72, reason: 'Luôn hài lòng', confidence: 0.83 }
    ],
    sentiment_score: 0.75,
    is_sarcasm: false,
    processing_status: 'done',
    audio_duration_sec: 9.8
  },
  {
    feedback_id: 'fb_006',
    customer_id: 'cust_a3f8c2d1e4b7f901', // Cùng khách với fb_001
    timestamp: { seconds: Math.floor((NOW - DAY - 2 * 3600000) / 1000) }, // Hôm qua
    location: 'Bàn 5',
    input_type: 'audio',
    transcript: 'Lại phải đợi lâu như mọi lần. Nhân viên thiếu người.',
    aspects: [
      { aspect: 'toc_do_phuc_vu', sentiment: 'negative', score: -0.88, reason: 'Đợi lâu lặp lại', confidence: 0.93 },
      { aspect: 'nhan_vien', sentiment: 'negative', score: -0.65, reason: 'Thiếu nhân sự', confidence: 0.79 }
    ],
    sentiment_score: -0.78,
    is_sarcasm: false,
    processing_status: 'done',
    audio_duration_sec: 7.2
  },
  {
    feedback_id: 'fb_007',
    customer_id: 'cust_f6c3a9e2d7b0f124',
    timestamp: { seconds: Math.floor((NOW - 20 * 60000) / 1000) }, // 20 phút trước
    location: 'Bàn 1',
    input_type: 'audio',
    transcript: '',
    aspects: [],
    sentiment_score: 0,
    is_sarcasm: false,
    processing_status: 'processing', // Đang xử lý
    audio_duration_sec: 6.5
  }
]

// ============================================================
// Mock data: customers — schema từ backend/db/schema.md §customers
// ============================================================
export const MOCK_CUSTOMERS = [
  {
    customer_id: 'cust_a3f8c2d1e4b7f901',
    phone_masked: '090****567',
    first_seen_at: { seconds: Math.floor((NOW - 21 * DAY) / 1000) },
    last_feedback_at: { seconds: Math.floor((NOW - 5 * 60000) / 1000) },
    feedback_count: 5,
    total_spending: 850000,
    avg_sentiment_score: -0.52,
    rfms_r: 0.98, rfms_f: 0.70, rfms_m: 0.55, rfms_s: 0.24,
    p_churn: 0.91,
    churn_risk_level: 'high',
    zns_sent_at: null,
    zns_voucher_code: null,
    updated_at: { seconds: Math.floor((NOW - 5 * 60000) / 1000) }
  },
  {
    customer_id: 'cust_c7e2f4a8b1d6e912',
    phone_masked: '091****234',
    first_seen_at: { seconds: Math.floor((NOW - 7 * DAY) / 1000) },
    last_feedback_at: { seconds: Math.floor((NOW - 2 * 3600000) / 1000) },
    feedback_count: 2,
    total_spending: 320000,
    avg_sentiment_score: -0.71,
    rfms_r: 0.88, rfms_f: 0.30, rfms_m: 0.22, rfms_s: 0.15,
    p_churn: 0.87,
    churn_risk_level: 'high',
    zns_sent_at: null,
    zns_voucher_code: null,
    updated_at: { seconds: Math.floor((NOW - 2 * 3600000) / 1000) }
  },
  {
    customer_id: 'cust_b9d4e7f1a2c3e084',
    phone_masked: '093****891',
    first_seen_at: { seconds: Math.floor((NOW - 14 * DAY) / 1000) },
    last_feedback_at: { seconds: Math.floor((NOW - 45 * 60000) / 1000) },
    feedback_count: 4,
    total_spending: 620000,
    avg_sentiment_score: 0.81,
    rfms_r: 0.94, rfms_f: 0.60, rfms_m: 0.48, rfms_s: 0.91,
    p_churn: 0.08,
    churn_risk_level: 'low',
    zns_sent_at: null,
    zns_voucher_code: null,
    updated_at: { seconds: Math.floor((NOW - 45 * 60000) / 1000) }
  },
  {
    customer_id: 'cust_d2a9c5f7e3b1d804',
    phone_masked: '097****312',
    first_seen_at: { seconds: Math.floor((NOW - 30 * DAY) / 1000) },
    last_feedback_at: { seconds: Math.floor((NOW - 4 * 3600000) / 1000) },
    feedback_count: 7,
    total_spending: 1200000,
    avg_sentiment_score: 0.12,
    rfms_r: 0.82, rfms_f: 0.85, rfms_m: 0.78, rfms_s: 0.56,
    p_churn: 0.62,
    churn_risk_level: 'medium',
    zns_sent_at: null,
    zns_voucher_code: null,
    updated_at: { seconds: Math.floor((NOW - 4 * 3600000) / 1000) }
  },
  {
    customer_id: 'cust_e4f1b8d6c9a2f713',
    phone_masked: '098****756',
    first_seen_at: { seconds: Math.floor((NOW - 60 * DAY) / 1000) },
    last_feedback_at: { seconds: Math.floor((NOW - DAY) / 1000) },
    feedback_count: 12,
    total_spending: 2800000,
    avg_sentiment_score: 0.74,
    rfms_r: 0.77, rfms_f: 1.00, rfms_m: 0.95, rfms_s: 0.88,
    p_churn: 0.04,
    churn_risk_level: 'low',
    zns_sent_at: null,
    zns_voucher_code: null,
    updated_at: { seconds: Math.floor((NOW - DAY) / 1000) }
  }
]

// ============================================================
// Mock tenant info — schema từ backend/db/schema.md §tenants
// ============================================================
export const MOCK_TENANT = {
  tenant_id: 'pho-ba-lan_1722500000000',
  business_name: 'Phở Bà Lan',
  industry: 'fnb',
  plan: 'pro',
  owner_email: 'balan.pho@gmail.com',
  is_active: true,
  churn_threshold: 0.85
}

// ============================================================
// Helper: format timestamp từ Firestore (hoặc mock) → Date object
// ============================================================
export function tsToDate(ts) {
  if (!ts) return null
  if (ts instanceof Date) return ts
  if (typeof ts.seconds === 'number') return new Date(ts.seconds * 1000)
  return new Date(ts)
}

// Helper: format thời gian tương đối
export function timeAgo(ts) {
  const date = tsToDate(ts)
  if (!date) return '—'
  const diff = Math.floor((Date.now() - date.getTime()) / 1000)
  if (diff < 60) return `${diff}s trước`
  if (diff < 3600) return `${Math.floor(diff / 60)} phút trước`
  if (diff < 86400) return `${Math.floor(diff / 3600)} giờ trước`
  return `${Math.floor(diff / 86400)} ngày trước`
}
