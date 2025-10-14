# BetterBros Props - Deployment Package

## Package Contents

This deployment package (`betterbros-props-package.zip`) contains everything needed to run the BetterBros Props application.

### Included Files

#### Core Application
- **app/**: Complete Streamlit UI application
  - `main.py`: Primary Streamlit application with multi-sport support
  - `CHANGELOG.md`: Version history and updates
  - `README.md`: App-specific documentation
  - `STYLING.md`: UI styling guidelines

#### Backend Source Code
- **src/**: Complete backend logic for all sports
  - **ingest/**: Data ingestion modules
    - `odds_api_client.py`: The Odds API integration (primary data source)
    - `sportgameodds_client.py`: SportsGameOdds API integration (secondary source)
    - `sleeper_client.py`: Mock data generator for NFL/NBA/MLB
    - `sport_config.py`: Sport-specific configuration (markets, positions, etc.)
    - `injuries_provider.py`: Injury data integration
    - `weather_provider.py`: Weather data integration
    - `baseline_stats.py`: Player baseline statistics
  - **features/**: Feature engineering pipeline
    - `pipeline.py`: Sport-aware feature generation
  - **models/**: ML models for probability estimation
    - `gbm.py`: Gradient boosting model
    - `bayes.py`: Bayesian hierarchical model
    - `calibration.py`: Model calibration and drift detection
  - **corr/**: Correlation modeling
    - `correlation.py`: Copula-based correlation analysis
  - **optimize/**: Portfolio optimization
    - `slip_opt.py`: Kelly criterion-based slip optimization
  - **eval/**: Evaluation and testing
    - `backtest.py`: Historical backtesting engine
    - `experiments.py`: Experiment tracking
    - `exports.py`: CSV export functionality
  - **snapshots/**: State management
    - `snapshot.py`: Lock and review past analyses
  - **keys/**: API key management
    - `manager.py`: Secure credential storage
  - **share/**: Export and sharing
    - `pack.py`: Anonymized sharing packages
  - **utils/**: Utilities
    - `prop_notifications.py`: Alert system
  - `config.py`: Central configuration

#### Documentation
- **docs/**: Comprehensive documentation
  - `GUIDE_NFL.md`: NFL-specific usage guide (positions, weather, props)
  - `GUIDE_NBA.md`: NBA-specific usage guide (positions, pace, props)
  - `GUIDE_MLB.md`: MLB-specific usage guide (ballparks, weather, props)
  - `ML_MODELS.md`: Machine learning model documentation
  - `FEATURES.md`: Feature engineering documentation
  - **api/**: API integration guides
    - `README.md`: Comprehensive API documentation
    - **REFERENCES/**: API query examples and screenshots

#### Configuration Files
- **requirements.txt**: Python dependencies
- **.env.example**: Environment variable template (no real API keys)
- **user_prefs.yaml**: User preferences and risk settings
- **README.md**: Project overview and quick start
- **QUICKSTART.md**: Quick start guide

## Installation

```bash
# Extract the package
unzip betterbros-props-package.zip
cd betterbros-props-package

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Add your API keys
```

## Required API Keys

Edit `.env` and add:

```env
# The Odds API (Required for real props data)
ODDS_API_KEY=your_odds_api_key_here

# Optional: SportsGameOdds API (alternative data source)
SPORTGAMEODDS_API_KEY=your_sportgameodds_key_here

# Optional: Weather API
OPENWEATHER_API_KEY=your_weather_key_here
```

Get API keys:
- The Odds API: https://the-odds-api.com/ (500 free requests)
- SportsGameOdds: https://sportsgameodds.com/
- OpenWeather: https://openweathermap.org/api

## Running the Application

### Streamlit UI (Recommended)

```bash
# Start the web interface
streamlit run app/main.py
```

The app will open in your browser at `http://localhost:8501`

### CLI Usage

```bash
# NFL analysis
python scripts/run_week.py --week 5 --season 2025 --sport NFL

# NBA analysis (date-based)
python scripts/run_week.py --season 2025 --sport NBA

# MLB analysis (date-based)
python scripts/run_week.py --season 2025 --sport MLB

# Run backtest
python scripts/run_week.py --mode backtest --start-week 1 --end-week 10 --sport NFL
```

## Multi-Sport Support

### NFL
- **14 prop markets**: Passing, rushing, receiving, touchdowns, kicking
- **Week-based**: Games occur weekly
- **Weather sensitive**: Outdoor games affected by wind, temperature, precipitation
- **Positions**: QB, RB, WR, TE, K

### NBA
- **11 prop markets**: Points, rebounds, assists, threes, combos (PRA, PA, PR)
- **Date-based**: Games occur nightly
- **Indoor**: No weather impact
- **Positions**: PG, SG, SF, PF, C

### MLB
- **11 prop markets**: Hits, home runs, RBIs, total bases, strikeouts, outs
- **Date-based**: Games occur daily
- **Weather sensitive**: Wind and temperature affect hitting/pitching
- **Positions**: Batter, Pitcher

## Configuration

Edit `user_prefs.yaml` to customize:

```yaml
# Risk tolerance
risk_mode: balanced  # conservative, balanced, aggressive

# Slip constraints
slip:
  min_legs: 2
  max_legs: 8
  min_odds: 1.5
  max_odds: 5.0

# Diversity targets
diversity:
  min_players: 3
  max_same_team: 3

# Export settings
export:
  format: csv
  include_analysis: true
```

## Features

### Core Capabilities
- Multi-sport support (NFL, NBA, MLB)
- Dual-model probability estimation (GBM + Bayesian)
- Correlation modeling with copulas
- Kelly criterion portfolio optimization
- Confidence intervals and calibration monitoring
- Injury and weather integration

### UI Features
- Interactive prop explorer
- Trend detection (hot streaks, defensive weaknesses)
- What-if scenario sandbox
- Correlation inspector
- Slip optimizer with diversity constraints
- CSV export

### Analysis Tools
- Historical backtesting
- Snapshot management
- Experiment tracking
- Calibration alerts

## Development Status

### Completed
- Multi-sport architecture (NFL, NBA, MLB)
- Mock data generators for all sports
- Sport-aware feature engineering
- The Odds API integration
- SportsGameOdds API integration
- Comprehensive documentation
- Sport-specific usage guides

### Pending (Future Enhancements)
- Real-time NBA injury data integration
- Real-time MLB injury data integration
- Sport-specific weather provider enhancements
- Live odds tracking
- Mobile-responsive UI
- Real-time push notifications
- Community sharing platform

## Testing

The application currently uses mock data by default for development. To test:

```bash
# Test multi-sport mock data
python test_multi_sport.py

# Test with real API (requires ODDS_API_KEY)
# Set mock_mode=False in app/main.py
```

## Support

For issues, questions, or feature requests:
1. Check the sport-specific guides in `docs/`
2. Review API documentation in `docs/api/`
3. Consult `QUICKSTART.md` for common setup issues

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool is for educational and analytical purposes only. Always gamble responsibly and within your means. Past performance does not guarantee future results.
