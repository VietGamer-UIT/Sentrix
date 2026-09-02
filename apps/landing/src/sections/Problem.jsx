import { useState, useEffect } from 'react'
import { useReducedMotion } from '../hooks/useReducedMotion'

/*
  Problem — narrative storytelling aligned to AISC'26 thuyết minh
  Core insight: khách không phàn nàn trực tiếp → rời đi im lặng → chủ quán không biết tại sao
  Nhấn mạnh: "silent customer problem" + 3 lỗ hổng thực tế
*/

export function Problem() {
  const reduced = useReducedMotion()
  const [showBreakdown, setShowBreakdown] = useState(false)

  useEffect(() => {
    if (reduced) { setShowBreakdown(true); return }
    const t = setInterval(() => setShowBreakdown(s => !s), 3000)
    return () => clearInterval(t)
  }, [reduced])

  return (
    <section
      id="van-de"
      className="section"
      style={{ background: 'var(--off-white)', borderTop: '1px solid var(--grey-100)' }}
    >
      <div className="container">
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 'var(--s-20)',
          alignItems: 'center',
        }} className="problem-grid">

          {/* LEFT — the story */}
          <div className="reveal">
            <span className="eyebrow" style={{ display: 'block', marginBottom: 'var(--s-5)' }}>
              Vấn đề
            </span>

            <h2 className="h3" style={{ color: 'var(--grey-900)', marginBottom: 'var(--s-6)' }}>
              Khách không hài lòng —<br />
              nhưng không nói ra.
            </h2>

            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--s-6)',
              borderLeft: '2px solid var(--grey-100)',
              paddingLeft: 'var(--s-6)',
            }}>
              <Moment speaker="Khách ở bàn">
                "Chờ 20 phút rồi. Hơi lâu."
              </Moment>

              <Moment speaker="Nhân viên" muted>
                không ai biết.
              </Moment>

              <Moment speaker="Chủ quán" muted>
                cũng không biết.
              </Moment>

              <Moment speaker="Khách" action>
                trả tiền và không bao giờ quay lại.
              </Moment>

              <div style={{
                paddingTop: 'var(--s-4)',
                borderTop: '1px solid var(--grey-200)',
              }}>
                <p style={{ fontSize: 'var(--t-sm)', color: 'var(--grey-400)', marginBottom: 'var(--s-2)' }}>
                  Hai tuần sau, chủ quán thấy trên Google Maps:
                </p>
                <StarRating />
                <p style={{
                  fontSize: 'var(--t-2xl)',
                  fontWeight: 800,
                  color: 'var(--grey-900)',
                  marginTop: 'var(--s-4)',
                  letterSpacing: '-0.02em',
                }}>
                  "Phục vụ chậm, không quay lại."
                </p>
                <p style={{
                  fontSize: 'var(--t-sm)',
                  color: 'var(--grey-400)',
                  marginTop: 'var(--s-2)',
                  fontStyle: 'italic',
                }}>
                  — Lúc này đã không còn cơ hội để xử lý.
                </p>
              </div>
            </div>
          </div>

          {/* RIGHT — visual */}
          <div className="reveal d-2">
            <p style={{
              fontSize: 'var(--t-sm)',
              color: 'var(--grey-300)',
              marginBottom: 'var(--s-5)',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              fontWeight: 600,
            }}>
              Khoảng trống thông tin giữa khách và quán
            </p>

            <div style={{
              background: 'var(--white)',
              border: '1px solid var(--grey-100)',
              borderRadius: 'var(--r-xl)',
              padding: 'var(--s-8)',
              boxShadow: 'var(--shadow-sm)',
              minHeight: 200,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
            }}>
              {!showBreakdown ? (
                <div key="stars" style={{ animation: reduced ? 'none' : 'fadeIn 0.4s ease' }}>
                  <div style={{
                    display: 'flex',
                    gap: 4,
                    marginBottom: 'var(--s-3)',
                  }} aria-label="3 trên 5 sao">
                    {[1,2,3,4,5].map(s => (
                      <svg key={s} width="28" height="28" viewBox="0 0 24 24"
                        fill={s <= 3 ? '#F59E0B' : 'var(--grey-100)'}
                        stroke={s <= 3 ? '#F59E0B' : 'var(--grey-200)'}
                        strokeWidth="1.5" aria-hidden="true">
                        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                      </svg>
                    ))}
                  </div>
                  <p style={{ fontSize: 'var(--t-xl)', fontWeight: 700, color: 'var(--grey-900)', marginBottom: 'var(--s-2)' }}>
                    3 sao.
                  </p>
                  <p style={{ fontSize: 'var(--t-sm)', color: 'var(--grey-400)', lineHeight: 1.6 }}>
                    Thức ăn? Phục vụ? Thời gian chờ? Không gian?<br />
                    Một con số không cho bạn biết cần sửa gì.
                  </p>
                  <p style={{
                    marginTop: 'var(--s-4)',
                    fontSize: 'var(--t-sm)',
                    fontWeight: 600,
                    color: 'var(--grey-400)',
                    fontStyle: 'italic',
                  }}>
                    Không biết → không thể cải thiện.
                  </p>
                </div>
              ) : (
                <div key="breakdown" style={{ animation: reduced ? 'none' : 'fadeIn 0.4s ease' }}>
                  <p style={{
                    fontSize: 'var(--t-xs)',
                    fontWeight: 600,
                    color: 'var(--teal)',
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    marginBottom: 'var(--s-4)',
                  }}>
                    Với Sentrix — bạn biết chính xác:
                  </p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--s-2)' }}>
                    <BreakdownRow label="Chất lượng món ăn" value="Tốt" positive />
                    <BreakdownRow label="Tốc độ phục vụ" value="Cần cải thiện" />
                    <BreakdownRow label="Thái độ nhân viên" value="Tốt" positive />
                  </div>
                </div>
              )}
            </div>

            {/* Three core gaps from thuyết minh */}
            <div style={{
              marginTop: 'var(--s-8)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--s-5)',
            }}>
              {[
                {
                  number: '01',
                  text: 'Phần lớn khách không nói thẳng khi gặp vấn đề — họ im lặng và không quay lại.',
                },
                {
                  number: '02',
                  text: 'Phản hồi đến qua Google Maps hoặc mạng xã hội — khi đã quá muộn để xử lý.',
                },
                {
                  number: '03',
                  text: 'Survey truyền thống cho điểm số, không cho biết điều gì cần thay đổi ngay hôm nay.',
                },
              ].map(item => (
                <div key={item.number} style={{ display: 'flex', gap: 'var(--s-4)' }}>
                  <span style={{
                    fontSize: 'var(--t-xs)',
                    fontWeight: 700,
                    color: 'var(--grey-300)',
                    letterSpacing: '0.06em',
                    flexShrink: 0,
                    paddingTop: 3,
                    minWidth: 24,
                  }}>{item.number}</span>
                  <p style={{
                    fontSize: 'var(--t-base)',
                    color: 'var(--grey-500)',
                    lineHeight: 1.65,
                  }}>{item.text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 900px) {
          .problem-grid { grid-template-columns: 1fr !important; gap: var(--s-12) !important; }
        }
      `}</style>
    </section>
  )
}

function Moment({ speaker, children, muted, action }) {
  return (
    <div>
      <p style={{
        fontSize: 'var(--t-xs)',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.08em',
        color: action ? 'var(--red)' : muted ? 'var(--grey-300)' : 'var(--teal)',
        marginBottom: 4,
      }}>
        {speaker}
      </p>
      <p style={{
        fontSize: action ? 'var(--t-lg)' : 'var(--t-base)',
        color: action ? 'var(--grey-700)' : muted ? 'var(--grey-300)' : 'var(--grey-700)',
        fontStyle: !action && !muted ? 'italic' : 'normal',
        fontWeight: action ? 600 : 400,
        lineHeight: 1.5,
      }}>
        {children}
      </p>
    </div>
  )
}

function StarRating() {
  return (
    <div style={{ display: 'flex', gap: 3 }} aria-label="3 sao trên Google">
      {[1,2,3,4,5].map(s => (
        <svg key={s} width="18" height="18" viewBox="0 0 24 24"
          fill={s <= 3 ? '#F59E0B' : 'var(--grey-200)'}
          stroke={s <= 3 ? '#F59E0B' : 'var(--grey-200)'}
          strokeWidth="1" aria-hidden="true">
          <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
        </svg>
      ))}
    </div>
  )
}

function BreakdownRow({ label, value, positive }) {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '10px 14px',
      background: positive ? 'var(--green-bg)' : 'var(--red-bg)',
      borderRadius: 'var(--r-sm)',
      border: `1px solid ${positive ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)'}`,
    }}>
      <span style={{ fontSize: 'var(--t-sm)', fontWeight: 600, color: 'var(--grey-700)' }}>{label}</span>
      <span style={{ fontSize: 'var(--t-xs)', fontWeight: 700, color: positive ? 'var(--green)' : 'var(--red)' }}>{value}</span>
    </div>
  )
}
