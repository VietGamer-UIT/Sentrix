import { useMemo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, PieChart, Pie
} from 'recharts'
import {
  MOCK_FEEDBACKS, MOCK_CUSTOMERS, MOCK_TENANT, timeAgo, tsToDate
} from '../mocks/firestoreMock.js'

/**
 * OverviewPage — Tổng quan realtime
 *
 * Dữ liệu đọc từ: (hiện tại mock, sau đổi thành Firestore SDK)
 *   - tenants/{tenant_id}/feedbacks → KPIs, chart sentiment, feed mới nhất
 *   - tenants/{tenant_id}/customers → số khách rủi ro cao
 *
 * Khi Tuyền setup Firebase:
 *   1. Tạo src/hooks/useFirestoreFeedbacks.js với onSnapshot
 *   2. Thay MOCK_FEEDBACKS → dữ liệu từ hook
 *   3. Đổi VITE_USE_MOCK_FIRESTORE=false
 *
 * Field names phải khớp chính xác: backend/db/schema.md
 */

// === Aspect labels tiếng Việt ===
const ASPECT_LABELS = {
  nhan_vien: 'Nhân viên',
  mon_an: 'Món ăn',
  khong_gian: 'Không gian',
  gia_ca: 'Giá cả',
  toc_do_phuc_vu: 'Tốc độ phục vụ',
  ve_sinh: 'Vệ sinh',
  khac: 'Khác'
}

const ASPECT_ICONS = {
  nhan_vien: '👨‍💼',
  mon_an: '🍜',
  khong_gian: '🏠',
  gia_ca: '💰',
  toc_do_phuc_vu: '⚡',
  ve_sinh: '🧹',
  khac: '❓'
}

// Sentiment score → màu gradient
function scoreToColor(score) {
  if (score >= 0.3) return 'var(--color-positive)'
  if (score <= -0.3) return 'var(--color-negative)'
  return 'var(--color-neutral-s)'
}

function sentimentLabel(score) {
  if (score >= 0.3) return { label: 'Tích cực', cls: 'positive' }
  if (score <= -0.3) return { label: 'Tiêu cực', cls: 'negative' }
  return { label: 'Trung lập', cls: 'neutral' }
}

export default function OverviewPage() {
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  // ── KPI Calculations ──────────────────────────────────────
  const doneFeedbacks = useMemo(() =>
    MOCK_FEEDBACKS.filter(f => f.processing_status === 'done'), [])

  const todayFeedbacks = useMemo(() =>
    doneFeedbacks.filter(f => tsToDate(f.timestamp) >= today), [doneFeedbacks])

  const avgSentiment = useMemo(() => {
    if (!doneFeedbacks.length) return 0
    return doneFeedbacks.reduce((s, f) => s + f.sentiment_score, 0) / doneFeedbacks.length
  }, [doneFeedbacks])

  const sarcasmCount = useMemo(() =>
    doneFeedbacks.filter(f => f.is_sarcasm).length, [doneFeedbacks])

  const highRiskCount = useMemo(() =>
    MOCK_CUSTOMERS.filter(c => c.churn_risk_level === 'high').length, [])

  // ── Biểu đồ: Aspect Sentiment (Bar chart) ────────────────
  const aspectData = useMemo(() => {
    const map = {}
    doneFeedbacks.forEach(f => {
      f.aspects.forEach(a => {
        if (!map[a.aspect]) map[a.aspect] = { pos: 0, neg: 0, neu: 0, count: 0, total: 0 }
        map[a.aspect].count++
        map[a.aspect].total += a.score
        if (a.sentiment === 'positive') map[a.aspect].pos++
        else if (a.sentiment === 'negative') map[a.aspect].neg++
        else map[a.aspect].neu++
      })
    })
    return Object.entries(map)
      .map(([key, val]) => ({
        aspect: key,
        label: ASPECT_LABELS[key] || key,
        icon: ASPECT_ICONS[key] || '❓',
        avgScore: val.count > 0 ? (val.total / val.count) : 0,
        positive: val.pos,
        negative: val.neg,
        neutral: val.neu,
        total: val.count
      }))
      .sort((a, b) => a.avgScore - b.avgScore) // Tiêu cực nhất ở trên
  }, [doneFeedbacks])

  // ── Biểu đồ: Phân bổ cảm xúc tổng quát (Pie chart) ──────
  const pieData = useMemo(() => {
    const pos = doneFeedbacks.filter(f => f.sentiment_score >= 0.3).length
    const neg = doneFeedbacks.filter(f => f.sentiment_score <= -0.3).length
    const neu = doneFeedbacks.length - pos - neg
    return [
      { name: 'Tích cực', value: pos, color: '#10B981' },
      { name: 'Trung lập', value: neu, color: '#6B7280' },
      { name: 'Tiêu cực', value: neg, color: '#EF4444' },
    ].filter(d => d.value > 0)
  }, [doneFeedbacks])

  // ── Feed: 5 phản hồi mới nhất ────────────────────────────
  const recentFeedbacks = useMemo(() =>
    [...MOCK_FEEDBACKS]
      .sort((a, b) => (b.timestamp?.seconds ?? 0) - (a.timestamp?.seconds ?? 0))
      .slice(0, 5), [])

  return (
    <div>
      {/* === KPI Cards === */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label">Phản hồi hôm nay</div>
          <div className="kpi-value">{todayFeedbacks.length}</div>
          <div className="kpi-sub">/ {doneFeedbacks.length} tổng tuần này</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Điểm cảm xúc TB</div>
          <div className="kpi-value" style={{ color: scoreToColor(avgSentiment) }}>
            {avgSentiment >= 0 ? '+' : ''}{avgSentiment.toFixed(2)}
          </div>
          <div className="kpi-sub">Thang điểm: -1.0 → +1.0</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Khách rủi ro cao</div>
          <div className="kpi-value" style={{ color: highRiskCount > 0 ? 'var(--color-danger)' : 'var(--color-success)' }}>
            {highRiskCount}
          </div>
          <div className="kpi-sub">P_churn &gt; 0.85 · cần chú ý</div>
        </div>

        <div className="kpi-card">
          <div className="kpi-label">Phát hiện mỉa mai</div>
          <div className="kpi-value" style={{ color: sarcasmCount > 0 ? 'var(--color-warning)' : 'var(--color-text-muted)' }}>
            {sarcasmCount}
          </div>
          <div className="kpi-sub">AI Fusion phát hiện sarcasm</div>
        </div>
      </div>

      {/* === Row 2: Charts === */}
      <div className="grid-2" style={{ marginBottom: 'var(--spacing-xl)' }}>

        {/* Aspect Sentiment Bar Chart */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">📊 Cảm xúc theo khía cạnh</span>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              {doneFeedbacks.length} phản hồi
            </span>
          </div>
          {aspectData.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📭</div>
              <p>Chưa có dữ liệu</p>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={aspectData} layout="vertical" margin={{ left: 10, right: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis
                  type="number" domain={[-1, 1]}
                  tick={{ fill: 'rgba(255,255,255,0.35)', fontSize: 11 }}
                  tickFormatter={v => v.toFixed(1)}
                />
                <YAxis
                  type="category" dataKey="label"
                  tick={{ fill: 'rgba(255,255,255,0.55)', fontSize: 11 }}
                  width={95}
                />
                <Tooltip
                  contentStyle={{ background: '#141720', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: 'rgba(255,255,255,0.9)', fontWeight: 700 }}
                  formatter={(val, name) => [val.toFixed(2), 'Điểm TB']}
                />
                <Bar dataKey="avgScore" radius={[0, 4, 4, 0]}>
                  {aspectData.map((entry, i) => (
                    <Cell key={i} fill={scoreToColor(entry.avgScore)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Sentiment Distribution Pie Chart */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">🎯 Phân bổ cảm xúc</span>
          </div>
          {pieData.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📭</div>
              <p>Chưa có dữ liệu</p>
            </div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={pieData} cx="50%" cy="50%"
                    outerRadius={80} innerRadius={45}
                    dataKey="value" paddingAngle={3}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={{ stroke: 'rgba(255,255,255,0.2)' }}
                  >
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: '#141720', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, fontSize: 12 }}
                    formatter={(val) => [`${val} phản hồi`]}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--spacing-md)', flexWrap: 'wrap' }}>
                {pieData.map(d => (
                  <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 'var(--font-size-xs)' }}>
                    <div style={{ width: 10, height: 10, borderRadius: 2, background: d.color }} />
                    <span style={{ color: 'var(--color-text-secondary)' }}>{d.name}: <strong>{d.value}</strong></span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* === Row 3: Recent Feedbacks Feed === */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">🔔 Phản hồi mới nhất</span>
          <a href="/feedbacks" style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-primary)', textDecoration: 'none' }}>
            Xem tất cả →
          </a>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
          {recentFeedbacks.map(fb => {
            const sl = sentimentLabel(fb.sentiment_score)
            return (
              <div key={fb.feedback_id} style={{
                display: 'flex', gap: 'var(--spacing-md)', alignItems: 'flex-start',
                padding: 'var(--spacing-md)', borderRadius: 'var(--radius-md)',
                background: 'rgba(255,255,255,0.025)',
                border: '1px solid var(--color-border)'
              }}>
                {/* Sentiment dot */}
                <div style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: scoreToColor(fb.sentiment_score),
                  marginTop: 6, flexShrink: 0
                }} />

                <div style={{ flex: 1, minWidth: 0 }}>
                  {/* Header */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', flexWrap: 'wrap', marginBottom: 6 }}>
                    <span className={`sentiment-badge sentiment-badge--${sl.cls}`}>
                      {sl.label} {fb.sentiment_score >= 0 ? '+' : ''}{fb.sentiment_score.toFixed(2)}
                    </span>
                    {fb.is_sarcasm && <span className="sarcasm-flag">⚠️ Mỉa mai</span>}
                    <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                      📍 {fb.location}
                    </span>
                    <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                      {fb.input_type === 'audio' ? '🎙️' : '✍️'} {timeAgo(fb.timestamp)}
                    </span>
                  </div>

                  {/* Transcript */}
                  <p style={{
                    fontSize: 'var(--font-size-sm)',
                    color: fb.processing_status === 'processing' ? 'var(--color-text-muted)' : 'var(--color-text-secondary)',
                    fontStyle: fb.processing_status === 'processing' ? 'italic' : 'normal',
                    marginBottom: fb.aspects.length ? 6 : 0
                  }}>
                    {fb.processing_status === 'processing'
                      ? '⏳ Đang phân tích...'
                      : fb.transcript
                        ? `"${fb.transcript}"`
                        : '(Không có transcript)'}
                  </p>

                  {/* Aspect chips */}
                  {fb.aspects.length > 0 && (
                    <div>
                      {fb.aspects.map((a, i) => (
                        <span key={i} className="aspect-chip">
                          {ASPECT_ICONS[a.aspect]} {ASPECT_LABELS[a.aspect]}
                          {' '}
                          <span style={{ color: scoreToColor(a.score) }}>
                            {a.sentiment === 'positive' ? '▲' : a.sentiment === 'negative' ? '▼' : '–'}
                          </span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
