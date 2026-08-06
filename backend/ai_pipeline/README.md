# Sentrix AI Pipeline

Thư mục này chứa các thành phần cốt lõi xử lý AI (Whisper, Librosa, ABSA, LLM Fusion, RFMS) của dự án.

## Dữ liệu ABSA_Dataset và UIT-ViSD4SA

Do kích thước cực lớn, các file dữ liệu thô (ví dụ: `ABSA_Dataset/`, `UIT-ViSD4SA/`) và file dữ liệu đã parse (`parsed_dataset.json`, `cleaned_absa_data.json`) **KHÔNG** được lưu trữ trên Git để tránh phình to repository.

Nếu bạn cần chạy hoặc test các tính năng ABSA bằng bộ dữ liệu đa lĩnh vực (7 domains: Beauty, Education, Hotel, Mother, Phone, Restaurant, Technology), vui lòng tái tạo file dữ liệu bằng cách:

1. Đảm bảo thư mục gốc của dataset (ví dụ: `ABSA_Dataset/`) được đặt tại `backend/ABSA_Dataset/ABSA_Dataset/`.
2. Chạy script parser để làm sạch và sinh file JSON tổng hợp:
   ```bash
   python backend/scripts/parse_absa_datasets.py
   ```
3. Sau khi chạy xong, file `backend/ABSA_Dataset/parsed_dataset.json` sẽ được tự động tạo ra chứa cấu trúc thống nhất sẵn sàng cho lõi LLM sử dụng (Few-shot prompting).
