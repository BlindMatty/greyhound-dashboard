import json

with open('nt_predictions_2026-06-28.json') as f:
    data = json.load(f)
    
    # Find Race 8 at DAR
    target_race = None
    for race in data.get('races', []):
        if race.get('track') == 'DAR' and race.get('raceNumber') == 8:
            target_race = race
            break
    
    if target_race:
        print(f"Race 8 at DAR (raceId: {target_race.get('raceId')})")
        print(f"Start time: {target_race.get('start_time')}")
        
        # Check highConfidencePicks
        hc_picks = data.get('highConfidencePicks', [])
        race_hc_picks = [p for p in hc_picks if p.get('raceNumber') == 8 and p.get('track') == 'DAR']
        
        print(f"\nHigh confidence picks for this race: {len(race_hc_picks)}")
        for pick in race_hc_picks:
            print(f"  Dog: {pick.get('dog')}")
            print(f"    isMlSpecialist: {pick.get('isMlSpecialist')}")
            print(f"    isEloEns: {pick.get('isEloEns')}")
            print(f"    shortlistResolvedMode: {pick.get('shortlistResolvedMode')}")
        
        # Check all dogs in the race
        print(f"\nAll dogs in race:")
        for dog in target_race.get('dogs', []):
            print(f"  {dog.get('dog')} (box {dog.get('box')})")
