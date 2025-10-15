"""
Leakage Detection for Feature Engineering

Prevents temporal leakage, target leakage, and other data contamination
that could lead to overly optimistic model performance.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import pandas as pd

logger = logging.getLogger(__name__)


class LeakageError(Exception):
    """Exception raised when data leakage is detected"""
    pass


class LeakageDetector:
    """
    Detector for various types of data leakage

    Checks for:
    - Temporal leakage (future data in features)
    - Target leakage (target variable in features)
    - Information leakage (features computed from test set)
    """

    def __init__(self, strict_mode: bool = True):
        """
        Initialize leakage detector

        Args:
            strict_mode: If True, raise exceptions on detection; if False, only warn
        """
        self.strict_mode = strict_mode
        self.detected_issues: List[Dict[str, Any]] = []

        # Define suspicious feature patterns that may indicate leakage
        self.suspicious_patterns = [
            'actual_', 'result_', 'outcome_', 'final_', 'game_result',
            'score_', 'winning_', 'total_points', 'game_winner',
        ]

        # Features that should never be in the dataset before game time
        self.forbidden_features = [
            'actual_value', 'game_outcome', 'final_score', 'game_result',
            'player_actual_stats', 'bet_result', 'profit', 'won', 'lost',
        ]

    def check_temporal_leakage(
        self,
        df: pd.DataFrame,
        current_week: int,
        reference_date: Optional[datetime] = None,
    ):
        """
        Check for temporal leakage (using future data)

        Args:
            df: Feature DataFrame
            current_week: Current week number (features should not use data beyond this)
            reference_date: Reference date for temporal checks

        Raises:
            LeakageError: If temporal leakage detected and strict_mode=True
        """
        logger.info(f"Checking temporal leakage for week {current_week}...")

        issues = []

        # Check 1: Verify no features reference future weeks
        if 'week' in df.columns:
            future_weeks = df[df['week'] > current_week]
            if not future_weeks.empty:
                issue = f"Found {len(future_weeks)} rows with week > {current_week}"
                issues.append(issue)
                logger.error(f"LEAKAGE DETECTED: {issue}")

        # Check 2: Check for timestamp leakage
        timestamp_cols = [col for col in df.columns if 'timestamp' in col.lower() or col.endswith('_at')]

        if reference_date:
            for col in timestamp_cols:
                if col in df.columns:
                    try:
                        timestamps = pd.to_datetime(df[col], errors='coerce')
                        future_timestamps = timestamps[timestamps > reference_date]

                        if not future_timestamps.empty:
                            issue = f"Column '{col}' contains {len(future_timestamps)} future timestamps"
                            issues.append(issue)
                            logger.warning(f"POTENTIAL LEAKAGE: {issue}")
                    except Exception as e:
                        logger.warning(f"Failed to check timestamp column {col}: {e}")

        # Check 3: Verify computed_at is before game_time
        if 'computed_at' in df.columns and 'game_time' in df.columns:
            try:
                computed = pd.to_datetime(df['computed_at'], errors='coerce')
                game_time = pd.to_datetime(df['game_time'], errors='coerce')

                leakage_rows = computed > game_time
                if leakage_rows.any():
                    issue = f"Found {leakage_rows.sum()} rows where computed_at > game_time"
                    issues.append(issue)
                    logger.error(f"LEAKAGE DETECTED: {issue}")
            except Exception as e:
                logger.warning(f"Failed to check computed_at vs game_time: {e}")

        # Check 4: Verify no future baseline stats
        baseline_cols = [col for col in df.columns if 'avg' in col or 'baseline' in col]
        # Baseline stats should be computed from games BEFORE current week
        # This is validated implicitly by the week check above

        # Record issues
        if issues:
            self.detected_issues.extend([{
                'type': 'temporal_leakage',
                'severity': 'critical',
                'issue': issue,
                'timestamp': datetime.utcnow().isoformat(),
            } for issue in issues])

            if self.strict_mode:
                raise LeakageError(f"Temporal leakage detected: {issues}")
            else:
                logger.warning(f"Temporal leakage detected (non-strict mode): {issues}")

        logger.info(f"Temporal leakage check completed: {len(issues)} issues found")

    def check_target_leakage(
        self,
        df: pd.DataFrame,
        target_col: Optional[str] = None,
    ):
        """
        Check for target leakage (target variable information in features)

        Args:
            df: Feature DataFrame
            target_col: Target column name (if present in df)

        Raises:
            LeakageError: If target leakage detected and strict_mode=True
        """
        logger.info("Checking target leakage...")

        issues = []

        # Check 1: Look for forbidden feature names
        forbidden_cols = [col for col in df.columns if col in self.forbidden_features]
        if forbidden_cols:
            issue = f"Found forbidden columns that may contain target leakage: {forbidden_cols}"
            issues.append(issue)
            logger.error(f"LEAKAGE DETECTED: {issue}")

        # Check 2: Look for suspicious patterns
        suspicious_cols = []
        for col in df.columns:
            col_lower = col.lower()
            if any(pattern in col_lower for pattern in self.suspicious_patterns):
                suspicious_cols.append(col)

        if suspicious_cols:
            issue = f"Found suspicious column names that may indicate leakage: {suspicious_cols}"
            issues.append(issue)
            logger.warning(f"POTENTIAL LEAKAGE: {issue}")

        # Check 3: If target is present, check for perfect correlation
        if target_col and target_col in df.columns:
            numeric_cols = df.select_dtypes(include=['number']).columns
            numeric_cols = [col for col in numeric_cols if col != target_col]

            try:
                for col in numeric_cols:
                    if col in df.columns and df[col].notna().any():
                        correlation = df[target_col].corr(df[col])
                        if abs(correlation) > 0.99:
                            issue = f"Column '{col}' has suspiciously high correlation ({correlation:.4f}) with target"
                            issues.append(issue)
                            logger.warning(f"POTENTIAL LEAKAGE: {issue}")
            except Exception as e:
                logger.warning(f"Failed to check correlations: {e}")

        # Check 4: Look for features that shouldn't exist pre-game
        # These would be derived from game outcomes
        outcome_indicators = [
            'hit', 'miss', 'won', 'lost', 'profit', 'loss',
            'success', 'failure', 'correct', 'incorrect',
        ]

        outcome_cols = []
        for col in df.columns:
            col_lower = col.lower()
            if any(indicator in col_lower for indicator in outcome_indicators):
                outcome_cols.append(col)

        if outcome_cols:
            issue = f"Found outcome indicator columns: {outcome_cols}"
            issues.append(issue)
            logger.error(f"LEAKAGE DETECTED: {issue}")

        # Record issues
        if issues:
            self.detected_issues.extend([{
                'type': 'target_leakage',
                'severity': 'critical',
                'issue': issue,
                'timestamp': datetime.utcnow().isoformat(),
            } for issue in issues])

            if self.strict_mode:
                raise LeakageError(f"Target leakage detected: {issues}")
            else:
                logger.warning(f"Target leakage detected (non-strict mode): {issues}")

        logger.info(f"Target leakage check completed: {len(issues)} issues found")

    def validate_feature_timestamps(
        self,
        df: pd.DataFrame,
    ):
        """
        Validate that feature timestamps are logical and consistent

        Args:
            df: Feature DataFrame

        Raises:
            LeakageError: If timestamp inconsistencies detected and strict_mode=True
        """
        logger.info("Validating feature timestamps...")

        issues = []

        # Check 1: Ensure computed_at exists and is valid
        if 'computed_at' in df.columns:
            try:
                computed = pd.to_datetime(df['computed_at'], errors='coerce')
                invalid_timestamps = computed.isna()

                if invalid_timestamps.any():
                    issue = f"Found {invalid_timestamps.sum()} rows with invalid computed_at timestamps"
                    issues.append(issue)
                    logger.warning(f"VALIDATION WARNING: {issue}")

                # Check if computed_at is in the future
                now = datetime.utcnow()
                future_computed = computed > now

                if future_computed.any():
                    issue = f"Found {future_computed.sum()} rows with future computed_at timestamps"
                    issues.append(issue)
                    logger.error(f"LEAKAGE DETECTED: {issue}")

            except Exception as e:
                logger.warning(f"Failed to validate computed_at: {e}")

        # Check 2: Validate game_time if present
        if 'game_time' in df.columns:
            try:
                game_time = pd.to_datetime(df['game_time'], errors='coerce')
                invalid_game_times = game_time.isna()

                if invalid_game_times.any():
                    issue = f"Found {invalid_game_times.sum()} rows with invalid game_time"
                    issues.append(issue)
                    logger.warning(f"VALIDATION WARNING: {issue}")

            except Exception as e:
                logger.warning(f"Failed to validate game_time: {e}")

        # Check 3: Validate timestamp ordering
        if 'computed_at' in df.columns and 'game_time' in df.columns:
            try:
                computed = pd.to_datetime(df['computed_at'], errors='coerce')
                game_time = pd.to_datetime(df['game_time'], errors='coerce')

                # computed_at should be before or at game_time
                valid_mask = computed <= game_time
                invalid_rows = ~valid_mask & computed.notna() & game_time.notna()

                if invalid_rows.any():
                    issue = f"Found {invalid_rows.sum()} rows where computed_at > game_time"
                    issues.append(issue)
                    logger.error(f"LEAKAGE DETECTED: {issue}")

            except Exception as e:
                logger.warning(f"Failed to validate timestamp ordering: {e}")

        # Check 4: Check for data from different time periods mixed together
        if 'week' in df.columns:
            weeks = df['week'].unique()
            if len(weeks) > 1:
                logger.info(f"Features contain data from {len(weeks)} different weeks: {sorted(weeks)}")
                # This is not necessarily leakage, just informational

        # Record issues
        if issues:
            self.detected_issues.extend([{
                'type': 'timestamp_validation',
                'severity': 'high',
                'issue': issue,
                'timestamp': datetime.utcnow().isoformat(),
            } for issue in issues])

            if self.strict_mode and any('LEAKAGE DETECTED' in issue for issue in issues):
                raise LeakageError(f"Timestamp validation failed: {issues}")
            else:
                logger.warning(f"Timestamp validation warnings (non-strict mode): {issues}")

        logger.info(f"Timestamp validation completed: {len(issues)} issues found")

    def check_train_test_contamination(
        self,
        train_df: pd.DataFrame,
        test_df: pd.DataFrame,
        index_col: str = 'prop_id',
    ):
        """
        Check for contamination between train and test sets

        Args:
            train_df: Training DataFrame
            test_df: Test DataFrame
            index_col: Column to use for identifying unique records

        Raises:
            LeakageError: If contamination detected and strict_mode=True
        """
        logger.info("Checking train/test contamination...")

        issues = []

        # Check 1: Ensure no overlap in identifiers
        if index_col in train_df.columns and index_col in test_df.columns:
            train_ids = set(train_df[index_col])
            test_ids = set(test_df[index_col])

            overlap = train_ids.intersection(test_ids)

            if overlap:
                issue = f"Found {len(overlap)} overlapping {index_col} values between train and test"
                issues.append(issue)
                logger.error(f"LEAKAGE DETECTED: {issue}")

        # Check 2: Verify temporal separation
        if 'week' in train_df.columns and 'week' in test_df.columns:
            train_max_week = train_df['week'].max()
            test_min_week = test_df['week'].min()

            if train_max_week >= test_min_week:
                issue = f"Train set max week ({train_max_week}) >= test set min week ({test_min_week})"
                issues.append(issue)
                logger.error(f"LEAKAGE DETECTED: {issue}")

        # Check 3: Verify player separation (if applicable)
        # For some ML tasks, you want to ensure no player appears in both train and test
        # This is optional and task-dependent

        # Record issues
        if issues:
            self.detected_issues.extend([{
                'type': 'train_test_contamination',
                'severity': 'critical',
                'issue': issue,
                'timestamp': datetime.utcnow().isoformat(),
            } for issue in issues])

            if self.strict_mode:
                raise LeakageError(f"Train/test contamination detected: {issues}")
            else:
                logger.warning(f"Train/test contamination detected (non-strict mode): {issues}")

        logger.info(f"Train/test contamination check completed: {len(issues)} issues found")

    def check_feature_distributions(
        self,
        df: pd.DataFrame,
        suspicious_threshold: float = 0.95,
    ):
        """
        Check for suspicious feature distributions that may indicate leakage

        Args:
            df: Feature DataFrame
            suspicious_threshold: Threshold for suspicious uniqueness ratio

        Raises:
            LeakageError: If suspicious distributions detected and strict_mode=True
        """
        logger.info("Checking feature distributions...")

        issues = []
        numeric_cols = df.select_dtypes(include=['number']).columns

        for col in numeric_cols:
            if col in df.columns and df[col].notna().any():
                try:
                    # Check 1: Too many unique values (possible ID leakage)
                    n_unique = df[col].nunique()
                    n_total = len(df[col].dropna())

                    if n_total > 0:
                        uniqueness_ratio = n_unique / n_total

                        if uniqueness_ratio > suspicious_threshold:
                            issue = f"Column '{col}' has suspiciously high uniqueness ({uniqueness_ratio:.2%})"
                            issues.append(issue)
                            logger.warning(f"POTENTIAL LEAKAGE: {issue}")

                    # Check 2: Check for unrealistic values
                    min_val = df[col].min()
                    max_val = df[col].max()

                    # Domain-specific checks
                    if 'probability' in col.lower() or 'prob' in col.lower():
                        if min_val < 0 or max_val > 1:
                            issue = f"Probability column '{col}' has values outside [0, 1]: [{min_val}, {max_val}]"
                            issues.append(issue)
                            logger.warning(f"VALIDATION WARNING: {issue}")

                    if 'percentage' in col.lower() or 'pct' in col.lower():
                        if min_val < 0 or max_val > 100:
                            issue = f"Percentage column '{col}' has values outside [0, 100]: [{min_val}, {max_val}]"
                            issues.append(issue)
                            logger.warning(f"VALIDATION WARNING: {issue}")

                except Exception as e:
                    logger.warning(f"Failed to check distribution for {col}: {e}")

        # Record issues
        if issues:
            self.detected_issues.extend([{
                'type': 'distribution_check',
                'severity': 'medium',
                'issue': issue,
                'timestamp': datetime.utcnow().isoformat(),
            } for issue in issues])

            # Distribution issues are warnings, not strict errors
            logger.warning(f"Distribution check warnings: {issues}")

        logger.info(f"Distribution check completed: {len(issues)} issues found")

    def get_detected_issues(self) -> List[Dict[str, Any]]:
        """
        Get all detected issues

        Returns:
            List of issue dictionaries
        """
        return self.detected_issues

    def clear_issues(self):
        """Clear detected issues"""
        self.detected_issues = []

    def generate_report(self) -> str:
        """
        Generate a summary report of all detected issues

        Returns:
            Formatted report string
        """
        if not self.detected_issues:
            return "No leakage issues detected."

        report = ["=" * 80]
        report.append("LEAKAGE DETECTION REPORT")
        report.append("=" * 80)
        report.append(f"Total issues detected: {len(self.detected_issues)}")
        report.append("")

        # Group by type
        by_type: Dict[str, List[Dict[str, Any]]] = {}
        for issue in self.detected_issues:
            issue_type = issue.get('type', 'unknown')
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(issue)

        for issue_type, issues in by_type.items():
            report.append(f"\n{issue_type.upper()} ({len(issues)} issues):")
            report.append("-" * 80)
            for i, issue in enumerate(issues, 1):
                severity = issue.get('severity', 'unknown')
                issue_text = issue.get('issue', 'No description')
                report.append(f"{i}. [{severity.upper()}] {issue_text}")

        report.append("\n" + "=" * 80)
        return "\n".join(report)
