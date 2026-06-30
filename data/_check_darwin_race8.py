import json

with open('nt_predictions_2026-06-28.json') as f:
    data = json.load(f)
    for race in data.get('races', []):
        if race.get('track') == 'DAR' and race.get('raceNumber') == 8:
            print(f"Race 8 at DAR:")
            for dog in race.get('dogs', []):
                print(f"  {dog.get('dog')}")
            break
