import { useState, useEffect, useMemo } from 'react'
import { useFeedbacks, useTenant, tsToDate, IS_MOCK } from '../mocks/useFirestore.js'
import { isToday } from 'date-fns'

/**
 * VoucherConfigPage — Cấu Hình Voucher & Ngân Sách
 * ==================================================
 * Author: Đoàn Hoàng Việt (Việt Gamer)
 *
 * Chủ quán tự chỉnh:
 *   - Giới hạn voucher/ngày (daily_voucher_limit)
 *   - Tỷ lệ trúng thưởng vòng quay (win_rate_percent)
 * Đồng hồ tiến độ: đã phát X/Y voucher hôm nay
 *
 * Gọi API: PUT /api/v1/gamification/voucher-config (tenant config route)
 * Đọc config: useTenant() hook
 */

const BACKEND_URL = import.meta.env.VITE_API_URL || 'https://sentrix-backend.onrender.com'
const TENANT_ID   = import.meta.env.VITE_DEMO_TENANT_ID || 'pho-ba-lan_1722500000000'

// Default config nếu Firestore chưa có
const DEFAULT_CONFIG = {
  daily_voucher_limit: 20,
  win_rate_percent: 30,
}

export default function VoucherConfigPage() {
  const { tenant }                          = useTenant()
  const { feedbacks, loading: fbLoading }   = useFeedbacks()

  // Config form state — khởi tạo từ tenant Firestore, cập nhật khi tenant load xong
  const [limitVal, setLimitVal]     = useState(DEFAULT_CONFIG.daily_voucher_limit)
  const [winRate, setWinRate]       = useState(DEFAULT_CONFIG.win_rate_percent)
  const [saving, setSaving]         = useState(false)
  const [saveMsg, setSaveMsg]       = useState(null) // { type: 'success'|'error', text: '' }
  const [dirty, setDirty]           = useState(false)

  // Prefill form từ tenant config khi load xong
  useEffect(() => {
    if (tenant) {
      setLimitVal(tenant.daily_voucher_limit ?? DEFAULT_CONFIG.daily_voucher_limit)
      setWinRate(tenant.win_rate_percent ?? DEFAULT_CONFIG.win_rate_percent)
      setDirty(false)
    }
  }, [tenant])

  // Đếm voucher đã phát hôm nay
  const issuedToday = useMemo(() =>
    feedbacks.filter(f =>
      f.voucher_issued === true &&
      f.timestamp &&
      isToday(f.timestamp)
    ).length, [feedbacks])

  const progressPct = limitVal > 0 ? Math.min(100, Math.round((issuedToday / limitVal) * 100)) : 0
  const isNearLimit = progressPct >= 80

  // Lưu config
  async function handleSave(e) {
    e.preventDefault()
    if (IS_MOCK) {
      setSaveMsg({ type: 'success', text: '✅ (Demo mode) Đã lưu thành công!' })
      setDirty(false)
      setTimeout(() => setSaveMsg(null), 3000)
      return
    }

    setSaving(true)
    setSaveMsg(null)
    try {
      // Gọi API PUT voucher-config (route đã tạo ở Module 1)
      // Endpoint: PUT /api/v1/gamification/voucher-config
      // Body: { tenant_id, daily_voucher_limit, win_rate_percent }
      const res = await fetch(`${BACKEND_URL}/api/v1/gamification/voucher-config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tenant_id: TENANT_ID,
          daily_voucher_limit: Number(limitVal),
          win_rate_percent: Number(winRate),
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }
      setSaveMsg({ type: 'success', text: '✅ Đã lưu cấu hình thành công!' })
      setDirty(false)
    } catch (err) {
      setSaveMsg({ type: 'error', text: `❌ Lưu thất bại: ${err.message}` })
    } finally {
      setSaving(false)
      setTimeout(() => setSaveMsg(null), 4000)
    }
  }

  return (
    <div>
      {/* Page Header */}
      <div style={{ marginBottom: 'var(--spacing-lg)' }}>
        <h2 style={{
          fontSize: 'var(--font-size-lg)', fontWeight: 800,
          color: 'var(--color-text-primary)', margin: 0
        }}>
          🎫 Cấu Hình Voucher & Ngân Sách
        </h2>
        <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)', marginTop: 4 }}>
          Kiểm soát số lượng và tỷ lệ phát voucher mỗi ngày
          {IS_MOCK && <span style={{ color: 'var(--color-warning)', marginLeft: 8 }}>• Demo Mode — thay đổi sẽ không lưu</span>}
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--spacing-xl)', alignItems: 'start' }}>

        {/* === Cột trái: Đồng hồ tiến độ voucher hôm nay === */}
        <div>
          <div className="card glass-card">
            <div style={{
              padding: 'var(--spacing-md) var(--spacing-lg)',
              borderBottom: '1px solid var(--color-border)',
              fontWeight: 700, fontSize: 'var(--font-size-base)', color: 'var(--color-text-primary)',
            }}>
              📊 Tiến Độ Phát Voucher Hôm Nay
            </div>
            <div style={{ padding: 'var(--spacing-xl) var(--spacing-lg)' }}>

              {/* Số lớn trung tâm */}
              <div style={{ textAlign: 'center', marginBottom: 'var(--spacing-xl)' }}>
                <div style={{
                  fontSize: 56, fontWeight: 800,
                  color: isNearLimit ? 'var(--color-danger)' : 'var(--color-primary)',
                  lineHeight: 1, marginBottom: 8,
                }}>
                  {fbLoading ? '—' : issuedToday}
                </div>
                <div style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
                  / <strong style={{ color: 'var(--color-text-secondary)' }}>{limitVal}</strong> voucher giới hạn hôm nay
                </div>
              </div>

              {/* Progress bar */}
              <div style={{ marginBottom: 'var(--spacing-md)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                    Đã phát
                  </span>
                  <span style={{
                    fontSize: 'var(--font-size-xs)', fontWeight: 700,
                    color: isNearLimit ? 'var(--color-danger)' : 'var(--color-text-secondary)',
                  }}>
                    {progressPct}%
                  </span>
                </div>
                <div style={{ height: 12, background: 'var(--color-border)', borderRadius: 99, overflow: 'hidden' }}>
                  <div style={{
                    height: '100%',
                    width: `${progressPct}%`,
                    background: progressPct >= 100
                      ? 'var(--color-danger)'
                      : progressPct >= 80
                        ? 'linear-gradient(90deg, var(--color-warning), var(--color-danger))'
                        : 'linear-gradient(90deg, var(--color-primary), var(--color-accent))',
                    borderRadius: 99,
                    transition: 'width 0.6s ease',
                  }} />
                </div>
              </div>

              {/* Cảnh báo gần limit */}
              {isNearLimit && (
                <div style={{
                  background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
                  borderRadius: 'var(--radius-sm)', padding: '10px 14px',
                  color: 'var(--color-danger)', fontSize: 'var(--font-size-sm)', fontWeight: 600,
                }}>
                  ⚠️ {progressPct >= 100 ? 'Đã đạt giới hạn! Vòng quay bị tắt.' : `Sắp đạt giới hạn (${progressPct}%). Cân nhắc tăng daily_voucher_limit.`}
                </div>
              )}

              {/* Ghi chú reset */}
              <div style={{
                marginTop: 'var(--spacing-md)', padding: '8px 12px',
                background: 'var(--color-bg)', borderRadius: 'var(--radius-sm)',
                fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)',
                textAlign: 'center',
              }}>
                🔄 Bộ đếm tự reset lúc 00:00 ICT mỗi ngày
              </div>
            </div>
          </div>

          {/* Mini stats */}
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr',
            gap: 'var(--spacing-md)', marginTop: 'var(--spacing-md)',
          }}>
            <div className="kpi-card glass-card" style={{ minHeight: 70 }}>
              <div className="kpi-label">Tỷ lệ trúng thưởng</div>
              <div className="kpi-value" style={{ color: 'var(--color-primary)' }}>{winRate}%</div>
            </div>
            <div className="kpi-card glass-card" style={{ minHeight: 70 }}>
              <div className="kpi-label">Tổng voucher phát (thật)</div>
              <div className="kpi-value">
                {fbLoading ? '—' : feedbacks.filter(f => f.voucher_issued).length}
              </div>
            </div>
          </div>
        </div>

        {/* === Cột phải: Form cấu hình === */}
        <div className="card glass-card">
          <div style={{
            padding: 'var(--spacing-md) var(--spacing-lg)',
            borderBottom: '1px solid var(--color-border)',
            fontWeight: 700, fontSize: 'var(--font-size-base)', color: 'var(--color-text-primary)',
          }}>
            ⚙️ Cấu Hình
          </div>
          <form onSubmit={handleSave} style={{ padding: 'var(--spacing-lg)', display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' }}>

            {/* daily_voucher_limit */}
            <div>
              <label style={{
                display: 'block', fontSize: 'var(--font-size-sm)', fontWeight: 700,
                color: 'var(--color-text-secondary)', marginBottom: 8,
              }}>
                Giới hạn voucher / ngày
              </label>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <input
                  type="number"
                  id="daily-voucher-limit"
                  min={1} max={1000}
                  value={limitVal}
                  onChange={e => { setLimitVal(Number(e.target.value)); setDirty(true) }}
                  style={{
                    width: 100, padding: '8px 12px',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-sm)',
                    fontSize: 'var(--font-size-base)',
                    color: 'var(--color-text-primary)',
                    background: 'var(--color-bg)',
                    outline: 'none',
                  }}
                />
                <span style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
                  voucher / ngày
                </span>
              </div>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: 4 }}>
                Khi đạt giới hạn, vòng quay tự động tắt. Gợi ý: 20-50 cho quán nhỏ.
              </div>
            </div>

            {/* win_rate_percent — slider */}
            <div>
              <label style={{
                display: 'block', fontSize: 'var(--font-size-sm)', fontWeight: 700,
                color: 'var(--color-text-secondary)', marginBottom: 8,
              }}>
                Tỷ lệ trúng thưởng vòng quay
              </label>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                <input
                  type="range"
                  id="win-rate-slider"
                  min={5} max={100} step={5}
                  value={winRate}
                  onChange={e => { setWinRate(Number(e.target.value)); setDirty(true) }}
                  style={{
                    flex: 1, accentColor: 'var(--color-primary)',
                    cursor: 'pointer', height: 6,
                  }}
                />
                <span style={{
                  minWidth: 48, textAlign: 'right',
                  fontSize: 'var(--font-size-md)', fontWeight: 800,
                  color: 'var(--color-primary)',
                }}>
                  {winRate}%
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>5% (tiết kiệm)</span>
                <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>100% (tất cả trúng)</span>
              </div>
              <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: 4 }}>
                Ví dụ: 30% = trung bình 3/10 người quay có voucher.
              </div>
            </div>

            {/* Nút Lưu */}
            <div>
              <button
                type="submit"
                id="btn-save-voucher-config"
                disabled={saving || !dirty}
                style={{
                  width: '100%', padding: '12px',
                  background: dirty ? 'var(--color-primary)' : 'var(--color-border)',
                  color: dirty ? '#fff' : 'var(--color-text-muted)',
                  border: 'none', borderRadius: 'var(--radius-md)',
                  fontSize: 'var(--font-size-base)', fontWeight: 700,
                  cursor: dirty ? 'pointer' : 'not-allowed',
                  transition: 'var(--transition)',
                  opacity: saving ? 0.7 : 1,
                }}
              >
                {saving ? '⏳ Đang lưu...' : dirty ? '💾 Lưu cấu hình' : '✓ Đã lưu'}
              </button>
            </div>

            {/* Thông báo save */}
            {saveMsg && (
              <div style={{
                padding: '10px 14px',
                background: saveMsg.type === 'success' ? 'rgba(0,182,155,0.1)' : 'rgba(239,68,68,0.1)',
                border: `1px solid ${saveMsg.type === 'success' ? 'rgba(0,182,155,0.3)' : 'rgba(239,68,68,0.3)'}`,
                borderRadius: 'var(--radius-sm)',
                color: saveMsg.type === 'success' ? 'var(--color-success)' : 'var(--color-danger)',
                fontSize: 'var(--font-size-sm)', fontWeight: 600,
                textAlign: 'center',
              }}>
                {saveMsg.text}
              </div>
            )}

            {/* Ghi chú kỹ thuật */}
            <div style={{
              padding: '10px 14px',
              background: 'var(--color-bg)', borderRadius: 'var(--radius-sm)',
              fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)',
              lineHeight: 1.6,
            }}>
              <strong>Ghi chú kỹ thuật:</strong><br />
              • Config lưu vào Firestore <code>tenants/{'{tenantId}'}</code><br />
              • Budget check chạy tại route <code>POST /api/v1/gamification/spin</code><br />
              • Voucher phát đến SĐT qua Zalo ZNS khi p_churn &gt; 0.85
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
