/**
 * seed-firestore.mjs — Script bơm mock data vào Firestore thật
 *
 * Chạy 1 lần: node seed-firestore.mjs
 * Yêu cầu: FIREBASE_PROJECT_ID, FIREBASE_CLIENT_EMAIL, FIREBASE_PRIVATE_KEY trong .env
 *
 * Collections sẽ được tạo:
 *   tenants/pho-ba-lan_1722500000000               — thông tin quán
 *   tenants/pho-ba-lan_1722500000000/feedbacks/*   — 12 phản hồi demo
 *   tenants/pho-ba-lan_1722500000000/customers/*   — 8 khách hàng demo
 */

import { initializeApp, cert } from 'firebase-admin/app'
import { getFirestore, Timestamp } from 'firebase-admin/firestore'
import { readFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

// ─── Load .env thủ công (không dùng dotenv để tránh dependency) ──────────────
const __dir = dirname(fileURLToPath(import.meta.url))
try {
  const envPath = resolve(__dir, '../../.env')
  const envContent = readFileSync(envPath, 'utf-8')
  envContent.split('\n').forEach(line => {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) return
    const eqIdx = trimmed.indexOf('=')
    if (eqIdx < 0) return
    const key = trimmed.slice(0, eqIdx).trim()
    let val   = trimmed.slice(eqIdx + 1).trim()
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1)
    }
    if (!process.env[key]) process.env[key] = val
  })
} catch {
  // .env không có → dùng process.env từ shell
}

// ─── Init Firebase Admin SDK ─────────────────────────────────────────────────
const app = initializeApp({
  credential: cert({
    projectId:   process.env.FIREBASE_PROJECT_ID,
    clientEmail: process.env.FIREBASE_CLIENT_EMAIL,
    privateKey:  (process.env.FIREBASE_PRIVATE_KEY || '').replace(/\\n/g, '\n'),
  }),
})
const db = getFirestore(app)

// ─── Helper timestamp ─────────────────────────────────────────────────────────
const now  = Date.now()
const DAY  = 86400000
function ts(msAgo) { return Timestamp.fromDate(new Date(now - msAgo)) }

// ─── TENANT ──────────────────────────────────────────────────────────────────
const TENANT_ID = 'pho-ba-lan_1722500000000'

const tenantData = {
  business_name:    'Phở Bà Lan',
  industry:         'fnb',
  plan:             'pro',
  owner_email:      'balan.pho@gmail.com',
  is_active:        true,
  churn_threshold:  0.85,
  created_at:       ts(90 * DAY),
}

// ─── FEEDBACKS (12 bản ghi đa dạng) ─────────────────────────────────────────
const feedbacks = [
  {
    feedback_id:        'fb_001',
    customer_id:        'cust_a3f8c2d1e4b7f901',
    timestamp:          ts(5 * 60000),
    location:           'Bàn 5',
    input_type:         'audio',
    transcript:         'Phục vụ tốt quá ha, đợi có 20 phút mà. Nước uống ngon!',
    aspects: [
      { aspect: 'toc_do_phuc_vu', sentiment: 'negative', score: -0.82, reason: 'Chờ 20 phút', confidence: 0.91 },
      { aspect: 'nhan_vien', sentiment: 'positive', score: 0.45, reason: 'Nhân viên được khen', confidence: 0.78 },
      { aspect: 'mon_an', sentiment: 'positive', score: 0.62, reason: 'Khen nước uống ngon', confidence: 0.85 },
    ],
    sentiment_score:    -0.21,
    overall_sentiment:  'Trung lập',
    is_sarcasm:         true,
    p_churn:            0.91,
    churn_risk_level:   'high',
    should_alert:       true,
    processing_status:  'done',
    audio_duration_sec: 8.4,
    total_spending:     150000,
  },
  {
    feedback_id:        'fb_002',
    customer_id:        'cust_b9d4e7f1a2c3e084',
    timestamp:          ts(45 * 60000),
    location:           'Bàn 12',
    input_type:         'text',
    transcript:         'Phở ngon lắm! Nhân viên nhiệt tình. Sẽ quay lại!',
    aspects: [
      { aspect: 'mon_an', sentiment: 'positive', score: 0.91, reason: 'Khen phở ngon', confidence: 0.95 },
      { aspect: 'nhan_vien', sentiment: 'positive', score: 0.84, reason: 'Khen nhiệt tình', confidence: 0.90 },
    ],
    sentiment_score:    0.88,
    overall_sentiment:  'Tích cực',
    is_sarcasm:         false,
    p_churn:            0.08,
    churn_risk_level:   'low',
    should_alert:       false,
    processing_status:  'done',
    audio_duration_sec: null,
    total_spending:     120000,
  },
  {
    feedback_id:        'fb_003',
    customer_id:        'cust_c7e2f4a8b1d6e912',
    timestamp:          ts(2 * 3600000),
    location:           'Khu VIP',
    input_type:         'audio',
    transcript:         'Không gian ồn quá, bàn bẩn, giá hơi cao so với chất lượng.',
    aspects: [
      { aspect: 'khong_gian', sentiment: 'negative', score: -0.75, reason: 'Phàn nàn ồn ào', confidence: 0.88 },
      { aspect: 've_sinh', sentiment: 'negative', score: -0.91, reason: 'Bàn bẩn', confidence: 0.94 },
      { aspect: 'gia_ca', sentiment: 'negative', score: -0.58, reason: 'Giá không tương xứng', confidence: 0.82 },
    ],
    sentiment_score:    -0.75,
    overall_sentiment:  'Tiêu cực',
    is_sarcasm:         false,
    p_churn:            0.87,
    churn_risk_level:   'high',
    should_alert:       true,
    processing_status:  'done',
    audio_duration_sec: 12.1,
    total_spending:     200000,
  },
  {
    feedback_id:        'fb_004',
    customer_id:        'cust_d2a9c5f7e3b1d804',
    timestamp:          ts(4 * 3600000),
    location:           'Bàn 3',
    input_type:         'text',
    transcript:         'Tạm ổn thôi. Bình thường.',
    aspects: [
      { aspect: 'khac', sentiment: 'neutral', score: 0.02, reason: 'Nhận xét trung lập', confidence: 0.61 },
    ],
    sentiment_score:    0.02,
    overall_sentiment:  'Trung lập',
    is_sarcasm:         false,
    p_churn:            0.62,
    churn_risk_level:   'medium',
    should_alert:       false,
    processing_status:  'done',
    audio_duration_sec: null,
    total_spending:     80000,
  },
  {
    feedback_id:        'fb_005',
    customer_id:        'cust_e4f1b8d6c9a2f713',
    timestamp:          ts(DAY - 3600000),
    location:           'Bàn 8',
    input_type:         'audio',
    transcript:         'Mỗi lần tới đây mình đều hài lòng. Giữ nguyên chất lượng nha!',
    aspects: [
      { aspect: 'mon_an', sentiment: 'positive', score: 0.78, reason: 'Hài lòng tổng thể', confidence: 0.86 },
      { aspect: 'nhan_vien', sentiment: 'positive', score: 0.72, reason: 'Luôn hài lòng', confidence: 0.83 },
    ],
    sentiment_score:    0.75,
    overall_sentiment:  'Tích cực',
    is_sarcasm:         false,
    p_churn:            0.04,
    churn_risk_level:   'low',
    should_alert:       false,
    processing_status:  'done',
    audio_duration_sec: 9.8,
    total_spending:     180000,
  },
  {
    feedback_id:        'fb_006',
    customer_id:        'cust_a3f8c2d1e4b7f901',
    timestamp:          ts(DAY + 2 * 3600000),
    location:           'Bàn 5',
    input_type:         'audio',
    transcript:         'Lại phải đợi lâu như mọi lần. Nhân viên thiếu người.',
    aspects: [
      { aspect: 'toc_do_phuc_vu', sentiment: 'negative', score: -0.88, reason: 'Đợi lâu lặp lại', confidence: 0.93 },
      { aspect: 'nhan_vien', sentiment: 'negative', score: -0.65, reason: 'Thiếu nhân sự', confidence: 0.79 },
    ],
    sentiment_score:    -0.78,
    overall_sentiment:  'Tiêu cực',
    is_sarcasm:         false,
    p_churn:            0.91,
    churn_risk_level:   'high',
    should_alert:       true,
    processing_status:  'done',
    audio_duration_sec: 7.2,
    total_spending:     150000,
  },
  {
    feedback_id:        'fb_007',
    customer_id:        'cust_f6c3a9e2d7b0f124',
    timestamp:          ts(20 * 60000),
    location:           'Bàn 1',
    input_type:         'audio',
    transcript:         'Nước lèo đậm đà, ăn nóng hổi. Bàn sạch. Thích!',
    aspects: [
      { aspect: 'mon_an', sentiment: 'positive', score: 0.84, reason: 'Khen nước lèo', confidence: 0.92 },
      { aspect: 've_sinh', sentiment: 'positive', score: 0.71, reason: 'Bàn sạch', confidence: 0.87 },
    ],
    sentiment_score:    0.78,
    overall_sentiment:  'Tích cực',
    is_sarcasm:         false,
    p_churn:            0.15,
    churn_risk_level:   'low',
    should_alert:       false,
    processing_status:  'done',
    audio_duration_sec: 6.5,
    total_spending:     100000,
  },
  {
    feedback_id:        'fb_008',
    customer_id:        'cust_g8h5k2m9n1p3q7r0',
    timestamp:          ts(3 * 3600000),
    location:           'Mang về',
    input_type:         'text',
    transcript:         'Order online nhưng thiếu topping, phải gọi điện khiếu nại mất 10p.',
    aspects: [
      { aspect: 'nhan_vien', sentiment: 'negative', score: -0.71, reason: 'Thiếu topping, phải khiếu nại', confidence: 0.88 },
      { aspect: 'toc_do_phuc_vu', sentiment: 'negative', score: -0.55, reason: 'Mất 10 phút giải quyết', confidence: 0.81 },
    ],
    sentiment_score:    -0.63,
    overall_sentiment:  'Tiêu cực',
    is_sarcasm:         false,
    p_churn:            0.74,
    churn_risk_level:   'medium',
    should_alert:       false,
    processing_status:  'done',
    audio_duration_sec: null,
    total_spending:     95000,
  },
  {
    feedback_id:        'fb_009',
    customer_id:        'cust_h1j4l7o0r3u6x9a2',
    timestamp:          ts(2 * DAY),
    location:           'Bàn 7',
    input_type:         'audio',
    transcript:         'Đồ ăn ngon nhưng chờ lâu quá, khoảng 30 phút. Không gian thoải mái.',
    aspects: [
      { aspect: 'mon_an', sentiment: 'positive', score: 0.71, reason: 'Đồ ăn ngon', confidence: 0.89 },
      { aspect: 'toc_do_phuc_vu', sentiment: 'negative', score: -0.79, reason: 'Chờ 30 phút', confidence: 0.92 },
      { aspect: 'khong_gian', sentiment: 'positive', score: 0.55, reason: 'Không gian thoải mái', confidence: 0.77 },
    ],
    sentiment_score:    0.16,
    overall_sentiment:  'Trung lập',
    is_sarcasm:         false,
    p_churn:            0.43,
    churn_risk_level:   'medium',
    should_alert:       false,
    processing_status:  'done',
    audio_duration_sec: 11.3,
    total_spending:     145000,
  },
  {
    feedback_id:        'fb_010',
    customer_id:        'cust_i2k5n8q1t4w7z0b3',
    timestamp:          ts(3 * DAY),
    location:           'Bàn 10',
    input_type:         'text',
    transcript:         'Giá rẻ mà chất lượng ổn. Đáng đồng tiền.',
    aspects: [
      { aspect: 'gia_ca', sentiment: 'positive', score: 0.82, reason: 'Giá rẻ, xứng đáng', confidence: 0.91 },
      { aspect: 'mon_an', sentiment: 'positive', score: 0.65, reason: 'Chất lượng ổn', confidence: 0.83 },
    ],
    sentiment_score:    0.74,
    overall_sentiment:  'Tích cực',
    is_sarcasm:         false,
    p_churn:            0.09,
    churn_risk_level:   'low',
    should_alert:       false,
    processing_status:  'done',
    audio_duration_sec: null,
    total_spending:     70000,
  },
  {
    feedback_id:        'fb_011',
    customer_id:        'cust_j3m6p9s2v5y8c1f4',
    timestamp:          ts(4 * DAY),
    location:           'Bàn 2',
    input_type:         'audio',
    transcript:         'Ổn mà, không có gì đặc biệt.',
    aspects: [
      { aspect: 'khac', sentiment: 'neutral', score: 0.05, reason: 'Trung bình', confidence: 0.60 },
    ],
    sentiment_score:    0.05,
    overall_sentiment:  'Trung lập',
    is_sarcasm:         false,
    p_churn:            0.51,
    churn_risk_level:   'medium',
    should_alert:       false,
    processing_status:  'done',
    audio_duration_sec: 4.2,
    total_spending:     110000,
  },
  {
    feedback_id:        'fb_012',
    customer_id:        'cust_k4n7q0t3w6z9d2g5',
    timestamp:          ts(5 * DAY),
    location:           'Khu VIP',
    input_type:         'audio',
    transcript:         'Tuyệt vời! Phở đặc biệt thật sự đặc biệt. Nước dùng trong, thơm. Nhân viên tận tình.',
    aspects: [
      { aspect: 'mon_an', sentiment: 'positive', score: 0.97, reason: 'Phở đặc biệt xuất sắc', confidence: 0.98 },
      { aspect: 'nhan_vien', sentiment: 'positive', score: 0.89, reason: 'Nhân viên tận tình', confidence: 0.93 },
    ],
    sentiment_score:    0.93,
    overall_sentiment:  'Tích cực',
    is_sarcasm:         false,
    p_churn:            0.02,
    churn_risk_level:   'low',
    should_alert:       false,
    processing_status:  'done',
    audio_duration_sec: 14.7,
    total_spending:     250000,
  },
]

// ─── CUSTOMERS (8 hồ sơ khách hàng) ─────────────────────────────────────────
const customers = [
  {
    customer_id:        'cust_a3f8c2d1e4b7f901',
    phone_masked:       '090****567',
    first_seen_at:      ts(21 * DAY),
    last_feedback_at:   ts(5 * 60000),
    feedback_count:     6,
    total_spending:     900000,
    avg_sentiment_score: -0.52,
    rfms_r: 0.98, rfms_f: 0.70, rfms_m: 0.55, rfms_s: 0.24,
    p_churn:            0.91,
    churn_risk_level:   'high',
    zns_sent_at:        null,
    zns_voucher_code:   null,
    updated_at:         ts(5 * 60000),
  },
  {
    customer_id:        'cust_c7e2f4a8b1d6e912',
    phone_masked:       '091****234',
    first_seen_at:      ts(7 * DAY),
    last_feedback_at:   ts(2 * 3600000),
    feedback_count:     2,
    total_spending:     320000,
    avg_sentiment_score: -0.71,
    rfms_r: 0.88, rfms_f: 0.30, rfms_m: 0.22, rfms_s: 0.15,
    p_churn:            0.87,
    churn_risk_level:   'high',
    zns_sent_at:        null,
    zns_voucher_code:   null,
    updated_at:         ts(2 * 3600000),
  },
  {
    customer_id:        'cust_g8h5k2m9n1p3q7r0',
    phone_masked:       '096****442',
    first_seen_at:      ts(10 * DAY),
    last_feedback_at:   ts(3 * 3600000),
    feedback_count:     3,
    total_spending:     285000,
    avg_sentiment_score: -0.63,
    rfms_r: 0.81, rfms_f: 0.25, rfms_m: 0.18, rfms_s: 0.22,
    p_churn:            0.74,
    churn_risk_level:   'medium',
    zns_sent_at:        null,
    zns_voucher_code:   null,
    updated_at:         ts(3 * 3600000),
  },
  {
    customer_id:        'cust_d2a9c5f7e3b1d804',
    phone_masked:       '097****312',
    first_seen_at:      ts(30 * DAY),
    last_feedback_at:   ts(4 * 3600000),
    feedback_count:     8,
    total_spending:     1280000,
    avg_sentiment_score: 0.12,
    rfms_r: 0.82, rfms_f: 0.85, rfms_m: 0.78, rfms_s: 0.56,
    p_churn:            0.62,
    churn_risk_level:   'medium',
    zns_sent_at:        null,
    zns_voucher_code:   null,
    updated_at:         ts(4 * 3600000),
  },
  {
    customer_id:        'cust_h1j4l7o0r3u6x9a2',
    phone_masked:       '094****881',
    first_seen_at:      ts(15 * DAY),
    last_feedback_at:   ts(2 * DAY),
    feedback_count:     3,
    total_spending:     435000,
    avg_sentiment_score: 0.16,
    rfms_r: 0.72, rfms_f: 0.40, rfms_m: 0.35, rfms_s: 0.62,
    p_churn:            0.43,
    churn_risk_level:   'medium',
    zns_sent_at:        null,
    zns_voucher_code:   null,
    updated_at:         ts(2 * DAY),
  },
  {
    customer_id:        'cust_f6c3a9e2d7b0f124',
    phone_masked:       '093****119',
    first_seen_at:      ts(5 * DAY),
    last_feedback_at:   ts(20 * 60000),
    feedback_count:     2,
    total_spending:     200000,
    avg_sentiment_score: 0.78,
    rfms_r: 0.99, rfms_f: 0.20, rfms_m: 0.15, rfms_s: 0.84,
    p_churn:            0.15,
    churn_risk_level:   'low',
    zns_sent_at:        null,
    zns_voucher_code:   null,
    updated_at:         ts(20 * 60000),
  },
  {
    customer_id:        'cust_b9d4e7f1a2c3e084',
    phone_masked:       '098****756',
    first_seen_at:      ts(14 * DAY),
    last_feedback_at:   ts(45 * 60000),
    feedback_count:     5,
    total_spending:     740000,
    avg_sentiment_score: 0.81,
    rfms_r: 0.94, rfms_f: 0.60, rfms_m: 0.48, rfms_s: 0.91,
    p_churn:            0.08,
    churn_risk_level:   'low',
    zns_sent_at:        null,
    zns_voucher_code:   null,
    updated_at:         ts(45 * 60000),
  },
  {
    customer_id:        'cust_e4f1b8d6c9a2f713',
    phone_masked:       '032****993',
    first_seen_at:      ts(60 * DAY),
    last_feedback_at:   ts(DAY),
    feedback_count:     13,
    total_spending:     2980000,
    avg_sentiment_score: 0.74,
    rfms_r: 0.77, rfms_f: 1.00, rfms_m: 0.95, rfms_s: 0.88,
    p_churn:            0.04,
    churn_risk_level:   'low',
    zns_sent_at:        null,
    zns_voucher_code:   null,
    updated_at:         ts(DAY),
  },
]

// ─── SEED ─────────────────────────────────────────────────────────────────────
async function seed() {
  console.log(`\n🌱 Bắt đầu seed Firestore: ${process.env.FIREBASE_PROJECT_ID}`)
  console.log(`   Tenant: ${TENANT_ID}\n`)

  // 1. Tenant document
  await db.doc(`tenants/${TENANT_ID}`).set(tenantData, { merge: true })
  console.log('✅ Tenant document')

  // 2. Feedbacks
  const fbBatch = db.batch()
  for (const fb of feedbacks) {
    const { feedback_id, ...data } = fb
    fbBatch.set(db.doc(`tenants/${TENANT_ID}/feedbacks/${feedback_id}`), data, { merge: true })
  }
  await fbBatch.commit()
  console.log(`✅ ${feedbacks.length} feedbacks`)

  // 3. Customers
  const cuBatch = db.batch()
  for (const cu of customers) {
    const { customer_id, ...data } = cu
    cuBatch.set(db.doc(`tenants/${TENANT_ID}/customers/${customer_id}`), data, { merge: true })
  }
  await cuBatch.commit()
  console.log(`✅ ${customers.length} customers`)

  console.log('\n🎉 Seed xong! Dashboard sẽ hiện data thật từ Firestore.\n')
  process.exit(0)
}

seed().catch(err => {
  console.error('❌ Seed lỗi:', err.message)
  process.exit(1)
})
