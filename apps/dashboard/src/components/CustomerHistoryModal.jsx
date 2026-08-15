import { useMemo } from 'react'
import { timeAgo } from '../mocks/useFirestore.js'

/**
 * CustomerHistoryModal — Hiển thị lịch sử đánh giá của một khách hàng
 */
export default function CustomerHistoryModal({ customer, feedbacks, onClose }) {
  // Lọc các phản hồi của khách hàng này
  const customerFeedbacks = useMemo(() => {
    return feedbacks
      .filter(f => f.customer_id === customer.customer_id)
      .sort((a, b) => (b.timestamp?.seconds ?? 0) - (a.timestamp?.seconds ?? 0))
  }, [feedbacks, customer])

  function scoreToColor(s) {
    return s >= 0.3 ? 'var(--color-positive)' : s <= -0.3 ? 'var(--color-negative)' : 'var(--color-neutral-s)'
  }

  // Đóng modal khi click ra ngoài
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) onClose()
  }

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(0,0,0,0.5)', zIndex: 100,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      animation: 'fadeIn 0.2s ease'
    }} onClick={handleOverlayClick}>
      
      <div style={{
        background: 'var(--color-bg-card)',
        width: '90%', maxWidth: 600,
        maxHeight: '90vh', display: 'flex', flexDirection: 'column',
        borderRadius: 'var(--radius-lg)',
        boxShadow: '0 10px 40px rgba(0,0,0,0.2)'
      }}>
        {/* Header */}
        <div style={{
          padding: 'var(--spacing-lg)', borderBottom: '1px solid var(--color-border)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center'
        }}>
          <div>
            <h2 style={{ fontSize: 'var(--font-size-lg)', marginBottom: 4 }}>
              Lịch sử của Khách Hàng
            </h2>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
              SĐT: {customer.phone_masked || customer.customer_id.slice(0, 12)}...
            </div>
          </div>
          <button onClick={onClose} style={{
            background: 'none', border: 'none', fontSize: 24, cursor: 'pointer',
            color: 'var(--color-text-muted)'
          }}>&times;</button>
        </div>

        {/* Body */}
        <div style={{ padding: 'var(--spacing-lg)', overflowY: 'auto', flex: 1 }}>
          {customerFeedbacks.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">📭</div>
              <p>Chưa có dữ liệu phản hồi nào.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
              {customerFeedbacks.map((fb, idx) => {
                const score = fb.sentiment_score ?? 0
                const isPos = score >= 0.3
                const isNeg = score <= -0.3
                const sentCls = isPos ? 'positive' : isNeg ? 'negative' : 'neutral'
                
                return (
                  <div key={fb.feedback_id} style={{
                    position: 'relative',
                    paddingLeft: 24,
                    borderLeft: `2px solid var(--color-border)`
                  }}>
                    {/* Timeline dot */}
                    <div style={{
                      position: 'absolute', left: -7, top: 4,
                      width: 12, height: 12, borderRadius: '50%',
                      background: scoreToColor(score),
                      border: '2px solid var(--color-bg-card)'
                    }} />
                    
                    <div style={{
                      background: '#FAFBFF', padding: 'var(--spacing-md)',
                      borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, alignItems: 'center' }}>
                        <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                          {timeAgo(fb.timestamp)} · {fb.location}
                        </span>
                        
                        {fb.is_suspicious ? (
                          <span className="sentiment-badge" style={{ background: 'rgba(239, 68, 68, 0.1)', color: 'var(--color-danger)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                            🚨 SPAM
                          </span>
                        ) : fb.processing_status === 'done' ? (
                          <span className={`sentiment-badge sentiment-badge--${sentCls}`}>
                            {isPos ? '+' : ''}{score.toFixed(2)}
                          </span>
                        ) : null}
                      </div>

                      <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
                        {fb.transcript ? `"${fb.transcript}"` : '(Không có văn bản)'}
                      </p>

                      {fb.is_sarcasm && (
                        <span className="sarcasm-flag" style={{ marginTop: 8, display: 'inline-flex' }}>⚠️ Mỉa mai</span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
