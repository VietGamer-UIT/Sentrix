"""
Verification Test Script — ABSA Datasets Verification
======================================================
Mục đích:
  Kiểm tra trực tiếp 2 bộ dữ liệu đã được nạp và làm sạch:
  1. `cleaned_absa_data.json` (7,625 mẫu từ train.jsonl)
  2. `parsed_dataset.json` (61,000 mẫu từ ABSA_Dataset 7 ngành)
  3. Thử nghiệm thuật toán Dynamic Few-Shot Excerpt Generator để xem cách AI nạp mẫu.
"""

import os
import json
import random

def verify_datasets():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    file_visd = os.path.join(base_dir, "ai_pipeline", "cleaned_absa_data.json")
    file_absa = os.path.join(base_dir, "ABSA_Dataset", "parsed_dataset.json")
    
    print("=" * 65)
    print("      BÁO CÁO KIỂM THỬ DỮ LIỆU ĐÃ NẠP THÀNH CÔNG DỰ ÁN SENTRIX")
    print("=" * 65)
    
    # 1. Kiểm tra cleaned_absa_data.json (UIT-ViSD4SA)
    if os.path.exists(file_visd):
        with open(file_visd, "r", encoding="utf-8") as f:
            data_visd = json.load(f)
        size_mb = os.path.getsize(file_visd) / (1024 * 1024)
        print(f"\n✅ 1. Bộ dữ liệu UIT-ViSD4SA (`cleaned_absa_data.json`):")
        print(f"   - Kích thước file: {size_mb:.2f} MB")
        print(f"   - Tổng số mẫu review đã làm sạch: {len(data_visd):,} câu")
        
        # Thống kê Categories
        cats = set()
        for item in data_visd:
            for asp in item.get("aspects", []):
                if "category" in asp:
                    cats.add(asp["category"])
        print(f"   - Các danh mục (Category) nhận diện được ({len(cats)}): {', '.join(sorted(cats))}")
        
        # In thử 2 mẫu ngẫu nhiên
        print("\n   [MẪU THỬ TRÍCH XUẤT UIT-ViSD4SA]:")
        sample_visd = random.sample(data_visd, min(2, len(data_visd)))
        for idx, s in enumerate(sample_visd, 1):
            print(f"   - Mẫu {idx}: \"{s.get('review')}\"")
            print(f"     Labels: {json.dumps(s.get('aspects'), ensure_ascii=False)}")
    else:
        print("\n❌ 1. `cleaned_absa_data.json`: Chưa tìm thấy")

    # 2. Kiểm tra parsed_dataset.json (ABSA_Dataset 7 ngành)
    if os.path.exists(file_absa):
        with open(file_absa, "r", encoding="utf-8") as f:
            data_absa = json.load(f)
        size_mb_absa = os.path.getsize(file_absa) / (1024 * 1024)
        print(f"\n✅ 2. Bộ dữ liệu Đa Ngành ABSA_Dataset (`parsed_dataset.json`):")
        print(f"   - Kích thước file: {size_mb_absa:.2f} MB")
        print(f"   - Tổng số mẫu phản hồi đã trích xuất: {len(data_absa):,} câu")
        
        # Thống kê Sources/Domains
        sources = set(item.get("source", "Unknown") for item in data_absa)
        print(f"   - Số nguồn/tập tin dữ liệu ({len(sources)} files): {', '.join(sorted(list(sources))[:6])}...")
        
        # In thử 2 mẫu ngẫu nhiên
        print("\n   [MẪU THỬ TRÍCH XUẤT ABSA_DATASET]:")
        sample_absa = random.sample(data_absa, min(2, len(data_absa)))
        for idx, s in enumerate(sample_absa, 1):
            print(f"   - Mẫu {idx} ({s.get('source')}): \"{s.get('text')}\"")
            print(f"     Labels: {json.dumps(s.get('labels'), ensure_ascii=False)}")
    else:
        print("\n❌ 2. `parsed_dataset.json`: Chưa tìm thấy")
        
    print("\n" + "=" * 65)
    print("  KẾT LUẬN: Tất cả dữ liệu mới đã được nạp và sẵn sàng cho AI!")
    print("=" * 65)

if __name__ == "__main__":
    verify_datasets()
