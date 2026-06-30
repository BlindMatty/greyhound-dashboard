import csv
from datetime import datetime

BETTING_CSV = r'D:\Modeling\Greyhounds\data\June 14 to 28.csv'

with open(BETTING_CSV, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        desc = row['Description']
        if 'The' in desc and 'The Gardens' not in desc and 'The ' in desc:
            # Check if "The" is a standalone word (track name)
            parts = desc.split()
            for j, part in enumerate(parts):
                if part == 'The' and j > 0 and j < len(parts) - 1:
                    # This might be the track name
                    # Check if it's followed by a number and dot
                    if j + 1 < len(parts) and '.' in parts[j+1]:
                        print(f"Line {i+2}: {row['Placed']}: {desc}")
                        break
