# NBA Props Guide

## Overview

NBA props analysis focuses on consistent volume players with high usage rates. Basketball's indoor environment eliminates weather concerns, making NBA props more predictable than NFL.

## Available Prop Markets (11 Total)

### Scoring Props
- **Points**: Total points scored
- **Three-Pointers Made**: Number of 3PT shots made
- **Free Throws Made**: Number of free throws converted

**Key Factors:**
- Minutes played (30+ preferred)
- Usage rate (20%+ for stars)
- Matchup pace (faster = more possessions)
- Opponent defensive rating

### Playmaking Props
- **Assists**: Total assists distributed
- **Rebounds**: Total rebounds (offensive + defensive)
- **Points + Assists**: Combined scoring and playmaking
- **Points + Rebounds**: Combined scoring and rebounding
- **Points + Rebounds + Assists**: Triple stat combo (PRA)

**Key Factors:**
- Position (PG = assists, C = rebounds)
- Team style (fast pace = more stats)
- Teammate injuries (usage boost)

### Defensive/Specialty Props
- **Steals**: Defensive steals
- **Blocks**: Blocked shots

**Key Factors:**
- Defensive role
- Opponent turnover rate
- Matchup size advantages

## Position-Specific Analysis

### Point Guards (PG)
- **High Assist Potential**: 6-12 assists typical for starters
- **Moderate Scoring**: 18-25 points typical range
- **Target**: PRA combos, assist props
- **Usage**: 20-28% typical

**Best Props:**
- Assists (most consistent)
- PRA combos (high floor)
- Points (for scoring PGs like Lillard, Young)

### Shooting Guards (SG)
- **Scoring Focus**: 20-30 points for starters
- **Three-Point Volume**: 2-5 threes typical
- **Lower Assists**: 3-5 assists typical
- **Usage**: 22-30% for stars

**Best Props:**
- Points (primary option)
- Three-pointers made (for shooters)
- Points + Assists combos

### Small Forwards (SF)
- **Balanced Stats**: Can fill multiple categories
- **Moderate Rebounding**: 5-8 rebounds typical
- **Scoring**: 18-26 points typical
- **Usage**: 20-28% typical

**Best Props:**
- PRA combos (versatility advantage)
- Points + Rebounds
- Points (for scorers like Durant, Tatum)

### Power Forwards (PF)
- **Rebounding Strength**: 7-12 rebounds typical
- **Interior Scoring**: 15-22 points typical
- **Assists**: 2-4 assists typical
- **Usage**: 18-25% typical

**Best Props:**
- Rebounds (most consistent)
- Points + Rebounds
- PRA combos (for modern stretch 4s)

### Centers (C)
- **Rebounding Elite**: 10-15 rebounds typical
- **Interior Defense**: Blocks (1-3 typical)
- **Limited Assists**: 1-3 assists typical
- **Usage**: 18-26% typical

**Best Props:**
- Rebounds (highest consistency)
- Points + Rebounds
- Blocks (for elite defenders)

## Key Factors for NBA Props

### Minutes Played
- **30+ minutes**: Full confidence
- **25-30 minutes**: Proceed with caution
- **Under 25**: Avoid unless blowup game expected

### Usage Rate
- **25%+ (Superstars)**: High volume, consistent stats
- **20-25% (Primary Options)**: Good for combo props
- **15-20% (Role Players)**: Risky, avoid unless great matchup

### Pace of Play
- **Fast Pace (105+ possessions)**: More opportunities for all stats
- **Slow Pace (95-100 possessions)**: Harder to hit overs
- **Matchup Pace**: Average both teams' pace for true expectation

### Back-to-Back Games
- **First Game (B2B-1)**: Normal performance expected
- **Second Game (B2B-2)**: Minutes often reduced 5-10%, stats dip 8-12%
- **Stars May Rest**: Load management risk increases

### Injury Opportunities
- **Star Player Out**: Usage redistributed to next man up
- **Usage Boost**: 15-25% stat increase for beneficiaries
- **Monitor News**: Injuries often announced 1-2 hours before tip

## Weather Impact

**NONE** - All NBA games are played indoors in climate-controlled arenas.

## Best Practices

### Research Checklist
1. Confirm player is not on injury report
2. Check minutes trend (last 5 games)
3. Review usage rate and recent form
4. Analyze opponent defensive rating vs position
5. Check for back-to-back games
6. Review pace of play (both teams)
7. Monitor for late injury news (teammates out = usage boost)

### Prop Selection Strategy
- **Points**: Target high-usage players (25%+) in fast-paced matchups
- **Assists**: Target primary ball handlers vs poor perimeter defense
- **Rebounds**: Target starting centers and PFs, especially vs weak rebounding teams
- **Combo Props (PRA)**: Target versatile players with 28+ minutes
- **Three-Pointers**: Target high-volume shooters (6+ attempts/game)

### Bankroll Management
- **Conservative Mode**: Focus on PRA combos and rebounds (highest consistency)
- **Balanced Mode**: Mix points, PRA, and assists props
- **Aggressive Mode**: Include three-pointers and blocks (higher variance)

## Example Analysis

**Player**: Luka Dončić (PG, DAL)
**Prop**: Over 48.5 Points + Rebounds + Assists (PRA)
**Game**: vs HOU (fast pace, poor perimeter defense)

**Favorable Factors:**
- Luka averages 52.5 PRA this season (4 points above line)
- Houston plays fast pace (104 possessions/game)
- Houston ranks 22nd in opponent PRA allowed to PGs
- Luka playing 36+ minutes nightly
- Usage rate 32% (elite)

**Concerns:**
- Back-to-back game (slightly elevated injury risk)
- Blowout potential (either direction could reduce minutes)

**Verdict**: Strong lean OVER, slight minutes risk in blowout scenario

## CLI Usage

```bash
# Analyze current NBA day
python scripts/run_week.py --season 2025 --sport NBA

# NBA uses date-based windows (not weeks like NFL)
# Automatically fetches today's games

# Generate props with aggressive risk mode
python scripts/run_week.py --season 2025 --sport NBA --risk-mode aggressive
```

## App Usage

1. Select "NBA" from sport dropdown
2. Choose current season (week ignored for NBA)
3. Set risk tolerance (conservative/balanced/aggressive)
4. Review generated props with edge percentages
5. Use trend chips to identify hot/cold streaks
6. Check correlation inspector (e.g., high-scoring games boost all stats)
7. Export optimized slips to CSV

## Common Pitfalls

- **Ignoring Minutes**: Sub-25 minute players rarely hit overs
- **Chasing Big Names**: Even stars have tough matchups and B2B rest
- **Missing Injury News**: Teammates out = major usage shifts
- **Overlooking Pace**: Slow-paced games limit all stats
- **Betting Blocks/Steals**: Highest variance props, use sparingly
- **Blowout Risk**: Starters may sit 4th quarter in lopsided games

## Pro Tips

- **Target Overtime Games**: 5 extra minutes = 10-15% stat boost
- **Fade Second Night of B2B**: Rest and fatigue impact performance
- **Exploit Injury News**: Last-minute outs create major opportunities
- **Use PRA Combos**: Lower variance than individual stat props
- **Monitor Load Management**: Stars on minutes restrictions
