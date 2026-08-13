import { useState, useMemo } from 'react'
import { useFeedbacks, timeAgo } from '../mocks/useFirestore.js'

const ASPECT_LABELS = {
  nhan_vien: 'Nhân viên', mon_an: 'Món ăn',
  khong_gian: 'Không gian', gia_ca: 'Giá cả',
  toc_do_phuc_vu: 'Tốc độ', ve_sinh: 'Vệ sinh', khac: 'Khác'
}

function scoreToColor(s) {
  return s >= 0.3 ? 'var(--color-positive)' : s <= -0.3 ? 'var(--color-negative)' : 'var(--color-neutral-s)'
}

/**
 * FeedbacksPage — Bảng toàn bộ phản hồi có filter
 * Giai đoạn 6: Dùng useFeedbacks() hook — Firestore thật hoặc mock tùy env
 */
export default function FeedbacksPage() {
  const { feedbacks, loading, error } = useFeedbacks()
  const [filterSentiment, setFilterSentiment] = useState('all')
  const [filterLocation, setFilterLocation]   = useState('all')
  const [filterType, setFilterType]           = useState('all')
  const [search, setSearch]                   = useState('')

  const LOCATIONS = useMemo(() =>
    [...new Set(feedbacks.map(f => f.location).filter(Boolean))], [feedbacks])

  const filtered = useMemo(() => {
    return [...feedbacks]
      .sort((a, b) => (b.timestamp?.seconds ?? 0) - (a.timestamp?.seconds ?? 0))
      .filter(f => {
        const score = f.sentiment_score ?? 0
        if (filterSentiment === 'positive' && score < 0.3) return false
        if (filterSentiment === 'negative' && score > -0.3) return false
        if (filterSentiment === 'neutral' && (score <= -0.3 || score >= 0.3)) return false
        if (filterLocation !== 'all' && f.location !== filterLocation) return false
        if (filterType !== 'all' && f.input_type !== filterType) return false
        if (search && !f.transcript?.toLowerCase().includes(search.toLowerCase())) return false
        return true
      })
  }, [feedbacks, filterSentiment, filterLocation, filterType, search])

  const selectStyle = {
    background: 'var(--color-bg-card)', border: '1px solid var(--color-border)',
    color: 'var(--color-text-secondary)', borderRadius: 'var(--radius-sm)',
    padding: '6px 10px', fontSize: 'var(--font-size-sm)', cursor: 'pointer',
    fontFamily: 'var(--font-family)'
  }

  if (loading) return (
    <div style={{ textAlign: 'center', padding: 'var(--spacing-2xl)', color: 'var(--color-text-muted)' }}>
      <div style={{ fontSize: '2rem', marginBottom: 'var(--spacing-md)' }}>⏳</div>
      <p>Đang tải phản hồi từ Firestore...</p>
    </div>
  )

  if (error) return (
    <div style={{ padding: 'var(--spacing-xl)', background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 'var(--radius-md)', color: 'var(--color-danger)' }}>
      <strong>⚠️ Lỗi Firestore:</strong> {error}
    </div>
  )

  return (
    <div>
      {/* Filters */}
      <div style={{ display: 'flex', gap: 'var(--spacing-sm)', flexWrap: 'wrap', marginBottom: 'var(--spacing-lg)', alignItems: 'center' }}>
        <input
          type="text" placeholder="🔍 Tìm trong transcript..."
          value={search} onChange={e => setSearch(e.target.value)}
          style={{ ...selectStyle, flex: 1, minWidth: 200 }}
        />
        <select value={filterSentiment} onChange={e => setFilterSentiment(e.target.value)} style={selectStyle}>
          <option value="all">Tất cả cảm xúc</option>
          <option value="positive">Tích cực ▲</option>
          <option value="neutral">Trung lập –</option>
          <option value="negative">Tiêu cực ▼</option>
        </select>
        <select value={filterLocation} onChange={e => setFilterLocation(e.target.value)} style={selectStyle}>
          <option value="all">Tất cả vị trí</option>
          {LOCATIONS.map(l => <option key={l} value={l}>{l}</option>)}
        </select>
        <select value={filterType} onChange={e => setFilterType(e.target.value)} style={selectStyle}>
          <option value="all">Audio & Text</option>
          <option value="audio">Ghi âm</option>
          <option value="text">Văn bản</option>
          <option value="audio_and_text">Cả hai</option>
        </select>
        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginLeft: 'auto' }}>
          {filtered.length} / {feedbacks.length} kết quả
        </span>
      </div>

      {feedbacks.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">📭</div>
            <p>Chưa có phản hồi nào trong Firestore.<br/>
              <small style={{ color: 'var(--color-text-muted)' }}>Khách hàng quét QR và gửi phản hồi để bắt đầu.</small>
            </p>
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Thời gian</th>
                  <th>Vị trí</th>
                  <th>Loại</th>
                  <th>Transcript</th>
                  <th>Cảm xúc</th>
                  <th>Khía cạnh</th>
                  <th>Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 && (
                  <tr><td colSpan={7}>
                    <div className="empty-state"><div className="empty-state-icon">🔍</div><p>Không có kết quả phù hợp</p></div>
                  </td></tr>
                )}
                {filtered.map(fb => {
                  const score  = fb.sentiment_score ?? 0
                  const isPos  = score >= 0.3
                  const isNeg  = score <= -0.3
                  const sentCls = isPos ? 'positive' : isNeg ? 'negative' : 'neutral'
                  return (
                    <tr key={fb.feedback_id}>
                      <td style={{ whiteSpace: 'nowrap', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)' }}>
                        {timeAgo(fb.timestamp)}
                      </td>
                      <td style={{ whiteSpace: 'nowrap', fontSize: 'var(--font-size-xs)' }}>{fb.location}</td>
                      <td style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>{fb.input_type === 'audio' ? 'Ghi âm' : fb.input_type === 'audio_and_text' ? 'Âm + Chữ' : 'Văn bản'}</td>
                      <td style={{ maxWidth: 280 }}>
                        {fb.processing_status === 'processing' ? (
                          <span style={{ color: 'var(--color-text-muted)', fontStyle: 'italic', fontSize: 'var(--font-size-xs)' }}>⏳ Đang phân tích...</span>
                        ) : (
                          <span style={{ fontSize: 'var(--font-size-xs)', lineHeight: 1.5, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                            {fb.transcript || <span style={{ color: 'var(--color-text-muted)' }}>(Trống)</span>}
                          </span>
                        )}
                        {fb.is_sarcasm && <span className="sarcasm-flag" style={{ marginTop: 4, display: 'inline-flex' }}>⚠️ Mỉa mai</span>}
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        {fb.processing_status === 'done' ? (
                          <span className={`sentiment-badge sentiment-badge--${sentCls}`}>
                            {isPos ? '+' : ''}{score.toFixed(2)}
                          </span>
                        ) : '—'}
                      </td>
                      <td style={{ maxWidth: 180 }}>
                        {(fb.aspects || []).slice(0, 3).map((a, i) => (
                          <span key={i} className="aspect-chip" style={{ fontSize: '0.65rem' }}>
                            {ASPECT_LABELS[a.aspect]?.split(' ')[0]}
                            <span style={{ color: scoreToColor(a.score ?? 0) }}>
                              {a.sentiment === 'positive' ? '▲' : a.sentiment === 'negative' ? '▼' : '–'}
                            </span>
                          </span>
                        ))}
                        {(fb.aspects?.length ?? 0) > 3 && <span className="aspect-chip">+{fb.aspects.length - 3}</span>}
                      </td>
                      <td>
                        <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>
                          {fb.processing_status === 'done' ? 'Xong' : fb.processing_status === 'processing' ? 'Xử lý...' : fb.processing_status === 'error' ? 'Lỗi' : 'Chờ'}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
