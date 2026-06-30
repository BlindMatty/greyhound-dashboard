import json

# Check a few prediction files for shortlistResolvedMode
files = [
    'vic_predictions_2026-06-14.json',
    'nt_predictions_2026-06-28.json',
    'qld_predictions_2026-06-14.json'
]

for filename in files:
    try:
        with open(filename) as f:
            data = json.load(f)
            hc_picks = data.get('highConfidencePicks', [])
            has_shortlist = any('shortlistResolvedMode' in p for p in hc_picks)
            print(f"{filename}: has shortlistResolvedMode: {has_shortlist}")
            if hc_picks:
                sample = hc_picks[0]
                if 'shortlistResolvedMode' in sample:
                    print(f"  Sample: {sample.get('dog')} -> {sample.get('shortlistResolvedMode')}")
    except Exception as e:
        print(f"{filename}: Error - {e}")
