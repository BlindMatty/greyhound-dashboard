import json

with open('nsw_predictions_2026-06-20.json') as f:
    data = json.load(f)
    for race in data.get('races', []):
        if race.get('track') == 'WPK':
            print(f"WPK: Race {race.get('raceNumber')} at {race.get('start_time')}")
            # Check if this matches the bet
            # Bet: 19:16 The Gardens 8. Zipper Moon-Win
            # Time: 19:16 (7:16 PM)
            if race.get('start_time') == '7:16PM' and race.get('raceNumber') == 8:
                print("  MATCH FOUND!")
                for dog in race.get('dogs', []):
                    if 'ZIPPER MOON' in str(dog.get('dog', '')).upper():
                        print(f"    Dog: {dog.get('dog')} (box {dog.get('box')})")
                break
