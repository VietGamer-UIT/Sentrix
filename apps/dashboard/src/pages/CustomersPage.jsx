import { useState, useMemo } from 'react'
import { MOCK_CUSTOMERS, MOCK_FEEDBACKS, timeAgo } from '../mocks/firestoreMock.js'

/**
 * CustomersPage — Danh sách khách hàng + P_churn risk
 *
 * Đọc: tenants/{tenant_id}/customers
 *   orderBy: p_churn DESC (mặc định — khách rủi ro cao nhất lên đầu)
 *   filter: churn_risk_level == "high" nếu bật filter
 *
 * Field names từ backend/db/schema.md §customers
 */
export default function CustomersPage() {
  const [filterRisk, setFilterRisk] = useState('all')
  const [sortBy, setSortBy] = useState('p_churn') // p_churn | last_feedback_at | feedback_count

  const sorted = useMemo(() => {
    return [...MOCK_CUSTOMERS]
      .filter(c => filterRisk === 'all' || c.churn_risk_level === filterRisk)
      .sort((a, b) => {
        if (sortBy === 'p_churn') return b.p_churn - a.p_churn
        if (sortBy === 'feedback_count') return b.feedback_count - a.feedback_count
        if (sortBy === 'last_feedback_at') return (b.last_feedback_at?.seconds ?? 0) - (a.last_feedback_at?.seconds ?? 0)
        return 0
      })
  }, [filterRisk, sortBy])

  // Lấy số feedbacks gần nhất của mỗi customer
  const customerFeedbackCounts = useMemo(() => {
    const map = {}
    MOCK_FEEDBACKS.forEach(f => {
      map[f.customer_id] = (map[f.customer_id] || 0) + 1
    })
    return map
  }, [])

  const riskStats = useMemo(() => ({
    high: MOCK_CUSTOMERS.filter(c => c.churn_risk_level === 'high').length,
    medium: MOCK_CUSTOMERS.filter(c => c.churn_risk_level === 'medium').length,
    low: MOCK_CUSTOMERS.filter(c => c.churn_risk_level === 'low').length,
  }), [])

  const selectStyle = {
    background: 'var(--color-bg-card)', border: '1px solid var(--color-border)',
    color: 'var(--color-text-secondary)', borderRadius: 'var(--radius-sm)',
    padding: '6px 10px', fontSize: 'var(--font-size-sm)', cursor: 'pointer',
    fontFamily: 'var(--font-family)'
  }

  return (
    <div>
      {/* Risk Summary KPI row */}
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', marginBottom: 'var(--spacing-xl)' }}>
        <div className="kpi-card" style={{ borderLeft: '3px solid var(--color-risk-high)', cursor: 'pointer' }}
          onClick={() => setFilterRisk(filterRisk === 'high' ? 'all' : 'high')}>
          <div className="kpi-label">Rủi ro cao</div>
          <div className="kpi-value" style={{ color: 'var(--color-risk-high)' }}>{riskStats.high}</div>
          <div className="kpi-sub">P_churn &gt; 0.85 — cần ZNS ngay</div>
        </div>
        <div className="kpi-card" style={{ borderLeft: '3px solid var(--color-risk-medium)', cursor: 'pointer' }}
          onClick={() => setFilterRisk(filterRisk === 'medium' ? 'all' : 'medium')}>
          <div className="kpi-label">Rủi ro trung bình</div>
          <div className="kpi-value" style={{ color: 'var(--color-risk-medium)' }}>{riskStats.medium}</div>
          <div className="kpi-sub">P_churn 0.50 – 0.85 — theo dõi</div>
        </div>
        <div className="kpi-card" style={{ borderLeft: '3px solid var(--color-risk-low)', cursor: 'pointer' }}
          onClick={() => setFilterRisk(filterRisk === 'low' ? 'all' : 'low')}>
          <div className="kpi-label">Rủi ro thấp</div>
          <div className="kpi-value" style={{ color: 'var(--color-risk-low)' }}>{riskStats.low}</div>
          <div className="kpi-sub">P_churn &lt; 0.50 — ổn định</div>
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 'var(--spacing-sm)', alignItems: 'center', marginBottom: 'var(--spacing-lg)' }}>
        <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>Lọc:</span>
        {['all', 'high', 'medium', 'low'].map(r => (
          <button key={r}
            className={`btn ${filterRisk === r ? 'btn--primary' : 'btn--ghost'}`}
            style={{ padding: '5px 12px' }}
            onClick={() => setFilterRisk(r)}
          >
            {r === 'all' ? 'Tất cả' : r === 'high' ? '🔴 Cao' : r === 'medium' ? '🟡 TB' : '🟢 Thấp'}
          </button>
        ))}
        <span style={{ marginLeft: 'auto', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
          Sắp xếp:
        </span>
        <select value={sortBy} onChange={e => setSortBy(e.target.value)} style={selectStyle}>
          <option value="p_churn">P_churn cao nhất</option>
          <option value="feedback_count">Nhiều feedback nhất</option>
          <option value="last_feedback_at">Gần đây nhất</option>
        </select>
      </div>

      {/* Customers Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>SĐT (masked)</th>
                <th>Rủi ro</th>
                <th>P_churn</th>
                <th>RFMS</th>
                <th>Feedback</th>
                <th>Cảm xúc TB</th>
                <th>Lần cuối</th>
                <th>ZNS</th>
              </tr>
            </thead>
            <tbody>
              {sorted.length === 0 && (
                <tr><td colSpan={8}>
                  <div className="empty-state">
                    <div className="empty-state-icon">👥</div>
                    <p>Không có khách hàng nào trong danh mục này</p>
                  </div>
                </td></tr>
              )}
              {sorted.map(c => {
                const sentColor = c.avg_sentiment_score >= 0.3 ? 'var(--color-positive)'
                  : c.avg_sentiment_score <= -0.3 ? 'var(--color-negative)' : 'var(--color-neutral-s)'
                const rfmsScores = [
                  { key: 'R', val: c.rfms_r, label: 'Recency' },
                  { key: 'F', val: c.rfms_f, label: 'Frequency' },
                  { key: 'M', val: c.rfms_m, label: 'Monetary' },
                  { key: 'S', val: c.rfms_s, label: 'Sentiment' },
                ]

                return (
                  <tr key={c.customer_id}>
                    <td>
                      <div style={{ fontWeight: 600, fontSize: 'var(--font-size-sm)', color: 'var(--color-text-primary)' }}>
                        {c.phone_masked}
                      </div>
                      <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                        {c.customer_id.slice(0, 18)}...
                      </div>
                    </td>
                    <td>
                      <span className={`risk-badge risk-badge--${c.churn_risk_level}`}>
                        {c.churn_risk_level === 'high' ? '🔴 Cao' : c.churn_risk_level === 'medium' ? '🟡 TB' : '🟢 Thấp'}
                      </span>
                    </td>
                    <td>
                      <div className="score-bar-wrap" style={{ minWidth: 100 }}>
                        <div className="score-bar-track">
                          <div className="score-bar-fill" style={{
                            width: `${c.p_churn * 100}%`,
                            background: c.churn_risk_level === 'high' ? 'var(--color-danger)'
                              : c.churn_risk_level === 'medium' ? 'var(--color-warning)' : 'var(--color-success)'
                          }} />
                        </div>
                        <span className="churn-pct" style={{
                          color: c.churn_risk_level === 'high' ? 'var(--color-danger)'
                            : c.churn_risk_level === 'medium' ? 'var(--color-warning)' : 'var(--color-success)'
                        }}>
                          {(c.p_churn * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 6 }}>
                        {rfmsScores.map(({ key, val, label }) => (
                          <div key={key} title={`${label}: ${(val * 100).toFixed(0)}%`}
                            style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                            <div style={{
                              width: 6, height: 28,
                              background: `rgba(0,194,255,${val})`,
                              borderRadius: 3,
                              border: '1px solid rgba(0,194,255,0.2)'
                            }} />
                            <span style={{ fontSize: '0.6rem', color: 'var(--color-text-muted)' }}>{key}</span>
                          </div>
                        ))}
                      </div>
                    </td>
                    <td style={{ textAlign: 'center', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                      {c.feedback_count}
                    </td>
                    <td>
                      <span style={{ color: sentColor, fontWeight: 700, fontSize: 'var(--font-size-sm)' }}>
                        {c.avg_sentiment_score >= 0 ? '+' : ''}{c.avg_sentiment_score.toFixed(2)}
                      </span>
                    </td>
                    <td style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>
                      {timeAgo(c.last_feedback_at)}
                    </td>
                    <td>
                      {c.churn_risk_level === 'high' ? (
                        <button className="btn btn--ghost" style={{ padding: '4px 10px', fontSize: '0.72rem' }}
                          title="Gửi Zalo ZNS cảnh báo — chức năng Giai đoạn 9">
                          📨 Gửi ZNS
                        </button>
                      ) : (
                        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>—</span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
