# NFL Props Guide

## Overview

NFL props analysis focuses on traditional football markets with special attention to game context, weather conditions, and matchup advantages.

## Available Prop Markets (14 Total)

### Passing Props
- **Passing Yards**: Total yards thrown by quarterback
- **Passing TDs**: Touchdown passes thrown
- **Pass Completions**: Number of completed passes
- **Pass Attempts**: Total pass attempts
- **Interceptions**: Passes intercepted by defense

**Key Factors:**
- Weather (wind, rain heavily impact passing)
- Opponent pass defense ranking
- Game script (trailing teams pass more)
- Offensive line strength

### Rushing Props
- **Rushing Yards**: Total yards gained on ground
- **Rushing TDs**: Rushing touchdowns scored
- **Rushing Attempts**: Number of carries

**Key Factors:**
- Opponent run defense ranking
- Game script (leading teams run more)
- Goal-line situations
- Weather (snow/wind favors rushing)

### Receiving Props
- **Receiving Yards**: Total yards caught
- **Receptions**: Number of catches
- **Receiving TDs**: Touchdowns via reception

**Key Factors:**
- Target share
- Red zone involvement
- Matchup vs coverage type
- QB accuracy and chemistry

### Special Teams
- **Kicking Points**: Total points from FG + XP

**Key Factors:**
- Dome vs outdoor
- Weather conditions
- Offensive efficiency (more scoring drives)

## Position-Specific Analysis

### Quarterbacks (QB)
- **High Consistency**: 78-90% performance stability
- **Weather Sensitive**: Passing yards drop 15-20% in adverse weather
- **Volume Matters**: Target 30+ pass attempts for passing yards props
- **Red Zone**: TD props depend on goal-line playcalling

### Running Backs (RB)
- **Moderate Consistency**: 70-82% performance stability
- **Touch Count**: Target 15+ touches for rushing yards
- **Game Script**: Leading teams give RBs more work
- **Pass Catching**: PPR leagues - check reception props for pass-catching backs

### Wide Receivers / Tight Ends (WR/TE)
- **Lower Consistency**: 65-80% performance stability
- **Target Share**: Need 20%+ team target share
- **Matchup Dependent**: Exploit weak cornerbacks/linebackers
- **Boom/Bust**: Higher variance than QB/RB props

## Weather Impact

### Temperature
- **Below 32°F**: Passing yards drop 12-18%
- **Below 20°F**: Fumbles increase, gameplay slows

### Wind
- **15+ mph**: Passing yards drop 10-15%, favor unders
- **20+ mph**: Deep passes nearly impossible
- **Kicking**: 15+ mph affects 45+ yard field goals

### Precipitation
- **Rain**: Ball handling issues, favor rushing props
- **Snow**: Heavy snow = major passing decline, unders preferred

### Dome Games
- **No Weather Impact**: Consistent performance
- **Higher Scoring**: Typically favor overs on TDs and yards

## Best Practices

### Research Checklist
1. Check weather forecast (for outdoor games)
2. Review injury report (especially offensive line)
3. Analyze opponent defensive rankings
4. Check recent game logs (last 4 weeks)
5. Identify game script expectations (close game vs blowout)
6. Review snap count trends
7. Check red zone usage rates

### Prop Selection Strategy
- **Passing Yards**: Target good weather, weak pass defense
- **Rushing Yards**: Target poor run defense, game script advantage
- **Receptions**: Target high-volume targets (8+ targets/game)
- **Touchdowns**: Higher variance - use sparingly, check red zone stats

### Bankroll Management
- **Conservative Mode**: Focus on QB/RB yards props (higher consistency)
- **Balanced Mode**: Mix yards props with reception props
- **Aggressive Mode**: Include TD props, target ceiling games

## Example Analysis

**Player**: Patrick Mahomes (QB, KC)
**Prop**: Over 275.5 Passing Yards
**Game**: vs JAX (weak pass defense, ranked 28th)

**Favorable Factors:**
- Dome game (no weather)
- Opponent allows 285 ypg passing (well above line)
- Mahomes averages 295 ypg this season
- Chiefs favored by 7 (likely passing in 2nd half)

**Concerns:**
- Chiefs may run more if leading big
- Mahomes resting in blowout

**Verdict**: Strong lean OVER, but cap exposure due to blowout risk

## CLI Usage

```bash
# Analyze current NFL week
python scripts/run_week.py --week 5 --season 2025 --sport NFL

# Run historical backtest
python scripts/run_week.py --mode backtest --start-week 1 --end-week 10 --sport NFL

# Generate props with conservative risk mode
python scripts/run_week.py --week 5 --season 2025 --sport NFL --risk-mode conservative
```

## App Usage

1. Select "NFL" from sport dropdown
2. Choose current week and season
3. Set risk tolerance (conservative/balanced/aggressive)
4. Review generated props with edge percentages
5. Use trend chips to identify hot/cold streaks
6. Check correlation inspector for related props
7. Export optimized slips to CSV

## Common Pitfalls

- **Overvaluing TDs**: Touchdown props are high variance, use sparingly
- **Ignoring Weather**: 15+ mph wind is a deal breaker for passing props
- **Chasing Stars**: Even elite players have bad matchups
- **Missing Injury News**: Late scratches kill props, check 90 mins before kickoff
- **Ignoring Game Script**: Blowouts change playcalling dramatically
