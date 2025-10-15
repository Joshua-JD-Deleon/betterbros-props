/**
 * Type definitions for BetterBros Props mobile app
 * Matches API types from backend
 */

export type Sport = 'nba' | 'nfl' | 'mlb' | 'nhl';
export type PropType = 'over_under' | 'goal_scorer' | 'combo';
export type BetDirection = 'over' | 'under' | 'yes' | 'no';
export type Platform = 'prizepicks' | 'underdog';
export type ModelType = 'xgboost' | 'lightgbm' | 'neural_net' | 'ensemble';

export interface PropLeg {
  id: string;
  player_id: string;
  player_name: string;
  stat_type: string;
  line: number;
  direction: BetDirection;
  odds?: number;
  team: string;
  opponent: string;
  game_id: string;
  position?: string;
}

export interface PropMarket {
  id: string;
  platform: Platform;
  sport: Sport;
  prop_type: PropType;
  legs: PropLeg[];
  payout_multiplier: number;
  created_at: string;
  start_time: string;
  expires_at?: string;
  is_active: boolean;
  min_legs: number;
  max_legs: number;
}

export interface DistributionStats {
  mean: number;
  median: number;
  std_dev: number;
  percentile_25: number;
  percentile_75: number;
  percentile_90: number;
  min_value: number;
  max_value: number;
}

export interface ModelPrediction {
  prop_leg_id: string;
  player_id: string;
  stat_type: string;
  predicted_value: number;
  line_value: number;
  prob_over: number;
  prob_under: number;
  confidence: number;
  edge: number;
  kelly_fraction?: number;
  distribution?: DistributionStats;
  model_type: ModelType;
  model_version: string;
  feature_importance?: Record<string, number>;
  predicted_at: string;
}

export interface SlipDriver {
  type: 'market_inefficiency' | 'model_edge' | 'correlation_play' | 'injury_impact' | 'line_movement';
  description: string;
  impact_score: number;
}

export interface SlipCandidate {
  prop_leg_id: string;
  player_name: string;
  stat_type: string;
  line: number;
  direction: BetDirection;
  edge: number;
  confidence: number;
  expected_value: number;
  drivers: SlipDriver[];
  primary_driver: string;
  risk_score: number;
  volatility: number;
  detected_at: string;
}

export interface ParlayCandidate {
  prop_leg_ids: string[];
  legs: PropLeg[];
  predictions: ModelPrediction[];
  expected_value: number;
  total_edge: number;
  win_probability: number;
  combined_confidence: number;
  kelly_stake?: number;
  max_correlation: number;
  diversification_score: number;
  rank: number;
  score: number;
}

export interface OptimizationConstraints {
  min_legs: number;
  max_legs: number;
  min_edge: number;
  min_confidence: number;
  max_correlation: number;
  max_player_exposure: number;
  max_team_exposure: number;
  max_game_exposure: number;
  require_diverse_stats: boolean;
  require_diverse_games: boolean;
}

export interface CorrelationPair {
  leg_id_1: string;
  leg_id_2: string;
  player_1: string;
  player_2: string;
  stat_type_1: string;
  stat_type_2: string;
  correlation: number;
  sample_size: number;
  p_value?: number;
  is_significant: boolean;
}

export interface Snapshot {
  id: string;
  name: string;
  description?: string;
  prop_markets: string[];
  predictions: string[];
  correlations?: string;
  sport: Sport;
  created_by: string;
  created_at: string;
  game_date?: string;
  is_locked: boolean;
  tags: string[];
}

export interface CalibrationMetrics {
  brier_score: number;
  log_loss: number;
  calibration_curve: Array<{
    predicted_prob: number;
    actual_prob: number;
    count: number;
  }>;
  confidence_buckets: Array<{
    bucket: string;
    win_rate: number;
    expected_rate: number;
    count: number;
  }>;
}

export interface TrendData {
  date: string;
  value: number;
  label?: string;
}

// Offline sync types
export interface OfflineSnapshot {
  snapshot_id: string;
  data: {
    props: PropMarket[];
    predictions: Record<string, ModelPrediction>;
    slips: SlipCandidate[];
    topSets: ParlayCandidate[];
  };
  timestamp: number;
  sport?: Sport;
}

export interface SyncStatus {
  lastSyncTime?: number;
  lastSnapshotId?: string;
  isOnline: boolean;
  isSyncing: boolean;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  error?: string;
  status: number;
}

export interface PropMarketsResponse {
  markets: PropMarket[];
  total: number;
  page: number;
  page_size: number;
}

export interface OptimizationResponse {
  candidates: ParlayCandidate[];
  total_evaluated: number;
  computation_time_ms: number;
}

export interface SlipDetectionResponse {
  slips: SlipCandidate[];
  total_evaluated: number;
}
