#!/usr/bin/env python3
"""
Analyze June 14-28 betting data and categorize by dashboard card types.

Categories:
1. ML TS + Elo top pick (isMlSpecialist && isEloEns)
2. ML TS + green dot picks (isMlSpecialist && isGreenDotPick)
3. ML TS + bet badge top picks (isMlSpecialist && hasBetBadge)
4. ML TS + bet badge + green dot top picks (isMlSpecialist && isGreenDotPick && hasBetBadge)

POT = Profit on Turnover = (Total Profit / Total Stake) * 100
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

# Track aliases - mapping from betting track names to prediction track codes
TRACK_CODE_ALIASES = {
    'Q2 PARKLANDS': 'QTT',
    'Q2': 'QTT',
    'PARKLANDS': 'QTT',
    'CANNINGTON': 'CAN',
    'GAWLER': 'GAW',
    'BULLI': 'BHL',
    'WANGANUI': 'WAN',
    'HATRICK': 'WAN',
    'MURRAY BRIDGE STRAIGHT': 'MBS',
    'MURRAY BRIDGE': 'MBS',
    'DARWIN': 'DAR',
    'ROCKHAMPTON': 'ROC',
    'BROKEN HILL': 'BHL',  # Need to verify
    'MANUKAU': 'MAN',  # Need to verify
    'ADDINGTON': 'AUK',  # Need to verify
    'HEALESVILLE': 'HVL',
    'SHEPPARTON': 'SHP',
    'GEELONG': 'GEL',
    'BENDIGO': 'BEN',
    'BALLARAT': 'BAL',
    'TRANALGON': 'TRA',
    'SALE': 'SLE',
    'MANDURAH': 'MAN',  # Might conflict with Manukau
    'RICHMOND': 'RIC',
    'NOWRA': 'NOW',
    'TOWNSVILLE': 'TOW',
    'CAPALABA': 'CAP',
    'CASINO': 'CAS',
    'DUBBO': 'DUB',
    'GOSFORD': 'GOS',
    'GOULBURN': 'GBN',
    'GRAFTON': 'GRA',
    'GUNNEDAH': 'GUN',
    'HORSHAM': 'HOR',
    'LAUNCESTON': 'LCN',
    'MAITLAND': 'MEA',
    'MOUNT': 'MTG',  # Mount Gambier?
    'NORTHAM': 'NOR',
    'SOUTHERN': 'SAN',  # Southern Cross?
    'TAMWORTH': 'TEM',  # Temora?
    'WAGGA': 'WAG',
    'WARRNAMBOOL': 'WBL',
    'WARRAGUL': 'WGL',
    'SANDOWN': 'SHP',  # Sandown might be SHP or SAN
    'ALBURY': 'WNS',  # Wentworth?
    'Q1': 'QST',  # Q1 Lakeside
    'Q': 'QOT',  # Generic Q track
    'ANGLE': 'APK',  # Angle Park
    'ASCOT': 'ASC',  # Need to check if this exists
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
    """Extract track, race number, and dog name from bet description."""
    # Pattern: "HH:MM Track X. DogName-Win | Betfair Bet ID..."
    # Example: "21:24 Darwin 5. Brittain On Fire-Win | Betfair Bet ID 1:433531634851"
    
    # Remove everything after the pipe
    desc = description.split('|')[0].strip()
    
    # Pattern: TIME TRACK RACE_NUM. DOG_NAME-Win
    # Use regex to extract
    pattern = r'^(\d+:\d+)\s+(\S+)\s+(\d+)\.\s+([^-]+)-Win\s*$'
    match = re.match(pattern, desc)
    
    if match:
        time_str = match.group(1)
        track = match.group(2)
        race_num = int(match.group(3))
        dog_name = match.group(4).strip()
        return track, race_num, dog_name
    
    # Try alternative pattern without time
    pattern2 = r'^(\S+)\s+(\d+)\.\s+([^-]+)-Win\s*$'
    match2 = re.match(pattern2, desc)
    
    if match2:
        track = match2.group(1)
        race_num = int(match2.group(2))
        dog_name = match2.group(3).strip()
        return track, race_num, dog_name
    
    # If all else fails, return raw description
    return desc, 0, desc


def load_betting_data():
    """Load betting data from CSV."""
    bets = []
    with open(BETTING_CSV, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            bets.append(row)
    return bets


def load_prediction_files_for_date(date_str):
    """Load all prediction files for a given date."""
    predictions = {}
    date_formatted = date_str.replace('-', '')  # e.g., "20260614"
    
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
    """Get all high confidence picks for a given date."""
    predictions = load_prediction_files_for_date(date_str)
    all_picks = []
    
    for state, data in predictions.items():
        picks = data.get('highConfidencePicks', [])
        for pick in picks:
            # Add state information
            pick_copy = dict(pick)
            pick_copy['_state'] = state
            all_picks.append(pick_copy)
    
    return all_picks


def match_bet_to_pick(bet, picks):
    """Try to match a bet to a prediction pick."""
    track, race_num, dog_name = extract_bet_info(bet['Description'])
    
    for pick in picks:
        # Normalize track names for comparison
        bet_track = normalize_track_code(track)
        pick_track = normalize_track_code(pick.get('track', ''))
        
        # Check if tracks match (after normalization)
        if bet_track == pick_track:
            # Check race number
            if int(pick.get('raceNumber', 0)) == race_num:
                # Check dog name (case-insensitive)
                pick_dog = str(pick.get('dog', '')).strip().upper()
                bet_dog = str(dog_name).strip().upper()
                
                if pick_dog == bet_dog:
                    return pick
    
    return None


def categorize_pick(pick):
    """Categorize a pick based on its properties."""
    categories = []
    
    is_ml_specialist = pick.get('isMlSpecialist', False)
    is_elo_ens = pick.get('isEloEns', False)
    is_green_dot = is_great_pot_track(pick.get('track', ''))
    
    # For bet badge, we need shortlistResolvedMode
    # If not present, we'll mark as unknown
    shortlist_mode = str(pick.get('shortlistResolvedMode', '')).strip().lower()
    has_bet_badge = (shortlist_mode == 'bet')
    
    # Category 1: ML TS + Elo
    if is_ml_specialist and is_elo_ens:
        categories.append('ML TS + Elo')
    
    # Category 2: ML TS + green dot
    if is_ml_specialist and is_green_dot:
        categories.append('ML TS + green dot')
    
    # Category 3: ML TS + bet badge
    if is_ml_specialist and has_bet_badge:
        categories.append('ML TS + bet badge')
    
    # Category 4: ML TS + bet badge + green dot
    if is_ml_specialist and has_bet_badge and is_green_dot:
        categories.append('ML TS + bet badge + green dot')
    
    # Also track basic ML TS
    if is_ml_specialist:
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
    
    # Group bets by date
    bets_by_date = defaultdict(list)
    for bet in bets:
        placed = bet['Placed'].strip()
        # Extract just the date part (before space)
        # Format: "28-Jun-26 10:08:30"
        try:
            date_part = placed.split()[0]
            date_obj = datetime.strptime(date_part, '%d-%b-%y')
            date_str = date_obj.strftime('%Y-%m-%d')
        except Exception as e:
            print(f"Warning: Could not parse date '{placed}': {e}")
            date_str = 'unknown'
        bets_by_date[date_str].append(bet)
    
    print(f"Dates: {list(bets_by_date.keys())}")
    
    # Initialize category stats
    category_stats = defaultdict(lambda: {
        'total_stake': 0.0,
        'total_profit': 0.0,
        'total_bets': 0,
        'bets': []
    })
    
    unmatched_bets = []
    
    # Process each date
    for date_str, date_bets in bets_by_date.items():
        print(f"\nProcessing {date_str} ({len(date_bets)} bets)...")
        
        # Load prediction picks for this date
        picks = get_picks_for_date(date_str)
        print(f"Loaded {len(picks)} picks for {date_str}")
        
        # For each bet, try to find a matching pick
        for bet in date_bets:
            matched_pick = match_bet_to_pick(bet, picks)
            
            if matched_pick:
                # Categorize the pick
                categories = categorize_pick(matched_pick)
                
                # If no specific category, just use ML TS
                if not categories:
                    categories = ['Other']
                
                # Add bet to each category
                stake = float(bet['Stake (AUD)'].replace('$', '').strip() or 0)
                profit = float(bet['Profit/Loss'].replace('$', '').replace(',', '').strip() or 0)
                
                for category in categories:
                    category_stats[category]['total_stake'] += stake
                    category_stats[category]['total_profit'] += profit
                    category_stats[category]['total_bets'] += 1
                    category_stats[category]['bets'].append({
                        'description': bet['Description'],
                        'stake': stake,
                        'profit': profit,
                        'status': bet['Status']
                    })
                
                # Also track all ML TS bets
                if 'ML TS' in categories:
                    category_stats['ML TS']['total_stake'] += stake
                    category_stats['ML TS']['total_profit'] += profit
                    category_stats['ML TS']['total_bets'] += 1
            else:
                unmatched_bets.append(bet)
    
    # Print results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    
    # Print category stats
    for category in [
        'ML TS + Elo',
        'ML TS + green dot',
        'ML TS + bet badge',
        'ML TS + bet badge + green dot',
        'ML TS',
        'Other'
    ]:
        if category in category_stats and category_stats[category]['total_bets'] > 0:
            stats = category_stats[category]
            pot = calculate_pot(stats['total_profit'], stats['total_stake'])
            print(f"\n{category}:")
            print(f"  Bets: {stats['total_bets']}")
            print(f"  Total Stake: ${stats['total_stake']:.2f}")
            print(f"  Total Profit: ${stats['total_profit']:.2f}")
            print(f"  POT: {pot:.2f}%")
    
    if unmatched_bets:
        print(f"\nUnmatched bets: {len(unmatched_bets)}")
        for bet in unmatched_bets[:5]:  # Print first 5
            print(f"  {bet['Placed']}: {bet['Description']}")


if __name__ == '__main__':
    main()
