# BetterBros Props

Advanced probability estimation and portfolio optimization for player props across NFL, NBA, and MLB.

## Features

### Multi-Sport Support 🏈 🏀 ⚾
- **NFL**: 14 prop markets including passing, rushing, receiving, touchdowns, and kicking
- **NBA**: 11 prop markets including points, rebounds, assists, three-pointers, and combos
- **MLB**: 11 prop markets including hits, home runs, RBIs, pitcher strikeouts, and outs

### Core Capabilities
- **Multi-Model Probability Estimation**: Combines gradient boosting and Bayesian hierarchical models for robust probability estimates
- **Correlation Modeling**: Uses copulas to capture complex dependencies between player props
- **Portfolio Optimization**: Kelly criterion-based slip optimization with diversity constraints
- **Uncertainty Quantification**: Confidence intervals and calibration monitoring
- **Contextual Intelligence**: Incorporates injuries, weather, and historical trends (sport-specific)

### User Interface
- **Interactive Streamlit Dashboard**: Clean, modern UI for exploring props and slips
- **Trend Chips**: Real-time detection of offensive surges, defensive weaknesses, and other key trends
- **What-If Sandbox**: Adjust probabilities interactively to explore scenarios
- **Correlation Inspector**: Visualize dependencies between player props
- **Calibration Monitor**: Real-time alerts when models drift

### Analysis Tools
- **Backtesting Engine**: Evaluate strategies on historical data
- **Snapshot Management**: Lock and review past analyses
- **Experiment Tracking**: Monitor all parameter changes and outcomes
- **CI Filtering**: Focus on high-confidence predictions

### Export & Sharing
- **CSV Export**: Props and slips export for external analysis
- **Anonymized Sharing**: Generate shareable packages without revealing sensitive info
- **API Key Management**: Secure credential storage

## Quick Start

### Installation

```bash
# Clone repository
cd nfl-props-analyzer

# Install dependencies
make dev

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

### Run the App

```bash
# Start Streamlit app
make run
```

### CLI Usage

```bash
# Analyze current week (NFL)
python scripts/run_week.py --week 5 --season 2025 --sport NFL

# Run backtest (NFL)
python scripts/run_week.py --mode backtest --start-week 1 --end-week 10 --sport NFL

# Analyze NBA/MLB (date-based)
python scripts/run_week.py --season 2025 --sport NBA
python scripts/run_week.py --season 2025 --sport MLB
```

## Configuration

Edit `user_prefs.yaml` to customize:
- Risk modes (conservative, balanced, aggressive)
- Slip constraints (min/max legs, odds ranges)
- Diversity targets
- Correlation settings
- Export paths
- UI preferences

## Tech Stack

- **Data Science**: pandas, numpy, scipy, scikit-learn
- **ML Models**: XGBoost, LightGBM, statsmodels
- **Correlation**: copulas library
- **UI**: Streamlit
- **APIs**: httpx for data ingestion
- **Config**: Pydantic for validation, YAML for storage

## ToS Compliance

This tool:
- Uses only official API endpoints (no scraping)
- Respects all rate limits
- Stores credentials securely
- Uses publicly available data sources

## Architecture

```
nfl-props-analyzer/
├── app/                 # Streamlit UI
├── src/
│   ├── ingest/         # Data ingestion (Sleeper, weather, injuries)
│   ├── features/       # Feature engineering & trends
│   ├── models/         # Probability models (GBM, Bayesian)
│   ├── corr/           # Correlation & copulas
│   ├── optimize/       # Slip optimization
│   ├── eval/           # Backtesting & evaluation
│   ├── snapshots/      # State management
│   ├── keys/           # API key management
│   └── share/          # Export & sharing
├── tests/              # Test suite
├── scripts/            # CLI tools
└── data/               # Data storage
```

## Development

```bash
# Run tests
make test

# Lint code
make lint

# Format code
make format

# Run backtest
make backtest
```

## Roadmap

- [ ] Real API integrations (Sleeper, OpenWeather)
- [ ] Historical data collection pipeline
- [ ] Model training on real outcomes
- [ ] Advanced copula models (vine copulas)
- [ ] Live odds tracking
- [ ] Mobile-responsive UI
- [ ] Real-time notifications
- [ ] Community sharing platform

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool is for educational and analytical purposes only. Always gamble responsibly and within your means. Past performance does not guarantee future results.
