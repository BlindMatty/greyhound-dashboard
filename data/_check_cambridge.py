import json

with open('nz_predictions_2026-06-18.json') as f:
    data = json.load(f)
    tracks = set(r.get('track', '') for r in data.get('races', []))
    print('NZ tracks:', sorted(tracks))
