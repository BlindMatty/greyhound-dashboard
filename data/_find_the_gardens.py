import json

with open('nsw_predictions_2026-06-20.json') as f:
    data = json.load(f)
    
    # Look for The Gardens or similar
    for race in data.get('races', []):
        track = race.get('track', '')
        if track not in ['APK', 'AUK', 'BAL', 'BEN', 'BHL', 'BUL', 'CAN', 'CAP', 'CAS', 'CCH', 'DAR', 'DHO', 'DUB', 'GAR', 'GAW', 'GBN', 'GEL', 'GOS', 'GRA', 'GUN', 'HOB', 'HOR', 'HVL', 'LCN', 'MAN', 'MBR', 'MEA', 'MEP', 'MTG', 'NOR', 'NOW', 'PNN', 'QOT', 'QST', 'QTT', 'RIC', 'RIS', 'ROC', 'SAN', 'SAP', 'SHP', 'SLE', 'SOU', 'TAR', 'TEM', 'TOW', 'TRA', 'WAG', 'WAK', 'WAN', 'WBL', 'WGL', 'WNS', 'WPK']:
            print(f"Unknown track code: {track}")
