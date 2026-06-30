#!/usr/bin/env python3
"""
Simplified analysis of June 14-28 betting data.

Just match bets by dog name and track to highConfidencePicks.
"""

import csv
import json
import os
import re
from collections import defaultdict
from datetime import datetime

# Configuration
BETTING_CSV = r'D:\Modeling\Greyhounds\data\June 14 to 28.csv'
PREDICTION_DIR = r'D:\Modeling\greyhound-dashboard\data'
STATES = ['vic', 'nsw', 'qld', 'wa', 'sa', 'tas', 'nz', 'nt']

# Great POT tracks (for green dot)
GREAT_POT_TRACKS = {'QTT', 'GAW', 'CAN', 'BHL', 'WAN', 'MBS'}

# Track aliases - comprehensive mapping
TRACK_CODE_ALIASES = {
    'Q2 PARKLANDS': 'QTT',
    'Q2': 'QTT',
    'PARKLANDS': 'QTT',
    'Q1 LAKESIDE': 'QST',
    'Q1': 'QST',
    'LAKESIDE': 'QST',
    'Q': 'QOT',
    'CANNINGTON': 'CAN',
    'CAN': 'CAN',
    'GAWLER': 'GAW',
    'BULLI': 'BHL',
    'BROKEN HILL': 'BHL',
    'BROKEN': 'BHL',
    'WANGANUI': 'WAN',
    'HATRICK': 'WAN',
    'MURRAY BRIDGE STRAIGHT': 'MBS',
    'MURRAY BRIDGE': 'MBS',
    'DARWIN': 'DAR',
    'ROCKHAMPTON': 'ROC',
    'MANUKAU': 'MAN',
    'ADDINGTON': 'AUK',
    'HEALESVILLE': 'HVL',
    'SHEPPARTON': 'SHP',
    'GEELONG': 'GEL',
    'BENDIGO': 'BEN',
    'BALLARAT': 'BAL',
    'TRANALGON': 'TRA',
    'SALE': 'SLE',
    'MANDURAH': 'MAN',
    'RICHMOND': 'RIC',
    'NOWRA': 'NOW',
    'TOWNSVILLE': 'TOW',
    'CAPALABA': 'CAP',
    'CASINO': 'CAS',
    'DUBBO': 'DUB',
    'GOSFORD': 'GOS',
    'GOULBURN': 'GBN',
    'GRAFTON': 'GRA',
    'THE GARDENS': 'GAR',
    'THE': 'GAR',
    'GUNNEDAH': 'GUN',
    'HORSHAM': 'HOR',
    'LAUNCESTON': 'LCN',
    'MAITLAND': 'MEA',
    'MOUNT': 'MTG',
    'NORTHAM': 'NOR',
    'SANDOWN': 'SAN',
    'WARRNAMBOOL': 'WBL',
    'WARRAGUL': 'WGL',
    'ANGLE': 'APK',
    'ANGLE PARK': 'APK',
    'CAMBRIDGE': 'CCH',
    'HOBART': 'HOB',
    'TAREE': 'TAR',
    'MOE': 'PNN',
}


def normalize_track_code(track):
    """Normalize track code to check against GREAT_POT_TRACKS."""
    if not track:
        return ''
    raw = str(track).strip().upper()
    return TRACK_CODE_ALIASES.get(raw, raw)


def is_great_pot_track(track):
    """Check if a track is a great POT track (green dot)."""
    normalized = normalize_track_code(track)
    return normalized in GREAT_POT_TRACKS


def extract_bet_info(description):
    """Extract track, box number, and dog name from bet description.
    
    Format: "HH:MM Track BOX. DogName-Win | ..."
    """
    # Remove everything after the pipe
    desc = description.split('|')[0].strip()
    
    # Pattern: TIME TRACK BOX. DOG_NAME-Win
    pattern = r'^(\d+:\d+)\s+(\S+)\s+(\d+)\.\s+([^-]+)-Win\s*$'
    match = re.match(pattern, desc)
    
    if match:
        track = match.group(2)
        box_num = int(match.group(3))
        dog_name = match.group(4).strip()
        return track, box_num, dog_name
    
    # Try alternative pattern without time
    pattern2 = r'^(\S+)\s+(\d+)\.\s+([^-]+)-Win\s*$'
    match2 = re.match(pattern2, desc)
    
    if match2:
        track = match2.group(1)
        box_num = int(match2.group(2))
        dog_name = match2.group(3).strip()
        return track, box_num, dog_name
    
    # If all else fails
    return desc, 0, desc


def load_betting_data():
    """Load betting data from CSV."""
    bets = []
    with open(BETTING_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            bets.append(row)
    return bets


def load_all_picks_for_date(date_str):
    """Load all high confidence picks for a given date across all states."""
    all_picks = []
    
    for state in STATES:
        filename = f"{state}_predictions_{date_str}.json"
        filepath = os.path.join(PREDICTION_DIR, filename)
        
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for pick in data.get('highConfidencePicks', []):
                        pick_copy = dict(pick)
                        pick_copy['_state'] = state
                        all_picks.append(pick_copy)
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
    
    return all_picks


def match_bet_to_pick_simple(bet, picks):
    """Match bet to pick by track and dog name."""
    track, box_num, dog_name = extract_bet_info(bet['Description'])
    
    bet_track = normalize_track_code(track)
    bet_dog = str(dog_name).strip().upper()
    
    # First try: exact track and dog name match
    for pick in picks:
        pick_track = normalize_track_code(pick.get('track', ''))
        pick_dog = str(pick.get('dog', '')).strip().upper()
        
        if pick_track == bet_track and pick_dog == bet_dog:
            # Verify box if available
            pick_box = pick.get('box', None)
            if pick_box is not None and box_num > 0:
                if int(pick_box) == box_num:
                    return pick
            else:
                return pick
    
    # Second try: just dog name match (in case track alias is wrong)
    for pick in picks:
        pick_dog = str(pick.get('dog', '')).strip().upper()
        if pick_dog == bet_dog:
            return pick
    
    return None


def categorize_pick(pick):
    """Categorize a pick based on its properties."""
    categories = []
    
    is_ml_specialist = pick.get('isMlSpecialist', False)
    is_elo_ens = pick.get('isEloEns', False)
    track = pick.get('track', '')
    is_green_dot = is_great_pot_track(track)
    
    # For bet badge
    shortlist_mode = str(pick.get('shortlistResolvedMode', '')).strip().lower()
    has_bet_badge = (shortlist_mode == 'bet')
    
    # Only categorize if it's an ML TS pick
    if not is_ml_specialist:
        return ['Other']
    
    # Category 1: ML TS + Elo
    if is_elo_ens:
        categories.append('ML TS + Elo')
    
    # Category 2: ML TS + green dot
    if is_green_dot:
        categories.append('ML TS + green dot')
    
    # Category 3: ML TS + bet badge
    if has_bet_badge:
        categories.append('ML TS + bet badge')
    
    # Category 4: ML TS + bet badge + green dot
    if has_bet_badge and is_green_dot:
        categories.append('ML TS + bet badge + green dot')
    
    # Always include ML TS
    categories.append('ML TS')
    
    return categories


def calculate_pot(total_profit, total_stake):
    """Calculate Profit on Turnover."""
    if total_stake == 0:
        return 0.0
    return (total_profit / total_stake) * 100


def main():
    print("Loading betting data...")
    bets = load_betting_data()
    print(f"Loaded {len(bets)} bets")
    
    # Filter for June 14-28 only
    filtered_bets = []
    for bet in bets:
        placed = bet['Placed'].strip()
        try:
            date_part = placed.split()[0]
            date_obj = datetime.strptime(date_part, '%d-%b-%y')
            date_str = date_obj.strftime('%Y-%m-%d')
            if '2026-06-14' <= date_str <= '2026-06-28':
                bet['_date'] = date_str
                filtered_bets.append(bet)
        except Exception as e:
            print(f"Warning: Could not parse date '{placed}': {e}")
    
    print(f"Bets in June 14-28: {len(filtered_bets)}")
    
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
    
    # Process each date
    for date_str, date_bets in sorted(bets_by_date.items()):
        print(f"\nProcessing {date_str} ({len(date_bets)} bets)...")
        
        # Load all picks for this date
        picks = load_all_picks_for_date(date_str)
        print(f"  Loaded {len(picks)} picks")
        
        for bet in date_bets:
            matched_pick = match_bet_to_pick_simple(bet, picks)
            
            if matched_pick:
                categories = categorize_pick(matched_pick)
                
                stake = float(str(bet['Stake (AUD)']).replace('$', '').strip() or 0)
                profit_str = str(bet['Profit/Loss']).replace('$', '').replace(',', '').strip()
                profit = float(profit_str) if profit_str else 0
                
                for category in categories:
                    category_stats[category]['total_stake'] += stake
                    category_stats[category]['total_profit'] += profit
                    category_stats[category]['total_bets'] += 1
            else:
                unmatched_count += 1
    
    # Print results
    print("\n" + "="*80)
    print("RESULTS (June 14-28 only)")
    print("="*80)
    
    target_categories = [
        'ML TS + Elo',
        'ML TS + green dot',
        'ML TS + bet badge',
        'ML TS + bet badge + green dot',
        'ML TS',
        'Other'
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
