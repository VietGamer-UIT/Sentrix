/**
 * ConsentWindow.jsx — Màn hình đồng ý xử lý dữ liệu cá nhân
 * ============================================================
 * Module 2 — Tuân thủ Nghị định 356/2025/NĐ-CP
 *
 * THIẾT KẾ PHÁP LÝ:
 *   Điều 6.3 NĐ 356/2025/NĐ-CP — KHÔNG tích checkbox sẵn.
 *   Điều 6.4 NĐ 356/2025/NĐ-CP — phải nêu rõ đây là dữ liệu NHẠY CẢM.
 *   Điều 6.2 NĐ 356/2025/NĐ-CP — lưu bằng chứng đồng ý (qua useConsent.giveConsent).
 *   Điều 5   NĐ 356/2025/NĐ-CP — liệt kê quyền xóa dữ liệu trong 20 ngày.
 *
 * Props:
 *   tenantId        string   — ID tenant từ QR code
 *   businessName    string   — Tên quán/doanh nghiệp
 *   onConsented     fn()     — Callback khi đồng ý thành công (mở RecordingOverlay)
 */

import { useState, useCallback } from 'react'
import { useConsent, CONSENT_VERSION } from '../hooks/useConsent.js'

function ConsentWindow({ tenantId, businessName, onConsented }) {
  const { giveConsent, isLoading } = useConsent(tenantId)

  // Điều 6.3 NĐ 356/2025: KHÔNG được tích sẵn — bắt buộc là false
  const [agreed, setAgreed]   = useState(false)
  const [expanded, setExpanded] = useState(false) // toggle xem thêm chi tiết

  const handleAgree = useCallback(async () => {
    if (!agreed || isLoading) return
    // Ghi nhận đồng ý (localStorage + server) — anonymous=false tại bước consent,
    // lựa chọn ẩn danh sẽ được chọn sau ở RecordingOverlay.
    await giveConsent({ anonymous: false, phone: null })
    onConsented()
  }, [agreed, isLoading, giveConsent, onConsented])

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 2000,
      background: 'rgba(0,0,0,0.55)',
      backdropFilter: 'blur(8px)',
      WebkitBackdropFilter: 'blur(8px)',
      display: 'flex', alignItems: 'flex-end',
      justifyContent: 'center',
      animation: 'consent-fade-in 0.25s ease forwards',
    }}>
      <div style={{
        width: '100%', maxWidth: 480,
        background: '#FFFFFF',
        borderRadius: '28px 28px 0 0',
        padding: '28px 24px 36px',
        boxShadow: '0 -8px 40px rgba(0,0,0,0.18)',
        animation: 'consent-slide-up 0.35s cubic-bezier(0.34,1.56,0.64,1) forwards',
        maxHeight: '92dvh',
        overflowY: 'auto',
      }}>

        {/* ── Kéo handle ── */}
        <div style={{
          width: 40, height: 4, borderRadius: 2,
          background: '#E5E7EB', margin: '0 auto 20px',
        }} />

        {/* ── Header ── */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          {/* Icon khiên bảo vệ */}
          <div style={{
            width: 44, height: 44, borderRadius: '50%', flexShrink: 0,
            background: 'linear-gradient(135deg, #0688A6, #2CD9E5)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
              stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
          </div>
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 800, color: '#111827', margin: 0 }}>
              Thông báo xử lý dữ liệu
            </h2>
            <p style={{ fontSize: 12, color: '#6B7280', margin: 0, marginTop: 2 }}>
              Căn cứ Nghị định 356/2025/NĐ-CP
            </p>
          </div>
        </div>

        {/* ── Nội dung chính ── */}
        {/* 3 Summary Cards — tóm tắt nhanh trước khi khách đọc chi tiết */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
          {[
            {
              title: 'Bảo mật tuyệt đối',
              desc: 'Dữ liệu mã hoá end-to-end, chỉ dùng nội bộ',
              icon: (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0688A6" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
              ),
            },
            {
              title: 'Không lưu SĐT định danh',
              desc: 'SĐT chỉ lưu dạng mã hoá một chiều nếu bạn đồng ý',
              icon: (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0688A6" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="5" y="2" width="14" height="20" rx="2" ry="2"/>
                  <line x1="12" y1="18" x2="12.01" y2="18"/>
                  <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
              ),
            },
            {
              title: 'Tự động xoá giọng nói',
              desc: 'File âm thanh bị xoá ngay sau khi chuyển thành văn bản',
              icon: (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0688A6" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6l-1 14H6L5 6"/>
                  <path d="M10 11v6"/>
                  <path d="M14 11v6"/>
                  <path d="M9 6V4h6v2"/>
                </svg>
              ),
            },
          ].map(({ title, desc, icon }) => (
            <div key={title} style={{
              flex: 1,
              background: '#F0F9FB',
              border: '1px solid rgba(6,136,166,0.15)',
              borderRadius: 12,
              padding: '10px 8px',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 5,
              textAlign: 'center',
            }}>
              <div style={{
                width: 36, height: 36, borderRadius: '50%',
                background: 'rgba(6,136,166,0.08)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0,
              }}>
                {icon}
              </div>
              <span style={{ fontSize: 11, fontWeight: 700, color: '#111827', lineHeight: 1.3 }}>{title}</span>
              <span style={{ fontSize: 10, color: '#6B7280', lineHeight: 1.4 }}>{desc}</span>
            </div>
          ))}
        </div>

        {/* Chi tiết pháp lý — thu gọn phía dưới */}
        <div style={{
          background: '#F9FAFB', borderRadius: 16,
          padding: '16px', marginBottom: 16,
          border: '1px solid #E5E7EB',
        }}>
          {/* Ai thu thập */}
          <p style={{ fontSize: 13, color: '#374151', marginBottom: 10, lineHeight: 1.6 }}>
            <strong style={{ color: '#111827' }}>{businessName}</strong> sử dụng nền tảng{' '}
            <strong style={{ color: '#0688A6' }}>Sentrix</strong> để thu thập phản hồi
            của bạn nhằm cải thiện chất lượng dịch vụ.
          </p>

          {/* Dữ liệu nhạy cảm — Điều 6.4 bắt buộc nêu rõ */}
          <div style={{
            background: 'rgba(239,68,68,0.06)', borderRadius: 10,
            padding: '10px 12px', marginBottom: 10,
            border: '1px solid rgba(239,68,68,0.15)',
          }}>
            <p style={{ fontSize: 12, color: '#B91C1C', margin: 0, lineHeight: 1.6 }}>
              <strong>Dữ liệu nhạy cảm (Điều 4.1.đ NĐ 356/2025):</strong> Giọng nói
              của bạn được phân loại là <strong>dữ liệu sinh trắc học</strong> — một loại
              dữ liệu cá nhân nhạy cảm được pháp luật bảo vệ đặc biệt.
            </p>
          </div>

          {/* Danh mục dữ liệu */}
          <div style={{ fontSize: 12, color: '#4B5563', lineHeight: 1.8 }}>
            <p style={{ marginBottom: 6, fontWeight: 600, color: '#111827' }}>Dữ liệu thu thập:</p>
            <ul style={{ paddingLeft: 16, margin: 0 }}>
              <li><strong>Giọng nói</strong> (ghi âm tối đa 15 giây) — dữ liệu sinh trắc học</li>
              <li><strong>Văn bản phản hồi</strong> (nếu chọn gõ thay vì nói)</li>
              <li><strong>Số điện thoại</strong> (chỉ khi bạn muốn nhận voucher; lưu dạng mã hoá)</li>
            </ul>
          </div>

          {/* Mục đích */}
          <div style={{ fontSize: 12, color: '#4B5563', lineHeight: 1.8, marginTop: 10 }}>
            <p style={{ marginBottom: 4, fontWeight: 600, color: '#111827' }}>Mục đích sử dụng:</p>
            <ul style={{ paddingLeft: 16, margin: 0 }}>
              <li>Phân tích cảm xúc để cải thiện dịch vụ</li>
              <li>Gửi voucher ưu đãi qua Zalo (nếu bạn đồng ý để lại SĐT)</li>
            </ul>
          </div>
        </div>

        {/* ── Xem thêm (toggle) ── */}
        <button
          onClick={() => setExpanded(e => !e)}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            fontSize: 12, color: '#0688A6', fontFamily: 'inherit',
            padding: '4px 0', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 4,
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2.5"
            style={{ transform: expanded ? 'rotate(180deg)' : 'none', transition: '0.2s' }}>
            <polyline points="6 9 12 15 18 9"/>
          </svg>
          {expanded ? 'Thu gọn' : 'Quyền của bạn và thêm chi tiết'}
        </button>

        {expanded && (
          <div style={{
            background: '#F9FAFB', borderRadius: 12, padding: '12px 14px',
            marginBottom: 12, fontSize: 12, color: '#4B5563', lineHeight: 1.8,
            border: '1px solid #E5E7EB',
          }}>
            <p style={{ fontWeight: 600, color: '#111827', marginBottom: 6 }}>
              Quyền của bạn (Điều 5 NĐ 356/2025/NĐ-CP):
            </p>
            <ul style={{ paddingLeft: 16, margin: 0 }}>
              <li><strong>Quyền từ chối:</strong> Bật “Phản hồi ẩn danh” để gửi phản hồi mà không cần để lại thông tin cá nhân</li>
              <li><strong>Yêu cầu xóa dữ liệu:</strong> Thực hiện trong <strong>20 ngày</strong> kể từ yêu cầu hợp lệ</li>
              <li><strong>Quyền xem dữ liệu:</strong> Liên hệ qua email hoặc fanpage của cơ sở</li>
            </ul>
            <p style={{ marginTop: 8, color: '#6B7280' }}>
              <strong>Bên xử lý dữ liệu thay mặt:</strong> Sentrix
            </p>
          </div>
        )}

        {/* ── Checkbox đồng ý — KHÔNG tích sẵn (Điều 6.3) ── */}
        <label
          id="consent-checkbox-label"
          style={{
            display: 'flex', alignItems: 'flex-start', gap: 10,
            cursor: 'pointer', marginBottom: 20, userSelect: 'none',
            padding: '12px', borderRadius: 12,
            background: agreed ? 'rgba(6,136,166,0.06)' : '#F9FAFB',
            border: `1.5px solid ${agreed ? 'rgba(6,136,166,0.4)' : '#E5E7EB'}`,
            transition: 'all 0.2s',
          }}
        >
          <div
            onClick={() => setAgreed(a => !a)}
            style={{
              width: 22, height: 22, borderRadius: 6, flexShrink: 0, marginTop: 1,
              border: `2px solid ${agreed ? '#0688A6' : '#D1D5DB'}`,
              background: agreed ? '#0688A6' : '#FFFFFF',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              transition: 'all 0.18s',
              cursor: 'pointer',
            }}
            role="checkbox"
            aria-checked={agreed}
            id="consent-checkbox"
            tabIndex={0}
            onKeyDown={e => { if (e.key === ' ' || e.key === 'Enter') setAgreed(a => !a) }}
          >
            {agreed && (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
                stroke="white" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
            )}
          </div>
          <span style={{ fontSize: 13, color: '#374151', lineHeight: 1.6, flex: 1 }}>
            Tôi đồng ý để{' '}
            <strong>{businessName}</strong> và <strong>Sentrix</strong> thu thập
            và xử lý dữ liệu của tôi (bao gồm{' '}
            <span style={{ color: '#B91C1C', fontWeight: 600 }}>dữ liệu sinh trắc học từ giọng nói</span>)
            theo mục đích đã nêu trên.
          </span>
        </label>

        {/* ── Nút CTA ── */}
        <button
          id="btn-consent-agree"
          onClick={handleAgree}
          disabled={!agreed || isLoading}
          style={{
            width: '100%',
            padding: '14px',
            borderRadius: 999,
            border: 'none',
            fontFamily: 'inherit', fontWeight: 700, fontSize: 16,
            cursor: agreed && !isLoading ? 'pointer' : 'not-allowed',
            background: agreed
              ? 'linear-gradient(135deg, #0688A6, #2CD9E5)'
              : '#E5E7EB',
            color: agreed ? '#FFFFFF' : '#9CA3AF',
            boxShadow: agreed ? '0 4px 20px rgba(6,136,166,0.35)' : 'none',
            transition: 'all 0.2s',
            marginBottom: 10,
          }}
        >
          {isLoading ? 'Đang xác nhận...' : '✓ Đồng ý và tiếp tục'}
        </button>

        {/* Từ chối — quyền không đồng ý */}
        <p style={{ textAlign: 'center', fontSize: 12, color: '#9CA3AF', lineHeight: 1.6 }}>
          Bạn có thể chọn <strong>Phản hồi ẩn danh</strong> ở bước tiếp theo
          để gửi phản hồi mà không cần để lại thông tin cá nhân.
        </p>
      </div>

      <style>{`
        @keyframes consent-fade-in {
          from { opacity: 0; }
          to   { opacity: 1; }
        }
        @keyframes consent-slide-up {
          from { transform: translateY(60px); opacity: 0; }
          to   { transform: translateY(0); opacity: 1; }
        }
      `}</style>
    </div>
  )
}

export default ConsentWindow
