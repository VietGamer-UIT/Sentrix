import { useState } from 'react'
import { submitPilotLead } from '../services/pilotService'
import { useReducedMotion } from '../hooks/useReducedMotion'

const STORE_TYPES = [
  'Quán cà phê',
  'Quán ăn / Nhà hàng',
  'Trà sữa / Đồ uống',
  'Bánh & Dessert',
  'Fast food / Street food',
  'Khác',
]

const BLANK = {
  storeName: '',
  contactName: '',
  contactInfo: '',
  storeType: '',
  storeSize: '',
  goal: '',
}

export function Pilot() {
  return (
    <section id="dung-thu" className="section" style={{
      background: 'var(--off-white)',
      borderTop: '1px solid var(--grey-100)',
    }}>
      <div className="container">

        {/* Heading */}
        <div className="reveal" style={{ marginBottom: 'var(--s-16)' }}>
          <span className="eyebrow" style={{ display: 'block', marginBottom: 'var(--s-4)' }}>
            Chương trình Pilot
          </span>
          <h2 className="h3" style={{ color: 'var(--grey-900)', marginBottom: 'var(--s-4)' }}>
            Một tuần thử. Không rủi ro.
          </h2>
          <p className="body-xl" style={{ maxWidth: 560 }}>
            Bắt đầu từ vài bàn — không cần thay đổi hệ thống, không tốn chi phí cài đặt. Sau một tuần bạn sẽ biết Sentrix phù hợp với quán mình không.
          </p>
        </div>

        {/* Steps */}
        <div className="reveal pilot-steps" style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(6, 1fr)',
          gap: 'var(--s-3)',
          marginBottom: 'var(--s-16)',
        }}>
          {[
            { n: '01', label: 'Đặt mã QR tại bàn' },
            { n: '02', label: 'Khách phản hồi' },
            { n: '03', label: 'Sentrix phân tích' },
            { n: '04', label: 'Nhân viên xử lý' },
            { n: '05', label: 'Chủ quán theo dõi' },
            { n: '06', label: 'Đánh giá kết quả' },
          ].map(s => (
            <div key={s.n} style={{
              background: 'var(--white)',
              border: '1px solid var(--grey-100)',
              borderRadius: 'var(--r-md)',
              padding: 'var(--s-4)',
            }}>
              <span style={{ fontSize: 'var(--t-xs)', fontWeight: 700, color: 'var(--teal)', display: 'block', marginBottom: 6 }}>
                {s.n}
              </span>
              <p style={{ fontSize: 'var(--t-sm)', color: 'var(--grey-600)', fontWeight: 500, lineHeight: 1.4 }}>
                {s.label}
              </p>
            </div>
          ))}
        </div>

        {/* Form layout */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '5fr 7fr',
          gap: 'var(--s-16)',
          alignItems: 'start',
        }} className="pilot-form-grid">

          {/* Left — pitch */}
          <div className="reveal">
            <h3 className="h5" style={{ color: 'var(--grey-900)', marginBottom: 'var(--s-5)' }}>
              Mang Sentrix vào quán của bạn.
            </h3>
            <p className="body-lg" style={{ marginBottom: 'var(--s-6)' }}>
              Điền thông tin bên cạnh. Đội ngũ Sentrix sẽ liên hệ để sắp xếp Pilot phù hợp với quy mô cửa hàng của bạn.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--s-3)', marginBottom: 'var(--s-8)' }}>
              {[
                'Không cần tích hợp POS hay hệ thống phức tạp',
                'Cài đặt trong vài phút — chỉ cần in mã QR',
                'Kết quả có thể đo lường ngay trong tuần đầu',
                'Hỗ trợ trực tiếp từ đội ngũ trong suốt giai đoạn Pilot',
              ].map((item, i) => (
                <div key={i} style={{ display: 'flex', gap: 'var(--s-3)', alignItems: 'center' }}>
                  <span style={{ color: 'var(--teal)', flexShrink: 0 }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" aria-hidden="true">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  </span>
                  <p style={{ fontSize: 'var(--t-base)', color: 'var(--grey-600)' }}>{item}</p>
                </div>
              ))}
            </div>

            <div style={{
              background: 'var(--teal-light)',
              border: '1px solid var(--teal-mid)',
              borderRadius: 'var(--r-md)',
              padding: 'var(--s-5)',
            }}>
              <p style={{ fontSize: 'var(--t-sm)', fontWeight: 700, color: 'var(--teal)', marginBottom: 6 }}>
                Ưu tiên Pilot tại Làng Đại học Quốc gia Hà Nội
              </p>
              <p style={{ fontSize: 'var(--t-sm)', color: 'var(--grey-500)', lineHeight: 1.6 }}>
                Giai đoạn hiện tại Sentrix ưu tiên hỗ trợ các quán cà phê và quán ăn trong khu vực Làng ĐH QGHN (Quốc Oai, Hà Nội). Miễn phí hoàn toàn trong giai đoạn Pilot.
              </p>
            </div>
          </div>

          {/* Right — form */}
          <div className="reveal d-2">
            <PilotForm />
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 1024px) {
          .pilot-steps { grid-template-columns: repeat(3, 1fr) !important; }
        }
        @media (max-width: 768px) {
          .pilot-steps { grid-template-columns: repeat(2, 1fr) !important; }
          .pilot-form-grid { grid-template-columns: 1fr !important; }
        }
        @media (max-width: 480px) {
          .pilot-steps { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </section>
  )
}

function PilotForm() {
  const [form, setForm] = useState(BLANK)
  const [errors, setErrors] = useState({})
  const [status, setStatus] = useState('idle')
  const reduced = useReducedMotion()

  const set = (f, v) => {
    setForm(prev => ({ ...prev, [f]: v }))
    if (errors[f]) setErrors(e => ({ ...e, [f]: null }))
  }

  const validate = () => {
    const e = {}
    if (!form.storeName.trim())  e.storeName  = 'Vui lòng nhập tên cửa hàng'
    if (!form.contactName.trim()) e.contactName = 'Vui lòng nhập tên người liên hệ'
    if (!form.contactInfo.trim()) e.contactInfo = 'Vui lòng nhập số điện thoại hoặc email'
    if (!form.storeType)          e.storeType  = 'Vui lòng chọn loại hình'
    return e
  }

  const submit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    setStatus('loading')
    try {
      await submitPilotLead(form)
      setStatus('success')
    } catch {
      setStatus('error')
    }
  }

  if (status === 'success') {
    return (
      <div style={{
        background: 'var(--white)',
        border: '1px solid var(--grey-100)',
        borderRadius: 'var(--r-xl)',
        padding: 'var(--s-12)',
        textAlign: 'center',
        boxShadow: 'var(--shadow-md)',
        animation: reduced ? 'none' : 'fadeInScale 0.4s ease',
      }}>
        <div style={{
          width: 56,
          height: 56,
          borderRadius: '50%',
          background: 'var(--green-bg)',
          border: '1px solid rgba(16,185,129,0.2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto var(--s-6)',
        }}>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="2.5" strokeLinecap="round" aria-hidden="true">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        </div>
        <h3 style={{ fontWeight: 800, fontSize: 'var(--t-2xl)', color: 'var(--grey-900)', marginBottom: 'var(--s-3)' }}>
          Đã nhận được đăng ký.
        </h3>
        <p style={{ fontSize: 'var(--t-base)', color: 'var(--grey-500)', lineHeight: 1.7 }}>
          Đội ngũ Sentrix sẽ liên hệ với bạn sớm nhất có thể để sắp xếp Pilot.
        </p>
        <button
          onClick={() => { setStatus('idle'); setForm(BLANK) }}
          style={{
            marginTop: 'var(--s-6)',
            background: 'none',
            border: '1px solid var(--grey-200)',
            borderRadius: 'var(--r-pill)',
            padding: '8px 20px',
            fontSize: 'var(--t-sm)',
            color: 'var(--grey-400)',
            cursor: 'pointer',
          }}
        >
          Gửi thêm đăng ký
        </button>
      </div>
    )
  }

  return (
    <form
      id="pilot-form"
      onSubmit={submit}
      noValidate
      style={{
        background: 'var(--white)',
        border: '1px solid var(--grey-100)',
        borderRadius: 'var(--r-xl)',
        padding: 'var(--s-8)',
        boxShadow: 'var(--shadow-sm)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--s-4)',
      }}
    >
      <p style={{ fontWeight: 800, fontSize: 'var(--t-xl)', color: 'var(--grey-900)', marginBottom: 'var(--s-2)' }}>
        Đăng ký dùng thử
      </p>

      <Field label="Tên cửa hàng *" error={errors.storeName}>
        <input id="f-store" className={`form-input${errors.storeName ? ' err' : ''}`}
          type="text" placeholder="Vd: Cà Phê Ánh Dương"
          value={form.storeName} onChange={e => set('storeName', e.target.value)}
          autoComplete="organization"
        />
      </Field>

      <Field label="Người liên hệ *" error={errors.contactName}>
        <input id="f-name" className={`form-input${errors.contactName ? ' err' : ''}`}
          type="text" placeholder="Tên chủ quán hoặc quản lý"
          value={form.contactName} onChange={e => set('contactName', e.target.value)}
          autoComplete="name"
        />
      </Field>

      <Field label="Số điện thoại / Email *" error={errors.contactInfo}>
        <input id="f-contact" className={`form-input${errors.contactInfo ? ' err' : ''}`}
          type="text" placeholder="0912 345 678 hoặc email@example.com"
          value={form.contactInfo} onChange={e => set('contactInfo', e.target.value)}
          autoComplete="tel"
        />
      </Field>

      <Field label="Loại hình cửa hàng *" error={errors.storeType}>
        <select id="f-type" className={`form-select${errors.storeType ? ' err' : ''}`}
          value={form.storeType} onChange={e => set('storeType', e.target.value)}
        >
          <option value="">Chọn loại hình...</option>
          {STORE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </Field>

      <Field label="Quy mô (số bàn hoặc mô tả)">
        <input id="f-size" className="form-input"
          type="text" placeholder="Vd: 15 bàn, khoảng 50 khách/ngày"
          value={form.storeSize} onChange={e => set('storeSize', e.target.value)}
        />
      </Field>

      <Field label="Bạn muốn cải thiện điều gì nhất?">
        <textarea id="f-goal" className="form-textarea"
          placeholder="Vd: Tôi muốn biết tại sao khách không quay lại..."
          value={form.goal} onChange={e => set('goal', e.target.value)}
        />
      </Field>

      <button
        id="pilot-submit"
        type="submit"
        className="btn btn-primary-lg"
        disabled={status === 'loading'}
        style={{
          width: '100%',
          marginTop: 'var(--s-2)',
          opacity: status === 'loading' ? 0.65 : 1,
        }}
      >
        {status === 'loading'
          ? <><Spinner />Đang gửi...</>
          : 'Đăng ký dùng thử'
        }
      </button>

      {status === 'error' && (
        <p style={{ fontSize: 'var(--t-sm)', color: 'var(--red)', textAlign: 'center' }}>
          Có lỗi xảy ra. Vui lòng thử lại.
        </p>
      )}

      <p style={{ fontSize: 'var(--t-xs)', color: 'var(--grey-300)', textAlign: 'center', lineHeight: 1.6 }}>
        Thông tin của bạn chỉ dùng để liên hệ về Pilot. Không spam, không chia sẻ bên thứ ba.
      </p>
    </form>
  )
}

function Field({ label, error, children }) {
  return (
    <div className="form-group">
      <label className="form-label">{label}</label>
      {children}
      {error && <span className="form-err">{error}</span>}
    </div>
  )
}

function Spinner() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
      style={{ animation: 'spin 0.7s linear infinite' }} aria-hidden="true">
      <circle cx="12" cy="12" r="10" stroke="rgba(255,255,255,0.25)"/>
      <path d="M12 2a10 10 0 0 1 10 10"/>
    </svg>
  )
}
