# BetterBros Props - Development Tracker

> **Ongoing tracking of features, enhancements, bugs, and roadmap**

Last Updated: 2025-10-14

---

## 📊 Current Status

**Version**: 1.0.0
**Status**: Production Ready
**Sports Supported**: NFL, NBA, MLB (Full support)

---

## ✅ Completed Features

<details>
<summary><strong>Click to expand: Recently Completed (Oct 2025)</strong></summary>

### Multi-Sport Integration (Oct 13-14, 2025)
- ✅ Sport configuration system (`src/ingest/sport_config.py`)
- ✅ The Odds API multi-sport support
- ✅ SportsGameOdds API integration
- ✅ NFL mock data generator (100 props)
- ✅ NBA mock data generator (75 props, 15 players)
- ✅ MLB mock data generator (55 props, 15 players)
- ✅ Sport-aware feature engineering
- ✅ Position handling for all sports
- ✅ Weather impact logic (NFL/MLB/NBA specific)
- ✅ Sport-specific usage guides

### Core Infrastructure (Oct 11-12, 2025)
- ✅ Streamlit UI with multi-tab interface
- ✅ Gradient boosting model (XGBoost/LightGBM)
- ✅ Bayesian hierarchical model
- ✅ Copula correlation analysis
- ✅ Kelly criterion optimization
- ✅ Backtesting engine
- ✅ Snapshot management
- ✅ Export system (CSV)
- ✅ API key management
- ✅ User preferences system

</details>

---

## 🚧 In Progress

<details>
<summary><strong>Click to expand: Currently Being Developed</strong></summary>

### Nothing Currently In Progress
All planned Phase 1 features are complete.

*Update this section when new work begins*

</details>

---

## 📋 Backlog (Prioritized)

<details>
<summary><strong>Click to expand: High Priority (Next Sprint)</strong></summary>

### Real-Time Data Integration

#### 1. NBA Injury Data Sources
**Priority**: High
**Effort**: Medium
**Description**: Integrate real-time NBA injury APIs
**Current State**: Using generic mock injuries
**Target APIs**:
- NBA Official Injury Report API
- Sports Reference API
- RotoWire API

**Acceptance Criteria**:
- Real-time injury status (Out, Doubtful, Questionable, Probable)
- Update frequency: Every 30 minutes
- Integration with feature pipeline

---

#### 2. MLB Injury Data Sources
**Priority**: High
**Effort**: Medium
**Description**: Integrate real-time MLB injury APIs
**Current State**: Using generic mock injuries
**Target APIs**:
- MLB Official Injury Report
- Sports Reference
- RotoWire

**Acceptance Criteria**:
- Real-time injury status
- Pitcher availability tracking
- Lineup change detection

---

#### 3. Enhanced Weather Provider
**Priority**: Medium
**Effort**: Low
**Description**: Integrate live weather APIs for MLB ballparks
**Current State**: Sport-aware mock weather implemented
**Target APIs**:
- OpenWeather API
- Weather Underground
- National Weather Service

**Acceptance Criteria**:
- Real-time weather for MLB ballparks
- Wind direction and speed
- Temperature and humidity
- Precipitation probability

</details>

<details>
<summary><strong>Click to expand: Medium Priority</strong></summary>

### Live Odds Tracking

#### 4. Real-Time Odds Updates
**Priority**: Medium
**Effort**: High
**Description**: Track odds changes in real-time
**Benefits**:
- Identify line movement
- Detect sharp action
- Alert on value opportunities

**Technical Approach**:
- WebSocket connection to odds provider
- Store odds history in database
- Calculate line movement velocity

---

#### 5. Line Movement Alerts
**Priority**: Medium
**Effort**: Low
**Description**: Notify when lines move significantly
**Features**:
- Configurable threshold (e.g., 5 points)
- Email/push notifications
- Historical movement visualization

---

### Mobile Optimization

#### 6. Responsive UI Redesign
**Priority**: Medium
**Effort**: High
**Description**: Make Streamlit app mobile-friendly
**Current Issue**: Desktop-only layout
**Target**:
- Mobile-first design
- Touch-optimized controls
- Simplified navigation

---

### Advanced Analytics

#### 7. Vine Copulas
**Priority**: Low
**Effort**: High
**Description**: Implement vine copulas for complex dependencies
**Benefits**:
- More accurate correlation modeling
- Better capture tail dependencies
- Improved slip diversification

**Technical**: Use `pyvinecopulib` library

---

#### 8. Model Ensemble Weights
**Priority**: Low
**Effort**: Medium
**Description**: Dynamic weighting of GBM vs Bayesian
**Current**: Fixed 60/40 split
**Target**: Adaptive weights based on recent performance

</details>

<details>
<summary><strong>Click to expand: Low Priority (Future)</strong></summary>

### Community Features

#### 9. Community Sharing Platform
**Priority**: Low
**Effort**: Very High
**Description**: Platform for users to share analyses
**Features**:
- Public/private sharing
- Leaderboards
- Follow successful analysts
- Discussion threads

---

#### 10. Push Notifications
**Priority**: Low
**Effort**: Medium
**Description**: Mobile push notifications
**Triggers**:
- High-value props detected
- Line movements
- Injury news
- Model drift alerts

</details>

---

## 🐛 Known Issues

<details>
<summary><strong>Click to expand: Bugs & Issues</strong></summary>

### High Priority Bugs
*None currently identified*

### Medium Priority Bugs
*None currently identified*

### Low Priority Issues

#### 1. Streamlit Caching Warnings
**Impact**: Low (cosmetic)
**Description**: Occasional cache warnings in Streamlit console
**Workaround**: Refresh page
**Fix**: Update cache decorators

---

#### 2. Large Parquet Files
**Impact**: Low (disk space)
**Description**: Cache files grow over time
**Workaround**: Manual cleanup
**Fix**: Implement auto-cleanup after 7 days

</details>

---

## 💡 Feature Requests

<details>
<summary><strong>Click to expand: User-Requested Features</strong></summary>

*Add feature requests from users here*

### Template
**Feature**: [Name]
**Requested By**: [User/Source]
**Date**: [YYYY-MM-DD]
**Priority**: [High/Medium/Low]
**Description**: [What they want]
**Rationale**: [Why it's valuable]
**Status**: [Under Review / Accepted / Declined / Implemented]

</details>

---

## 🔬 Experiments & A/B Tests

<details>
<summary><strong>Click to expand: Ongoing Experiments</strong></summary>

*Track experimental features and their outcomes*

### Template
**Experiment**: [Name]
**Started**: [YYYY-MM-DD]
**Duration**: [X weeks]
**Hypothesis**: [What we're testing]
**Metrics**: [What we're measuring]
**Results**: [Outcome]
**Decision**: [Keep / Discard / Modify]

</details>

---

## 📈 Performance Metrics

<details>
<summary><strong>Click to expand: System Performance Tracking</strong></summary>

### Current Benchmarks (as of Oct 14, 2025)

**Model Performance**:
- GBM Training Time: ~2 minutes (on 1000 props)
- Bayesian Inference: ~5 minutes (1000 props)
- Prediction Time: <1 second (100 props)

**API Performance**:
- The Odds API Response Time: ~500ms
- Props Fetch (Full Week): ~10 seconds

**UI Performance**:
- App Load Time: ~3 seconds
- Props Table Render: ~500ms (100 rows)
- Correlation Heatmap: ~2 seconds

**Target Improvements**:
- [ ] Reduce Bayesian inference to <3 minutes
- [ ] Cache API responses for 15 minutes
- [ ] Optimize correlation calculations

</details>

---

## 🎯 Roadmap

<details>
<summary><strong>Click to expand: Long-Term Vision</strong></summary>

### Phase 1: Foundation (COMPLETE ✅)
- Multi-sport support (NFL, NBA, MLB)
- Core ML models (GBM + Bayesian)
- Correlation analysis
- Kelly optimization
- Streamlit UI
- Mock data for all sports

### Phase 2: Real-Time Data (Q4 2025)
- Live injury data (NBA, MLB)
- Enhanced weather integration
- Real-time odds tracking
- Line movement alerts

### Phase 3: Advanced Analytics (Q1 2026)
- Vine copulas
- Dynamic model ensembles
- Advanced backtesting
- Strategy comparison tools

### Phase 4: Mobile & Community (Q2 2026)
- Mobile-optimized UI
- Push notifications
- Community sharing platform
- Leaderboards

### Phase 5: Enterprise Features (Q3 2026)
- Multi-user support
- Team collaboration
- Advanced permissions
- API access for third-party integrations

</details>

---

## 📝 Development Notes

<details>
<summary><strong>Click to expand: Technical Debt & Refactoring</strong></summary>

### Code Quality Issues

#### Moderate Technical Debt
1. **Streamlit State Management**: Some components use session_state inconsistently
   - **Impact**: Medium
   - **Effort to Fix**: Low
   - **Priority**: Medium

2. **Test Coverage**: Core modules well-tested, but some edge cases missing
   - **Current Coverage**: ~75%
   - **Target**: 85%+
   - **Priority**: Medium

3. **Type Hints**: Not all functions have complete type annotations
   - **Impact**: Low (IDE hints)
   - **Priority**: Low

### Refactoring Candidates

1. **Feature Pipeline**: Could be split into smaller, more modular functions
2. **Optimization Logic**: Extract constraints into separate validator class
3. **API Clients**: Share more common code between OddsAPI and SportsGameOdds

</details>

---

## 🔄 Change Log

<details>
<summary><strong>Click to expand: Recent Changes</strong></summary>

### Version 1.0.0 (Oct 14, 2025)
- ✅ Multi-sport support (NFL, NBA, MLB)
- ✅ Mock data generators for all sports
- ✅ Sport-aware feature engineering
- ✅ Comprehensive documentation
- ✅ Production-ready cleanup

### Version 0.9.0 (Oct 13, 2025)
- ✅ SportsGameOdds API integration
- ✅ Sport configuration system
- ✅ Multi-sport UI selector

### Version 0.8.0 (Oct 12, 2025)
- ✅ Streamlit UI redesign
- ✅ Correlation inspector
- ✅ What-if sandbox
- ✅ Calibration monitor

### Version 0.7.0 (Oct 11, 2025)
- ✅ Initial release
- ✅ NFL support only
- ✅ Core ML models
- ✅ Basic UI

</details>

---

## 🎓 Learning & Resources

<details>
<summary><strong>Click to expand: Useful References</strong></summary>

### Documentation
- **Main README**: `README.md`
- **Master Guide**: `MASTER_GUIDE.md`
- **NFL Guide**: `docs/GUIDE_NFL.md`
- **NBA Guide**: `docs/GUIDE_NBA.md`
- **MLB Guide**: `docs/GUIDE_MLB.md`
- **API Docs**: `docs/api/README.md`

### External Resources
- **The Odds API Docs**: https://the-odds-api.com/docs
- **Kelly Criterion**: https://en.wikipedia.org/wiki/Kelly_criterion
- **Copulas**: https://en.wikipedia.org/wiki/Copula_(probability_theory)
- **XGBoost Docs**: https://xgboost.readthedocs.io/

### Academic Papers
- "Kelly Criterion for Multi-Asset Portfolios" (MacLean et al.)
- "Copula-Based Correlation Models" (Embrechts et al.)
- "Bayesian Hierarchical Models for Sports Analytics" (Various)

</details>

---

## 📞 Contact & Contributions

### Reporting Issues
- Create detailed bug reports with:
  - Steps to reproduce
  - Expected vs actual behavior
  - System info (OS, Python version)
  - Relevant logs

### Feature Suggestions
- Describe the use case
- Explain why it's valuable
- Suggest implementation approach (if technical)

### Code Contributions
- Follow existing code style
- Add tests for new features
- Update documentation
- Create PR with clear description

---

**End of Development Tracker**

*Keep this document updated as development progresses*
