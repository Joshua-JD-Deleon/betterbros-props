#!/usr/bin/env python3
"""
CLI script to check when props are likely to be available.

Usage:
    python scripts/check_props_availability.py

This will show you when to check for props based on upcoming game schedules.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest.odds_api_client import OddsAPIClient
from src.utils.prop_notifications import (
    PropAvailabilityChecker,
    format_availability_message
)
import os


def main():
    """Check prop availability and display recommendations."""
    print("\n" + "=" * 60)
    print("NFL PROPS AVAILABILITY CHECKER")
    print("=" * 60)
    print()

    # Check if API key is set
    api_key = os.getenv('ODDS_API_KEY')
    if not api_key:
        print("ERROR: ODDS_API_KEY not found in environment")
        print("Please set it in your .env file or export it:")
        print("  export ODDS_API_KEY=your_api_key_here")
        return 1

    try:
        # Fetch upcoming games
        print("Fetching upcoming NFL games...")
        client = OddsAPIClient(api_key=api_key)
        games = client.get_upcoming_games()

        if not games:
            print("\nNo upcoming games found.")
            return 0

        print(f"Found {len(games)} upcoming games\n")

        # Analyze availability
        checker = PropAvailabilityChecker()
        analysis = checker.analyze_games(games)

        # Display formatted results
        print(format_availability_message(analysis))

        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        print("-" * 60)

        if analysis['games_with_props_now']:
            print("✓ You should fetch props NOW for the available games")
            print("  Run: streamlit run app/main.py")
            print("  Or: python examples/fetch_props_demo.py")

        elif analysis['check_soon']:
            print("⏰ Check back within the next 6 hours")
            print("  Props should be posted soon for upcoming games")

        elif analysis['check_later']:
            next_check = checker.get_next_check_time(games)
            if next_check:
                print(f"📅 Next check recommended: {next_check.strftime('%A, %B %d at %I:%M %p %Z')}")
                print(f"  Set a reminder to check again then")

        else:
            print("⚠ No props expected in the near future")
            print("  Props are posted 24-48 hours before games")

        print()
        return 0

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
