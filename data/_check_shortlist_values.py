import json
from collections import Counter

with open('nt_predictions_2026-06-28.json') as f:
    data = json.load(f)
    hc_picks = data.get('highConfidencePicks', [])
    
    modes = Counter()
    for pick in hc_picks:
        mode = pick.get('shortlistResolvedMode', 'NOT_SET')
        modes[mode] += 1
    
    print("shortlistResolvedMode values in NT predictions:")
    for mode, count in sorted(modes.items()):
        print(f"  {mode}: {count}")
    
    print(f"\nTotal HC picks: {len(hc_picks)}")
