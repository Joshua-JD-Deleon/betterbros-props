# BetterBros Props API - Endpoint Reference

Complete reference for all API endpoints in the BetterBros Props API.

## Base URL

- Development: `http://localhost:8000`
- Production: `https://api.betterbros.com` (TBD)

## Authentication

All endpoints except `/health` and `/` require authentication via JWT Bearer token:

```
Authorization: Bearer <jwt_token>
```

### Subscription Tiers

- **Free**: Basic access to props and predictions
- **Pro**: Access to optimization, backtesting, what-if analysis
- **Enterprise**: Access to experiments, advanced analytics

---

## Core Endpoints

### Root

#### `GET /`
Get API information and version.

**Response:**
```json
{
  "service": "BetterBros Props API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

#### `GET /health`
Health check endpoint with dependency status.

**Response:**
```json
{
  "status": "healthy",
  "service": "betterbros-props-api",
  "version": "1.0.0",
  "environment": "development",
  "dependencies": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

---

## Authentication (`/auth`)

### `GET /auth/me`
Get current user profile.

**Auth Required:** Yes

**Response:** `UserProfile`
```json
{
  "user_id": "user_123",
  "email": "user@example.com",
  "name": "John Doe",
  "subscription_tier": "pro",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### `PUT /auth/me`
Update user profile.

**Auth Required:** Yes

**Request Body:**
```json
{
  "name": "Updated Name"
}
```

### `GET /auth/subscription`
Get subscription status.

**Auth Required:** Yes

**Response:**
```json
{
  "user_id": "user_123",
  "subscription_tier": "pro",
  "is_active": true
}
```

### `POST /auth/subscription/upgrade`
Initiate subscription upgrade.

**Auth Required:** Yes

**Request Body:**
```json
{
  "target_tier": "enterprise"
}
```

---

## Props Markets (`/props`)

### `GET /props`
List available prop markets with filtering.

**Auth Required:** Yes

**Query Parameters:**
- `sport` (optional): Sport type (nba, nfl, mlb, nhl)
- `platform` (optional): Platform (prizepicks, underdog)
- `is_active` (default: true): Filter active markets
- `start_time_after` (optional): Filter by start time
- `page` (default: 1): Page number
- `page_size` (default: 50, max: 100): Items per page

**Response:** `PropMarketResponse`
```json
{
  "markets": [
    {
      "id": "market_123",
      "platform": "prizepicks",
      "sport": "nba",
      "prop_type": "over_under",
      "legs": [...],
      "payout_multiplier": 3.0,
      "created_at": "2024-01-01T00:00:00Z",
      "start_time": "2024-01-01T19:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 50
}
```

### `GET /props/{market_id}`
Get specific prop market.

**Auth Required:** Yes

**Response:** `PropMarket`

### `POST /props/import`
Import prop markets from external platforms.

**Auth Required:** Yes

**Request Body:** `PropMarketCreate`
```json
{
  "platform": "prizepicks",
  "sport": "nba",
  "markets": [...]
}
```

### `POST /props/refresh`
Trigger refresh of prop markets from external API.

**Auth Required:** Yes

**Request Body:**
```json
{
  "platform": "prizepicks",
  "sport": "nba"
}
```

**Response:**
```json
{
  "status": "success",
  "platform": "prizepicks",
  "sport": "nba",
  "updated_count": 45
}
```

### `DELETE /props/{market_id}`
Soft delete a prop market.

**Auth Required:** Yes

**Response:** 204 No Content

---

## Context Data (`/context`)

### `POST /context`
Fetch contextual data for specified games.

**Auth Required:** Yes

**Request Body:** `ContextDataRequest`
```json
{
  "game_ids": ["game_1", "game_2"],
  "sport": "nba",
  "include_injuries": true,
  "include_weather": true,
  "include_team_stats": true
}
```

**Response:** `List[ContextData]`

### `GET /context/injuries/{sport}`
Get current injury reports.

**Auth Required:** Yes

**Query Parameters:**
- `team_id` (optional): Filter by team

**Response:** List of injury reports

### `GET /context/weather/{game_id}`
Get weather data for a specific game.

**Auth Required:** Yes

**Response:**
```json
{
  "game_id": "game_123",
  "weather": {
    "temperature": 72,
    "wind_speed": 5,
    "conditions": "Clear"
  }
}
```

### `GET /context/team-stats/{team_id}`
Get comprehensive team statistics.

**Auth Required:** Yes

**Query Parameters:**
- `season` (optional): Filter by season

### `GET /context/matchup/{game_id}`
Get comprehensive matchup context.

**Auth Required:** Yes

---

## Features (`/features`)

### `POST /features/compute`
Compute feature sets for specified prop legs.

**Auth Required:** Yes

**Request Body:** `FeatureSetRequest`
```json
{
  "prop_leg_ids": ["leg_1", "leg_2"],
  "include_historical": true,
  "lookback_days": 30
}
```

**Response:** `FeatureSetResponse`

### `GET /features/{prop_leg_id}`
Get cached or compute feature set for a prop leg.

**Auth Required:** Yes

**Response:** `FeatureSet`

### `POST /features/batch`
Batch compute features for multiple prop legs.

**Auth Required:** Yes

**Request Body:**
```json
{
  "prop_leg_ids": ["leg_1", "leg_2"],
  "force_recompute": false
}
```

### `GET /features/player/{player_id}/historical`
Get historical feature trends for a player.

**Auth Required:** Yes

**Query Parameters:**
- `stat_type`: Stat type
- `lookback_days` (default: 30): Days to look back

### `POST /features/invalidate-cache`
Invalidate feature cache.

**Auth Required:** Yes

**Request Body:**
```json
{
  "prop_leg_ids": ["leg_1", "leg_2"]  // or null for all
}
```

---

## Model Predictions (`/model`)

### `POST /model/predict`
Generate predictions for specified prop legs.

**Auth Required:** Yes

**Request Body:** `ModelPredictionRequest`
```json
{
  "prop_leg_ids": ["leg_1", "leg_2"],
  "model_type": "xgboost",
  "use_ensemble": true
}
```

**Response:** `ModelPredictionResponse`

### `GET /model/{prop_leg_id}`
Get cached prediction or generate new one.

**Auth Required:** Yes

**Query Parameters:**
- `model_type` (optional): Model type to use

**Response:** `ModelPrediction`

### `POST /model/batch`
Batch generate predictions.

**Auth Required:** Yes

**Request Body:**
```json
{
  "prop_leg_ids": ["leg_1", "leg_2"],
  "model_type": "xgboost",
  "use_ensemble": true
}
```

### `GET /model/models/available`
List all available model versions.

**Auth Required:** Yes

**Response:**
```json
{
  "models": [
    {
      "model_type": "xgboost",
      "version": "v1.0.0",
      "metrics": {...}
    }
  ],
  "default_model": "xgboost-v1.0.0"
}
```

### `GET /model/models/{model_type}/info`
Get detailed model information.

**Auth Required:** Yes

**Query Parameters:**
- `version` (optional): Model version

### `POST /model/calibrate`
Calibrate predictions based on historical accuracy.

**Auth Required:** Yes

### `POST /model/explain/{prop_leg_id}`
Generate prediction explanation (SHAP values).

**Auth Required:** Yes

---

## Correlations (`/correlations`)

### `POST /correlations`
Compute correlation matrix for specified prop legs.

**Auth Required:** Yes

**Request Body:** `CorrelationRequest`
```json
{
  "prop_leg_ids": ["leg_1", "leg_2", "leg_3"],
  "lookback_days": 30,
  "min_sample_size": 10
}
```

**Response:** `CorrelationMatrix`

### `GET /correlations/{prop_leg_id}/related`
Find props with highest correlation.

**Auth Required:** Yes

**Query Parameters:**
- `min_correlation` (default: 0.3): Minimum correlation
- `max_results` (default: 10): Maximum results

### `POST /correlations/matrix`
Get full correlation matrix.

**Auth Required:** Yes

### `GET /correlations/player/{player_id}/stats`
Get correlations between player's stat types.

**Auth Required:** Yes

**Query Parameters:**
- `lookback_days` (default: 30)

### `POST /correlations/team/{team_id}/player-correlations`
Get correlations between team players.

**Auth Required:** Yes

### `DELETE /correlations/cache`
Clear correlation cache.

**Auth Required:** Yes

---

## Optimization (`/optimize`)

### `POST /optimize/parlays`
Optimize parlay combinations.

**Auth Required:** Pro Tier

**Request Body:** `OptimizationRequest`
```json
{
  "prop_leg_ids": ["leg_1", "leg_2", "leg_3"],
  "constraints": {
    "min_legs": 2,
    "max_legs": 5,
    "min_edge": 0.05,
    "min_confidence": 0.6,
    "max_correlation": 0.3
  },
  "top_k": 10,
  "algorithm": "greedy"
}
```

**Response:** `OptimizationResponse`

### `POST /optimize/slips`
Detect high-edge slip opportunities.

**Auth Required:** Yes

**Request Body:** `SlipDetectionRequest`
```json
{
  "min_edge": 0.1,
  "min_confidence": 0.65,
  "max_risk": 0.5,
  "top_k": 20
}
```

**Response:** `SlipDetectionResponse`

### `POST /optimize/validate-parlay`
Validate user-selected parlay.

**Auth Required:** Yes

**Request Body:**
```json
{
  "prop_leg_ids": ["leg_1", "leg_2"]
}
```

**Response:**
```json
{
  "is_valid": true,
  "warnings": [],
  "metrics": {
    "expected_value": 1.5,
    "max_correlation": 0.25
  }
}
```

### `POST /optimize/simulate`
Run Monte Carlo simulation for parlay.

**Auth Required:** Pro Tier

**Request Body:**
```json
{
  "prop_leg_ids": ["leg_1", "leg_2"],
  "num_simulations": 10000
}
```

### `GET /optimize/strategies`
List available optimization strategies.

**Auth Required:** Yes

### `POST /optimize/auto-build`
Automatically build optimal parlays.

**Auth Required:** Pro Tier

**Query Parameters:**
- `sport` (optional)
- `target_payout` (optional)
- `max_risk` (default: 0.5)

---

## Evaluation (`/eval`)

### `POST /eval/backtest`
Run backtest with specified configuration.

**Auth Required:** Pro Tier

**Request Body:** `BacktestRequest`
```json
{
  "config": {
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-03-01T00:00:00Z",
    "strategy": "threshold",
    "min_edge": 0.1,
    "simulated_bankroll": 10000,
    "stake_method": "kelly_fraction"
  }
}
```

**Response:** `BacktestResult`

### `GET /eval/backtest/{backtest_id}`
Retrieve saved backtest result.

**Auth Required:** Yes

**Response:** `BacktestResult`

### `GET /eval/backtests`
List all backtests for current user.

**Auth Required:** Yes

### `POST /eval/quick-backtest`
Run quick backtest with simplified parameters.

**Auth Required:** Yes

### `POST /eval/calibration`
Evaluate model calibration over date range.

**Auth Required:** Pro Tier

**Request Body:**
```json
{
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-03-01T00:00:00Z",
  "model_version": "v1.0.0"
}
```

### `POST /eval/performance-by-segment`
Analyze performance broken down by segments.

**Auth Required:** Pro Tier

**Query Parameters:**
- `segment_by`: Segment type (sport, stat_type, player, team)

### `GET /eval/live-tracking`
Get live performance tracking for today's bets.

**Auth Required:** Yes

---

## Export (`/export`)

### `POST /export`
Export data in specified format.

**Auth Required:** Yes

**Request Body:** `ExportRequest`
```json
{
  "snapshot_id": "snap_123",
  "include_predictions": true,
  "include_features": false,
  "format": "json"
}
```

**Response:** `ExportResponse`

### `GET /export/snapshot/{snapshot_id}`
Export a complete snapshot.

**Auth Required:** Yes

**Query Parameters:**
- `format` (default: json): Export format

### `GET /export/predictions/csv`
Export predictions as CSV.

**Auth Required:** Yes

**Query Parameters:**
- `prop_leg_ids` (optional): Comma-separated IDs

### `GET /export/parlays/excel`
Export optimized parlays as Excel.

**Auth Required:** Yes

**Query Parameters:**
- `date` (optional): Date filter

### `POST /export/backtest-results`
Export backtest results.

**Auth Required:** Yes

### `GET /export/daily-report/{date}`
Export comprehensive daily report.

**Auth Required:** Yes

---

## Snapshots (`/snapshots`)

### `GET /snapshots`
List snapshots with filtering.

**Auth Required:** Yes

**Query Parameters:**
- `sport` (optional)
- `tag` (optional)
- `page` (default: 1)
- `page_size` (default: 50)

**Response:** `SnapshotResponse`

### `GET /snapshots/{snapshot_id}`
Get detailed snapshot information.

**Auth Required:** Yes

**Response:** `Snapshot`

### `POST /snapshots`
Create a new snapshot.

**Auth Required:** Yes

**Request Body:** `SnapshotCreate`
```json
{
  "name": "Pre-game analysis",
  "description": "Props for tonight's games",
  "sport": "nba",
  "game_date": "2024-01-15T00:00:00Z",
  "prop_leg_ids": ["leg_1", "leg_2"],
  "tags": ["nba", "tuesday"]
}
```

**Response:** `Snapshot`

### `PUT /snapshots/{snapshot_id}`
Update snapshot metadata.

**Auth Required:** Yes

### `DELETE /snapshots/{snapshot_id}`
Delete a snapshot.

**Auth Required:** Yes

### `POST /snapshots/{snapshot_id}/lock`
Lock snapshot to prevent modifications.

**Auth Required:** Yes

### `POST /snapshots/{snapshot_id}/compare/{other_snapshot_id}`
Compare two snapshots.

**Auth Required:** Yes

### `GET /snapshots/{snapshot_id}/outcomes`
Get actual outcomes for snapshot props.

**Auth Required:** Yes

---

## Experiments (`/experiments`)

### `GET /experiments`
List experiments.

**Auth Required:** Yes

**Query Parameters:**
- `status` (optional): Filter by status
- `page`, `page_size`: Pagination

**Response:** `ExperimentResponse`

### `GET /experiments/{experiment_id}`
Get experiment details.

**Auth Required:** Yes

**Response:** `Experiment`

### `POST /experiments`
Create a new experiment.

**Auth Required:** Enterprise Tier

**Request Body:** `ExperimentCreate`

### `POST /experiments/{experiment_id}/start`
Start running an experiment.

**Auth Required:** Enterprise Tier

### `POST /experiments/{experiment_id}/stop`
Stop a running experiment.

**Auth Required:** Enterprise Tier

### `GET /experiments/{experiment_id}/metrics`
Get real-time experiment metrics.

**Auth Required:** Yes

### `POST /experiments/{experiment_id}/promote`
Promote experiment model to production.

**Auth Required:** Enterprise Tier

### `POST /experiments/compare`
Compare multiple experiments.

**Auth Required:** Yes

**Request Body:**
```json
{
  "experiment_ids": ["exp_1", "exp_2"]
}
```

### `DELETE /experiments/{experiment_id}`
Delete an experiment.

**Auth Required:** Enterprise Tier

---

## API Keys (`/keys`)

### `GET /keys`
List user's API keys.

**Auth Required:** Yes

**Query Parameters:**
- `source` (optional): Filter by source

**Response:** `ApiKeyResponse`

### `GET /keys/{key_id}`
Get API key details.

**Auth Required:** Yes

**Response:** `ApiKey`

### `POST /keys`
Create or update an API key.

**Auth Required:** Yes

**Request Body:** `ApiKeyCreate`
```json
{
  "source": "prizepicks",
  "name": "My PrizePicks Key",
  "key": "pk_live_..."
}
```

### `PUT /keys/{key_id}`
Update API key metadata.

**Auth Required:** Yes

### `DELETE /keys/{key_id}`
Delete an API key.

**Auth Required:** Yes

### `POST /keys/{key_id}/validate`
Validate an API key.

**Auth Required:** Yes

### `GET /keys/{key_id}/usage`
Get usage statistics for an API key.

**Auth Required:** Yes

---

## What-If Analysis (`/whatif`)

### `POST /whatif`
Run what-if analysis for scenarios.

**Auth Required:** Pro Tier

**Request Body:** `WhatIfRequest`
```json
{
  "prop_leg_id": "leg_123",
  "scenarios": [
    {
      "player_id": "player_456",
      "stat_type": "points",
      "injury_status": "questionable",
      "usage_rate_adjustment": 0.05
    }
  ]
}
```

**Response:** `WhatIfResponse`

### `POST /whatif/injury-impact`
Analyze impact of player injury.

**Auth Required:** Pro Tier

**Request Body:**
```json
{
  "prop_leg_id": "leg_123",
  "injured_player_id": "player_456"
}
```

### `POST /whatif/lineup-change`
Analyze impact of lineup changes.

**Auth Required:** Pro Tier

**Request Body:**
```json
{
  "game_id": "game_789",
  "lineup_changes": [...]
}
```

### `POST /whatif/usage-sensitivity`
Analyze sensitivity to usage rate changes.

**Auth Required:** Pro Tier

**Query Parameters:**
- `usage_range`: Tuple of min/max adjustment
- `num_steps` (default: 10): Number of steps

### `POST /whatif/matchup-difficulty`
Analyze matchup difficulty impact.

**Auth Required:** Pro Tier

### `POST /whatif/pace-impact`
Analyze game pace impact.

**Auth Required:** Pro Tier

### `POST /whatif/custom-scenario`
Run custom scenario with arbitrary adjustments.

**Auth Required:** Pro Tier

---

## Historical Data (`/history`)

### `POST /history/player`
Get historical performance for a player.

**Auth Required:** Yes

**Request Body:** `HistoricalRequest`

**Response:** `HistoricalResponse`

### `GET /history/player/{player_id}/games`
Get player game log.

**Auth Required:** Yes

**Query Parameters:**
- `sport`: Sport type
- `season` (optional)
- `start_date`, `end_date` (optional)

### `GET /history/player/{player_id}/splits`
Get player performance splits.

**Auth Required:** Yes

**Query Parameters:**
- `stat_type`: Stat type
- `split_by`: Split type (home_away, opponent, month, day_of_week)
- `lookback_days` (default: 90)

### `GET /history/team/{team_id}/stats`
Get historical team statistics.

**Auth Required:** Yes

**Query Parameters:**
- `sport`: Sport type
- `season` (optional)

### `GET /history/matchup/{team1_id}/{team2_id}/history`
Get head-to-head history.

**Auth Required:** Yes

**Query Parameters:**
- `sport`: Sport type
- `lookback_games` (default: 10, max: 50)

### `GET /history/player/{player_id}/trends`
Get player stat trends.

**Auth Required:** Yes

**Query Parameters:**
- `stat_type`: Stat type
- `window_size` (default: 5, min: 3, max: 20)

### `GET /history/player/{player_id}/streaks`
Get player streaks.

**Auth Required:** Yes

**Query Parameters:**
- `stat_type`: Stat type
- `threshold`: Threshold value

### `GET /history/league/{sport}/leaders`
Get league leaders for a stat.

**Auth Required:** Yes

**Query Parameters:**
- `stat_type`: Stat type
- `limit` (default: 10, max: 100)

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
Invalid request parameters or body.

```json
{
  "error": "Validation Error",
  "message": "Invalid request data",
  "detail": {...}
}
```

### 401 Unauthorized
Missing or invalid authentication token.

```json
{
  "error": "Unauthorized",
  "message": "Invalid authentication token"
}
```

### 403 Forbidden
Insufficient subscription tier or permissions.

```json
{
  "error": "Forbidden",
  "message": "This endpoint requires pro subscription"
}
```

### 404 Not Found
Resource not found.

```json
{
  "error": "Not Found",
  "message": "Resource not found"
}
```

### 429 Too Many Requests
Rate limit exceeded.

```json
{
  "error": "Rate Limit Exceeded",
  "message": "Too many requests. Please try again later."
}
```

### 500 Internal Server Error
Server error.

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred"
}
```

---

## Rate Limits

Default rate limits (configurable):
- **Free Tier**: 100 requests per minute
- **Pro Tier**: 500 requests per minute
- **Enterprise Tier**: 2000 requests per minute

Rate limit headers included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704067200
```

---

## Pagination

List endpoints support pagination with consistent parameters:

**Query Parameters:**
- `page` (default: 1): Page number
- `page_size` (default: 50, max: 100): Items per page

**Response Format:**
```json
{
  "items": [...],
  "total": 250,
  "page": 1,
  "page_size": 50
}
```

---

## Interactive Documentation

For interactive API documentation with try-it-out functionality:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
