import { FAQItem } from '../components/FAQItem'

const FAQS = [
  {
    q: 'Khách có phải tải ứng dụng không?',
    a: 'Không. Sentrix hoạt động hoàn toàn trên trình duyệt web. Khách chỉ cần quét mã QR tại bàn bằng camera điện thoại — không cần tải ứng dụng, không cần đăng nhập, không cần tài khoản.',
  },
  {
    q: 'Khách phải nói hay gõ? Có thể làm cả hai không?',
    a: 'Cả hai đều được. Sentrix hỗ trợ giọng nói (ghi âm → chuyển văn bản tự động) và nhập liệu bằng bàn phím. Khách chọn cách phù hợp với mình. Cả hai hình thức đều được phân tích theo cùng một quy trình AI.',
  },
  {
    q: 'Quán nhỏ (5–15 bàn) có dùng được không?',
    a: 'Được. Sentrix không yêu cầu quy mô tối thiểu. Trên thực tế, quán có quy mô vừa và nhỏ thường hưởng lợi nhiều hơn — vì vấn đề xảy ra ở từng bàn dễ truy xuất và xử lý nhanh hơn.',
  },
  {
    q: 'Sentrix khác gì so với một form khảo sát hoặc app đánh giá?',
    a: 'Form khảo sát cho điểm số — Sentrix tạo ra hành động. Thay vì hỏi "Bạn chấm mấy điểm?", Sentrix để khách nói tự nhiên, rồi phân tích từng khía cạnh cụ thể (món ăn, tốc độ, thái độ, không gian), xác định mức độ ưu tiên và chuyển thành thông báo cho nhân viên ngay lập tức. Không cần chủ quán ngồi đọc báo cáo thủ công.',
  },
  {
    q: 'Giọng nói và dữ liệu khách được xử lý như thế nào?',
    a: 'Giọng nói được chuyển thành văn bản ngay sau khi ghi, sau đó audio được xóa. Khách có thể phản hồi ẩn danh — không cần để lại tên hay số điện thoại. Sentrix chỉ thu thập dữ liệu cần thiết cho mục đích vận hành, không chia sẻ với bên thứ ba.',
  },
  {
    q: 'Có cần tích hợp với phần mềm POS hay hệ thống quản lý bàn không?',
    a: 'Không. Sentrix hoạt động hoàn toàn độc lập qua mã QR. Không cần tích hợp POS, phần mềm quản lý bàn hay bất kỳ hệ thống nào đang có. Bạn chỉ cần in mã QR và dán tại bàn — mọi thứ còn lại Sentrix tự xử lý.',
  },
  {
    q: 'Nhân viên nhận thông báo bằng cách nào?',
    a: 'Khi Sentrix phát hiện vấn đề cần xử lý ngay, hệ thống gửi thông báo đến thiết bị của nhân viên (điện thoại hoặc máy tính bảng tại quầy) — hiển thị số bàn và loại vấn đề. Nhân viên nhận thông tin đúng thời điểm, không cần phỏng đoán.',
  },
  {
    q: 'Sentrix có thay thế nhân viên không?',
    a: 'Không. Sentrix giúp nhân viên biết cần làm gì và làm đúng lúc. Hệ thống chỉ chuyển thông tin — quyết định xử lý vẫn là của con người. Mục tiêu là giúp đội ngũ của bạn phản ứng nhanh hơn, không phải thay thế họ.',
  },
]

export function FAQ() {
  return (
    <section id="faq" className="section" style={{ background: 'var(--white)' }}>
      <div className="container">
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 2fr',
          gap: 'var(--s-16)',
          alignItems: 'start',
        }} className="faq-grid">

          {/* Left */}
          <div className="reveal">
            <span className="eyebrow" style={{ display: 'block', marginBottom: 'var(--s-4)' }}>
              Câu hỏi thường gặp
            </span>
            <h2 className="h4" style={{ color: 'var(--grey-900)', marginBottom: 'var(--s-5)' }}>
              Bạn còn thắc mắc?
            </h2>
            <p className="body-lg" style={{ marginBottom: 'var(--s-6)' }}>
              Không tìm thấy câu trả lời bạn cần — liên hệ trực tiếp với chúng tôi.
            </p>
            <a
              href="#dung-thu"
              onClick={(e) => { e.preventDefault(); document.querySelector('#dung-thu')?.scrollIntoView({ behavior: 'smooth' }) }}
              className="btn btn-primary"
            >
              Đăng ký Pilot
            </a>
          </div>

          {/* Right */}
          <div className="reveal d-2">
            {FAQS.map((faq, i) => (
              <FAQItem key={i} index={i} question={faq.q} answer={faq.a} />
            ))}
          </div>
        </div>
      </div>

      <style>{`
        @media (max-width: 768px) {
          .faq-grid { grid-template-columns: 1fr !important; gap: var(--s-8) !important; }
        }
      `}</style>
    </section>
  )
}
