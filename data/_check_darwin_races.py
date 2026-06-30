import json

with open('nt_predictions_2026-06-28.json') as f:
    data = json.load(f)
    for race in data.get('races', []):
        if race.get('track') == 'DAR':
            print(f"Race {race.get('raceNumber')} at {race.get('start_time')}")
