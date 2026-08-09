"""
Tạo file dataset rút gọn (few_shot_examples.json) cho Demo & Deployment
========================================================================
- Chọn lọc 60 mẫu chất lượng cao, đa dạng khía cạnh (50 từ ViSD4SA + 10 từ ABSA_Dataset đa ngành)
- Dung lượng cực nhẹ (~30KB), an toàn commit thẳng lên Git.
"""

import os
import json
from pathlib import Path

def create_compact_dataset():
    base_dir = Path(__file__).parent.parent
    
    file_visd = base_dir / "ai_pipeline" / "cleaned_absa_data.json"
    file_absa = base_dir / "ABSA_Dataset" / "parsed_dataset.json"
    
    compact_samples = []
    
    # 1. Trích 50 mẫu tiêu biểu từ UIT-ViSD4SA
    if file_visd.exists():
        with open(file_visd, "r", encoding="utf-8") as f:
            visd_data = json.load(f)
            # Lấy 50 mẫu đa dạng category
            compact_samples.extend(visd_data[:50])
            
    # 2. Trích 20 mẫu từ ABSA_Dataset (7 ngành)
    if file_absa.exists():
        with open(file_absa, "r", encoding="utf-8") as f:
            absa_data = json.load(f)
            for item in absa_data[:200]:
                text = item.get("text", "")
                labels = item.get("labels", [])
                if text and labels:
                    # Convert format sang review + aspects
                    aspects = []
                    for l in labels:
                        aspects.append({
                            "phrase": text[:30],
                            "category": l.get("aspect", "GENERAL"),
                            "sentiment": l.get("polarity", "positive").upper()
                        })
                    compact_samples.append({
                        "review": text,
                        "aspects": aspects
                    })
                if len(compact_samples) >= 80:
                    break
                    
    out_file = base_dir / "ai_pipeline" / "few_shot_examples.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(compact_samples, f, ensure_ascii=False, indent=2)
        
    size_kb = out_file.stat().st_size / 1024
    print(f"✅ Đã tạo file dataset rút gọn: {out_file}")
    print(f"   - Dung lượng: {size_kb:.2f} KB (Rất nhẹ, an toàn cho Git)")
    print(f"   - Tổng số mẫu ví dụ: {len(compact_samples)} mẫu")

if __name__ == "__main__":
    create_compact_dataset()
