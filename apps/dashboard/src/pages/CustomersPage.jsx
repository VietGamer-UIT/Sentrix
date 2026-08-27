import { useState, useMemo } from 'react'
import { useCustomers, useFeedbacks, timeAgo } from '../mocks/useFirestore.js'
import CustomerHistoryModal from '../components/CustomerHistoryModal.jsx'

/**
 * CustomersPage — Danh sách khách hàng + P_churn risk
 * Giai đoạn 6: Dùng useCustomers() + useFeedbacks() hooks — Firestore thật hoặc mock tùy env
 *
 * Collection: tenants/{tenant_id}/customers ORDER BY p_churn DESC
 * Fields: backend/db/schema.md §customers
 */

/**
 * Badge trạng thái ZNS.
 * zns_status: 'sent' = đã gửi ZNS thành công
 *             'budget_exceeded' = hết ngân sách ZNS hôm nay
 *             null + phone_masked = chưa gửi (high risk nhưng chưa trigger)
 *             null + !phone_masked = khách ẩn danh — không thể gửi ZNS
 */
function ZnsBadge({ customer }) {
  const { zns_sent_at, zns_voucher_code, zns_status, phone_masked, churn_risk_level } = customer

  if (zns_sent_at && zns_voucher_code) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        <span style={{
          display: 'inline-flex', alignItems: 'center', gap: 5,
          padding: '3px 9px', borderRadius: 20,
          background: 'rgba(0,182,155,0.10)', color: '#00B69B',
          border: '1px solid rgba(0,182,155,0.25)',
          fontSize: 'var(--font-size-xs)', fontWeight: 700,
        }}>
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
          Đã gửi ZNS
        </span>
        <span style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>
          {zns_voucher_code}
        </span>
      </div>
    )
  }

  if (zns_status === 'budget_exceeded') {
    return (
      <span style={{
        display: 'inline-flex', alignItems: 'center', gap: 5,
        padding: '3px 9px', borderRadius: 20,
        background: 'rgba(255,164,18,0.10)', color: '#FFA412',
        border: '1px solid rgba(255,164,18,0.25)',
        fontSize: 'var(--font-size-xs)', fontWeight: 700,
      }}>
        Hết ngân sách ZNS
      </span>
    )
  }

  if (!phone_masked) {
    return (
      <span style={{
        display: 'inline-flex', alignItems: 'center', gap: 5,
        padding: '3px 9px', borderRadius: 20,
        background: 'rgba(156,163,175,0.10)', color: '#9CA3AF',
        border: '1px solid rgba(156,163,175,0.2)',
        fontSize: 'var(--font-size-xs)', fontWeight: 600,
      }}>
        Khách ẩn danh
      </span>
    )
  }

  if (churn_risk_level === 'high') {
    return (
      <button
        className="btn btn--ghost"
        style={{ padding: '4px 10px', fontSize: '0.72rem' }}
        title="Gửi Tin nhắn Zalo — Giai đoạn 9"
      >
        Gửi ZNS
      </button>
    )
  }

  return <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>—</span>
}

function SkeletonTable() {
  return (
    <div>
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: 'var(--spacing-xl)' }}>
        {[1, 2, 3].map(i => <div key={i} className="kpi-card skeleton-box" style={{ height: 90 }} />)}
      </div>
      <div className="card skeleton-box" style={{ height: 400 }} />
    </div>
  )
}

export default function CustomersPage() {
  const { customers, loading: cuLoading, error: cuError } = useCustomers()
  const { feedbacks } = useFeedbacks()

  const [filterRisk, setFilterRisk] = useState('all')
  const [sortBy, setSortBy]         = useState('last_feedback_at')
  const [selectedCustomer, setSelectedCustomer] = useState(null)

  const riskStats = useMemo(() => ({
    high:   customers.filter(c => c.churn_risk_level === 'high').length,
    medium: customers.filter(c => c.churn_risk_level === 'medium').length,
    low:    customers.filter(c => c.churn_risk_level === 'low').length,
  }), [customers])

  const sorted = useMemo(() => {
    return [...customers]
      .filter(c => filterRisk === 'all' || c.churn_risk_level === filterRisk)
      .sort((a, b) => {
        if (sortBy === 'p_churn')          return (b.p_churn ?? 0) - (a.p_churn ?? 0)
        if (sortBy === 'feedback_count')   return (b.feedback_count ?? 0) - (a.feedback_count ?? 0)
        if (sortBy === 'last_feedback_at') return (b.last_feedback_at?.seconds ?? 0) - (a.last_feedback_at?.seconds ?? 0)
        return 0
      })
  }, [customers, filterRisk, sortBy])

  const selectStyle = {
    background: 'var(--color-bg-card)', border: '1px solid var(--color-border)',
    color: 'var(--color-text-secondary)', borderRadius: 'var(--radius-sm)',
    padding: '6px 10px', fontSize: 'var(--font-size-sm)', cursor: 'pointer',
    fontFamily: 'var(--font-family)'
  }

  if (cuLoading) return <SkeletonTable />

  if (cuError) return (
    <div style={{ padding: 'var(--spacing-xl)', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 'var(--radius-md)', color: 'var(--color-danger)' }}>
      <strong>Lỗi Firestore:</strong> {cuError}
    </div>
  )

  return (
    <div>
      {/* Risk Summary */}
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: 'var(--spacing-xl)' }}>
        {[
          { key: 'high',   color: 'var(--color-risk-high)',   label: 'Rủi ro cao',    sub: 'Nguy cơ > 85% — gửi ZNS ngay' },
          { key: 'medium', color: 'var(--color-risk-medium)', label: 'Rủi ro trung bình', sub: 'Nguy cơ 50–85% — theo dõi' },
          { key: 'low',    color: 'var(--color-risk-low)',    label: 'Rủi ro thấp',   sub: 'Nguy cơ < 50% — ổn định' },
        ].map(({ key, color, label, sub }) => (
          <div key={key} className="kpi-card"
            style={{ borderLeft: `3px solid ${color}`, cursor: 'pointer' }}
            onClick={() => setFilterRisk(filterRisk === key ? 'all' : key)}>
            <div className="kpi-label">{label}</div>
            <div className="kpi-value" style={{ color }}>{riskStats[key]}</div>
            <div className="kpi-sub">{sub}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 'var(--spacing-sm)', alignItems: 'center', marginBottom: 'var(--spacing-lg)', flexWrap: 'wrap' }}>
        <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>Lọc:</span>
        {['all', 'high', 'medium', 'low'].map(r => (
          <button key={r}
            className={`btn ${filterRisk === r ? 'btn--primary' : 'btn--ghost'}`}
            style={{ padding: '5px 12px' }}
            onClick={() => setFilterRisk(r)}>
            {r === 'all' ? 'Tất cả' : r === 'high' ? 'Cao' : r === 'medium' ? 'Trung bình' : 'Thấp'}
          </button>
        ))}
        <span style={{ marginLeft: 'auto', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>Sắp xếp:</span>
        <select value={sortBy} onChange={e => setSortBy(e.target.value)} style={selectStyle}>
          <option value="p_churn">Nguy cơ cao nhất</option>
          <option value="feedback_count">Nhiều feedback nhất</option>
          <option value="last_feedback_at">Gần đây nhất</option>
        </select>
      </div>

      {/* Table hoặc empty state */}
      {customers.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <img src="/sentrix-logo.png" alt="Sentrix" style={{ width: 72, opacity: 0.35, marginBottom: 'var(--spacing-md)' }} />
            <p>Chưa có khách hàng nào.<br/>
              <small style={{ color: 'var(--color-text-muted)' }}>Khi khách gửi phản hồi có kèm SĐT, hồ sơ sẽ xuất hiện ở đây.</small>
            </p>
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Số điện thoại</th>
                  <th>Rủi ro</th>
                  <th>Nguy cơ rời bỏ</th>
                  <th>Lòng trung thành</th>
                  <th>Feedback</th>
                  <th>Cảm xúc TB</th>
                  <th>Lần cuối</th>
                  <th>Trạng thái ZNS</th>
                </tr>
              </thead>
              <tbody>
                {sorted.length === 0 && (
                  <tr><td colSpan={8}>
                    <div className="empty-state"><p>Không có khách hàng nào trong mức rủi ro này</p></div>
                  </td></tr>
                )}
                {sorted.map(c => {
                  const pChurn = c.p_churn ?? 0
                  const avgSent = c.avg_sentiment_score ?? 0
                  const sentColor = avgSent >= 0.3 ? 'var(--color-positive)' : avgSent <= -0.3 ? 'var(--color-negative)' : 'var(--color-neutral-s)'
                  const riskColor = c.churn_risk_level === 'high' ? 'var(--color-danger)' : c.churn_risk_level === 'medium' ? 'var(--color-warning)' : 'var(--color-success)'

                  const rfmsScores = [
                    { key: 'R', val: c.rfms_r ?? 0 }, { key: 'F', val: c.rfms_f ?? 0 },
                    { key: 'M', val: c.rfms_m ?? 0 }, { key: 'S', val: c.rfms_s ?? 0 },
                  ]

                  return (
                    <tr key={c.customer_id} onClick={() => setSelectedCustomer(c)} style={{ cursor: 'pointer' }}>
                      <td>
                        <div style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
                          {c.phone_masked || 'Khách vãng lai'}
                        </div>
                      </td>
                      <td>
                        <span className={`risk-badge risk-badge--${c.churn_risk_level}`}>
                          {c.churn_risk_level === 'high' ? 'Cao' : c.churn_risk_level === 'medium' ? 'Trung bình' : 'Thấp'}
                        </span>
                      </td>
                      <td>
                        <div className="score-bar-wrap" style={{ minWidth: 100 }}>
                          <div className="score-bar-track">
                            <div className="score-bar-fill" style={{ width: `${pChurn * 100}%`, background: riskColor }} />
                          </div>
                          <span className="churn-pct" style={{ color: riskColor }}>{(pChurn * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 6 }}>
                          {rfmsScores.map(({ key, val }) => (
                            <div key={key} title={`${key}: ${(val * 100).toFixed(0)}%`} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                              <div style={{ width: 6, height: 28, background: `rgba(0,194,255,${val})`, borderRadius: 3, border: '1px solid rgba(0,194,255,0.2)' }} />
                              <span style={{ fontSize: '0.6rem', color: 'var(--color-text-muted)' }}>{key}</span>
                            </div>
                          ))}
                        </div>
                      </td>
                      <td style={{ textAlign: 'center', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                        {c.feedback_count ?? 0}
                      </td>
                      <td>
                        <span style={{ color: sentColor, fontWeight: 700, fontSize: 'var(--font-size-sm)' }}>
                          {avgSent >= 0 ? '+' : ''}{avgSent.toFixed(2)}
                        </span>
                      </td>
                      <td style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>
                        {timeAgo(c.last_feedback_at)}
                      </td>
                      <td onClick={e => e.stopPropagation()}>
                        <ZnsBadge customer={c} />
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {selectedCustomer && (
        <CustomerHistoryModal
          customer={selectedCustomer}
          feedbacks={feedbacks}
          onClose={() => setSelectedCustomer(null)}
        />
      )}
    </div>
  )
}
