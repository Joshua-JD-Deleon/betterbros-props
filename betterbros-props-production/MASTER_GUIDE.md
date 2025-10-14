# BetterBros Props - Master Technical Guide

> **Comprehensive guide to all modules, features, and capabilities across the entire application**

Last Updated: 2025-10-14

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Data Ingestion Layer](#data-ingestion-layer)
3. [Feature Engineering](#feature-engineering)
4. [Machine Learning Models](#machine-learning-models)
5. [Correlation Analysis](#correlation-analysis)
6. [Portfolio Optimization](#portfolio-optimization)
7. [Evaluation & Testing](#evaluation--testing)
8. [API Key Management](#api-key-management)
9. [Sharing & Export](#sharing--export)
10. [Snapshots & State Management](#snapshots--state-management)
11. [User Interface (Streamlit App)](#user-interface-streamlit-app)
12. [Configuration System](#configuration-system)
13. [Multi-Sport Support](#multi-sport-support)
14. [Utilities & Helpers](#utilities--helpers)

---

## Architecture Overview

<details>
<summary><strong>Click to expand: System Architecture</strong></summary>

### High-Level Flow

```
Data Ingestion → Feature Engineering → ML Models → Correlation → Optimization → UI Display
      ↓                  ↓                  ↓            ↓             ↓           ↓
  API Clients      Feature Pipeline    GBM/Bayes    Copulas    Kelly Criterion  Streamlit
```

### Directory Structure

```
betterbros-props/
├── app/                    # Streamlit UI application
│   └── main.py            # Main app entry point
├── src/                   # Backend source code
│   ├── ingest/           # Data ingestion (APIs, weather, injuries)
│   ├── features/         # Feature engineering pipeline
│   ├── models/           # ML probability models
│   ├── corr/             # Correlation & copula analysis
│   ├── optimize/         # Portfolio optimization
│   ├── eval/             # Backtesting & evaluation
│   ├── keys/             # API key management
│   ├── snapshots/        # State management
│   ├── share/            # Export & sharing
│   ├── utils/            # Utilities
│   └── config.py         # Central configuration
├── data/                 # Data storage (cache, snapshots)
├── docs/                 # User documentation
├── scripts/              # CLI tools
├── tests/                # Test suite
└── models/               # Trained ML models
```

### Core Philosophy

1. **Multi-Sport Support**: NFL, NBA, MLB with sport-specific logic
2. **Dual Data Sources**: The Odds API (primary) + SportsGameOdds (secondary)
3. **Ensemble Modeling**: GBM + Bayesian for robust probabilities
4. **Correlation-Aware**: Copulas capture complex dependencies
5. **Kelly Optimization**: Mathematical bankroll management
6. **Uncertainty Quantification**: Confidence intervals on all predictions

</details>

---

## Data Ingestion Layer

<details>
<summary><strong>Click to expand: API Clients & Data Sources</strong></summary>

### Module: `src/ingest/`

#### 1. **The Odds API Client** (`odds_api_client.py`)

**Purpose**: Primary data source for player props across all sports

**Key Functions**:
- `get_upcoming_games()`: Fetch upcoming games for a sport
- `get_player_props(game_id, market)`: Fetch props for specific game/market
- `fetch_all_player_props()`: Comprehensive prop fetch for all games

**Sport Support**:
- NFL: 14 prop markets (passing_yds, rushing_yds, receiving_yds, pass_tds, etc.)
- NBA: 11 prop markets (points, rebounds, assists, threes, PRA combos)
- MLB: 11 prop markets (hits, home_runs, rbis, strikeouts, total_bases)

**Configuration**:
```python
client = OddsAPIClient(api_key="your_key", sport="NFL")  # or "NBA", "MLB"
props = client.fetch_all_player_props(markets=["player_pass_yds", "player_pass_tds"])
```

**Rate Limits**: 500 free requests/month, then paid tiers

---

#### 2. **SportsGameOdds Client** (`sportgameodds_client.py`)

**Purpose**: Alternative/supplementary data source

**Key Functions**:
- `get_games()`: Fetch games by sport/date
- `get_player_props()`: Fetch player props
- Similar API to OddsAPIClient for easy swapping

**Usage**: Set `SPORTGAMEODDS_API_KEY` in `.env`

---

#### 3. **Sport Configuration** (`sport_config.py`)

**Purpose**: Centralized sport-specific configuration

**Key Functions**:
- `get_sport_key(sport)`: Map "NFL" → "americanfootball_nfl"
- `get_prop_markets(sport)`: Get all prop markets for a sport
- `normalize_prop_type(market, sport)`: Standardize prop naming
- `infer_position(prop_type, sport)`: Guess player position from prop type

**Sport Keys**:
```python
NFL: "americanfootball_nfl"
NBA: "basketball_nba"
MLB: "baseball_mlb"
```

---

#### 4. **Sleeper Client / Mock Data** (`sleeper_client.py`)

**Purpose**: Mock data generator for development/testing

**Key Functions**:
- `fetch_current_props(week, season, sport)`: Main entry point
- `_get_mock_props_nfl()`: Generate 100 NFL props
- `_get_mock_props_nba()`: Generate 75 NBA props (15 players × 5 prop types)
- `_get_mock_props_mlb()`: Generate 55 MLB props (10 batters + 5 pitchers)

**Mock Data Features**:
- Realistic player names (Mahomes, Luka, Ohtani, etc.)
- Realistic prop lines and odds
- Sport-specific positions and stats
- Cached to parquet files for speed

**Cache Location**: `data/cache/sleeper_{sport}_{week}_{season}.parquet`

---

#### 5. **Weather Provider** (`weather_provider.py`)

**Purpose**: Weather data for outdoor games (NFL, MLB)

**Key Functions**:
- `fetch_weather_for_game(game_id, date)`: Get weather for a game
- `enrich_props_with_weather(props_df)`: Add weather columns to dataframe

**Weather Factors**:
- Temperature (°F)
- Wind speed (mph)
- Precipitation probability (%)
- Is dome game (bool)

**Sport Logic**:
- **NFL**: All weather factors matter (wind affects passing, cold affects ball handling)
- **MLB**: Wind and temperature critical (affects fly balls, HRs)
- **NBA**: Always indoor, no weather impact

---

#### 6. **Injuries Provider** (`injuries_provider.py`)

**Purpose**: Player injury data

**Key Functions**:
- `fetch_injuries(sport, week, season)`: Get injury reports
- `enrich_props_with_injuries(props_df)`: Add injury status to dataframe

**Injury Statuses**: Out, Doubtful, Questionable, Probable, Healthy

**Current State**: Uses mock injuries. Future: Integrate real injury APIs

---

#### 7. **Baseline Stats** (`baseline_stats.py`)

**Purpose**: Historical player statistics

**Key Functions**:
- `fetch_player_baselines(sport, season)`: Get season averages
- `get_player_baseline(player_id, stat_type)`: Get specific stat

**Stats Tracked**:
- Season averages (yards, points, hits, etc.)
- Last 5 game averages
- Career averages
- Split stats (home/away, vs opponent, etc.)

</details>

---

## Feature Engineering

<details>
<summary><strong>Click to expand: Feature Pipeline & Transformations</strong></summary>

### Module: `src/features/pipeline.py`

**Purpose**: Transform raw props data into ML-ready features

### Main Function

```python
def build_full_features(props_df: pd.DataFrame, sport: str = "NFL") -> pd.DataFrame:
    """
    Complete feature engineering pipeline.

    Input: Raw props with lines and odds
    Output: Feature-rich dataframe ready for ML models
    """
```

### Feature Categories

#### 1. **Player Form Features**
- Recent game performance (last 1, 3, 5, 10 games)
- Consistency score (variance in recent games)
- Trend direction (improving vs declining)
- Hot streak detection (3+ games above average)

**Position-Specific Consistency**:
- NFL QB: 78-90% (most consistent)
- NFL RB: 70-82%
- NFL WR/TE: 65-80%
- NBA PG/SG/SF/PF/C: 68-85%
- MLB Batter/Pitcher: 60-78% (highest variance)

#### 2. **Usage Features**
- Snap share / minutes percentage
- Target share / shot attempts
- Red zone / clutch usage
- Game script impact

**Sport-Specific**:
- **NFL**: Snap %, target %, red zone %
- **NBA**: Minutes %, shot attempts %, clutch usage
- **MLB**: Plate appearance %, RISP situations

#### 3. **Matchup Features**
- Opponent defensive ranking
- Historical performance vs opponent
- Home/away splits
- Division/conference games

#### 4. **Context Features**
- Game total (over/under)
- Spread (expected margin)
- Team pace of play
- Rest days / back-to-back

#### 5. **Weather Features** (NFL/MLB only)
- Temperature (affects ball physics)
- Wind speed (affects passing/fly balls)
- Precipitation (affects handling)
- Dome game (no weather)

**Weather Impact Calculation**:
```python
# NFL: Wind > 15 mph = -15% passing yards
# MLB: Wind blowing out > 10 mph = +20% HR probability
# NBA: Always "None" (indoor)
```

#### 6. **Injury Features**
- Player injury status
- Key teammates out (usage boost)
- Opponent injuries (matchup advantage)

#### 7. **Odds-Derived Features**
- Implied probability from odds
- Market inefficiency score
- Line movement (if available)
- Sharp vs square action

### Feature Engineering Process

```python
# Step 1: Load raw props
props_df = fetch_current_props(week=5, season=2025, sport="NFL")

# Step 2: Build features
features_df = build_full_features(props_df, sport="NFL")

# Step 3: Feature validation
# - Check for nulls
# - Scale numeric features
# - Encode categorical features

# Step 4: Ready for ML models
predictions = model.predict_proba(features_df)
```

### Sport-Aware Feature Logic

The pipeline automatically detects sport and adjusts:
- Position recognition (QB/RB/WR vs PG/SG/SF vs BATTER/PITCHER)
- Usage metrics (snaps vs minutes vs plate appearances)
- Weather impact (critical vs moderate vs none)
- Consistency expectations (position-specific)

</details>

---

## Machine Learning Models

<details>
<summary><strong>Click to expand: Probability Estimation Models</strong></summary>

### Module: `src/models/`

**Philosophy**: Ensemble of complementary models for robust predictions

### 1. **Gradient Boosting Model** (`gbm.py`)

**Algorithm**: XGBoost or LightGBM

**Strengths**:
- Captures non-linear relationships
- Handles missing data well
- Fast training and prediction
- Feature importance insights

**Training Process**:
```python
from src.models.gbm import GradientBoostingModel

model = GradientBoostingModel(model_type="xgboost")
model.train(features_df, outcomes_df)
probabilities = model.predict_proba(new_features_df)
```

**Hyperparameters**:
- Max depth: 6-8
- Learning rate: 0.01-0.1
- N estimators: 100-500
- Min child weight: 1-5

**Output**: Point estimate probability (e.g., 0.65 = 65% chance of hitting over)

---

### 2. **Bayesian Hierarchical Model** (`bayes.py`)

**Algorithm**: PyMC3 or Stan

**Strengths**:
- Quantifies uncertainty (confidence intervals)
- Incorporates prior knowledge
- Handles small sample sizes
- Player-specific effects

**Model Structure**:
```
Global Effect (all players)
  ↓
Position Effect (QB, RB, WR, etc.)
  ↓
Player Effect (individual skill)
  ↓
Game Context Effect
  ↓
Final Probability
```

**Training Process**:
```python
from src.models.bayes import BayesianModel

model = BayesianModel()
model.fit(features_df, outcomes_df)
mean_prob, ci_lower, ci_upper = model.predict_with_uncertainty(new_features_df)
```

**Output**:
- Mean probability (e.g., 0.65)
- 95% CI (e.g., [0.58, 0.72])

---

### 3. **Ensemble Combination**

**Strategy**: Weighted average of GBM and Bayesian

```python
ensemble_prob = 0.6 * gbm_prob + 0.4 * bayes_prob
```

**Rationale**:
- GBM: Better at capturing patterns in abundant data
- Bayesian: Better at quantifying uncertainty
- Ensemble: Best of both worlds

---

### 4. **Model Calibration** (`calibration.py`)

**Purpose**: Ensure predicted probabilities match real-world frequencies

**Calibration Check**:
```python
# If model predicts 70% on 100 props, ~70 should hit
# If 80 hit, model is over-calibrated (too conservative)
# If 60 hit, model is under-calibrated (too aggressive)
```

**Calibration Methods**:
- Platt scaling
- Isotonic regression
- Beta calibration

**Monitoring**:
```python
from src.models.calibration import CalibrationMonitor

monitor = CalibrationMonitor()
monitor.check_calibration(predictions, actual_outcomes)
# Returns: calibration_score, drift_alert
```

**Drift Detection**:
- Weekly calibration checks
- Alert if score drops below 0.85
- Auto-retrain trigger

---

### Model Training Pipeline

```python
# 1. Load historical data
historical_df = load_past_outcomes(weeks=1-10, season=2024)

# 2. Build features
features_df = build_full_features(historical_df)

# 3. Train models
gbm_model = GradientBoostingModel()
gbm_model.train(features_df, outcomes)

bayes_model = BayesianModel()
bayes_model.fit(features_df, outcomes)

# 4. Validate
test_predictions = gbm_model.predict_proba(test_features_df)
calibration_score = check_calibration(test_predictions, test_outcomes)

# 5. Save
gbm_model.save("models/gbm_nfl_week5.pkl")
bayes_model.save("models/bayes_nfl_week5.pkl")
```

</details>

---

## Correlation Analysis

<details>
<summary><strong>Click to expand: Copula-Based Correlation Modeling</strong></summary>

### Module: `src/corr/correlation.py`

**Purpose**: Capture dependencies between player props for portfolio optimization

### Why Correlation Matters

**Example**:
- Mahomes passing yards OVER + Kelce receiving yards OVER = highly correlated
- If Mahomes throws for 300+, Kelce likely catches 80+
- Portfolio should account for this dependency

### Correlation Types

#### 1. **Same-Game Correlations**
- QB passing yards ↔ WR receiving yards (positive)
- Team total points ↔ Individual player TDs (positive)
- RB rushing attempts ↔ QB passing attempts (negative in run-heavy games)

#### 2. **Cross-Game Correlations**
- Weather-based (all outdoor games in snow)
- Opponent-based (two WRs vs same weak secondary)

#### 3. **Sport-Specific Correlations**
- **NFL**: High QB-receiver correlation
- **NBA**: High pace-driven correlations (all players benefit from fast games)
- **MLB**: Ballpark-driven correlations (hitter-friendly parks boost all batters)

### Copula Models

**What is a Copula?**
A mathematical function that models joint probability distributions.

**Types Used**:
1. **Gaussian Copula**: Symmetric correlations
2. **T-Copula**: Handles extreme events (both players pop off or both bust)
3. **Clayton Copula**: Lower-tail dependence (both underperform together)
4. **Gumbel Copula**: Upper-tail dependence (both overperform together)

### Implementation

```python
from src.corr.correlation import CorrelationAnalyzer

analyzer = CorrelationAnalyzer()

# Estimate correlations from historical data
correlation_matrix = analyzer.estimate_correlations(props_df, historical_outcomes)

# Fit copula
copula = analyzer.fit_copula(props_df, copula_type="t")

# Sample correlated outcomes
correlated_samples = copula.sample(n_simulations=10000)
```

### Correlation Matrix

Example for 3 props:
```
              Mahomes Pass Yds  Kelce Rec Yds  Hill Rec Yds
Mahomes Pass Yds      1.00            0.65          0.58
Kelce Rec Yds         0.65            1.00          0.35
Hill Rec Yds          0.58            0.35          1.00
```

### Using Correlations in Optimization

The optimizer uses correlation matrix to:
1. Avoid over-concentrated risk
2. Build diversified slips
3. Size positions appropriately

**Example**:
- High correlation (0.65+): Reduce combined exposure
- Low correlation (<0.30): Safe to combine
- Negative correlation: Natural hedge

</details>

---

## Portfolio Optimization

<details>
<summary><strong>Click to expand: Kelly Criterion & Slip Building</strong></summary>

### Module: `src/optimize/slip_opt.py`

**Purpose**: Build optimal prop combinations (slips) using Kelly criterion

### Kelly Criterion

**Formula**:
```
Kelly % = (bp - q) / b

where:
- b = decimal odds - 1
- p = win probability (from models)
- q = 1 - p (lose probability)
```

**Example**:
- Prop has -110 odds (1.91 decimal) → b = 0.91
- Model predicts 60% win probability → p = 0.60, q = 0.40
- Kelly = (0.91 × 0.60 - 0.40) / 0.91 = 0.16 (16% of bankroll)

### Fractional Kelly

**Problem**: Full Kelly is aggressive, high variance

**Solution**: Use fractional Kelly (e.g., 0.25 or 0.5 Kelly)

```python
# Quarter Kelly (most conservative)
position_size = kelly_percentage * 0.25

# Half Kelly (balanced)
position_size = kelly_percentage * 0.5
```

### Slip Optimizer

**Objective**: Maximize expected value while respecting constraints

```python
from src.optimize.slip_opt import SlipOptimizer

optimizer = SlipOptimizer(
    risk_mode="balanced",  # conservative, balanced, aggressive
    min_legs=2,
    max_legs=6,
    min_odds=1.5,
    max_odds=5.0
)

slips = optimizer.optimize(props_df, probabilities, correlations)
```

### Optimization Constraints

#### 1. **Leg Count**
- Min: 2 legs (parlays only)
- Max: 8 legs (avoid lottery tickets)

#### 2. **Odds Range**
- Min odds: 1.50 (-200) - avoid heavy juice
- Max odds: 5.00 (+400) - avoid long shots

#### 3. **Diversity Constraints**
- Max props from same player: 1-2
- Max props from same team: 2-3
- Max props from same game: 3-4

#### 4. **Correlation Constraints**
- Max sum of correlations in slip: 2.0
- Avoid highly correlated groups (sum >3.0)

#### 5. **Edge Threshold**
- Minimum edge: 5% (model prob - implied prob)
- Target edge: 10%+

### Risk Modes

#### Conservative Mode
- Fractional Kelly: 0.25
- Min edge: 8%
- Max legs: 4
- High diversity requirements

#### Balanced Mode
- Fractional Kelly: 0.5
- Min edge: 5%
- Max legs: 6
- Moderate diversity

#### Aggressive Mode
- Fractional Kelly: 0.75
- Min edge: 3%
- Max legs: 8
- Relaxed diversity

### Output

```python
[
  {
    "slip_id": 1,
    "legs": [
      {"player": "Mahomes", "prop": "Pass Yds", "line": 275.5, "pick": "OVER"},
      {"player": "Kelce", "prop": "Rec Yds", "line": 65.5, "pick": "OVER"},
    ],
    "combined_odds": 2.64,
    "win_probability": 0.42,
    "expected_value": 1.11,  # $1.11 return per $1 bet
    "kelly_percentage": 0.12,  # 12% of bankroll
    "risk_score": 0.65  # 0-1 scale
  },
  ...
]
```

</details>

---

## Evaluation & Testing

<details>
<summary><strong>Click to expand: Backtesting & Performance Analysis</strong></summary>

### Module: `src/eval/`

### 1. **Backtesting Engine** (`backtest.py`)

**Purpose**: Evaluate strategies on historical data

**Process**:
```python
from src.eval.backtest import Backtester

backtester = Backtester(
    start_week=1,
    end_week=10,
    season=2024,
    sport="NFL"
)

results = backtester.run_backtest(
    strategy="kelly_balanced",
    initial_bankroll=1000
)
```

**Metrics Tracked**:
- Total ROI
- Win rate
- Average edge
- Sharpe ratio
- Max drawdown
- Kelly deviation

**Output**:
```python
{
  "total_bets": 250,
  "wins": 142,
  "win_rate": 0.568,
  "total_roi": 0.18,  # 18% return
  "sharpe_ratio": 1.45,
  "max_drawdown": -0.12,  # -12% worst period
  "final_bankroll": 1180
}
```

---

### 2. **Experiment Tracking** (`experiments.py`)

**Purpose**: Track all parameter changes and outcomes

**Usage**:
```python
from src.eval.experiments import ExperimentTracker

tracker = ExperimentTracker()

# Start experiment
exp_id = tracker.start_experiment(
    name="test_conservative_kelly",
    parameters={"kelly_fraction": 0.25, "min_edge": 0.08}
)

# Run experiment
results = run_strategy(parameters)

# Log results
tracker.log_results(exp_id, results)

# Compare experiments
best_exp = tracker.get_best_experiment(metric="sharpe_ratio")
```

---

### 3. **Export System** (`exports.py`)

**Purpose**: Export props and slips to CSV

**Functions**:
```python
from src.eval.exports import export_props, export_slips

# Export all props with probabilities
export_props(
    props_df,
    probabilities,
    filepath="exports/week5_props.csv"
)

# Export optimized slips
export_slips(
    slips,
    filepath="exports/week5_slips.csv"
)
```

**CSV Format**:
```csv
player,prop_type,line,odds,model_prob,edge,confidence_lower,confidence_upper
Patrick Mahomes,Pass Yds,275.5,-110,0.68,0.15,0.62,0.74
Travis Kelce,Rec Yds,65.5,-105,0.58,0.08,0.52,0.64
```

</details>

---

## API Key Management

<details>
<summary><strong>Click to expand: Secure Credential Storage</strong></summary>

### Module: `src/keys/manager.py`

**Purpose**: Securely store and retrieve API keys

### Storage Methods

#### 1. **Environment Variables** (Default)
```bash
# .env file
ODDS_API_KEY=your_key_here
SPORTGAMEODDS_API_KEY=your_key_here
OPENWEATHER_API_KEY=your_key_here
```

#### 2. **Encrypted File Storage**
```python
from src.keys.manager import KeyManager

manager = KeyManager()

# Store key (encrypted)
manager.store_key("odds_api", "your_key_here")

# Retrieve key
api_key = manager.get_key("odds_api")
```

**Encryption**: Uses Fernet (symmetric encryption)

#### 3. **System Keychain** (macOS/Linux)
```python
manager = KeyManager(backend="keychain")
manager.store_key("odds_api", "your_key_here")
```

### API Key Validation

```python
# Validate key works
is_valid = manager.validate_key("odds_api")

# Check remaining quota
quota = manager.check_quota("odds_api")
# Returns: {"remaining": 450, "total": 500}
```

### Best Practices

1. **Never commit .env to git**
2. **Use .env.example as template**
3. **Rotate keys monthly**
4. **Monitor usage quotas**
5. **Use different keys for dev/prod**

</details>

---

## Sharing & Export

<details>
<summary><strong>Click to expand: Anonymized Packages & Sharing</strong></summary>

### Module: `src/share/pack.py`

**Purpose**: Create shareable analysis packages without revealing sensitive info

### Creating a Share Package

```python
from src.share.pack import create_share_package

package = create_share_package(
    props_df=props_df,
    slips=optimized_slips,
    week=5,
    season=2025,
    sport="NFL",
    anonymize=True  # Remove personal info
)

# Saves to: shares/nfl_week5_2025_share.zip
```

### Package Contents

```
share_package.zip
├── props.csv           # Props with probabilities (anonymized)
├── slips.csv           # Optimized slips
├── analysis.json       # Summary stats
├── correlations.csv    # Correlation matrix
└── README.txt          # How to use this package
```

### Anonymization

Removes:
- API keys
- User preferences
- Personal bankroll amounts
- Experiment history

Keeps:
- All analysis results
- Probabilities and edges
- Slip recommendations
- Model insights

### Importing a Share Package

```python
from src.share.pack import load_share_package

data = load_share_package("shares/nfl_week5_2025_share.zip")

props_df = data["props"]
slips = data["slips"]
correlations = data["correlations"]
```

</details>

---

## Snapshots & State Management

<details>
<summary><strong>Click to expand: Locking & Reviewing Past Analyses</strong></summary>

### Module: `src/snapshots/snapshot.py`

**Purpose**: Save and restore complete analysis states

### Creating a Snapshot

```python
from src.snapshots.snapshot import SnapshotManager

snapshot_mgr = SnapshotManager()

# Save current analysis
snapshot_id = snapshot_mgr.create_snapshot(
    props_df=props_df,
    features_df=features_df,
    probabilities=probabilities,
    slips=slips,
    metadata={
        "week": 5,
        "season": 2025,
        "sport": "NFL",
        "model_version": "v1.2.3"
    }
)
```

### Snapshot Storage

```
data/snapshots/
├── nfl_week5_2025_abc123.snapshot
├── nba_2025_10_14_def456.snapshot
└── mlb_2025_10_15_ghi789.snapshot
```

### Loading a Snapshot

```python
# List available snapshots
snapshots = snapshot_mgr.list_snapshots(sport="NFL", season=2025)

# Load specific snapshot
snapshot = snapshot_mgr.load_snapshot(snapshot_id="abc123")

props_df = snapshot["props"]
slips = snapshot["slips"]
metadata = snapshot["metadata"]
```

### Use Cases

1. **Compare Strategies**: Run different optimization on same props
2. **Audit Trail**: Review what was recommended at time of bet
3. **Model Improvement**: Compare new models to old on same data
4. **Learning**: Review successful vs unsuccessful analyses

</details>

---

## User Interface (Streamlit App)

<details>
<summary><strong>Click to expand: Streamlit App Features & Layout</strong></summary>

### Module: `app/main.py`

**Purpose**: Interactive web interface for all features

### App Layout

#### 1. **Sidebar Controls**
- Sport selector (NFL/NBA/MLB)
- Data source (Odds API / Mock Data)
- Week/Season selectors
- Risk mode (Conservative/Balanced/Aggressive)
- Refresh button

#### 2. **Main Content Tabs**

**Tab 1: Props Explorer**
- Table of all props with probabilities
- Filter by position, team, prop type
- Sort by edge, confidence
- Trend chips (🔥 hot streak, ❄️ cold streak, 🎯 target)
- Export to CSV button

**Tab 2: Slip Optimizer**
- Display optimized slips
- Slip cards with:
  - Combined odds
  - Win probability
  - Expected value
  - Risk score
- Diversity metrics
- Export slips button

**Tab 3: Correlation Inspector**
- Heatmap of correlations
- Scatter plots of prop relationships
- Filter by game, team
- Identify hedges and stacks

**Tab 4: What-If Sandbox**
- Adjust probabilities manually
- See impact on slip optimization
- Test different scenarios
- Save custom scenarios

**Tab 5: Calibration Monitor**
- Model performance metrics
- Calibration curve
- Drift alerts
- Historical accuracy

**Tab 6: Settings**
- User preferences
- API key management
- Export paths
- UI customization

### Interactive Features

#### Trend Chips
- 🔥 **Hot Streak**: 3+ games above average
- ❄️ **Cold Streak**: 3+ games below average
- 🎯 **High Confidence**: Narrow confidence interval
- ⚠️ **Low Confidence**: Wide confidence interval
- 💥 **Ceiling Game**: Matchup suggests explosion
- 🐌 **Floor Game**: Matchup suggests limited upside

#### Filters
- Position (QB, RB, WR, TE, K)
- Prop type (yards, TDs, receptions, etc.)
- Team
- Edge threshold (show only 5%+ edge)
- Confidence threshold

#### Visualizations
- Probability distribution curves
- Edge bar charts
- Correlation heatmaps
- Win rate time series
- Bankroll growth charts

</details>

---

## Configuration System

<details>
<summary><strong>Click to expand: User Preferences & Settings</strong></summary>

### Configuration Files

#### 1. **user_prefs.yaml**

Main configuration file for user preferences:

```yaml
# Risk tolerance
risk_mode: balanced  # conservative, balanced, aggressive

# Slip constraints
slip:
  min_legs: 2
  max_legs: 6
  min_odds: 1.5
  max_odds: 5.0
  min_edge: 0.05

# Diversity settings
diversity:
  min_players: 3
  max_same_team: 3
  max_same_game: 4
  max_same_position: 2

# Correlation settings
correlation:
  max_correlation: 0.70
  copula_type: "t"

# Export settings
export:
  format: "csv"
  include_probabilities: true
  include_features: false
  include_analysis: true

# UI preferences
ui:
  default_sport: "NFL"
  default_data_source: "mock"
  props_per_page: 50
  theme: "dark"
```

#### 2. **.env**

Environment variables for secrets:

```env
# API Keys
ODDS_API_KEY=your_key_here
SPORTGAMEODDS_API_KEY=your_key_here
OPENWEATHER_API_KEY=your_key_here

# Paths
DATA_DIR=./data
CACHE_DIR=./data/cache
EXPORTS_DIR=./exports

# App Settings
DEBUG=False
LOG_LEVEL=INFO
```

#### 3. **src/config.py**

Python configuration module:

```python
from src.config import Config

config = Config()

# Access settings
risk_mode = config.risk_mode
min_edge = config.slip.min_edge
max_legs = config.slip.max_legs
```

### Configuration Hierarchy

1. **Defaults** (in code)
2. **user_prefs.yaml** (overrides defaults)
3. **Environment variables** (overrides YAML)
4. **UI settings** (overrides all, session only)

</details>

---

## Multi-Sport Support

<details>
<summary><strong>Click to expand: Sport-Specific Logic & Differences</strong></summary>

### Sport Configuration

Each sport has unique characteristics handled by the system:

### NFL (American Football)

**Prop Markets (14)**:
- Passing: yards, TDs, completions, attempts, interceptions
- Rushing: yards, TDs, attempts
- Receiving: yards, TDs, receptions
- Kicking: total points

**Positions**: QB, RB, WR, TE, K

**Key Factors**:
- Weather critical (wind, temperature, precipitation)
- Game script (leading teams run more)
- Injuries impact usage dramatically
- Weekly schedule (once per week)

**Consistency**:
- QB: Highest (78-90%)
- RB: Moderate (70-82%)
- WR/TE: Lower (65-80%)

**Best Props**: Passing/rushing yards (most consistent)

---

### NBA (Basketball)

**Prop Markets (11)**:
- Scoring: points, three-pointers, free throws
- Playmaking: assists
- Rebounding: rebounds
- Defense: steals, blocks
- Combos: points+assists, points+rebounds, PRA

**Positions**: PG, SG, SF, PF, C

**Key Factors**:
- Minutes played (30+ preferred)
- Usage rate (20%+ for stars)
- Pace of play (faster = more stats)
- Back-to-back games (fatigue)
- All indoor (no weather)

**Consistency**:
- All positions: 68-85% (moderate variance)

**Best Props**: PRA combos, points, assists

---

### MLB (Baseball)

**Prop Markets (11)**:
- Batters: hits, home runs, RBIs, total bases, runs, stolen bases
- Pitchers: strikeouts, hits allowed, earned runs, walks, outs recorded

**Positions**: BATTER, PITCHER

**Key Factors**:
- Ballpark (hitter vs pitcher friendly)
- Weather (wind, temperature affect fly balls)
- Platoon splits (RHB vs LHP, LHB vs RHP)
- Lineup position (1-4 get more at-bats)
- Pitcher pitch count limits

**Consistency**:
- Batters: Low (60-75%)
- Pitchers: Moderate (65-80%)

**Best Props**: Pitcher strikeouts, batter hits

---

### Sport Detection

The system automatically detects sport from game IDs and adjusts logic:

```python
def infer_sport_from_game_id(game_id: str) -> str:
    if game_id.startswith("nfl_"):
        return "NFL"
    elif game_id.startswith("nba_"):
        return "NBA"
    elif game_id.startswith("mlb_"):
        return "MLB"
```

### Sport-Specific Processing

Feature engineering, weather impact, and optimization all adapt based on sport parameter.

</details>

---

## Utilities & Helpers

<details>
<summary><strong>Click to expand: Notification System & Other Utils</strong></summary>

### Module: `src/utils/`

#### Prop Notifications (`prop_notifications.py`)

**Purpose**: Alert system for value props and opportunities

**Features**:
- Email alerts for high-edge props
- Push notifications (via external service)
- Discord/Slack webhooks
- Custom thresholds

**Usage**:
```python
from src.utils.prop_notifications import NotificationManager

notifier = NotificationManager(
    email="user@example.com",
    min_edge=0.10  # Alert for 10%+ edge
)

# Check props and send alerts
notifier.check_and_notify(props_df, probabilities)
```

**Alert Format**:
```
🚨 High Value Prop Alert!

Player: Patrick Mahomes
Prop: Pass Yds OVER 275.5
Odds: -110 (implied 52.4%)
Model: 68% (15.6% edge)
Confidence: [62%, 74%]

Recommendation: 🟢 Strong bet
Kelly: 12% of bankroll
```

</details>

---

## Appendix

### Quick Reference

**Start the app**:
```bash
streamlit run app/main.py
```

**CLI analysis**:
```bash
python scripts/run_week.py --week 5 --season 2025 --sport NFL
```

**Run tests**:
```bash
pytest tests/
```

**Backtest strategy**:
```bash
python scripts/run_week.py --mode backtest --start-week 1 --end-week 10
```

### File Locations

- **Props cache**: `data/cache/`
- **Exports**: `exports/`
- **Snapshots**: `data/snapshots/`
- **Models**: `models/`
- **Logs**: `logs/`

### Troubleshooting

**Issue**: API returns no games
- Check sport is in season
- Verify API key is valid
- Check quota not exceeded

**Issue**: Models not loading
- Check `models/` directory exists
- Verify model files present
- Retrain if needed

**Issue**: Slow performance
- Clear cache: `rm data/cache/*.parquet`
- Reduce prop count
- Use fewer simulation iterations

---

**End of Master Guide**

For sport-specific details, see:
- `docs/GUIDE_NFL.md`
- `docs/GUIDE_NBA.md`
- `docs/GUIDE_MLB.md`
