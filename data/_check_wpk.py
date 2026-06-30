import json

with open('nsw_predictions_2026-06-18.json') as f:
    data = json.load(f)
    for race in data.get('races', []):
        if race.get('track') == 'WPK':
            print(f"WPK race: {race.get('raceNumber')} at {race.get('start_time')}")
            for dog in race.get('dogs', []):
                print(f"  {dog.get('dog')}")
            break
