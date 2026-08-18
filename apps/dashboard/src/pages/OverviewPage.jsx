import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, PieChart, Pie
} from 'recharts'
import { useFeedbacks, useCustomers, timeAgo, tsToDate } from '../mocks/useFirestore.js'

/**
 * OverviewPage — Tổng quan realtime
 *
 * Giai đoạn 6: Dùng useFeedbacks() + useCustomers() thay vì import mock trực tiếp.
 * Hook tự động switch giữa Firestore thật và mock tùy VITE_USE_MOCK_FIRESTORE.
 *
 * Collections (backend/db/schema.md):
 *   tenants/{tenant_id}/feedbacks   — onSnapshot realtime
 *   tenants/{tenant_id}/customers   — onSnapshot realtime
 */

const ASPECT_LABELS = {
  nhan_vien: 'Nhân viên', mon_an: 'Món ăn', khong_gian: 'Không gian',
  gia_ca: 'Giá cả', toc_do_phuc_vu: 'Tốc độ PV', ve_sinh: 'Vệ sinh', khac: 'Khác'
}

const ASPECT_ICONS = {
  nhan_vien: '👩‍🍳', mon_an: '🍲', khong_gian: '🏪',
  gia_ca: '💰', toc_do_phuc_vu: '⚡', ve_sinh: '✨', khac: '📌'
}

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
  const { feedbacks, loading: fbLoading, error: fbError } = useFeedbacks()
  const { customers, loading: cuLoading }                  = useCustomers()

  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const doneFeedbacks = useMemo(() =>
    feedbacks.filter(f => f.processing_status === 'done' && !f.is_suspicious), [feedbacks])

  const todayFeedbacks = useMemo(() =>
    doneFeedbacks.filter(f => tsToDate(f.timestamp) >= today), [doneFeedbacks])

  const avgSentiment = useMemo(() => {
    if (!doneFeedbacks.length) return 0
    return doneFeedbacks.reduce((s, f) => s + (f.sentiment_score ?? 0), 0) / doneFeedbacks.length
  }, [doneFeedbacks])

  const sarcasmCount = useMemo(() =>
    doneFeedbacks.filter(f => f.is_sarcasm).length, [doneFeedbacks])

  const highRiskCount = useMemo(() =>
    customers.filter(c => c.churn_risk_level === 'high').length, [customers])

  const aspectData = useMemo(() => {
    const map = {}
    doneFeedbacks.forEach(f => {
      (f.aspects || []).forEach(a => {
        // Backend mới lưu: category (enum) + sentiment_en + score
        // Mock cũ dùng: aspect (enum) + sentiment (en) + score
        const cat  = a.category || a.aspect || 'khac'
        const sent = a.sentiment_en || (a.sentiment === 'Tích cực' ? 'positive' : a.sentiment === 'Tiêu cực' ? 'negative' : a.sentiment) || 'neutral'
        const sc   = typeof a.score === 'number' ? a.score : (sent === 'positive' ? 1 : sent === 'negative' ? -1 : 0)
        if (!map[cat]) map[cat] = { pos: 0, neg: 0, neu: 0, count: 0, total: 0 }
        map[cat].count++
        map[cat].total += sc
        if (sent === 'positive') map[cat].pos++
        else if (sent === 'negative') map[cat].neg++
        else map[cat].neu++
      })
    })
    return Object.entries(map)
      .map(([key, val]) => ({
        aspect: key, label: ASPECT_LABELS[key] || key, icon: ASPECT_ICONS[key] || '❓',
        avgScore: val.count > 0 ? val.total / val.count : 0,
        positive: val.pos, negative: val.neg, neutral: val.neu, total: val.count
      }))
      .sort((a, b) => a.avgScore - b.avgScore)
  }, [doneFeedbacks])

  const pieData = useMemo(() => {
    const pos = doneFeedbacks.filter(f => (f.sentiment_score ?? 0) >= 0.3).length
    const neg = doneFeedbacks.filter(f => (f.sentiment_score ?? 0) <= -0.3).length
    return [
      { name: 'Tích cực', value: pos, color: '#10B981' },
      { name: 'Trung lập', value: doneFeedbacks.length - pos - neg, color: '#6B7280' },
      { name: 'Tiêu cực', value: neg, color: '#EF4444' },
    ].filter(d => d.value > 0)
  }, [doneFeedbacks])

  const recentFeedbacks = useMemo(() =>
    [...feedbacks]
      .sort((a, b) => (b.timestamp?.seconds ?? 0) - (a.timestamp?.seconds ?? 0))
      .slice(0, 5), [feedbacks])

  // Loading / Error states
  if (fbLoading || cuLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 'var(--spacing-2xl)', color: 'var(--color-text-muted)' }}>
        <div style={{ fontSize: '2rem', marginBottom: 'var(--spacing-md)' }}>⏳</div>
        <p>Đang tải dữ liệu từ Firestore...</p>
      </div>
    )
  }
  if (fbError) {
    return (
      <div style={{
        padding: 'var(--spacing-xl)', background: 'rgba(239,68,68,0.08)',
        border: '1px solid rgba(239,68,68,0.2)', borderRadius: 'var(--radius-md)',
        color: 'var(--color-danger)', marginBottom: 'var(--spacing-lg)'
      }}>
        <strong>⚠️ Lỗi kết nối Firestore:</strong> {fbError}<br/>
        <small style={{ color: 'var(--color-text-muted)', marginTop: 8, display: 'block' }}>
          Kiểm tra Firebase Security Rules và credentials trong .env
        </small>
      </div>
    )
  }

  return (
    <div>
      {/* KPI Cards */}
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
          <div className="kpi-sub">Nguy cơ &gt; 85% · cần chú ý</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Phát hiện mỉa mai</div>
          <div className="kpi-value" style={{ color: sarcasmCount > 0 ? 'var(--color-warning)' : 'var(--color-text-muted)' }}>
            {sarcasmCount}
          </div>
          <div className="kpi-sub">AI phát hiện mỉa mai</div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid-2" style={{ marginBottom: 'var(--spacing-xl)' }}>
        <div className="card">
          <div className="card-header">
            <span className="card-title">Cảm xúc theo khía cạnh</span>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              {doneFeedbacks.length} phản hồi
            </span>
          </div>
          {aspectData.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📭</div>
              <p>Chưa có dữ liệu phân tích</p>
            </div>
          ) : (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={aspectData} layout="vertical" margin={{ left: 10, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" />
                  <XAxis type="number" domain={[-1, 1]} tick={{ fill: 'var(--color-text-muted)', fontSize: 11 }} tickFormatter={v => v.toFixed(1)} />
                  <YAxis type="category" dataKey="label" tick={{ fill: 'var(--color-text-secondary)', fontSize: 11 }} width={95} />
                  <Tooltip
                    contentStyle={{ background: '#FFFFFF', border: '1px solid var(--color-border)', borderRadius: 8, fontSize: 12, boxShadow: '0 4px 16px rgba(0,0,0,0.1)' }}
                    labelStyle={{ color: 'var(--color-text-primary)', fontWeight: 700 }}
                    formatter={(val) => [val.toFixed(2), 'Điểm TB']}
                  />
                  <Bar dataKey="avgScore" radius={[0, 4, 4, 0]}>
                    {aspectData.map((entry, i) => <Cell key={i} fill={scoreToColor(entry.avgScore)} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
          )}
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title">Phân bổ cảm xúc</span></div>
          {pieData.length === 0 ? (
            <div className="empty-state"><div className="empty-state-icon">📭</div><p>Chưa có dữ liệu</p></div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" outerRadius={65} innerRadius={40} dataKey="value" paddingAngle={3}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    labelLine={{ stroke: 'rgba(0,0,0,0.15)' }}>
                    {pieData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#FFFFFF', border: '1px solid var(--color-border)', borderRadius: 8, fontSize: 12, boxShadow: '0 4px 16px rgba(0,0,0,0.1)' }} formatter={(val) => [`${val} phản hồi`]} />
                </PieChart>
              </ResponsiveContainer>
              <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--spacing-md)', flexWrap: 'wrap' }}>
                {pieData.map(d => (
                  <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 'var(--font-size-xs)' }}>
                    <div style={{ width: 10, height: 10, borderRadius: 2, background: d.color }} />
                    <span style={{ color: 'var(--color-text-secondary)', fontWeight: 600 }}>{d.name}: <strong style={{ color: 'var(--color-text-primary)' }}>{d.value}</strong></span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Recent Feedbacks */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Phản hồi mới nhất</span>
          <Link to="/feedbacks" style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-primary)', textDecoration: 'none' }}>Xem tất cả</Link>
        </div>
        {recentFeedbacks.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📭</div>
            <p>Chưa có phản hồi nào. Khách hàng quét QR để bắt đầu.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
            {recentFeedbacks.map(fb => {
              const sl = sentimentLabel(fb.sentiment_score ?? 0)
              return (
                  <div key={fb.feedback_id} style={{
                    display: 'flex', gap: 'var(--spacing-md)', alignItems: 'flex-start',
                    padding: 'var(--spacing-md)', borderRadius: 'var(--radius-md)',
                    background: '#FAFBFF', border: '1px solid var(--color-border)'
                  }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: scoreToColor(fb.sentiment_score ?? 0), marginTop: 6, flexShrink: 0 }} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-sm)', flexWrap: 'wrap', marginBottom: 6 }}>
                      <span className={`sentiment-badge sentiment-badge--${sl.cls}`}>
                        {sl.label} {(fb.sentiment_score ?? 0) >= 0 ? '+' : ''}{(fb.sentiment_score ?? 0).toFixed(2)}
                      </span>
                      {fb.is_sarcasm && <span className="sarcasm-flag">⚠️ Mỉa mai</span>}
                      <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>{fb.location}</span>
                      <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                        {fb.input_type === 'audio' ? 'Ghi âm' : 'Văn bản'} · {timeAgo(fb.timestamp)}
                      </span>
                    </div>
                    <p style={{ fontSize: 'var(--font-size-sm)', color: fb.processing_status === 'processing' ? 'var(--color-text-muted)' : 'var(--color-text-secondary)', fontStyle: fb.processing_status === 'processing' ? 'italic' : 'normal', marginBottom: (fb.aspects?.length) ? 6 : 0 }}>
                      {fb.processing_status === 'processing' ? '⏳ Đang phân tích...' : fb.transcript ? `"${fb.transcript}"` : '(Không có transcript)'}
                    </p>
                    {(fb.aspects?.length > 0) && (
                      <div>
                        {(fb.aspects || []).map((a, i) => {
                          const cat  = a.category || a.aspect || 'khac'
                          const sent = a.sentiment_en || (a.sentiment === 'Tích cực' ? 'positive' : a.sentiment === 'Tiêu cực' ? 'negative' : a.sentiment) || 'neutral'
                          const sc   = typeof a.score === 'number' ? a.score : (sent === 'positive' ? 1 : sent === 'negative' ? -1 : 0)
                          return (
                            <span key={i} className="aspect-chip">
                              {ASPECT_LABELS[cat] || cat}
                              {' '}<span style={{ color: scoreToColor(sc) }}>{sent === 'positive' ? '▲' : sent === 'negative' ? '▼' : '–'}</span>
                            </span>
                          )
                        })}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
