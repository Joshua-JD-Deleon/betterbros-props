"""
Demonstration script for ML models and calibration system.

This script shows:
1. Training a GBM model (with fallback to logistic regression)
2. Calibrating probabilities
3. Estimating uncertainty
4. Generating predictions with confidence intervals
5. Creating calibration plots
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from src.models import (
    GradientBoostingModel,
    estimate_probabilities,
    calibrate_probabilities,
    plot_calibration_curve,
    train_gbm
)


def create_mock_training_data(n_samples: int = 200) -> pd.DataFrame:
    """Create realistic mock training data."""
    np.random.seed(42)

    data = pd.DataFrame({
        'player_id': [f'player_{i}' for i in range(n_samples)],
        'team': np.random.choice(['KC', 'BUF', 'SF', 'DAL', 'PHI'], n_samples),
        'line': np.random.uniform(50, 300, n_samples),
        'line_zscore': np.random.randn(n_samples),
        'recent_form': np.random.uniform(0.3, 0.9, n_samples),
        'matchup_difficulty': np.random.uniform(0.2, 0.8, n_samples),
        'injury_risk': np.random.choice([0, 0.1, 0.2], n_samples, p=[0.7, 0.2, 0.1]),
        'weather_impact': np.random.uniform(-0.1, 0.1, n_samples),
        'home_away': np.random.choice(['home', 'away'], n_samples),
        'pace': np.random.uniform(95, 105, n_samples),
    })

    # Generate outcome based on features (with some noise)
    logit = (
        -0.5 * data['line_zscore'] +  # Lower line = more likely to go over
        1.0 * (data['recent_form'] - 0.5) +  # Good form = more likely over
        -0.8 * (data['matchup_difficulty'] - 0.5) +  # Easy matchup = more likely over
        -1.5 * data['injury_risk'] +  # Injury = less likely over
        0.3 * data['weather_impact'] +
        0.2 * (data['home_away'] == 'home').astype(float)
    )

    # Add noise
    logit += np.random.normal(0, 1, n_samples)

    # Convert to probability and sample outcome
    prob = 1 / (1 + np.exp(-logit))
    data['outcome'] = (np.random.uniform(0, 1, n_samples) < prob).astype(int)

    return data


def create_mock_props_data(n_props: int = 20) -> pd.DataFrame:
    """Create mock current week props."""
    np.random.seed(123)

    props = pd.DataFrame({
        'player_id': [f'player_{i}' for i in range(100, 100 + n_props)],
        'player_name': [f'Player {i}' for i in range(n_props)],
        'team': np.random.choice(['KC', 'BUF', 'SF', 'DAL', 'PHI'], n_props),
        'position': np.random.choice(['QB', 'RB', 'WR', 'TE'], n_props, p=[0.2, 0.3, 0.35, 0.15]),
        'stat_type': np.random.choice(['passing_yards', 'rushing_yards', 'receiving_yards'], n_props),
        'line': np.random.uniform(50, 300, n_props),
        'over_odds': np.random.choice([-110, -115, -105, -120], n_props),
        'under_odds': np.random.choice([-110, -115, -105, -120], n_props),
        'line_zscore': np.random.randn(n_props),
        'recent_form': np.random.uniform(0.3, 0.9, n_props),
        'matchup_difficulty': np.random.uniform(0.2, 0.8, n_props),
        'injury_risk': np.random.choice([0, 0.1, 0.2], n_props, p=[0.7, 0.2, 0.1]),
        'weather_impact': np.random.uniform(-0.1, 0.1, n_props),
        'home_away': np.random.choice(['home', 'away'], n_props),
        'pace': np.random.uniform(95, 105, n_props),
    })

    return props


def main():
    print("=" * 70)
    print("NFL Props Analyzer - ML Models & Calibration Demo")
    print("=" * 70)
    print()

    # 1. Create training data
    print("Step 1: Creating mock training data...")
    training_data = create_mock_training_data(n_samples=200)
    print(f"  Created {len(training_data)} historical prop records")
    print(f"  Outcome distribution: {training_data['outcome'].mean():.1%} hit rate")
    print()

    # 2. Train GBM model
    print("Step 2: Training GBM model...")
    feature_cols = ['line_zscore', 'recent_form', 'matchup_difficulty',
                    'injury_risk', 'weather_impact', 'pace']
    X_train = training_data[feature_cols]
    y_train = training_data['outcome']

    model = GradientBoostingModel(model_type="lightgbm")
    try:
        metrics = model.train(X_train, y_train, validation_split=0.2)
        print(f"  Training complete!")
        print(f"  - Validation AUC: {metrics['val_auc']:.4f}")
        print(f"  - Validation Log Loss: {metrics['val_logloss']:.4f}")
        if 'model_fallback' in metrics:
            print(f"  - Note: Using {metrics['model_fallback']} fallback")
    except Exception as e:
        print(f"  Warning: Model training failed: {e}")
        print(f"  Continuing with heuristic predictions...")
        model = None
    print()

    # 3. Get feature importance
    if model is not None and model.model is not None:
        print("Step 3: Feature Importance...")
        importance = model.get_feature_importance(top_n=5)
        if not importance.empty:
            print("  Top features:")
            for _, row in importance.iterrows():
                print(f"    - {row['feature']}: {row['importance']:.4f}")
        print()

    # 4. Test calibration on training set
    print("Step 4: Evaluating calibration on training set...")
    if model is not None and model.model is not None:
        train_probs = model.predict_proba(X_train)
        calibrated_probs, cal_metrics = calibrate_probabilities(
            train_probs, y_train, method="isotonic"
        )
        print(f"  - Brier Score: {cal_metrics['brier_score']:.4f}")
        print(f"  - Expected Calibration Error: {cal_metrics['ece']:.4f}")
        print(f"  - Log Loss: {cal_metrics['log_loss']:.4f}")
        print()

        # Create calibration plot
        reports_dir = Path(__file__).parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        plot_path = reports_dir / "calibration_curve.png"
        plot_calibration_curve(
            calibrated_probs, y_train.values,
            save_path=str(plot_path),
            title="Model Calibration (Training Set)"
        )

    # 5. Generate predictions for current week
    print("Step 5: Generating predictions for current week props...")
    current_props = create_mock_props_data(n_props=20)
    print(f"  Loaded {len(current_props)} props for analysis")
    print()

    # Make predictions
    if model is not None and model.model is not None:
        result_df = estimate_probabilities(current_props, models=[model])
    else:
        result_df = estimate_probabilities(current_props, models=None)

    # 6. Display results
    print("Step 6: Top 10 Props by Expected Value...")
    print()

    # Calculate expected value (simplified)
    def odds_to_payout(odds):
        if odds < 0:
            return 100 / abs(odds)
        else:
            return odds / 100

    result_df['payout_over'] = result_df['over_odds'].apply(odds_to_payout)
    result_df['ev_over'] = result_df['prob_over'] * result_df['payout_over'] - (1 - result_df['prob_over'])
    result_df['ev_pct'] = result_df['ev_over'] * 100

    # Sort by EV
    top_props = result_df.nlargest(10, 'ev_pct')

    print(f"{'Player':<20} {'Stat':<15} {'Line':>6} {'Prob':>6} {'CI Width':>9} {'EV %':>7}")
    print("-" * 70)
    for _, prop in top_props.iterrows():
        print(
            f"{prop['player_name']:<20} "
            f"{prop['stat_type']:<15} "
            f"{prop['line']:>6.1f} "
            f"{prop['prob_over']:>6.1%} "
            f"{prop['ci_width']:>9.3f} "
            f"{prop['ev_pct']:>7.1f}%"
        )
    print()

    # 7. Show uncertainty analysis
    print("Step 7: Uncertainty Analysis...")
    print()
    high_confidence = result_df.nsmallest(5, 'ci_width')
    print("High Confidence Props (Narrow CI):")
    for _, prop in high_confidence.iterrows():
        print(
            f"  {prop['player_name']:<20} "
            f"{prop['stat_type']:<15} "
            f"P={prop['prob_over']:.3f} "
            f"[{prop['ci_lower']:.3f}, {prop['ci_upper']:.3f}]"
        )
    print()

    # 8. Summary statistics
    print("=" * 70)
    print("Summary Statistics")
    print("=" * 70)
    print(f"Total props analyzed: {len(result_df)}")
    print(f"Average probability: {result_df['prob_over'].mean():.3f}")
    print(f"Average CI width: {result_df['ci_width'].mean():.3f}")
    print(f"Average uncertainty (sigma): {result_df['sigma'].mean():.3f}")
    print(f"Props with positive EV: {(result_df['ev_pct'] > 0).sum()}")
    print(f"Props with EV > 5%: {(result_df['ev_pct'] > 5).sum()}")
    print()

    # 9. Save results
    output_dir = Path(__file__).parent.parent / "data" / "predictions"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "demo_predictions.csv"

    result_df.to_csv(output_file, index=False)
    print(f"Results saved to: {output_file}")
    print()

    print("Demo complete!")


if __name__ == "__main__":
    main()
