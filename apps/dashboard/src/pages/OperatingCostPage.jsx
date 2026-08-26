import { useMemo } from 'react'
import { useFeedbacks, useCustomers, IS_MOCK } from '../mocks/useFirestore.js'

/**
 * OperatingCostPage — Tài Chính & Chi Phí Vận Hành
 * ==================================================
 * Author: Đoàn Hoàng Việt (Việt Gamer)
 *
 * Ước tính COGS (Cost of Goods Sold) / OpEx từ số lượt API thực tế:
 *   - Whisper STT:   n_audio_feedbacks × đơn giá ($0.006/phút ≈ ~30s/lượt → ~$0.003/lượt)
 *   - Gemini ABSA:   n_processed_feedbacks × đơn giá
 *   - Zalo ZNS:      n_zns_sent × đơn giá
 *   - Hosting (fix): Render + Vercel
 *
 * ⚠️ LƯU Ý QUAN TRỌNG:
 *   Đây là ước tính nội bộ từ log Firestore — không phải hóa đơn thật.
 *   Đơn giá cấu hình qua biến môi trường VITE_COST_* để team chỉnh dễ.
 *   Mục đích: minh hoạ bảng OpEx trong thuyết minh dự án AISC'26.
 *
 * ĐƠN GIÁ MẶC ĐỊNH (override qua VITE_COST_* trong .env):
 *   Whisper:  $0.003/lượt (= $0.006/phút × 0.5 phút trung bình)
 *   Gemini:   $0.0001/lượt (Flash-Lite rất rẻ, ~100K input token = $0.01)
 *   ZNS:      1,000 VNĐ/tin
 *   Render:   $0/tháng (free tier) + optional $7/tháng nếu cần uptime
 *   Vercel:   $0/tháng (Hobby tier)
 *
 * Tỷ giá USD→VNĐ: 25,000 (cấu hình qua VITE_USD_VND_RATE)
 */

// Đơn giá mặc định — override qua .env dashboard
const COST = {
  whisper_per_call:   parseFloat(import.meta.env.VITE_COST_WHISPER_PER_CALL   || '0.003'),   // USD
  gemini_per_call:    parseFloat(import.meta.env.VITE_COST_GEMINI_PER_CALL    || '0.0001'),  // USD
  zns_per_message:    parseFloat(import.meta.env.VITE_COST_ZNS_PER_MSG        || '1000'),    // VNĐ
  render_monthly:     parseFloat(import.meta.env.VITE_COST_RENDER_MONTHLY_USD || '0'),       // USD/tháng
  vercel_monthly:     parseFloat(import.meta.env.VITE_COST_VERCEL_MONTHLY_USD || '0'),       // USD/tháng
  usd_vnd_rate:       parseFloat(import.meta.env.VITE_USD_VND_RATE            || '25000'),   // 1 USD = ? VNĐ
}

function fmtVND(amount) {
  if (amount >= 1_000_000) return `${(amount / 1_000_000).toFixed(2)} triệu ₫`
  if (amount >= 1_000)    return `${Math.round(amount).toLocaleString('vi-VN')} ₫`
  return `${amount.toFixed(0)} ₫`
}

function fmtUSD(amount) {
  return `$${amount.toFixed(4)}`
}

// Màu gradient theo mức chi phí
function costColor(vnd) {
  if (vnd > 500_000) return 'var(--color-danger)'
  if (vnd > 100_000) return 'var(--color-warning)'
  return 'var(--color-success)'
}

export default function OperatingCostPage() {
  const { feedbacks, loading: fbLoading } = useFeedbacks()

  // Đếm số lượt gọi API từ feedbacks Firestore
  const counts = useMemo(() => {
    const audio    = feedbacks.filter(f => f.input_type === 'audio' && f.processing_status === 'done').length
    const processed = feedbacks.filter(f => f.processing_status === 'done').length
    const zns      = feedbacks.filter(f => f.zns_sent_at != null).length
    return { audio, processed, zns }
  }, [feedbacks])

  // Chi phí theo hạng mục
  const costs = useMemo(() => {
    const whisperUSD   = counts.audio * COST.whisper_per_call
    const geminiUSD    = counts.processed * COST.gemini_per_call
    const znsVND       = counts.zns * COST.zns_per_message
    const hostingUSD   = COST.render_monthly + COST.vercel_monthly

    // Quy đổi tất cả sang VNĐ
    const whisperVND   = whisperUSD * COST.usd_vnd_rate
    const geminiVND    = geminiUSD * COST.usd_vnd_rate
    const hostingVND   = hostingUSD * COST.usd_vnd_rate
    const totalVND     = whisperVND + geminiVND + znsVND + hostingVND

    return {
      items: [
        {
          id: 'whisper',
          label:     'Whisper STT (giọng nói → văn bản)',
          icon:      '🎙️',
          provider:  'OpenAI',
          count:     counts.audio,
          unit:      'lượt audio',
          unitPrice: `${fmtUSD(COST.whisper_per_call)}/lượt`,
          vnd:       whisperVND,
          note:      '~30s/lượt × $0.006/phút',
        },
        {
          id: 'gemini',
          label:     'Gemini ABSA (phân tích cảm xúc)',
          icon:      '🤖',
          provider:  'Google',
          count:     counts.processed,
          unit:      'lượt phản hồi',
          unitPrice: `${fmtUSD(COST.gemini_per_call)}/lượt`,
          vnd:       geminiVND,
          note:      'Flash-Lite ~100K token/$0.01',
        },
        {
          id: 'zns',
          label:     'Zalo ZNS (tin nhắn chăm sóc khách)',
          icon:      '💬',
          provider:  'Zalo',
          count:     counts.zns,
          unit:      'tin nhắn ZNS',
          unitPrice: `${(COST.zns_per_message).toLocaleString('vi-VN')} ₫/tin`,
          vnd:       znsVND,
          note:      'ZNS Notification Service',
        },
        {
          id: 'hosting',
          label:     'Hosting (Render + Vercel)',
          icon:      '☁️',
          provider:  'Render / Vercel',
          count:     1,
          unit:      'tháng',
          unitPrice: `${fmtUSD(hostingUSD)}/tháng`,
          vnd:       hostingVND,
          note:      'Free tier, $0 hiện tại',
        },
      ],
      totalVND,
      whisperVND, geminiVND, znsVND, hostingVND,
    }
  }, [counts])

  const loading = fbLoading

  return (
    <div>
      {/* Page Header */}
      <div style={{ marginBottom: 'var(--spacing-lg)' }}>
        <h2 style={{
          fontSize: 'var(--font-size-lg)', fontWeight: 800,
          color: 'var(--color-text-primary)', margin: 0
        }}>
          💰 Tài Chính & Chi Phí Vận Hành
        </h2>
        <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)', marginTop: 4 }}>
          Ước tính OpEx từ số lượt API thực tế — phục vụ minh hoạ bảng COGS trong thuyết minh AISC'26
          {IS_MOCK && <span style={{ color: 'var(--color-warning)', marginLeft: 8 }}>• Demo Data</span>}
        </p>
      </div>

      {/* Disclaimer nổi bật */}
      <div style={{
        display: 'flex', alignItems: 'flex-start', gap: 10,
        background: 'rgba(6,136,166,0.06)',
        border: '1px solid rgba(6,136,166,0.2)',
        borderRadius: 'var(--radius-md)',
        padding: 'var(--spacing-md) var(--spacing-lg)',
        marginBottom: 'var(--spacing-xl)',
        fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)',
        lineHeight: 1.6,
      }}>
        <span style={{ fontSize: 20 }}>ℹ️</span>
        <div>
          <strong>Ước tính nội bộ — không phải hóa đơn thật từ nhà cung cấp.</strong><br />
          Số lượt đếm từ Firestore realtime. Đơn giá cấu hình qua biến môi trường <code>VITE_COST_*</code>.<br />
          Tỷ giá: 1 USD = {COST.usd_vnd_rate.toLocaleString('vi-VN')} ₫ (cấu hình qua <code>VITE_USD_VND_RATE</code>).
        </div>
      </div>

      {/* KPI tổng */}
      <div className="kpi-grid" style={{ marginBottom: 'var(--spacing-xl)' }}>
        <div className="kpi-card glass-card">
          <div className="kpi-label">Tổng chi phí ước tính</div>
          <div className="kpi-value" style={{ color: costColor(costs.totalVND) }}>
            {loading ? '—' : fmtVND(costs.totalVND)}
          </div>
          <div className="kpi-sub">tích lũy từ {feedbacks.length} phản hồi</div>
        </div>
        <div className="kpi-card glass-card">
          <div className="kpi-label">Chi phí / phản hồi</div>
          <div className="kpi-value" style={{ color: 'var(--color-text-primary)' }}>
            {loading || feedbacks.length === 0 ? '—' : fmtVND(costs.totalVND / feedbacks.length)}
          </div>
          <div className="kpi-sub">trung bình COGS / feedback</div>
        </div>
        <div className="kpi-card glass-card">
          <div className="kpi-label">Lượt STT (Whisper)</div>
          <div className="kpi-value">{loading ? '—' : counts.audio}</div>
          <div className="kpi-sub">phản hồi giọng nói</div>
        </div>
        <div className="kpi-card glass-card">
          <div className="kpi-label">Tin ZNS đã gửi</div>
          <div className="kpi-value">{loading ? '—' : counts.zns}</div>
          <div className="kpi-sub">khách chăm sóc tự động</div>
        </div>
      </div>

      {/* Bảng chi tiết OpEx */}
      <div className="card glass-card" style={{ marginBottom: 'var(--spacing-xl)' }}>
        <div style={{
          padding: 'var(--spacing-md) var(--spacing-lg)',
          borderBottom: '1px solid var(--color-border)',
          fontWeight: 700, fontSize: 'var(--font-size-base)', color: 'var(--color-text-primary)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <span>📋 Bảng Chi Tiết Hạng Mục</span>
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', fontWeight: 400 }}>
            Tích lũy từ lúc demo bắt đầu
          </span>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'var(--color-bg)', borderBottom: '1px solid var(--color-border)' }}>
                {['Hạng Mục', 'Nhà Cung Cấp', 'Số Lượt', 'Đơn Giá', 'Thành Tiền (≈)', 'Ghi Chú'].map(h => (
                  <th key={h} style={{
                    padding: '12px 16px', textAlign: 'left',
                    fontSize: 'var(--font-size-xs)', fontWeight: 700,
                    color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em',
                    whiteSpace: 'nowrap',
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {costs.items.map((item, i) => (
                <tr key={item.id} style={{
                  borderBottom: '1px solid var(--color-border)',
                  background: i % 2 === 0 ? 'transparent' : 'var(--color-bg)',
                }}>
                  {/* Hạng mục */}
                  <td style={{ padding: '14px 16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: 20 }}>{item.icon}</span>
                      <div>
                        <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
                          {item.label}
                        </div>
                      </div>
                    </div>
                  </td>
                  {/* Provider */}
                  <td style={{ padding: '14px 16px', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
                    {item.provider}
                  </td>
                  {/* Số lượt */}
                  <td style={{ padding: '14px 16px', fontSize: 'var(--font-size-md)', fontWeight: 700, color: 'var(--color-text-primary)' }}>
                    {loading ? '—' : item.count.toLocaleString('vi-VN')}
                    <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', fontWeight: 400, marginLeft: 4 }}>
                      {item.unit}
                    </span>
                  </td>
                  {/* Đơn giá */}
                  <td style={{ padding: '14px 16px', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', fontFamily: 'monospace' }}>
                    {item.unitPrice}
                  </td>
                  {/* Thành tiền */}
                  <td style={{ padding: '14px 16px' }}>
                    <span style={{
                      fontSize: 'var(--font-size-sm)', fontWeight: 700,
                      color: costColor(item.vnd),
                    }}>
                      {loading ? '—' : fmtVND(item.vnd)}
                    </span>
                  </td>
                  {/* Ghi chú */}
                  <td style={{ padding: '14px 16px', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                    {item.note}
                  </td>
                </tr>
              ))}
            </tbody>
            {/* Tổng cộng */}
            <tfoot>
              <tr style={{ background: 'rgba(6,136,166,0.05)', borderTop: '2px solid var(--color-primary)' }}>
                <td colSpan={4} style={{ padding: '14px 16px', fontWeight: 800, color: 'var(--color-text-primary)', fontSize: 'var(--font-size-base)' }}>
                  TỔNG CỘNG (ước tính)
                </td>
                <td style={{ padding: '14px 16px' }}>
                  <span style={{
                    fontSize: 'var(--font-size-md)', fontWeight: 800,
                    color: costColor(costs.totalVND),
                  }}>
                    {loading ? '—' : fmtVND(costs.totalVND)}
                  </span>
                </td>
                <td style={{ padding: '14px 16px', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                  Không gồm lao động
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      {/* Biểu đồ tỷ trọng chi phí */}
      <div className="card glass-card">
        <div style={{
          padding: 'var(--spacing-md) var(--spacing-lg)',
          borderBottom: '1px solid var(--color-border)',
          fontWeight: 700, fontSize: 'var(--font-size-base)', color: 'var(--color-text-primary)',
        }}>
          📊 Tỷ Trọng Chi Phí
        </div>
        <div style={{ padding: 'var(--spacing-lg)', display: 'flex', flexDirection: 'column', gap: 12 }}>
          {costs.items.map(item => {
            const pct = costs.totalVND > 0 ? (item.vnd / costs.totalVND) * 100 : 0
            const barColor = item.id === 'whisper' ? '#0688A6' :
                             item.id === 'gemini'  ? '#8B5CF6' :
                             item.id === 'zns'     ? '#10B981' : '#9CA3AF'
            return (
              <div key={item.id}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', fontWeight: 600 }}>
                    {item.icon} {item.label}
                  </span>
                  <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 700, color: barColor }}>
                    {loading ? '—' : `${pct.toFixed(1)}%`}
                  </span>
                </div>
                <div style={{ height: 8, background: 'var(--color-border)', borderRadius: 99, overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', width: `${pct}%`, background: barColor,
                    borderRadius: 99, transition: 'width 0.6s ease',
                    minWidth: item.vnd > 0 ? 4 : 0,
                  }} />
                </div>
              </div>
            )
          })}
        </div>

        {/* Hướng dẫn chỉnh đơn giá */}
        <div style={{
          margin: '0 var(--spacing-lg) var(--spacing-lg)',
          padding: '10px 14px',
          background: 'var(--color-bg)',
          borderRadius: 'var(--radius-sm)',
          fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)',
          lineHeight: 1.6,
        }}>
          <strong>Chỉnh đơn giá:</strong> Thêm vào <code>apps/dashboard/.env</code>:
          <br />
          <code>VITE_COST_WHISPER_PER_CALL=0.003</code> &nbsp;
          <code>VITE_COST_GEMINI_PER_CALL=0.0001</code> &nbsp;
          <code>VITE_COST_ZNS_PER_MSG=1000</code> &nbsp;
          <code>VITE_USD_VND_RATE=25000</code>
        </div>
      </div>
    </div>
  )
}
