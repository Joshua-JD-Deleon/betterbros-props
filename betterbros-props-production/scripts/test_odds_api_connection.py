#!/usr/bin/env python3
"""
Test The Odds API connection using the official sample code.

This verifies that the API key is working and shows available sports/games.
"""

import requests
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load API key from environment
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv('ODDS_API_KEY')

if not API_KEY:
    print("ERROR: ODDS_API_KEY not found in environment")
    print("Please set it in your .env file")
    sys.exit(1)

print("=" * 70)
print("THE ODDS API CONNECTION TEST")
print("=" * 70)
print(f"\nUsing API Key: {API_KEY[:10]}...{API_KEY[-4:]}\n")

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Test 1: Get list of in-season sports
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

print("-" * 70)
print("TEST 1: Getting list of in-season sports...")
print("-" * 70)

sports_response = requests.get(
    'https://api.the-odds-api.com/v4/sports',
    params={
        'api_key': API_KEY
    }
)

if sports_response.status_code != 200:
    print(f'❌ Failed to get sports: status_code {sports_response.status_code}')
    print(f'Response body: {sports_response.text}')
    sys.exit(1)
else:
    sports_json = sports_response.json()
    print(f'✓ Connected! Found {len(sports_json)} in-season sports\n')

    # Find NFL
    nfl_sport = None
    for sport in sports_json:
        if sport['key'] == 'americanfootball_nfl':
            nfl_sport = sport
            print(f"✓ NFL Found:")
            print(f"  Title: {sport['title']}")
            print(f"  Key: {sport['key']}")
            print(f"  Active: {sport.get('active', 'N/A')}")
            print(f"  Has Outrights: {sport.get('has_outrights', 'N/A')}")
            break

    if not nfl_sport:
        print("⚠ NFL not found in active sports list")

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Test 2: Get NFL games with h2h/spreads odds
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

print("\n" + "-" * 70)
print("TEST 2: Getting NFL games with odds (h2h, spreads)...")
print("-" * 70)

SPORT = 'americanfootball_nfl'
REGIONS = 'us'
MARKETS = 'h2h,spreads'
ODDS_FORMAT = 'american'
DATE_FORMAT = 'iso'

odds_response = requests.get(
    f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds',
    params={
        'api_key': API_KEY,
        'regions': REGIONS,
        'markets': MARKETS,
        'oddsFormat': ODDS_FORMAT,
        'dateFormat': DATE_FORMAT,
    }
)

if odds_response.status_code != 200:
    print(f'❌ Failed to get odds: status_code {odds_response.status_code}')
    print(f'Response body: {odds_response.text}')
else:
    odds_json = odds_response.json()
    print(f'✓ Number of events: {len(odds_json)}\n')

    # Show first few games
    if odds_json:
        print("Sample games:")
        for i, game in enumerate(odds_json[:3], 1):
            print(f"\n  {i}. {game['away_team']} @ {game['home_team']}")
            print(f"     ID: {game['id']}")
            print(f"     Kickoff: {game['commence_time']}")
            print(f"     Bookmakers: {len(game.get('bookmakers', []))}")
    else:
        print("⚠ No games found")

    # Check the usage quota
    print(f"\n📊 API Usage:")
    print(f"   Remaining requests: {odds_response.headers.get('x-requests-remaining', 'N/A')}")
    print(f"   Used requests: {odds_response.headers.get('x-requests-used', 'N/A')}")

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Test 3: Get player props for first game (if available)
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if odds_json and len(odds_json) > 0:
    print("\n" + "-" * 70)
    print("TEST 3: Getting player props for first game...")
    print("-" * 70)

    first_game = odds_json[0]
    event_id = first_game['id']

    print(f"\nTesting event: {first_game['away_team']} @ {first_game['home_team']}")

    # Test with a few player prop markets
    PROP_MARKETS = 'player_pass_tds,player_pass_yds,player_rush_yds'
    BOOKMAKERS = 'draftkings,fanduel,betmgm'

    props_response = requests.get(
        f'https://api.the-odds-api.com/v4/sports/{SPORT}/events/{event_id}/odds',
        params={
            'api_key': API_KEY,
            'regions': REGIONS,
            'markets': PROP_MARKETS,
            'oddsFormat': ODDS_FORMAT,
            'bookmakers': BOOKMAKERS,
        }
    )

    if props_response.status_code == 404:
        print("⚠ No props available for this event yet (404)")
    elif props_response.status_code != 200:
        print(f'❌ Failed to get props: status_code {props_response.status_code}')
        print(f'Response body: {props_response.text}')
    else:
        props_json = props_response.json()
        bookmakers = props_json.get('bookmakers', [])

        if not bookmakers:
            print("⚠ No bookmakers/props available yet")
        else:
            print(f"✓ Found {len(bookmakers)} bookmakers with props\n")

            # Count total props
            total_props = 0
            for bookmaker in bookmakers:
                for market in bookmaker.get('markets', []):
                    total_props += len(market.get('outcomes', []))

            print(f"Total prop outcomes: {total_props}")

            # Show sample prop
            if bookmakers and bookmakers[0].get('markets'):
                sample_market = bookmakers[0]['markets'][0]
                sample_outcome = sample_market['outcomes'][0] if sample_market.get('outcomes') else None

                if sample_outcome:
                    print(f"\nSample prop:")
                    print(f"  Market: {sample_market['key']}")
                    print(f"  Player: {sample_outcome.get('description', sample_outcome.get('name'))}")
                    print(f"  Line: {sample_outcome.get('point')}")
                    print(f"  Direction: {sample_outcome.get('name')}")
                    print(f"  Odds: {sample_outcome.get('price')}")

        # Check the usage quota
        print(f"\n📊 API Usage:")
        print(f"   Remaining requests: {props_response.headers.get('x-requests-remaining', 'N/A')}")
        print(f"   Used requests: {props_response.headers.get('x-requests-used', 'N/A')}")

print("\n" + "=" * 70)
print("✓ TEST COMPLETE")
print("=" * 70)
