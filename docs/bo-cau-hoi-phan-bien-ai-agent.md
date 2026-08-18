# Bộ câu hỏi phản biện AI Agent — Xác minh sản phẩm chạy thật, đúng, đầy đủ

**Mục đích:** Dùng bộ này để "vặn" bất kỳ AI Agent nào (Claude, Gemini, Cursor, Copilot...) khi nghi ngờ nó đang báo cáo sai sự thật ("ảo giác"), khi hệ thống chạy lỗi, hoặc trước khi chấp nhận một tính năng là "đã xong". Nguyên tắc chung: **không hỏi "đã xong chưa" (AI luôn nói xong) — mà bắt nó CHỨNG MINH bằng bằng chứng chạy được, kèm output thật.**

---

## 0. Nguyên tắc dùng bộ câu hỏi này

- Luôn yêu cầu **bằng chứng thực thi** (log, output console, ảnh chụp màn hình, response JSON thật) — không chấp nhận câu trả lời chỉ mô tả bằng lời ("nó sẽ trả về...", "hệ thống sẽ hiển thị...").
- Nếu AI trả lời bằng thì tương lai/điều kiện ("sẽ", "nên", "có thể sẽ") thay vì thì hiện tại đã xảy ra ("đã chạy, kết quả là...") → đó là dấu hiệu nó đang suy đoán chứ không phải đã kiểm chứng. Hỏi lại ngay: **"Bạn đã thực sự chạy chưa hay đang đoán?"**
- Yêu cầu AI **tự chạy lại từ đầu, môi trường sạch** (clean install / restart server) trước khi báo "hoạt động" — rất nhiều lỗi chỉ xuất hiện khi build lại từ đầu chứ không phải trên môi trường đã cache sẵn.
- Không hỏi 1 câu rồi tin — hỏi theo **chuỗi truy vết** (traceback): từ hành động người dùng → request → xử lý → response → hiển thị, và bắt AI chỉ ra bằng chứng ở TỪNG bước.

---

## I. Nhóm câu hỏi xác minh KHẢ NĂNG CHẠY ĐƯỢC (Executability)

1. Bạn vừa chạy lệnh gì, trên máy/môi trường nào, và output đầy đủ (không cắt bớt) là gì?
2. Nếu tôi clone lại repo này trên máy sạch (chưa cài gì) và làm đúng theo README, nó có chạy được không? Bạn đã thử việc đó chưa hay chỉ đang giả định "chắc là chạy được"?
3. Lệnh cài đặt dependency (`npm install`, `pip install -r requirements.txt`...) có chạy thành công không, có warning/error nào bị bỏ qua không?
4. Build production (`npm run build`, `docker build`...) có pass không? Cho tôi xem log build đầy đủ, không phải chỉ dòng cuối "Build successful".
5. Có biến môi trường (API key, DB URL...) nào bắt buộc mà chưa được khai báo trong `.env.example` không? Nếu thiếu, app có tự báo lỗi rõ ràng hay chỉ crash im lặng?
6. App có khởi động được từ trạng thái database rỗng (fresh DB, chưa có dữ liệu) không, hay đang ngầm giả định đã có sẵn dữ liệu mẫu?
7. Tất cả các service phụ thuộc (DB, Redis, third-party API...) có đang thực sự chạy/kết nối được không, hay bạn đang giả lập (mock) mà báo cáo như thật?

---

## II. Nhóm câu hỏi FRONTEND ↔ BACKEND (điểm hay lỗi nhất)

8. Frontend đang gọi đúng URL/base URL nào? Cho tôi xem giá trị thật của biến cấu hình đó (không phải placeholder).
9. Request đó có **thực sự tới được** backend không — cho tôi xem log phía backend ghi nhận request đến (không phải chỉ code frontend "gọi đúng cú pháp" nhưng chưa test).
10. Response trả về có đúng schema/kiểu dữ liệu mà frontend đang parse không? Nếu backend đổi 1 field, frontend có báo lỗi rõ ràng hay chết lặng lẽ?
11. CORS đã được cấu hình đúng domain/port thật chưa, hay đang để `*` tạm thời (rủi ro khi lên production)?
12. Khi backend trả lỗi (4xx/5xx), frontend có hiển thị thông báo lỗi cho người dùng không, hay đứng im/trắng màn hình?
13. Có đang gọi nhầm API version, endpoint cũ, hoặc mock data từ lúc dev quên xóa không?
14. Authentication token (nếu có) có được đính kèm đúng ở mọi request cần xác thực không? Token hết hạn thì UI xử lý ra sao?
15. Nếu tắt backend đi, frontend có báo "mất kết nối" rõ ràng cho người dùng không, hay hiển thị dữ liệu cũ/rỗng như thể mọi thứ bình thường?

---

## III. Nhóm câu hỏi LUỒNG DỮ LIỆU (Data flow / Persistence)

16. Dữ liệu tôi nhập vào ở bước 1 có thực sự được lưu xuống database không? Cho tôi xem trực tiếp bản ghi đó trong DB (query thật), không phải chỉ log "đã lưu thành công".
17. Nếu tôi tắt app rồi mở lại, dữ liệu còn nguyên không?
18. Hai người dùng thao tác đồng thời (concurrent) có bị ghi đè/mất dữ liệu của nhau không?
19. Dữ liệu đi qua bao nhiêu bước biến đổi (transform) từ lúc nhập vào tới lúc hiển thị? Ở mỗi bước, kiểu dữ liệu và giá trị có đúng như kỳ vọng không (in ra kiểm tra từng bước, không suy luận)?
20. Với hệ multi-tenant (như Sentrix): dữ liệu của tenant A có chắc chắn không lộ sang tenant B không? Đã test thử bằng 2 tài khoản thật chưa?
21. Nếu một bước xử lý giữa chừng bị lỗi (ví dụ gọi API bên thứ 3 timeout), dữ liệu có bị lưu ở trạng thái nửa vời (corrupt) không, hay có cơ chế rollback/retry?

---

## IV. Nhóm câu hỏi THUẬT TOÁN / LOGIC NGHIỆP VỤ

22. Với input cụ thể X, thuật toán trả ra output gì — chạy thật và dán kết quả, đừng mô tả bằng lời công thức.
23. Có test case biên (edge case) nào đã thử chưa: input rỗng, input cực lớn, input sai định dạng, số âm, ký tự đặc biệt, tiếng Việt có dấu?
24. Công thức/model (ví dụ churn probability, RFMS...) có thật sự đang chạy trên dữ liệu thật, hay hệ số đang hard-code/giả định để demo cho đẹp?
25. Nếu hai input gần giống nhau (chỉ khác 1 chi tiết nhỏ), output có thay đổi hợp lý tương ứng không, hay bất biến bất thường (dấu hiệu logic không thực sự đọc input)?
26. Thuật toán có được test với bộ dữ liệu độc lập (không phải bộ đã dùng để "tinh chỉnh" cho ra kết quả đẹp) không?
27. Nếu kết quả thuật toán sai, có cách nào truy vết được lỗi nằm ở bước nào (logging từng bước trung gian) hay là một hộp đen không thể debug?

---

## V. Nhóm câu hỏi ĐỘ CHÍNH XÁC KẾT QUẢ ĐẦU RA

28. Con số/kết quả này bạn lấy từ đâu — chạy thực tế hay suy luận theo "thường thì sẽ ra như vậy"?
29. Nếu tôi tự tay tính lại bằng công cụ khác (Excel, tính tay, gọi API trực tiếp bằng Postman), kết quả có khớp không?
30. Đơn vị đo (VNĐ, %, giây, token...) có nhất quán xuyên suốt không, có chỗ nào nhầm đơn vị không?
31. Có làm tròn số ở đâu gây sai lệch tích lũy không (đặc biệt với tiền tệ)?
32. Nếu gọi lại cùng một request 2 lần, kết quả có giống nhau (deterministic) không? Nếu không giống, có giải thích được lý do (random seed, LLM temperature...) không?

---

## VI. Nhóm câu hỏi TRẢI NGHIỆM NGƯỜI DÙNG (UX)

33. Từ lúc người dùng bấm nút tới lúc thấy kết quả mất bao lâu thực tế (đo bằng đồng hồ, không phải ước lượng)? Có loading indicator trong lúc chờ không?
34. Trên thiết bị di động thật (không phải chỉ resize trình duyệt), giao diện có vỡ layout không?
35. Người dùng lớn tuổi/không rành công nghệ có tự thao tác được mà không cần hướng dẫn thêm không?
36. Nếu người dùng bấm nút 2 lần liên tiếp (double-click), hệ thống có xử lý 2 lần / lỗi trùng dữ liệu không?
37. Thông báo lỗi hiển thị cho người dùng có dễ hiểu không, hay là raw error message/stack trace kỹ thuật?
38. Có test thử với người dùng thật (không phải chính đội dev) chưa? Họ có hoàn thành được luồng chính không cần trợ giúp?

---

## VII. Nhóm câu hỏi XỬ LÝ LỖI & EDGE CASE

39. Mất mạng giữa chừng thì sao? App có báo lỗi và cho thử lại không, hay treo vô thời hạn?
40. Server quá tải / rate limit từ API bên thứ 3 (Whisper, Gemini...) bị chặn thì hệ thống phản ứng ra sao — có fallback không hay lỗi toàn bộ pipeline?
41. File/dữ liệu đầu vào sai định dạng hoàn toàn (ví dụ upload ảnh thay vì audio) có được chặn với thông báo rõ ràng không, hay làm sập hệ thống?
42. Có giới hạn (rate limit, kích thước file, độ dài input...) để chống lạm dụng/tấn công không?
43. Nếu một microservice/API phụ thuộc chết hẳn, các phần còn lại của hệ thống có tiếp tục hoạt động được ở mức tối thiểu không (graceful degradation)?

---

## VIII. Nhóm câu hỏi BẢO MẬT & DỮ LIỆU

44. API key, mật khẩu, secret có bị lộ trong code, log, hay response trả về client không?
45. Người dùng A có thể truy cập/sửa dữ liệu của người dùng B bằng cách đổi ID trên URL không (kiểm tra IDOR)?
46. Input người dùng có được validate/sanitize trước khi đưa vào query DB không (chống injection)?
47. Dữ liệu nhạy cảm (số điện thoại, ghi âm giọng nói...) có được mã hóa khi lưu trữ và truyền tải không?

---

## IX. Nhóm câu hỏi HIỆU NĂNG & VẬN HÀNH

48. Hệ thống chịu được bao nhiêu người dùng đồng thời trước khi chậm/sập — đã thử load test chưa hay chỉ đoán?
49. Chi phí vận hành thực tế (API call, hosting) ở mức tải trung bình là bao nhiêu — tính từ số liệu thật hay ước lượng lý thuyết?
50. Có log/monitoring để phát hiện lỗi trong lúc vận hành thật không, hay chỉ biết khi người dùng báo?

---

## X. Nhóm câu hỏi CHUYÊN DÙNG ĐỂ BẮT "ẢO GIÁC" CỦA AI AGENT

Đây là nhóm quan trọng nhất khi nghi ngờ AI đang báo cáo sai:

51. **"Bạn vừa nói X hoạt động — hãy dán nguyên văn output/log của lần chạy đó, không diễn giải lại bằng lời."**
52. **"Dòng code/API/thư viện bạn vừa dùng có thật sự tồn tại không? Cho tôi link tài liệu chính thức."** (AI hay bịa tên hàm/package không tồn tại)
53. **"Bạn đã đọc toàn bộ file đó chưa, hay đang suy đoán nội dung dựa trên tên file?"**
54. **"Nếu tôi chạy lại lệnh này ngay bây giờ trên máy tôi, kết quả có giống hệt bạn vừa báo không? Nếu có sai khác, khả năng do đâu?"**
55. **"Trước đó bạn báo lỗi Y đã sửa xong — nhưng lỗi đó có còn tái hiện không nếu test lại đúng kịch bản ban đầu?"** (AI hay báo "đã fix" nhưng chỉ sửa triệu chứng, chưa test lại root cause)
56. **"Bạn có đang giả định điều gì mà chưa xác minh không? Liệt kê ra."** (ép AI tự khai ra các lỗ hổng giả định)
57. **"Con số/thống kê bạn vừa đưa ra lấy từ nguồn nào? Nếu không có nguồn xác thực, hãy nói rõ đây là ước lượng."**
58. **"Frontend gọi API endpoint nào — đọc thẳng từ code, đừng nhớ lại từ cuộc trò chuyện trước."** (tránh AI dựa vào ngữ cảnh cũ đã lỗi thời)
59. **"Nếu 2 file/2 phần code mâu thuẫn nhau, bạn ưu tiên cái nào và tại sao — bạn đã kiểm tra cả hai chưa hay chỉ đọc 1 cái?"**
60. **"Sau khi sửa, bạn đã chạy lại toàn bộ luồng end-to-end (không chỉ phần vừa sửa) để đảm bảo không phá vỡ chỗ khác chưa?"** (regression check)

---

## XI. Checklist rút gọn — dùng nhanh khi hệ thống báo lỗi

Khi frontend không gọi được backend hoặc có lỗi bất kỳ, đi theo đúng thứ tự này với AI Agent:

1. Log lỗi thật (browser console + network tab + server log) là gì — dán nguyên văn.
2. Request có rời khỏi frontend không? (Network tab: request có xuất hiện không, status code là gì)
3. Nếu request có gửi đi: backend có nhận được không? (server log có ghi nhận request đến không)
4. Nếu backend nhận được: xử lý có lỗi ở đâu? (log traceback đầy đủ)
5. Nếu backend xử lý xong: response gửi về đúng format frontend cần không?
6. Nếu response đúng: frontend parse/hiển thị có lỗi ở đâu (console error)?
7. Ở mỗi bước trên, yêu cầu AI **dán bằng chứng thật**, không chấp nhận "chắc là do..." khi chưa kiểm tra.

---

*Ghi chú: bộ câu hỏi này mang tính khung tổng quát, áp dụng được cho bất kỳ dự án phần mềm nào (kể cả Sentrix). Với từng dự án cụ thể, nên bổ sung thêm câu hỏi riêng theo đặc thù kiến trúc (ví dụ với Sentrix: pipeline Whisper→Gemini→Firestore→React cần thêm câu hỏi kiểm tra riêng cho từng chặng).*
