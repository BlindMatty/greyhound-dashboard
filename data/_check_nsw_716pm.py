import json

with open('nsw_predictions_2026-06-20.json') as f:
    data = json.load(f)
    for race in data.get('races', []):
        if race.get('start_time') == '7:16PM':
            print(f"Race at 7:16 PM: {race.get('track')} Race {race.get('raceNumber')}")
            for dog in race.get('dogs', []):
                print(f"  {dog.get('dog')}")
