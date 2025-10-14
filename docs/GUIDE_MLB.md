# MLB Props Guide

## Overview

MLB props analysis focuses on batter-pitcher matchups, ballpark factors, and weather conditions. Baseball has the highest variance among the three sports, requiring careful bankroll management.

## Available Prop Markets (11 Total)

### Batter Props
- **Hits**: Total hits recorded (single, double, triple, HR)
- **Home Runs**: Home runs hit
- **RBIs**: Runs batted in
- **Total Bases**: Weighted stat (1B=1, 2B=2, 3B=3, HR=4)
- **Runs Scored**: Times crossing home plate
- **Stolen Bases**: Successful steals

**Key Factors:**
- Batter handedness vs pitcher handedness
- Ballpark dimensions (hitter-friendly vs pitcher-friendly)
- Wind direction and speed
- Recent form (hot/cold streak)
- Lineup position (1-4 = more opportunities)

### Pitcher Props
- **Strikeouts**: Total strikeouts recorded
- **Hits Allowed**: Total hits surrendered
- **Earned Runs Allowed**: Runs allowed (excluding errors)
- **Walks**: Free passes issued
- **Outs Recorded**: Total outs (innings pitched × 3)

**Key Factors:**
- Opponent team strikeout rate
- Ballpark dimensions
- Weather (temperature, wind, humidity)
- Pitch count limits (80-100 typical)
- Bullpen quality (early exit risk)

## Position-Specific Analysis

### Batters
- **Low Consistency**: 60-75% performance stability
- **High Variance**: Even elite hitters fail 65% of at-bats
- **Lineup Position Matters**: Top 4 = 4-5 ABs, Bottom 5 = 3-4 ABs
- **Platoon Advantage**: RHB vs LHP and LHB vs RHP = 15-20% boost

**Best Props:**
- Hits (most predictable batter prop)
- Total Bases (rewards extra-base hits)
- RBIs (for middle-of-order hitters in good lineups)

**Risky Props:**
- Home Runs (very high variance)
- Stolen Bases (limited attempts, success rate varies)

### Pitchers
- **Moderate Consistency**: 65-80% performance stability
- **Pitch Count Risk**: Early exit if struggling or high pitch count
- **Bullpen Dependence**: Weak bullpen = pressure to stay longer
- **Weather Sensitive**: Wind and temperature affect all stats

**Best Props:**
- Strikeouts (most consistent for high-K pitchers)
- Outs Recorded (linked to innings pitched)
- Hits Allowed (for elite pitchers in weak lineups)

**Risky Props:**
- Earned Runs (defense-dependent)
- Walks (high variance game-to-game)

## Key Factors for MLB Props

### Batter vs Pitcher Matchup
- **Platoon Splits**: RHB vs RHP and LHB vs LHP = disadvantage (-15% to -20%)
- **Platoon Advantage**: RHB vs LHP and LHB vs RHP = advantage (+15% to +20%)
- **Historical Matchup**: Check if batter has faced pitcher before (small sample, use cautiously)

### Ballpark Factors

#### Hitter-Friendly Parks
- **Coors Field (COL)**: Extreme hitter park, thin air
- **Great American Ball Park (CIN)**: Small dimensions
- **Globe Life Field (TEX)**: Retractable roof, hitter-friendly
- **Effect**: 10-25% boost to hits, HRs, and runs

#### Pitcher-Friendly Parks
- **Oracle Park (SF)**: Deep outfield, marine layer
- **T-Mobile Park (SEA)**: Large dimensions
- **Marlins Park (MIA)**: Deep fences
- **Effect**: 10-20% reduction to hits, HRs, and runs

### Weather Impact

#### Temperature
- **85°F+**: Ball carries better, favors hitters (+8-12% HR distance)
- **Below 60°F**: Ball doesn't carry, favors pitchers (-10-15% HR distance)
- **Optimal**: 75-85°F for hitting

#### Wind
- **Blowing Out (10+ mph)**: Major boost to HR props (+20-30%)
- **Blowing In (10+ mph)**: Suppress HR and fly ball outs (+15-25% to pitcher props)
- **Cross Wind**: Minimal impact on power, slight impact on fly balls

#### Humidity
- **High Humidity (70%+)**: Ball carries slightly better
- **Low Humidity (30% or less)**: Ball doesn't carry as well
- **Moderate Impact**: Less important than wind and temperature

### Lineup Position
- **1-2 (Leadoff)**: Speed focus, most plate appearances (4-5 PA)
- **3-5 (Heart of Order)**: Power hitters, RBI opportunities (4-5 PA)
- **6-9 (Bottom Order)**: Fewer opportunities (3-4 PA)
- **Target**: Positions 1-5 for volume stats (hits, total bases)

### Umpire Factor
- **Large Strike Zone**: Favors pitchers (more Ks, fewer hits/walks)
- **Small Strike Zone**: Favors hitters (more walks, harder to K)
- **Impact**: 5-10% on outcomes

## Best Practices

### Research Checklist
1. Check weather forecast (wind direction critical)
2. Review batter vs pitcher handedness
3. Analyze ballpark factors
4. Check recent form (last 7 days)
5. Review lineup position
6. Check umpire strike zone tendencies
7. Monitor injury reports and lineup changes (posted ~30 mins before first pitch)

### Prop Selection Strategy
- **Hits**: Target top-of-order batters with platoon advantage in hitter parks
- **Home Runs**: Need wind blowing out + hitter park + power hitter
- **RBIs**: Target 3-5 hitters in strong lineups
- **Strikeouts (Pitcher)**: Target high-K pitchers vs high-K teams
- **Total Bases**: Good balance of consistency + upside

### Bankroll Management
- **Conservative Mode**: Focus on pitcher strikeouts and batter hits (most consistent)
- **Balanced Mode**: Mix hits, total bases, and pitcher outs props
- **Aggressive Mode**: Include home runs and RBIs (high variance)

## Example Analysis

**Player**: Shohei Ohtani (DH, LAD)
**Prop**: Over 1.5 Total Bases
**Game**: vs COL at Coors Field

**Favorable Factors:**
- Coors Field (extreme hitter park)
- Wind blowing out 12 mph
- RHB vs LHP (platoon advantage)
- Ohtani averaging 2.1 TB/game this season
- Ohtani batting 3rd (4-5 plate appearances)
- Temperature 82°F (ideal hitting conditions)

**Concerns:**
- Opponent pitcher has good LHP splits
- Small sample at Coors this season

**Verdict**: Strong lean OVER, ideal hitting environment

## CLI Usage

```bash
# Analyze current MLB day
python scripts/run_week.py --season 2025 --sport MLB

# MLB uses date-based windows (not weeks like NFL)
# Automatically fetches today's games

# Generate props with conservative risk mode
python scripts/run_week.py --season 2025 --sport MLB --risk-mode conservative
```

## App Usage

1. Select "MLB" from sport dropdown
2. Choose current season (week ignored for MLB)
3. Set risk tolerance (conservative/balanced/aggressive)
4. Review generated props with edge percentages
5. Use trend chips to identify hot/cold streaks
6. Check correlation inspector (same game correlations)
7. Export optimized slips to CSV

## Common Pitfalls

- **Ignoring Weather**: Wind direction is critical for HR and fly ball props
- **Overlooking Platoon Splits**: Handedness matchup is 15-20% factor
- **Chasing Home Runs**: HR props are extremely high variance
- **Missing Lineup News**: Late scratches are common, check 30 mins before first pitch
- **Ignoring Ballpark**: Coors Field vs Oracle Park is night and day difference
- **Betting on Weak Lineups**: Bottom of order (7-9) get fewer opportunities

## Pro Tips

- **Target Coors Field**: The ultimate hitter paradise
- **Fade Pitchers in Wind**: 10+ mph out = avoid pitcher unders
- **Exploit Platoon Advantage**: RHB vs LHP is a significant edge
- **Check Double-Headers**: Starters may get rest, bullpen games common
- **Weather Changes**: Wind can shift during game, but props lock at first pitch
- **Strikeout Props (Pitcher)**: Most consistent MLB prop market
- **Total Bases > Hits**: Rewards extra-base hits, better for power hitters

## Variance Management

Baseball has the highest variance of the three sports:
- Even .300 hitters fail 70% of at-bats
- Elite pitchers have bad outings
- Weather can change everything

**Recommendations:**
- Use smaller unit sizes than NFL/NBA
- Diversify across multiple games
- Focus on volume stats (hits, strikeouts) over home runs
- Accept that even great analysis will lose 40-45% of the time
