"""
Feature Transformers for ML Pipeline

Handles feature normalization, encoding, interaction creation,
and missing value imputation for machine learning models.
"""
import logging
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder

logger = logging.getLogger(__name__)


class FeatureTransformer:
    """
    Transformer for feature engineering operations

    Handles:
    - Normalization/standardization of numeric features
    - Categorical encoding
    - Feature interaction creation
    - Missing value handling
    """

    def __init__(self):
        """Initialize feature transformer"""
        self.scalers: Dict[str, StandardScaler] = {}
        self.encoders: Dict[str, LabelEncoder] = {}
        self.feature_means: Dict[str, float] = {}
        self.feature_stds: Dict[str, float] = {}

        # Define feature types
        self.numeric_features = [
            'season_avg', 'last_3_avg', 'last_5_avg', 'last_10_avg',
            'median_value', 'std_dev', 'min_value', 'max_value',
            'games_played', 'home_away_split', 'usage_rate', 'target_share',
            'days_rest', 'career_avg_vs_opponent', 'opponent_defense_rank',
            'opponent_pace', 'opponent_strength', 'opponent_yards_allowed_per_game',
            'opponent_yards_per_game', 'temperature', 'wind_speed',
            'precipitation_prob', 'humidity', 'game_total', 'spread',
            'line_movement', 'implied_probability', 'odds', 'odds_value',
            'line', 'line_vs_baseline', 'ewma_trend', 'volatility',
            'ceiling_score', 'floor_score', 'pace_adjusted_avg',
            'rest_advantage', 'weather_impact', 'age', 'years_exp',
            'height', 'weight',
        ]

        self.categorical_features = [
            'position', 'injury_status', 'venue_type', 'stat_type',
        ]

        self.binary_features = [
            'is_home', 'primetime_game',
        ]

    def normalize_features(
        self,
        df: pd.DataFrame,
        fit: bool = True,
    ) -> pd.DataFrame:
        """
        Normalize numeric features using standardization (z-score)

        Args:
            df: Input DataFrame
            fit: Whether to fit scalers on this data (True for training)

        Returns:
            DataFrame with normalized features
        """
        logger.info("Normalizing numeric features...")

        df_norm = df.copy()

        # Get numeric columns that exist in the dataframe
        numeric_cols = [col for col in self.numeric_features if col in df.columns]

        for col in numeric_cols:
            if col not in df_norm.columns:
                continue

            # Skip columns with all NaN or single unique value
            if df_norm[col].isna().all() or df_norm[col].nunique() <= 1:
                logger.warning(f"Skipping normalization for {col} (all NaN or constant)")
                continue

            try:
                if fit:
                    # Fit and transform
                    mean_val = df_norm[col].mean()
                    std_val = df_norm[col].std()

                    # Store for later use
                    self.feature_means[col] = mean_val
                    self.feature_stds[col] = std_val

                    # Normalize (handle std=0 case)
                    if std_val > 1e-6:
                        df_norm[f'{col}_normalized'] = (df_norm[col] - mean_val) / std_val
                    else:
                        df_norm[f'{col}_normalized'] = 0.0
                else:
                    # Transform using stored statistics
                    if col in self.feature_means and col in self.feature_stds:
                        mean_val = self.feature_means[col]
                        std_val = self.feature_stds[col]

                        if std_val > 1e-6:
                            df_norm[f'{col}_normalized'] = (df_norm[col] - mean_val) / std_val
                        else:
                            df_norm[f'{col}_normalized'] = 0.0
                    else:
                        logger.warning(f"No stored stats for {col}, skipping normalization")

            except Exception as e:
                logger.warning(f"Failed to normalize {col}: {e}")
                df_norm[f'{col}_normalized'] = 0.0

        logger.info(f"Normalized {len(numeric_cols)} numeric features")
        return df_norm

    def encode_categoricals(
        self,
        df: pd.DataFrame,
        fit: bool = True,
    ) -> pd.DataFrame:
        """
        Encode categorical features using label encoding and one-hot encoding

        Args:
            df: Input DataFrame
            fit: Whether to fit encoders on this data (True for training)

        Returns:
            DataFrame with encoded categorical features
        """
        logger.info("Encoding categorical features...")

        df_encoded = df.copy()

        # Get categorical columns that exist in the dataframe
        categorical_cols = [col for col in self.categorical_features if col in df.columns]

        for col in categorical_cols:
            if col not in df_encoded.columns:
                continue

            try:
                # Fill NaN with 'unknown'
                df_encoded[col] = df_encoded[col].fillna('unknown').astype(str)

                if fit:
                    # Label encoding for ordinal features
                    encoder = LabelEncoder()
                    df_encoded[f'{col}_encoded'] = encoder.fit_transform(df_encoded[col])
                    self.encoders[col] = encoder
                else:
                    # Transform using stored encoder
                    if col in self.encoders:
                        encoder = self.encoders[col]
                        # Handle unknown categories
                        known_classes = set(encoder.classes_)
                        df_encoded[f'{col}_encoded'] = df_encoded[col].apply(
                            lambda x: encoder.transform([x])[0] if x in known_classes else -1
                        )
                    else:
                        logger.warning(f"No stored encoder for {col}, using default encoding")
                        df_encoded[f'{col}_encoded'] = 0

                # One-hot encoding for nominal features (if needed)
                if col == 'position':
                    # One-hot encode position
                    position_dummies = pd.get_dummies(
                        df_encoded[col],
                        prefix=col,
                        drop_first=False,
                    )
                    df_encoded = pd.concat([df_encoded, position_dummies], axis=1)

            except Exception as e:
                logger.warning(f"Failed to encode {col}: {e}")
                df_encoded[f'{col}_encoded'] = 0

        logger.info(f"Encoded {len(categorical_cols)} categorical features")
        return df_encoded

    def create_interactions(
        self,
        df: pd.DataFrame,
        max_interactions: int = 10,
    ) -> pd.DataFrame:
        """
        Create interaction features between important variables

        Args:
            df: Input DataFrame
            max_interactions: Maximum number of interaction features to create

        Returns:
            DataFrame with interaction features
        """
        logger.info("Creating interaction features...")

        df_interact = df.copy()

        # Define key interaction pairs
        interactions = [
            # Player performance x matchup quality
            ('season_avg', 'opponent_defense_rank'),
            ('last_3_avg', 'opponent_strength'),
            # Line value x player form
            ('line_vs_baseline', 'recent_form'),
            ('line_vs_baseline', 'ewma_trend'),
            # Pace x usage
            ('opponent_pace', 'usage_rate'),
            ('opponent_pace', 'target_share'),
            # Weather x performance
            ('wind_speed', 'season_avg'),
            ('temperature', 'season_avg'),
            # Home/away x opponent
            ('home_away_split', 'opponent_strength'),
            # Volatility x line position
            ('volatility', 'line_vs_baseline'),
        ]

        created = 0
        for feat1, feat2 in interactions:
            if created >= max_interactions:
                break

            if feat1 in df_interact.columns and feat2 in df_interact.columns:
                try:
                    # Multiplicative interaction
                    interaction_name = f'{feat1}_x_{feat2}'
                    df_interact[interaction_name] = (
                        df_interact[feat1].fillna(0) * df_interact[feat2].fillna(0)
                    )
                    created += 1
                except Exception as e:
                    logger.warning(f"Failed to create interaction {feat1} x {feat2}: {e}")

        logger.info(f"Created {created} interaction features")
        return df_interact

    def handle_missing(
        self,
        df: pd.DataFrame,
        strategy: str = 'smart',
    ) -> pd.DataFrame:
        """
        Handle missing values using various strategies

        Args:
            df: Input DataFrame
            strategy: Imputation strategy ('mean', 'median', 'zero', 'smart')

        Returns:
            DataFrame with imputed missing values
        """
        logger.info(f"Handling missing values with strategy: {strategy}")

        df_filled = df.copy()

        # Get numeric columns
        numeric_cols = df_filled.select_dtypes(include=[np.number]).columns

        if strategy == 'smart':
            # Use domain knowledge for smart imputation
            fill_values = {
                # Performance metrics: use 0 if missing
                'season_avg': 0.0,
                'last_3_avg': 0.0,
                'last_5_avg': 0.0,
                'last_10_avg': 0.0,
                'median_value': 0.0,
                'min_value': 0.0,
                'max_value': 0.0,
                # Variability: use median if missing
                'std_dev': lambda x: x.median(),
                'volatility': lambda x: x.median(),
                # Counts: use 0
                'games_played': 0,
                # Rates and shares: use league average
                'usage_rate': 0.25,
                'target_share': 0.20,
                # Matchup features: use league average
                'opponent_defense_rank': 16,
                'opponent_pace': 24.0,
                'opponent_strength': 0.7,
                # Context features: use neutral values
                'temperature': 65.0,
                'wind_speed': 5.0,
                'precipitation_prob': 0.1,
                'humidity': 50.0,
                'game_total': 47.5,
                'spread': 0.0,
                # Derived features: use 0
                'ewma_trend': 0.0,
                'line_vs_baseline': 0.0,
                'recent_form': 0,
                'rest_advantage': 0.0,
                'weather_impact': 0.0,
                # Binary features: use mode
                'is_home': lambda x: x.mode()[0] if len(x.mode()) > 0 else True,
                'primetime_game': 0,
            }

            for col in numeric_cols:
                if df_filled[col].isna().any():
                    if col in fill_values:
                        fill_val = fill_values[col]
                        if callable(fill_val):
                            # Use function to compute fill value
                            try:
                                df_filled[col] = df_filled[col].fillna(fill_val(df_filled[col]))
                            except Exception:
                                df_filled[col] = df_filled[col].fillna(0.0)
                        else:
                            # Use constant fill value
                            df_filled[col] = df_filled[col].fillna(fill_val)
                    else:
                        # Default: use median for this column
                        median_val = df_filled[col].median()
                        df_filled[col] = df_filled[col].fillna(median_val if not pd.isna(median_val) else 0.0)

        elif strategy == 'mean':
            for col in numeric_cols:
                if df_filled[col].isna().any():
                    mean_val = df_filled[col].mean()
                    df_filled[col] = df_filled[col].fillna(mean_val if not pd.isna(mean_val) else 0.0)

        elif strategy == 'median':
            for col in numeric_cols:
                if df_filled[col].isna().any():
                    median_val = df_filled[col].median()
                    df_filled[col] = df_filled[col].fillna(median_val if not pd.isna(median_val) else 0.0)

        elif strategy == 'zero':
            df_filled = df_filled.fillna(0.0)

        else:
            raise ValueError(f"Unknown imputation strategy: {strategy}")

        # Fill categorical columns with 'unknown'
        categorical_cols = df_filled.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            df_filled[col] = df_filled[col].fillna('unknown')

        missing_after = df_filled.isna().sum().sum()
        logger.info(f"Missing values after imputation: {missing_after}")

        return df_filled

    def get_feature_importance_groups(self) -> Dict[str, List[str]]:
        """
        Get feature groups for importance analysis

        Returns:
            Dictionary mapping group names to feature lists
        """
        return {
            'player_performance': [
                'season_avg', 'last_3_avg', 'last_5_avg', 'last_10_avg',
                'median_value', 'std_dev', 'games_played',
            ],
            'player_context': [
                'home_away_split', 'usage_rate', 'target_share',
                'days_rest', 'injury_status_encoded',
            ],
            'matchup_quality': [
                'opponent_defense_rank', 'opponent_pace', 'opponent_strength',
                'career_avg_vs_opponent', 'historical_matchup_avg',
            ],
            'environmental': [
                'venue_type_encoded', 'temperature', 'wind_speed',
                'precipitation_prob', 'primetime_game',
            ],
            'market_signals': [
                'line_movement', 'implied_probability', 'odds_value',
                'line_vs_baseline', 'book_consensus',
            ],
            'derived_metrics': [
                'ewma_trend', 'volatility', 'ceiling_score', 'floor_score',
                'recent_form', 'pace_adjusted_avg', 'rest_advantage',
                'weather_impact',
            ],
        }

    def select_features(
        self,
        df: pd.DataFrame,
        feature_groups: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Select specific feature groups

        Args:
            df: Input DataFrame
            feature_groups: List of group names to include (None = all)

        Returns:
            DataFrame with only selected features
        """
        if feature_groups is None:
            return df

        groups = self.get_feature_importance_groups()
        selected_features = []

        for group_name in feature_groups:
            if group_name in groups:
                selected_features.extend(groups[group_name])

        # Always include metadata columns
        metadata_cols = ['prop_id', 'player_id', 'player_name', 'team', 'opponent', 'stat_type', 'line']
        selected_features = metadata_cols + [f for f in selected_features if f in df.columns]

        return df[selected_features]

    def validate_features(
        self,
        df: pd.DataFrame,
    ) -> Tuple[bool, List[str]]:
        """
        Validate feature DataFrame for common issues

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []

        # Check for infinite values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if np.isinf(df[col]).any():
                issues.append(f"Column {col} contains infinite values")

        # Check for very high variance (potential data quality issue)
        for col in numeric_cols:
            if df[col].std() > 1000:
                issues.append(f"Column {col} has very high variance: {df[col].std():.2f}")

        # Check for constant columns
        for col in df.columns:
            if df[col].nunique() <= 1:
                issues.append(f"Column {col} is constant (only {df[col].nunique()} unique values)")

        # Check required columns
        required_cols = ['prop_id', 'player_id', 'stat_type', 'line']
        missing_required = [col for col in required_cols if col not in df.columns]
        if missing_required:
            issues.append(f"Missing required columns: {missing_required}")

        is_valid = len(issues) == 0
        return is_valid, issues
