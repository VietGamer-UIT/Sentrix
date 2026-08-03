# Sentrix AI Pipeline

Thư mục này chứa các thành phần cốt lõi xử lý AI (Whisper, Librosa, ABSA, LLM Fusion, RFMS) của dự án.

## Dữ liệu ABSA (`cleaned_absa_data.json`)

Do kích thước lớn, file dữ liệu đã làm sạch `cleaned_absa_data.json` **KHÔNG** được lưu trữ trên Git để tối ưu repository. 

Nếu bạn cần chạy hoặc test các tính năng ABSA, vui lòng tái tạo file này bằng cách:

1. Tải bộ dữ liệu gốc UIT-ViSD4SA từ nguồn: [https://github.com/kimkim00/UIT-ViSD4SA](https://github.com/kimkim00/UIT-ViSD4SA). (Đã có sẵn trong thư mục `backend/UIT-ViSD4SA` nếu bạn clone đủ).
2. Chạy script parser để làm sạch và sinh file JSON:
   ```bash
   python backend/ai_pipeline/data_parser.py
   ```
3. Sau khi chạy xong, file `backend/ai_pipeline/cleaned_absa_data.json` sẽ được tự động tạo ra và sẵn sàng cho lõi LLM sử dụng.
