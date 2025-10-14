# NFL Props Analyzer - Streamlit App

## Overview

The NFL Props Analyzer Streamlit app is the main user interface for analyzing NFL player props, generating optimized parlays, and running backtests. Built with Streamlit for rapid prototyping and easy deployment.

## Quick Start

```bash
# From project root
streamlit run app/main.py
```

**Default URL:** http://localhost:8501

## Environment Setup

The app requires the following environment variable:

```bash
export ODDS_API_KEY=your_api_key_here
```

Or create a `.env` file in the project root:

```
ODDS_API_KEY=your_api_key_here
```

## App Structure

### Main Components

- **`main.py`**: Single-file Streamlit application (108KB)
  - Theme configuration and CSS customization
  - Session state management
  - Data fetch and slip generation controls
  - Analysis visualization tabs
  - Calibration monitoring
  - Quick Actions bar

### Configuration

- **`.streamlit/config.toml`**: Streamlit configuration
  - Theme colors (green-based palette)
  - Light mode enforcement
  - Server settings

## Features

### 1. Quick Actions Bar
Located at the top of the app for rapid access to common tasks:
- **Snapshot**: Save current analysis state
- **Export**: Export props to CSV
- **Shortcuts**: View keyboard shortcuts
- **Start Guide**: Quick start tutorial

### 2. Data Fetch Controls
- Week and season selection
- Odds API integration
- Bankroll management
- Risk mode configuration

### 3. Slip Generation
- Number of slips control
- Minimum edge threshold
- Parlay leg constraints
- Confidence interval filtering
- Correlation diversity targeting

### 4. Analysis Results (Tabbed Interface)
- **Trend Chips**: AI-generated insights
- **Props Grid**: Individual prop analysis with search/filter
- **Slips & Builder**: Optimized parlays + manual slip builder
- **Correlations**: Heatmap visualization
- **Backtest**: Historical strategy performance

### 5. Calibration Banner
Real-time model calibration monitoring with ECE and Brier scores.

## Key User Flows

### Generate Optimized Slips
1. Set week/season in Data Fetch Controls
2. Configure bankroll and risk mode
3. Adjust slip generation parameters
4. Click main generate button
5. Review results in Analysis Results tabs

### Manual Slip Building
1. Navigate to "Slips & Builder" tab
2. Use "Manual Slip Construction" expander
3. Add props from Props Grid (via + buttons)
4. Review metrics and save

### Export Analysis
1. Generate props/slips
2. Click "Export" in Quick Actions
3. Find CSV in `./exports/` directory

## Styling & Theme

### Color Palette
- **Primary Green**: `#008057`
- **Background**: `#d9d8df` (light grey)
- **Secondary Background**: `#fafafa` (white)
- **Text**: `#484554` (dark grey)

### Custom CSS Features
- Transparent slider backgrounds
- Green-themed controls (no red)
- Hover effects with transitions
- Consistent spacing and borders
- Quick Actions bar with green borders

See `STYLING.md` for detailed customization guide.

## Session State Variables

Key variables managed in `st.session_state`:

- `props_df`: Current props DataFrame
- `slips`: Generated optimized slips
- `config`: User configuration
- `corr_matrix`: Correlation matrix
- `calibration_history`: Model calibration metrics
- `manual_slip`: Manually built slip legs
- `search_query`: Props search text
- `favorited_props`: Set of favorited prop IDs

## Performance Considerations

- **Caching**: Uses `@st.cache_data` for expensive operations
- **Lazy Loading**: Tabs load content only when selected
- **Efficient Filtering**: In-memory DataFrame operations
- **Background Processing**: Streamlit's native async handling

## Recent Changes

See `CHANGELOG.md` for Phase 1 UX enhancements including:
- Quick Actions bar implementation
- Search & filter functionality
- Icon removal and styling updates
- Slider color fixes
- Light mode enforcement

## Troubleshooting

### App Not Loading
```bash
# Check if port 8501 is in use
lsof -ti:8501 | xargs kill -9

# Clear cache
rm -rf ~/.streamlit/cache

# Restart
streamlit run app/main.py
```

### CSS Not Updating
- Hard refresh browser: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+F5` (Windows)
- Check browser console for errors
- Clear browser cache for localhost

### Missing Environment Variables
```bash
# Verify API key is set
echo $ODDS_API_KEY

# Or check .env file
cat .env
```

## Development

### Adding New Features

1. **New Tab**: Add to `st.tabs()` list in main()
2. **New Control**: Add to appropriate expander section
3. **New CSS**: Add to `apply_theme_css()` function
4. **New Session State**: Initialize in `initialize_session_state()`

### Code Style
- Functions use docstrings
- Session state accessed via `st.session_state`
- CSS uses CSS variables for consistency
- Comments explain complex logic

## Deployment

### Local Development
```bash
streamlit run app/main.py
```

### Production (Streamlit Cloud)
1. Push to GitHub repository
2. Connect repository in Streamlit Cloud
3. Set `ODDS_API_KEY` in Secrets
4. Deploy from `app/main.py`

### Docker (Future)
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /app
WORKDIR /app
CMD ["streamlit", "run", "app/main.py"]
```

## Related Documentation

- **Project Root**: `../README.md` - Project overview
- **Features**: `../docs/FEATURES.md` - Detailed feature documentation
- **ML Models**: `../docs/ML_MODELS.md` - Model architecture
- **API Setup**: `../ODDS_API_SETUP.md` - Odds API configuration
- **Styling Guide**: `./STYLING.md` - CSS customization

## Support

For issues or questions:
1. Check logs in terminal where Streamlit is running
2. Review browser console for frontend errors
3. Verify environment variables are set
4. Check `../DELIVERY_SUMMARY.md` for implementation details

## License

See project root for license information.
