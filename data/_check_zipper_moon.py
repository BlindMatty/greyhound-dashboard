import json

with open('nsw_predictions_2026-06-20.json') as f:
    data = json.load(f)
    hc_picks = data.get('highConfidencePicks', [])
    
    for pick in hc_picks:
        if 'ZIPPER MOON' in str(pick.get('dog', '')).upper():
            print(f"Found Zipper Moon in HC picks:")
            print(f"  Track: {pick.get('track')}")
            print(f"  Race: {pick.get('raceNumber')}")
            print(f"  Box: {pick.get('box')}")
            print(f"  isMlSpecialist: {pick.get('isMlSpecialist')}")
            print(f"  isEloEns: {pick.get('isEloEns')}")
            print(f"  shortlistResolvedMode: {pick.get('shortlistResolvedMode', 'NOT SET')}")
            break
    else:
        print("Zipper Moon not found in HC picks")
