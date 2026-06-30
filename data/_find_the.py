import csv
from datetime import datetime

BETTING_CSV = r'D:\Modeling\Greyhounds\data\June 14 to 28.csv'

with open(BETTING_CSV, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        placed = row['Placed'].strip()
        desc = row['Description']
        try:
            date_part = placed.split()[0]
            date_obj = datetime.strptime(date_part, '%d-%b-%y')
            date_str = date_obj.strftime('%Y-%m-%d')
            if '2026-06-14' <= date_str <= '2026-06-28':
                if ' The ' in desc or desc.startswith('The '):
                    print(f"Line {i+2}: {date_str}: {desc}")
        except:
            pass
