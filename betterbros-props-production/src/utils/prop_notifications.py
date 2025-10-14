"""
Prop availability notifications and reminders.

Helps users know when to check for props based on optimal timing windows.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pytz


class PropAvailabilityChecker:
    """
    Checks upcoming games and determines when props are likely to be available.

    Bookmakers typically post props 24-48 hours before kickoff and remove them
    1-2 hours before game time.
    """

    # Prop availability windows
    OPTIMAL_CHECK_HOURS_BEFORE = 36  # Best time to check (36 hours before)
    EARLIEST_CHECK_HOURS_BEFORE = 48  # Earliest props might appear
    LATEST_CHECK_HOURS_BEFORE = 24  # Latest recommended check time
    PROPS_DISAPPEAR_HOURS_BEFORE = 2  # When props typically disappear

    def __init__(self):
        self.now = datetime.now(pytz.UTC)

    def analyze_games(self, games: List[Dict]) -> Dict:
        """
        Analyze upcoming games and provide prop availability recommendations.

        Args:
            games: List of game dicts with 'commence_time', 'home_team', 'away_team'

        Returns:
            Dict with analysis results:
                - games_with_props_now: Games that should have props available now
                - check_soon: Games to check within next 6 hours
                - check_later: Games to check after 6 hours (with suggested times)
                - too_late: Games where props likely already removed
        """
        games_with_props_now = []
        check_soon = []
        check_later = []
        too_late = []

        for game in games:
            analysis = self._analyze_single_game(game)

            if analysis['status'] == 'available_now':
                games_with_props_now.append(analysis)
            elif analysis['status'] == 'check_soon':
                check_soon.append(analysis)
            elif analysis['status'] == 'check_later':
                check_later.append(analysis)
            else:  # too_late
                too_late.append(analysis)

        return {
            'games_with_props_now': games_with_props_now,
            'check_soon': check_soon,
            'check_later': check_later,
            'too_late': too_late,
            'summary': self._generate_summary(
                games_with_props_now, check_soon, check_later, too_late
            )
        }

    def _analyze_single_game(self, game: Dict) -> Dict:
        """Analyze a single game's prop availability."""
        game_time_str = game.get('commence_time')

        # Parse game time
        if isinstance(game_time_str, str):
            if game_time_str.endswith('Z'):
                game_time = datetime.fromisoformat(game_time_str.replace('Z', '+00:00'))
            else:
                game_time = datetime.fromisoformat(game_time_str)
        else:
            game_time = game_time_str

        # Ensure timezone aware
        if game_time.tzinfo is None:
            game_time = game_time.replace(tzinfo=pytz.UTC)

        hours_until_game = (game_time - self.now).total_seconds() / 3600

        matchup = f"{game.get('away_team')} @ {game.get('home_team')}"

        # Determine status
        if hours_until_game < self.PROPS_DISAPPEAR_HOURS_BEFORE:
            status = 'too_late'
            message = f"Props likely already removed (game in {hours_until_game:.1f}h)"
            check_time = None
        elif hours_until_game <= self.LATEST_CHECK_HOURS_BEFORE:
            status = 'available_now'
            message = f"Props should be available NOW (game in {hours_until_game:.1f}h)"
            check_time = self.now
        elif hours_until_game <= self.OPTIMAL_CHECK_HOURS_BEFORE:
            status = 'check_soon'
            message = f"Check within next few hours (game in {hours_until_game:.1f}h)"
            check_time = self.now + timedelta(hours=2)
        else:
            # Calculate optimal check time (36 hours before game)
            optimal_check = game_time - timedelta(hours=self.OPTIMAL_CHECK_HOURS_BEFORE)
            hours_until_check = (optimal_check - self.now).total_seconds() / 3600

            status = 'check_later'
            message = f"Check in {hours_until_check:.1f}h (game in {hours_until_game:.1f}h)"
            check_time = optimal_check

        return {
            'matchup': matchup,
            'game_time': game_time,
            'hours_until_game': hours_until_game,
            'status': status,
            'message': message,
            'check_time': check_time,
            'event_id': game.get('id')
        }

    def _generate_summary(
        self,
        available_now: List,
        check_soon: List,
        check_later: List,
        too_late: List
    ) -> str:
        """Generate a human-readable summary."""
        lines = []

        if available_now:
            lines.append(f"✓ {len(available_now)} game(s) have props available NOW")

        if check_soon:
            lines.append(f"⏰ {len(check_soon)} game(s) - check within next 6 hours")

        if check_later:
            next_check = min(g['check_time'] for g in check_later)
            hours_until = (next_check - self.now).total_seconds() / 3600
            lines.append(
                f"📅 {len(check_later)} game(s) - next check in {hours_until:.1f} hours "
                f"({next_check.strftime('%I:%M %p %Z')})"
            )

        if too_late:
            lines.append(f"✗ {len(too_late)} game(s) - props already removed")

        if not any([available_now, check_soon, check_later]):
            lines.append("No upcoming games with props available in the near future")

        return "\n".join(lines)

    def get_next_check_time(self, games: List[Dict]) -> Optional[datetime]:
        """
        Get the next recommended time to check for props.

        Args:
            games: List of upcoming games

        Returns:
            Next optimal check time, or None if no games
        """
        analysis = self.analyze_games(games)

        if analysis['games_with_props_now']:
            return self.now

        if analysis['check_soon']:
            return self.now + timedelta(hours=2)

        if analysis['check_later']:
            return min(g['check_time'] for g in analysis['check_later'])

        return None


def get_prop_availability_status(games: List[Dict]) -> Dict:
    """
    Convenience function to check prop availability status.

    Args:
        games: List of game dictionaries from odds API

    Returns:
        Analysis results with recommendations
    """
    checker = PropAvailabilityChecker()
    return checker.analyze_games(games)


def format_availability_message(analysis: Dict) -> str:
    """
    Format the availability analysis into a user-friendly message.

    Args:
        analysis: Results from PropAvailabilityChecker.analyze_games()

    Returns:
        Formatted string for display
    """
    lines = [
        "=" * 60,
        "PROP AVAILABILITY STATUS",
        "=" * 60,
        "",
        analysis['summary'],
        ""
    ]

    if analysis['games_with_props_now']:
        lines.extend([
            "",
            "🟢 AVAILABLE NOW:",
            "-" * 60
        ])
        for game in analysis['games_with_props_now']:
            lines.append(f"  • {game['matchup']}")
            lines.append(f"    Game: {game['game_time'].strftime('%a, %b %d at %I:%M %p %Z')}")

    if analysis['check_soon']:
        lines.extend([
            "",
            "🟡 CHECK WITHIN NEXT 6 HOURS:",
            "-" * 60
        ])
        for game in analysis['check_soon']:
            lines.append(f"  • {game['matchup']}")
            lines.append(f"    Game: {game['game_time'].strftime('%a, %b %d at %I:%M %p %Z')}")

    if analysis['check_later']:
        lines.extend([
            "",
            "🔵 CHECK LATER:",
            "-" * 60
        ])
        for game in analysis['check_later'][:5]:  # Show first 5
            lines.append(f"  • {game['matchup']}")
            lines.append(f"    Game: {game['game_time'].strftime('%a, %b %d at %I:%M %p %Z')}")
            lines.append(f"    Check: {game['check_time'].strftime('%a, %b %d at %I:%M %p %Z')}")

        if len(analysis['check_later']) > 5:
            lines.append(f"  ... and {len(analysis['check_later']) - 5} more")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)
