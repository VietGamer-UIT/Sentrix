"""
Data Parser for UIT-ViSD4SA — Trích xuất Aspect-Based Sentiment Analysis (ABSA)
=============================================================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
Mục đích:
- Đọc file JSONL chứa dữ liệu học thuật UIT-ViSD4SA.
- Xử lý lỗi lệch index ký tự (character offset) do file gốc gán nhãn theo Byte Offset (UTF-8).
- Chuyển đổi dữ liệu sang định dạng JSON có cấu trúc chuẩn cho Few-Shot Prompting.
"""

import os
import json
import jsonlines
import logging
from typing import List, Dict, Any

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

def parse_uit_visd4sa(input_filepath: str, output_filepath: str) -> None:
    """
    Đọc dữ liệu raw, cắt chuỗi chính xác dựa trên offset và xuất ra JSON sạch.
    
    Args:
        input_filepath: Đường dẫn đến file train.jsonl
        output_filepath: Đường dẫn lưu file cleaned_absa_data.json
    """
    if not os.path.exists(input_filepath):
        logger.error(f"Không tìm thấy file: {input_filepath}")
        return

    cleaned_data: List[Dict[str, Any]] = []
    
    logger.info(f"Đang xử lý file: {input_filepath}...")
    
    # Mở file .jsonl để đọc
    with jsonlines.open(input_filepath) as reader:
        for obj in reader:
            text: str = obj.get("text", "")
            labels: List[List] = obj.get("labels", [])
            
            # Encode chuỗi sang UTF-8 bytes để fix lỗi lệch index do ký tự Unicode (tiếng Việt)
            text_bytes = text.encode("utf-8")
            
            aspects: List[Dict[str, str]] = []
            
            for label in labels:
                if len(label) != 3:
                    continue
                    
                start_idx, end_idx, cat_polarity = label
                
                # Split Category và Polarity (vd: "GENERAL#POSITIVE" -> "GENERAL", "POSITIVE")
                if "#" not in cat_polarity:
                    continue
                    
                category, sentiment = cat_polarity.split("#", 1)
                
                # CẮT CHUỖI: Dùng byte offset thay vì character offset
                # Sau đó decode ngược lại thành string, bỏ qua lỗi nếu byte bị cắt vỡ (thường là an toàn nếu index chuẩn)
                phrase_bytes = text_bytes[start_idx:end_idx]
                phrase = phrase_bytes.decode("utf-8", errors="ignore").strip()
                
                aspects.append({
                    "phrase": phrase,
                    "category": category,
                    "sentiment": sentiment
                })
            
            # Chỉ lưu những câu có chứa ít nhất 1 aspect
            if aspects:
                cleaned_data.append({
                    "review": text,
                    "aspects": aspects
                })

    # Ghi dữ liệu đã làm sạch ra file JSON
    with open(output_filepath, "w", encoding="utf-8") as out_file:
        json.dump(cleaned_data, out_file, ensure_ascii=False, indent=2)
        
    logger.info(f"Đã xử lý thành công {len(cleaned_data)} câu review.")
    logger.info(f"Dữ liệu sạch đã được lưu tại: {output_filepath}")


if __name__ == "__main__":
    # Đường dẫn tương đối từ thư mục gốc của repo
    INPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "UIT-ViSD4SA", "data", "train.jsonl")
    OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "cleaned_absa_data.json")
    
    parse_uit_visd4sa(INPUT_FILE, OUTPUT_FILE)
