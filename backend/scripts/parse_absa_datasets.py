import os
import csv
import json
import glob
import re

def parse_txt_file(filepath):
    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by block like #1, #2...
    blocks = re.split(r'#\d+\n', content)
    for block in blocks:
        lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
        if len(lines) >= 2:
            text = lines[0]
            labels_line = lines[1]
            labels = []
            # Extract {ASPECT, polarity}
            matches = re.findall(r'\{([^,]+),\s*([^}]+)\}', labels_line)
            for aspect, polarity in matches:
                labels.append({
                    "aspect": aspect.strip(),
                    "polarity": polarity.strip().lower()
                })
            if labels:
                results.append({
                    "source": os.path.basename(filepath),
                    "text": text,
                    "labels": labels
                })
    return results

def parse_csv_file(filepath):
    results = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader, [])
        if not headers:
            return results
        
        # Identify text column
        text_col_idx = -1
        for i, h in enumerate(headers):
            h_lower = h.lower()
            if h_lower in ['data', 'cmt', 'text', 'review']:
                text_col_idx = i
                break
        
        if text_col_idx == -1:
            print(f"[Warning] Could not find text column in {filepath}. Headers: {headers}")
            return results
        
        # Identify aspect columns
        ignore_cols = ['id', '', 'Unnamed: 0']
        aspect_cols = {}
        for i, h in enumerate(headers):
            if i != text_col_idx and h.lower() not in ignore_cols:
                aspect_cols[i] = h
        
        for row in reader:
            if not row or len(row) <= text_col_idx:
                continue
            text = row[text_col_idx].strip()
            if not text:
                continue
            
            labels = []
            for i, aspect_name in aspect_cols.items():
                if i < len(row):
                    val = row[i].strip().lower()
                    polarity = None
                    if val in ['positive', '1']:
                        polarity = 'positive'
                    elif val in ['negative', '-1']:
                        polarity = 'negative'
                    elif val in ['neutral', '2']: # assuming 2 is neutral if 0 is not mentioned
                        polarity = 'neutral'
                    
                    if polarity:
                        labels.append({
                            "aspect": aspect_name,
                            "polarity": polarity
                        })
            
            if labels: # Only keep if there are valid labels
                results.append({
                    "source": os.path.basename(filepath),
                    "text": text,
                    "labels": labels
                })
    return results

def main():
    dataset_dir = os.path.join('backend', 'ABSA_Dataset', 'ABSA_Dataset')
    output_file = os.path.join('backend', 'ABSA_Dataset', 'parsed_dataset.json')
    all_data = []
    
    if not os.path.exists(dataset_dir):
        print(f"Directory not found: {dataset_dir}")
        return
        
    for root, dirs, files in os.walk(dataset_dir):
        for file in files:
            filepath = os.path.join(root, file)
            if file.endswith('.txt') and file.lower() != 'read_me.txt':
                print(f"Parsing TXT: {filepath}")
                all_data.extend(parse_txt_file(filepath))
            elif file.endswith('.csv'):
                print(f"Parsing CSV: {filepath}")
                all_data.extend(parse_csv_file(filepath))
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
        
    print(f"\nParsed total {len(all_data)} samples.")
    print(f"Saved to {output_file}")

if __name__ == '__main__':
    main()
