import React from 'react'

export const ASPECT_LABELS = {
  nhan_vien: 'Nhân viên', mon_an: 'Món ăn',
  khong_gian: 'Không gian',  gia_ca: 'Giá cả',
  toc_do_phuc_vu: 'Tốc độ',
  toc_do: 'Tốc độ',
  ve_sinh: 'Vệ sinh',
  vi_tri: 'Vị trí', khac: 'Khác'
}

/**
 * Lấy category key từ aspect object.
 * Backend mới lưu: { category: "mon_an", sentiment_en: "positive", ... }
 * Mock cũ dùng:    { aspect: "mon_an", sentiment: "positive", ... }
 * Hàm này tương thích cả hai.
 */
export function getAspectCategory(a) {
  return a.category || a.aspect || 'khac'
}

export function getAspectSentimentEn(a) {
  // Backend mới: sentiment_en = "positive"|"negative"|"neutral"
  // Mock cũ: sentiment = "positive"|"negative" (tiếng Anh)
  // Backend cũ có thể: sentiment = "Tích cực" (tiếng Việt)
  const raw = a.sentiment_en || a.sentiment || ''
  if (raw === 'positive' || raw === 'Tích cực') return 'positive'
  if (raw === 'negative' || raw === 'Tiêu cực') return 'negative'
  return 'neutral'
}

export function getAspectScore(a) {
  // Ưu tiên field score numeric [-1,1] từ backend
  if (typeof a.score === 'number') return a.score
  // Fallback: suy ra từ sentiment
  const sent = getAspectSentimentEn(a)
  return sent === 'positive' ? 1 : sent === 'negative' ? -1 : 0
}

export function scoreToColor(s) {
  return s >= 0.3 ? 'var(--color-positive)' : s <= -0.3 ? 'var(--color-negative)' : 'var(--color-neutral-s)'
}

/**
 * Chip khía cạnh, hỗ trợ hiển thị đủ các khía cạnh.
 */
export function AspectCellExpanded({ aspects }) {
  if (!aspects || aspects.length === 0) return null

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
      {aspects.map((a, i) => {
        const cat  = getAspectCategory(a)
        const sent = getAspectSentimentEn(a)
        const sc   = getAspectScore(a)
        const sign = sent === 'positive' ? '+' : sent === 'negative' ? '-' : '–'
        return (
          <span key={i} className="aspect-chip" style={{ fontSize: '0.65rem' }}>
            {ASPECT_LABELS[cat] || cat}
            <span style={{ 
              color: scoreToColor(sc), 
              marginLeft: 4,
              fontWeight: sent === 'neutral' ? 400 : 800,
              fontSize: sent === 'neutral' ? 'inherit' : '0.8rem'
            }}>
              {sign}
            </span>
          </span>
        )
      })}
    </div>
  )
}
