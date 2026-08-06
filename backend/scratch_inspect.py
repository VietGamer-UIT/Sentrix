import csv
import glob

with open('backend/scratch_out.txt', 'w', encoding='utf-8') as out:
    for f in glob.glob('backend/ABSA_Dataset/ABSA_Dataset/*/*.*'):
        out.write(f"\n--- {f} ---\n")
        if f.endswith('.csv'):
            with open(f, encoding='utf-8') as file:
                reader = csv.reader(file)
                for _ in range(3):
                    try:
                        out.write(str(next(reader, None)) + "\n")
                    except StopIteration:
                        break
        else:
            with open(f, encoding='utf-8') as file:
                out.write(''.join(file.readlines()[:5]) + "\n")
