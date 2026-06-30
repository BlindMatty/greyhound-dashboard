#!/usr/bin/env python3
"""
Analyze POT for specific dates (June 9, 12, 24) for the dashboard card selections.
Excluding pure ML TS top picks.
"""

import csv
import json
import os
import re
from collections import defaultdict
from datetime import datetime

# Configuration
BETTING_FILES = [
    r'D:\Modeling\Greyhounds\data\May 5 to June 14.csv',  # Covers June 9, 12
    r'D:\Modeling\Greyhounds\data\June 14 to 28.csv',   # Covers June 24
]
PREDICTION_DIR = r'D:\Modeling\greyhound-dashboard\data'
STATES = ['vic', 'nsw', 'qld', 'wa', 'sa', 'tas', 'nz', 'nt']

# Great POT tracks (for green dot)
GREAT_POT_TRACKS = {'QTT', 'GAW', 'CAN', 'BHL', 'WAN', 'MBS'}

# Track aliases
TRACK_CODE_ALIASES = {
    'Q2 PARKLANDS': 'QTT', 'Q2': 'QTT', 'PARKLANDS': 'QTT',
    'Q1 LAKESIDE': 'QST', 'Q1': 'QST', 'LAKESIDE': 'QST',
    'Q1 Lakeside': 'QST', 'Q2 Parklands': 'QTT',
    'QOT': 'QST',  # QOT seems to be another code for Lakeside
    'CANNINGTON': 'CAN', 'GAWLER': 'GAW', 'BULLI': 'BHL',
    'WANGANUI': 'WAN', 'HATRICK': 'WAN',
    'MURRAY BRIDGE STRAIGHT': 'MBS', 'MURRAY BRIDGE': 'MBS',
    'DARWIN': 'DAR', 'ROCKHAMPTON': 'ROC', 'BROKEN HILL': 'BHL',
    'MANUKAU': 'MAN', 'ADDINGTON': 'AUK', 'HEALESVILLE': 'HVL',
    'SHEPPARTON': 'SHP', 'GEELONG': 'GEL', 'BENDIGO': 'BEN',
    'BALLARAT': 'BAL', 'TRANALGON': 'TRA', 'SALE': 'SLE',
    'MANDURAH': 'MAN', 'RICHMOND': 'RIC', 'NOWRA': 'NOW',
    'TOWNSVILLE': 'TOW', 'CAPALABA': 'CAP', 'CASINO': 'CAS',
    'DUBBO': 'DUB', 'GOSFORD': 'GOS', 'GOULBURN': 'GBN',
    'GRAFTON': 'GRA', 'GUNNEDAH': 'GUN', 'HORSHAM': 'HOR',
    'LAUNCESTON': 'LCN', 'MAITLAND': 'MEA', 'MOUNT': 'MTG',
    'NORTHAM': 'NOR', 'SANDOWN': 'SAN', 'WARRNAMBOOL': 'WBL',
    'WARRAGUL': 'WGL', 'ANGLE': 'APK', 'ANGLE PARK': 'APK',
    'CAMBRIDGE': 'CCH', 'HOBART': 'HOB', 'TAREE': 'TAR',
    'THE GARDENS': 'GAR', 'GARDENS': 'GAR',
    'DHO': 'HOB',  # DHO seems to be Hobart
}

TARGET_DATES = ['2026-06-09', '2026-06-12', '2026-06-24']

def normalize_track_code(track):
    if not track:
        return ''
    raw = str(track).strip().upper()
    return TRACK_CODE_ALIASES.get(raw, raw)

def is_great_pot_track(track):
    normalized = normalize_track_code(track)
    return normalized in GREAT_POT_TRACKS

def extract_bet_info(description):
    desc = description.split('|')[0].strip()
    
    # Pattern 1: "HH:MM Track R. DogName-Win" (track and dog can have spaces)
    pattern1 = r'^(\d+:\d+)\s+(.+?)\s+(\d+)\.\s+(.+)-Win\s*$'
    match = re.match(pattern1, desc)
    if match:
        return match.group(2).strip(), int(match.group(3)), match.group(4).strip()
    
    # Pattern 2: "Track R. DogName-Win" (without time, track and dog can have spaces)
    pattern2 = r'^(.+?)\s+(\d+)\.\s+(.+)-Win\s*$'
    match = re.match(pattern2, desc)
    if match:
        return match.group(1).strip(), int(match.group(2)), match.group(3).strip()
    
    # Pattern 3: "HH:MM Track R. DogName-RX DIST GrX |" (with race details, track and dog can have spaces)
    pattern3 = r'^(\d+:\d+)\s+(.+?)\s+(\d+)\.\s+(.+)-[^-]+\s*$'
    match = re.match(pattern3, desc)
    if match:
        return match.group(2).strip(), int(match.group(3)), match.group(4).strip()
    
    # Pattern 4: "Track R. DogName-RX DIST GrX |" (with race details, no time, track and dog can have spaces)
    pattern4 = r'^(.+?)\s+(\d+)\.\s+(.+)-[^-]+\s*$'
    match = re.match(pattern4, desc)
    if match:
        return match.group(1).strip(), int(match.group(2)), match.group(3).strip()
    
    return desc, 0, desc

def load_betting_data():
    all_bets = []
    for file_path in BETTING_FILES:
        if not os.path.exists(file_path):
            continue
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                all_bets.append(row)
    return all_bets

def load_prediction_files_for_date(date_str):
    predictions = {}
    date_formatted = date_str.replace('-', '')
    for state in STATES:
        filename = f"{state}_predictions_{date_str}.json"
        filepath = os.path.join(PREDICTION_DIR, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    predictions[state] = data
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
    return predictions

def get_picks_for_date(date_str):
    predictions = load_prediction_files_for_date(date_str)
    all_picks = []
    for state, data in predictions.items():
        picks = data.get('highConfidencePicks', [])
        for pick in picks:
            pick_copy = dict(pick)
            pick_copy['_state'] = state
            all_picks.append(pick_copy)
    return all_picks

def normalize_dog_name(dog_name):
    """Normalize dog name for comparison - remove punctuation and standardize."""
    if not dog_name:
        return ''
    # Remove apostrophes and other punctuation, then standardize
    normalized = str(dog_name).strip().upper()
    # Remove apostrophes and replace with spaces or nothing
    normalized = normalized.replace("'", "").replace("-", " ")
    # Remove extra spaces
    normalized = ' '.join(normalized.split())
    return normalized

def match_bet_to_pick(bet, picks):
    track, race_num, dog_name = extract_bet_info(bet['Description'])
    bet_track = normalize_track_code(track)
    bet_dog = normalize_dog_name(dog_name)
    
    for pick in picks:
        pick_track = normalize_track_code(pick.get('track', ''))
        pick_dog = normalize_dog_name(pick.get('dog', ''))
        
        if pick_track == bet_track and int(pick.get('raceNumber', 0)) == race_num and pick_dog == bet_dog:
            return pick
    
    # Try just track and dog name match (any race)
    for pick in picks:
        pick_dog = normalize_dog_name(pick.get('dog', ''))
        if pick_dog == bet_dog:
            return pick
    
    # Try track and race number match (any dog)
    for pick in picks:
        pick_track = normalize_track_code(pick.get('track', ''))
        if pick_track == bet_track and int(pick.get('raceNumber', 0)) == race_num:
            return pick
    
    return None

def categorize_pick(pick):
    categories = []
    is_ml_specialist = pick.get('isMlSpecialist', False)
    is_elo_ens = pick.get('isEloEns', False)
    track = pick.get('track', '')
    is_green_dot = is_great_pot_track(track)
    shortlist_mode = str(pick.get('shortlistResolvedMode', '')).strip().lower()
    has_bet_badge = (shortlist_mode == 'bet')
    
    # Only categorize if it's an ML TS pick with additional qualifiers
    if not is_ml_specialist:
        return []
    
    if is_elo_ens:
        categories.append('ML TS + Elo')
    if is_green_dot:
        categories.append('ML TS + green dot')
    if has_bet_badge:
        categories.append('ML TS + bet badge')
    if has_bet_badge and is_green_dot:
        categories.append('ML TS + bet badge + green dot')
    
    return categories

def calculate_pot(total_profit, total_stake):
    if total_stake == 0:
        return 0.0
    return (total_profit / total_stake) * 100

def main():
    print("Loading betting data...")
    all_bets = load_betting_data()
    print(f"Loaded {len(all_bets)} bets from all files")
    
    # Filter for target dates only
    filtered_bets = []
    for bet in all_bets:
        placed = bet['Placed'].strip()
        try:
            date_part = placed.split()[0]
            date_obj = datetime.strptime(date_part, '%d-%b-%y')
            date_str = date_obj.strftime('%Y-%m-%d')
            if date_str in TARGET_DATES:
                bet['_date'] = date_str
                filtered_bets.append(bet)
        except Exception as e:
            print(f"Warning: Could not parse date '{placed}': {e}")
    
    print(f"Bets in target dates {TARGET_DATES}: {len(filtered_bets)}")
    
    # Group bets by date
    bets_by_date = defaultdict(list)
    for bet in filtered_bets:
        bets_by_date[bet['_date']].append(bet)
    
    # Initialize category stats
    category_stats = defaultdict(lambda: {
        'total_stake': 0.0,
        'total_profit': 0.0,
        'total_bets': 0,
    })
    
    unmatched_count = 0
    
    # Process each target date
    for date_str, date_bets in sorted(bets_by_date.items()):
        print(f"\nProcessing {date_str} ({len(date_bets)} bets)...")
        picks = get_picks_for_date(date_str)
        print(f"  Loaded {len(picks)} picks")
        
        for bet in date_bets:
            matched_pick = match_bet_to_pick(bet, picks)
            
            if matched_pick:
                categories = categorize_pick(matched_pick)
                
                # Only include bets that have specific categories (exclude pure ML TS)
                if categories:
                    stake = float(str(bet['Stake (AUD)']).replace('$', '').strip() or 0)
                    profit_str = str(bet['Profit/Loss']).replace('$', '').replace(',', '').strip()
                    profit = float(profit_str) if profit_str else 0
                    
                    for category in categories:
                        category_stats[category]['total_stake'] += stake
                        category_stats[category]['total_profit'] += profit
                        category_stats[category]['total_bets'] += 1
            else:
                unmatched_count += 1
                print(f"  Unmatched: {bet['Placed']}: {bet['Description']}")
    
    # Print results
    print("\n" + "="*80)
    print("RESULTS (June 9, 12, 24 only - Excluding pure ML TS)")
    print("="*80)
    
    target_categories = [
        'ML TS + Elo',
        'ML TS + green dot',
        'ML TS + bet badge',
        'ML TS + bet badge + green dot',
    ]
    
    for category in target_categories:
        if category in category_stats and category_stats[category]['total_bets'] > 0:
            stats = category_stats[category]
            pot = calculate_pot(stats['total_profit'], stats['total_stake'])
            print(f"\n{category}:")
            print(f"  Bets: {stats['total_bets']}")
            print(f"  Total Stake: ${stats['total_stake']:.2f}")
            print(f"  Total Profit: ${stats['total_profit']:.2f}")
            print(f"  POT: {pot:.2f}%")
    
    print(f"\nUnmatched bets: {unmatched_count}")

if __name__ == '__main__':
    main()