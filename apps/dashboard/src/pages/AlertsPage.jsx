import { useState, useCallback } from 'react'
import { useLiveAlerts } from '../hooks/useLiveAlerts.js'
import { IS_MOCK } from '../mocks/useFirestore.js'

/**
 * AlertsPage — Staff Alert Dashboard
 * ====================================
 * Milestone 5: Realtime alerts từ Firestore onSnapshot
 *
 * Hiển thị yêu cầu hỗ trợ từ khách hàng (SUPPORT_REQUEST intent),
 * cho phép nhân viên ghi nhận (ACKNOWLEDGE) và đánh dấu xử lý xong (RESOLVE).
 *
 * Flow:
 *   1. Alert tạo khi khách nói "Cho tôi thêm nước" → intent = SUPPORT_REQUEST
 *   2. Nhân viên thấy alert realtime trong tab này
 *   3. Nhấn "Ghi nhận" → ACKNOWLEDGED
 *   4. Nhấn "Đã xử lý" → RESOLVED (ẩn khỏi danh sách mặc định)
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const TENANT_ID = import.meta.env.VITE_DEMO_TENANT_ID || 'pho-ba-lan_1722500000000'

// ─────────────────────────────────────────────────────────────────────────────
// Constants & Helpers
// ─────────────────────────────────────────────────────────────────────────────

const STATUS_META = {
  CREATED:      { label: 'Chờ xử lý',  color: '#EF4444', bg: '#EF444415' },
  ACKNOWLEDGED: { label: 'Đang xử lý', color: '#FFA412', bg: '#FFA41215' },
  RESOLVED:     { label: 'Đã xong',    color: '#00B69B', bg: '#00B69B15' },
}

function timeAgo(ts) {
  if (!ts) return '—'
  const date = ts.toDate ? ts.toDate() : new Date(ts)
  const diffMs = Date.now() - date.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return 'Vừa xong'
  if (diffMin < 60) return `${diffMin} phút trước`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24) return `${diffH} giờ trước`
  return `${Math.floor(diffH / 24)} ngày trước`
}

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

function StatusBadge({ status }) {
  const meta = STATUS_META[status] || { label: status, color: '#9CA3AF', bg: '#9CA3AF15' }
  return (
    <span style={{
      display: 'inline-block',
      padding: '2px 10px',
      borderRadius: 6,
      fontSize: 'var(--font-size-xs)',
      fontWeight: 700,
      color: meta.color,
      background: meta.bg,
      border: `1px solid ${meta.color}40`,
    }}>
      {meta.label}
    </span>
  )
}

function AlertCard({ alert, onAcknowledge, onResolve, actionLoading }) {
  const isLoading = actionLoading === alert.alert_id

  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 12,
      padding: '16px 20px',
      display: 'flex',
      flexDirection: 'column',
      gap: 12,
      transition: 'box-shadow 0.2s',
      // Highlight mới (CREATED)
      ...(alert.status === 'CREATED' ? {
        borderLeft: '3px solid #EF4444',
        boxShadow: '0 0 0 1px #EF444420',
      } : {}),
      // Mờ đi khi RESOLVED
      ...(alert.status === 'RESOLVED' ? { opacity: 0.65 } : {}),
    }}>
      {/* Header: location + status + time */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{
            background: 'rgba(0,194,255,0.1)',
            color: '#00C2FF',
            border: '1px solid rgba(0,194,255,0.25)',
            borderRadius: 6,
            padding: '2px 10px',
            fontSize: 'var(--font-size-xs)',
            fontWeight: 700,
          }}>
            📍 {alert.location || 'Không rõ'}
          </span>
          <StatusBadge status={alert.status} />
        </div>
        <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-xs)' }}>
          {timeAgo(alert.created_at)}
        </span>
      </div>

      {/* Transcript */}
      <p style={{
        margin: 0,
        color: 'var(--color-text-primary)',
        fontSize: 'var(--font-size-sm)',
        lineHeight: 1.6,
        padding: '10px 14px',
        background: 'rgba(255,255,255,0.04)',
        borderRadius: 8,
        borderLeft: '3px solid rgba(0,194,255,0.3)',
        fontStyle: 'italic',
      }}>
        "{alert.transcript || '(không có nội dung)'}"
      </p>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
        {alert.status === 'CREATED' && (
          <button
            id={`btn-ack-${alert.alert_id}`}
            disabled={isLoading}
            onClick={() => onAcknowledge(alert.alert_id)}
            style={{
              padding: '6px 16px',
              borderRadius: 8,
              border: '1px solid #FFA41260',
              background: '#FFA41215',
              color: '#FFA412',
              fontWeight: 700,
              fontSize: 'var(--font-size-xs)',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              opacity: isLoading ? 0.6 : 1,
              transition: 'all 0.15s',
            }}
          >
            {isLoading ? '...' : '✋ Ghi nhận'}
          </button>
        )}
        {(alert.status === 'CREATED' || alert.status === 'ACKNOWLEDGED') && (
          <button
            id={`btn-resolve-${alert.alert_id}`}
            disabled={isLoading}
            onClick={() => onResolve(alert.alert_id)}
            style={{
              padding: '6px 16px',
              borderRadius: 8,
              border: '1px solid #00B69B60',
              background: '#00B69B15',
              color: '#00B69B',
              fontWeight: 700,
              fontSize: 'var(--font-size-xs)',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              opacity: isLoading ? 0.6 : 1,
              transition: 'all 0.15s',
            }}
          >
            {isLoading ? '...' : '✅ Đã xử lý'}
          </button>
        )}
        {alert.status === 'RESOLVED' && (
          <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-xs)' }}>
            Đã xử lý xong — {timeAgo(alert.resolved_at)}
          </span>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Page
// ─────────────────────────────────────────────────────────────────────────────

export default function AlertsPage() {
  const { alerts, loading, error, pendingCount } = useLiveAlerts({ maxItems: 100 })
  const [actionLoading, setActionLoading] = useState(null)   // alert_id đang xử lý
  const [actionError, setActionError]     = useState(null)
  const [showResolved, setShowResolved]   = useState(false)

  // Lọc theo tab
  const filteredAlerts = showResolved
    ? alerts
    : alerts.filter(a => a.status !== 'RESOLVED')

  const pending   = alerts.filter(a => a.status === 'CREATED')
  const inprog    = alerts.filter(a => a.status === 'ACKNOWLEDGED')
  const resolved  = alerts.filter(a => a.status === 'RESOLVED')

  // ── API calls ──────────────────────────────────────────────────────────────

  const patchAlert = useCallback(async (alertId, action) => {
    if (IS_MOCK) {
      // Mock: simulate optimistic update
      console.log(`[AlertsPage] MOCK ${action} alert ${alertId}`)
      return
    }

    setActionLoading(alertId)
    setActionError(null)
    try {
      const url = `${API_BASE}/api/v1/tenants/${TENANT_ID}/alerts/${alertId}/${action}`
      const resp = await fetch(url, { method: 'PATCH' })
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}))
        throw new Error(body.detail || `HTTP ${resp.status}`)
      }
      // Firestore onSnapshot sẽ tự cập nhật UI khi Firestore thay đổi
    } catch (err) {
      console.error(`[AlertsPage] ${action} failed:`, err)
      setActionError(`Không thể ${action === 'acknowledge' ? 'ghi nhận' : 'xử lý'} alert: ${err.message}`)
    } finally {
      setActionLoading(null)
    }
  }, [])

  const handleAcknowledge = (alertId) => patchAlert(alertId, 'acknowledge')
  const handleResolve     = (alertId) => patchAlert(alertId, 'resolve')

  // ── Render ─────────────────────────────────────────────────────────────────

  if (loading) {
    return (
      <div style={{ padding: '40px 24px', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
        <div style={{
          width: 36, height: 36, margin: '0 auto 12px',
          border: '3px solid rgba(255,255,255,0.1)',
          borderTopColor: '#00C2FF',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite',
        }} />
        Đang tải alerts...
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '40px 24px', color: '#EF4444', textAlign: 'center' }}>
        ⚠️ Không thể tải alerts: {error.message}
      </div>
    )
  }

  return (
    <div style={{ padding: '24px', maxWidth: 900, margin: '0 auto' }}>
      {/* Page Header */}
      <div style={{ marginBottom: 24, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 id="alerts-page-title" style={{
            margin: 0, fontSize: 'var(--font-size-xl)', fontWeight: 800,
            color: 'var(--color-text-primary)',
          }}>
            🔔 Yêu cầu hỗ trợ
            {pendingCount > 0 && (
              <span id="alerts-pending-badge" style={{
                marginLeft: 10,
                background: '#EF4444',
                color: '#fff',
                borderRadius: 20,
                padding: '1px 10px',
                fontSize: 'var(--font-size-sm)',
                fontWeight: 700,
                verticalAlign: 'middle',
              }}>
                {pendingCount}
              </span>
            )}
          </h1>
          <p style={{ margin: '4px 0 0', color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
            Realtime — cập nhật tự động khi có yêu cầu mới
            {IS_MOCK && <span style={{ marginLeft: 8, color: '#FFA412' }}>[MOCK DATA]</span>}
          </p>
        </div>

        {/* Summary chips */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Chip count={pending.length}  label="Chờ xử lý"  color="#EF4444" />
          <Chip count={inprog.length}   label="Đang xử lý" color="#FFA412" />
          <Chip count={resolved.length} label="Đã xong"    color="#00B69B" />
        </div>
      </div>

      {/* Action error banner */}
      {actionError && (
        <div style={{
          background: '#EF444415', border: '1px solid #EF444440',
          borderRadius: 8, padding: '10px 16px', marginBottom: 16,
          color: '#EF4444', fontSize: 'var(--font-size-sm)',
        }}>
          ⚠️ {actionError}
          <button
            onClick={() => setActionError(null)}
            style={{ marginLeft: 12, background: 'none', border: 'none', color: '#EF4444', cursor: 'pointer', fontWeight: 700 }}
          >✕</button>
        </div>
      )}

      {/* Filter toggle */}
      <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
        <FilterBtn active={!showResolved} onClick={() => setShowResolved(false)}>
          Đang mở ({filteredAlerts.filter(a => a.status !== 'RESOLVED').length + (showResolved ? 0 : 0)})
        </FilterBtn>
        <FilterBtn active={showResolved} onClick={() => setShowResolved(true)}>
          Tất cả ({alerts.length})
        </FilterBtn>
      </div>

      {/* Alert list */}
      {filteredAlerts.length === 0 ? (
        <div style={{
          textAlign: 'center', padding: '60px 24px',
          color: 'var(--color-text-secondary)',
          background: 'var(--color-surface)',
          borderRadius: 12, border: '1px dashed var(--color-border)',
        }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>✅</div>
          <div style={{ fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 4 }}>
            Không có yêu cầu hỗ trợ nào
          </div>
          <div style={{ fontSize: 'var(--font-size-sm)' }}>
            Khi khách gửi yêu cầu, alert sẽ xuất hiện ở đây theo thời gian thực.
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {filteredAlerts.map(alert => (
            <AlertCard
              key={alert.alert_id}
              alert={alert}
              onAcknowledge={handleAcknowledge}
              onResolve={handleResolve}
              actionLoading={actionLoading}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Utility components
// ─────────────────────────────────────────────────────────────────────────────

function Chip({ count, label, color }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      background: `${color}15`, color,
      border: `1px solid ${color}40`,
      borderRadius: 20, padding: '3px 12px',
      fontSize: 'var(--font-size-xs)', fontWeight: 700,
    }}>
      <span style={{ fontWeight: 800 }}>{count}</span> {label}
    </span>
  )
}

function FilterBtn({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '6px 16px',
        borderRadius: 8,
        border: `1px solid ${active ? '#00C2FF40' : 'var(--color-border)'}`,
        background: active ? 'rgba(0,194,255,0.1)' : 'transparent',
        color: active ? '#00C2FF' : 'var(--color-text-secondary)',
        fontWeight: active ? 700 : 400,
        fontSize: 'var(--font-size-xs)',
        cursor: 'pointer',
        transition: 'all 0.15s',
      }}
    >
      {children}
    </button>
  )
}
