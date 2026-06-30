import json

with open('vic_predictions_2026-06-14.json') as f:
    data = json.load(f)
    hc_picks = data.get('highConfidencePicks', [])
    
    print(f"Total HC picks: {len(hc_picks)}")
    if hc_picks:
        print("\nFirst pick keys:")
        for key in sorted(hc_picks[0].keys()):
            print(f"  {key}")
        
        print("\nSample pick:")
        print(json.dumps(hc_picks[0], indent=2))
