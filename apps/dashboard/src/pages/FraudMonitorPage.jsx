import { useMemo, useState } from 'react'
import { useFeedbacks, timeAgo, tsToDate, IS_MOCK } from '../mocks/useFirestore.js'
import { isToday, isThisWeek } from 'date-fns'

/**
 * FraudMonitorPage — Giám Sát Chống Gian Lận
 * =============================================
 * Author: Đoàn Hoàng Việt (Việt Gamer)
 *
 * Hiển thị bằng chứng trực quan cơ chế chống gian lận 3 lớp đang chạy:
 *   Lớp 1 (invalid_short_audio / invalid_low_snr): Chất lượng audio kém
 *   Lớp 2 (rate_limited):                          Gửi quá nhiều lần
 *   Lớp 3 (invalid_semantic):                      Nội dung vô nghĩa / spam
 *   Lớp 4 (suspicious): Phát hiện bất thường khác (is_suspicious=true)
 *
 * Dữ liệu: filter từ useFeedbacks() hook đã có — không query Firestore mới
 */

// Map validity_status → metadata
const LAYER_META = {
  invalid_short_audio: { lop: 1, label: 'Audio quá ngắn',       color: '#FFA412', textColor: '#fff', icon: '🎙️' },
  invalid_low_snr:     { lop: 1, label: 'Nhiễu âm thanh',       color: '#FFA412', textColor: '#fff', icon: '📡' },
  rate_limited:        { lop: 2, label: 'Vượt tần suất gửi',    color: '#EF4444', textColor: '#fff', icon: '🚫' },
  invalid_semantic:    { lop: 3, label: 'Nội dung vô nghĩa',    color: '#8B5CF6', textColor: '#fff', icon: '🤖' },
  valid:               { lop: null, label: 'Hợp lệ',            color: '#00B69B', textColor: '#fff', icon: '✅' },
}

function getLayerMeta(f) {
  if (f.is_suspicious && f.validity_status === 'valid') {
    return { lop: 4, label: 'Bất thường', color: '#EF4444', textColor: '#fff', icon: '⚠️' }
  }
  return LAYER_META[f.validity_status] || { lop: null, label: f.validity_status || 'Không rõ', color: '#9CA3AF', textColor: '#fff', icon: '❓' }
}

function LayerBadge({ meta }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      background: meta.color + '18',
      color: meta.color,
      border: `1px solid ${meta.color}40`,
      borderRadius: 6, padding: '2px 8px',
      fontSize: 'var(--font-size-xs)', fontWeight: 700,
      whiteSpace: 'nowrap',
    }}>
      {meta.icon} {meta.lop ? `Lớp ${meta.lop}` : ''} {meta.label}
    </span>
  )
}

function StatCard({ label, value, sub, color }) {
  return (
    <div className="kpi-card glass-card" style={{ minHeight: 90 }}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value" style={{ color: color || 'var(--color-text-primary)' }}>
        {value}
      </div>
      {sub && <div className="kpi-sub" style={{ color: 'var(--color-text-muted)' }}>{sub}</div>}
    </div>
  )
}

export default function FraudMonitorPage() {
  const { feedbacks, loading, error } = useFeedbacks()
  const [layerFilter, setLayerFilter] = useState('all')

  // Tất cả các lượt bị chặn hoặc đánh dấu bất thường
  const blockedAll = useMemo(() =>
    feedbacks.filter(f =>
      f.validity_status !== 'valid' || f.is_suspicious
    ), [feedbacks])

  const blockedToday = useMemo(() =>
    blockedAll.filter(f => isToday(tsToDate(f.timestamp))), [blockedAll])

  const blockedWeek = useMemo(() =>
    blockedAll.filter(f => isThisWeek(tsToDate(f.timestamp), { weekStartsOn: 1 })), [blockedAll])

  // Breakdown theo lớp (toàn thời gian)
  const byLayer = useMemo(() => {
    const counts = { 1: 0, 2: 0, 3: 0, 4: 0 }
    blockedAll.forEach(f => {
      const meta = getLayerMeta(f)
      if (meta.lop) counts[meta.lop] = (counts[meta.lop] || 0) + 1
    })
    return counts
  }, [blockedAll])

  // Bảng chi tiết — filter theo lớp nếu cần
  const tableRows = useMemo(() => {
    return [...blockedAll]
      .sort((a, b) => (b.timestamp?.seconds ?? 0) - (a.timestamp?.seconds ?? 0))
      .filter(f => {
        if (layerFilter === 'all') return true
        const meta = getLayerMeta(f)
        return String(meta.lop) === layerFilter
      })
      .slice(0, 50)
  }, [blockedAll, layerFilter])

  if (loading) {
    return (
      <div>
        <div className="kpi-grid">
          {[1,2,3,4].map(i => <div key={i} className="kpi-card skeleton-box" style={{ height: 90 }} />)}
        </div>
        <div className="card skeleton-box" style={{ height: 400 }} />
      </div>
    )
  }

  if (error) {
    return (
      <div style={{
        padding: 'var(--spacing-xl)', background: 'rgba(239,68,68,0.08)',
        border: '1px solid rgba(239,68,68,0.2)', borderRadius: 'var(--radius-md)',
        color: 'var(--color-danger)'
      }}>
        <strong>⚠️ Lỗi kết nối Firestore:</strong> {error}
      </div>
    )
  }

  return (
    <div>
      {/* Page Header */}
      <div style={{ marginBottom: 'var(--spacing-lg)' }}>
        <h2 style={{
          fontSize: 'var(--font-size-lg)', fontWeight: 800,
          color: 'var(--color-text-primary)', margin: 0
        }}>
          🛡️ Giám Sát Chống Gian Lận
        </h2>
        <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)', marginTop: 4 }}>
          Theo dõi realtime các lượt phản hồi bị lọc bởi hệ thống Anti-Fraud 3 lớp
          {IS_MOCK && <span style={{ color: 'var(--color-warning)', marginLeft: 8 }}>• Demo Data</span>}
        </p>
      </div>

      {/* KPI Cards — 4 thẻ số liệu */}
      <div className="kpi-grid" style={{ marginBottom: 'var(--spacing-xl)' }}>
        <StatCard
          label="Bị chặn hôm nay"
          value={blockedToday.length}
          sub={`/ ${feedbacks.filter(f => isToday(tsToDate(f.timestamp))).length} tổng lượt`}
          color="var(--color-danger)"
        />
        <StatCard
          label="Bị chặn tuần này"
          value={blockedWeek.length}
          color="var(--color-warning)"
        />
        <StatCard
          label="Lớp 1 — Audio"
          value={byLayer[1] || 0}
          sub="Audio ngắn / nhiễu cao"
          color="#FFA412"
        />
        <StatCard
          label="Lớp 2+3 — Logic/NLP"
          value={(byLayer[2] || 0) + (byLayer[3] || 0)}
          sub={`Rate-limit: ${byLayer[2]||0} • Semantic: ${byLayer[3]||0}`}
          color="#EF4444"
        />
      </div>

      {/* Breakdown theo lớp — bar visual */}
      <div className="card glass-card" style={{ marginBottom: 'var(--spacing-xl)' }}>
        <div className="card-header" style={{ padding: 'var(--spacing-md) var(--spacing-lg)', borderBottom: '1px solid var(--color-border)' }}>
          <span style={{ fontWeight: 700, color: 'var(--color-text-primary)' }}>
            Phân tích theo Lớp Chặn
          </span>
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginLeft: 8 }}>
            toàn thời gian · {blockedAll.length} lượt
          </span>
        </div>
        <div style={{ padding: 'var(--spacing-lg)', display: 'flex', flexDirection: 'column', gap: 14 }}>
          {[
            { lop: 1, label: 'Lớp 1 — Chất lượng Audio (SNR/thời lượng)', color: '#FFA412', count: byLayer[1] || 0 },
            { lop: 2, label: 'Lớp 2 — Rate Limiting (tần suất)',            color: '#EF4444', count: byLayer[2] || 0 },
            { lop: 3, label: 'Lớp 3 — Semantic Validity (LLM)',             color: '#8B5CF6', count: byLayer[3] || 0 },
            { lop: 4, label: 'Lớp 4 — Bất thường khác',                    color: '#6B7280', count: byLayer[4] || 0 },
          ].map(row => {
            const total = blockedAll.length || 1
            const pct = Math.round((row.count / total) * 100)
            return (
              <div key={row.lop}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', fontWeight: 600 }}>
                    {row.label}
                  </span>
                  <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 700, color: row.color }}>
                    {row.count} ({pct}%)
                  </span>
                </div>
                <div style={{
                  height: 8, background: 'var(--color-border)', borderRadius: 99, overflow: 'hidden'
                }}>
                  <div style={{
                    height: '100%', width: `${pct}%`, background: row.color,
                    borderRadius: 99, transition: 'width 0.6s ease',
                    minWidth: row.count > 0 ? 4 : 0,
                  }} />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Bảng chi tiết */}
      <div className="card glass-card">
        <div className="card-header" style={{
          padding: 'var(--spacing-md) var(--spacing-lg)',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap',
        }}>
          <span style={{ fontWeight: 700, color: 'var(--color-text-primary)' }}>
            Lượt bị đánh dấu gần nhất
          </span>
          {/* Filter theo lớp */}
          <div style={{ display: 'flex', gap: 6 }}>
            {[
              { v: 'all', label: 'Tất cả' },
              { v: '1',   label: 'Lớp 1' },
              { v: '2',   label: 'Lớp 2' },
              { v: '3',   label: 'Lớp 3' },
              { v: '4',   label: 'Lớp 4' },
            ].map(opt => (
              <button
                key={opt.v}
                onClick={() => setLayerFilter(opt.v)}
                style={{
                  padding: '4px 12px', border: '1px solid var(--color-border)',
                  borderRadius: 6, cursor: 'pointer', fontSize: 'var(--font-size-xs)',
                  fontWeight: layerFilter === opt.v ? 700 : 400,
                  background: layerFilter === opt.v ? 'var(--color-primary)' : 'transparent',
                  color: layerFilter === opt.v ? '#fff' : 'var(--color-text-muted)',
                  transition: 'var(--transition)',
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          {tableRows.length === 0 ? (
            <div style={{ padding: 'var(--spacing-xl)', textAlign: 'center', color: 'var(--color-text-muted)' }}>
              ✅ Không có lượt bị chặn {layerFilter !== 'all' ? `ở Lớp ${layerFilter}` : ''} trong bộ nhớ hiện tại
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'var(--color-bg)', borderBottom: '1px solid var(--color-border)' }}>
                  {['Thời gian', 'Vị trí', 'Loại', 'SĐT (mask)', 'Lý do chặn', 'Lớp'].map(h => (
                    <th key={h} style={{
                      padding: '10px 16px', textAlign: 'left',
                      fontSize: 'var(--font-size-xs)', fontWeight: 700,
                      color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em',
                      whiteSpace: 'nowrap',
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {tableRows.map((f, i) => {
                  const meta = getLayerMeta(f)
                  return (
                    <tr key={f.feedback_id || i} style={{
                      borderBottom: '1px solid var(--color-border)',
                      background: i % 2 === 0 ? 'transparent' : 'var(--color-bg)',
                    }}>
                      <td style={{ padding: '10px 16px', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>
                        {timeAgo(f.timestamp)}
                      </td>
                      <td style={{ padding: '10px 16px', fontSize: 'var(--font-size-sm)' }}>
                        {f.location || '—'}
                      </td>
                      <td style={{ padding: '10px 16px', fontSize: 'var(--font-size-sm)' }}>
                        <span style={{
                          padding: '2px 8px', borderRadius: 4,
                          background: f.input_type === 'audio' ? 'rgba(6,136,166,0.1)' : 'rgba(107,114,128,0.1)',
                          color: f.input_type === 'audio' ? 'var(--color-primary)' : 'var(--color-text-muted)',
                          fontSize: 'var(--font-size-xs)', fontWeight: 600,
                        }}>
                          {f.input_type === 'audio' ? '🎙 Audio' : '✏️ Text'}
                        </span>
                      </td>
                      <td style={{ padding: '10px 16px', fontSize: 'var(--font-size-sm)', fontFamily: 'monospace', color: 'var(--color-text-secondary)' }}>
                        {f.phone_masked || '—'}
                      </td>
                      <td style={{ padding: '10px 16px' }}>
                        <LayerBadge meta={meta} />
                      </td>
                      <td style={{ padding: '10px 16px', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
                        {meta.lop ? `Lớp ${meta.lop}` : '—'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>

        {tableRows.length >= 50 && (
          <div style={{ padding: 'var(--spacing-md) var(--spacing-lg)', borderTop: '1px solid var(--color-border)', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)', textAlign: 'center' }}>
            Hiển thị 50 lượt gần nhất — xuất CSV để xem đầy đủ
          </div>
        )}
      </div>
    </div>
  )
}
