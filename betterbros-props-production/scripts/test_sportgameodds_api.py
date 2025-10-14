#!/usr/bin/env python3
"""
Test the SportsGameOdds API connection and explore data structure.

This script will help us understand the API's response format
so we can build the client adapter.
"""

import requests
import json
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load API key from environment
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv('SPORTGAMEODDS_API_KEY', '5143772607962504')
BASE_URL = 'https://api.sportsgameodds.com/v2'

print("=" * 70)
print("SPORTSGAMEODDS API CONNECTION TEST")
print("=" * 70)
print(f"\nUsing API Key: {API_KEY[:10]}...{API_KEY[-4:]}\n")

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Test 1: Get NFL games/events
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

print("-" * 70)
print("TEST 1: Getting NFL games/events...")
print("-" * 70)

# Try to get NFL events - might need to explore endpoint structure
headers = {
    'X-API-Key': API_KEY,
    'Accept': 'application/json'
}

# First, let's try to understand the API structure
# Common endpoints might be: /events, /games, /sports, /odds

endpoints_to_try = [
    '/sports',
    '/events',
    '/games',
    '/odds',
    '/nfl/events',
    '/nfl/odds',
    '/americanfootball_nfl/events',
]

print("\nExploring API endpoints...")
for endpoint in endpoints_to_try:
    url = f"{BASE_URL}{endpoint}"
    print(f"\nTrying: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")

        if response.status_code == 200:
            print(f"  ✓ Success! Response size: {len(response.text)} bytes")

            try:
                data = response.json()
                print(f"  Response type: {type(data)}")

                if isinstance(data, list):
                    print(f"  Array length: {len(data)}")
                    if len(data) > 0:
                        print(f"  First item keys: {list(data[0].keys())}")
                        print(f"\n  Sample data:")
                        print(json.dumps(data[0], indent=2)[:500] + "...")
                elif isinstance(data, dict):
                    print(f"  Object keys: {list(data.keys())}")
                    print(f"\n  Sample data:")
                    print(json.dumps(data, indent=2)[:500] + "...")

                # Save successful response for analysis
                output_file = f"/tmp/sportgameodds_{endpoint.replace('/', '_')}.json"
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"  Saved full response to: {output_file}")

            except json.JSONDecodeError:
                print(f"  Response is not JSON: {response.text[:200]}")

        elif response.status_code == 404:
            print(f"  ✗ Not found")
        elif response.status_code == 401:
            print(f"  ✗ Unauthorized - API key may be invalid")
        elif response.status_code == 403:
            print(f"  ✗ Forbidden - may need different permissions")
        else:
            print(f"  Response: {response.text[:200]}")

    except requests.exceptions.Timeout:
        print(f"  ✗ Timeout")
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error: {str(e)}")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
print("\nNext steps:")
print("1. Review the saved JSON files in /tmp/")
print("2. Identify the correct endpoint for NFL player props")
print("3. Understand the data structure for building the client")
