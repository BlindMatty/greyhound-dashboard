import csv
from datetime import datetime

BETTING_CSV = r'D:\Modeling\Greyhounds\data\June 14 to 28.csv'

# Load betting data
with open(BETTING_CSV, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    bets = list(reader)

# Filter for June 14-28
filtered_bets = []
for bet in bets:
    placed = bet['Placed'].strip()
    try:
        date_part = placed.split()[0]
        date_obj = datetime.strptime(date_part, '%d-%b-%y')
        date_str = date_obj.strftime('%Y-%m-%d')
        if '2026-06-14' <= date_str <= '2026-06-28':
            bet['_date'] = date_str
            filtered_bets.append(bet)
    except:
        pass

print(f"Total bets in June 14-28: {len(filtered_bets)}")

# Extract track names from all bets
from collections import Counter
import re

track_names = Counter()
for bet in filtered_bets:
    desc = bet['Description']
    # Extract track (second token)
    parts = desc.split()
    if len(parts) >= 2:
        track = parts[1]
        track_names[track] += 1

print("\nTrack distribution in June 14-28 bets:")
for track, count in sorted(track_names.items()):
    print(f"  {track}: {count}")
