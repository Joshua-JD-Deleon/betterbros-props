# Machine Learning Models & Calibration System

This document describes the ML models and calibration system for the NFL Props Analyzer.

## Overview

The system provides three main components:

1. **Gradient Boosting Models (GBM)** - For probability estimation
2. **Calibration System** - For probability calibration and uncertainty quantification
3. **Bayesian Models (Stub)** - Placeholder for future hierarchical models

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Prediction Pipeline                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Props Data → Feature Engineering → Model Ensemble →        │
│                                                              │
│  → Calibration → Uncertainty Estimation → Predictions       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 1. Gradient Boosting Models

### Implementation

Located in: `/Users/joshuadeleon/nfl-props-analyzer/src/models/gbm.py`

### Features

- **Model Types**: LightGBM (preferred) or XGBoost
- **Fallback**: Logistic Regression when GBM libraries unavailable
- **Feature Importance**: Automatic extraction and ranking
- **Model Persistence**: Save/load functionality
- **Early Stopping**: Prevents overfitting

### Usage

```python
from src.models import GradientBoostingModel, train_gbm

# Method 1: Using the class
model = GradientBoostingModel(model_type="lightgbm")
metrics = model.train(X, y, validation_split=0.2)
probs = model.predict_proba(X_new)

# Method 2: Using convenience function
result = train_gbm(features_df, target='hit')
model = result['model']
feature_importance = result['feature_importance']
metrics = result['metrics']

# Save model
model.save(Path("models/gbm_model.pkl"))

# Load model
loaded_model = GradientBoostingModel()
loaded_model.load(Path("models/gbm_model.pkl"))
```

### Hyperparameters

**LightGBM** (default):
```python
{
    'objective': 'binary',
    'boosting_type': 'gbdt',
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'n_estimators': 200
}
```

**XGBoost**:
```python
{
    'objective': 'binary:logistic',
    'max_depth': 6,
    'learning_rate': 0.05,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'n_estimators': 200
}
```

### Heuristic Fallback

When no trained model is available, the system uses a sophisticated heuristic:

```python
prob_over = base_prob
  - 0.08 * line_zscore          # Line vs baseline
  + 0.15 * (recent_form - 0.5)  # Recent performance
  + 0.10 * (0.5 - matchup_diff)  # Matchup ease
  - 0.12 * injury_risk           # Injury impact
  + 0.08 * weather_impact        # Weather conditions
  + noise
```

This ensures reasonable predictions even before training data is available.

## 2. Calibration System

### Implementation

Located in: `/Users/joshuadeleon/nfl-props-analyzer/src/models/calibration.py`

### Components

#### CalibrationEvaluator

Evaluates and improves model calibration:

```python
from src.models import CalibrationEvaluator

evaluator = CalibrationEvaluator(n_bins=10)

# Evaluate calibration
metrics = evaluator.evaluate_calibration(y_true, y_pred)
# Returns: ece, mce, brier_score, log_loss

# Fit calibration map
evaluator.fit_calibration_map(y_true, y_pred, method="isotonic")

# Apply calibration
calibrated_probs = evaluator.apply_calibration(y_pred)

# Check for drift
alert = evaluator.check_calibration_alert(recent_outcomes, threshold=0.15)
```

#### Calibration Methods

1. **Isotonic Regression** (default)
   - Non-parametric
   - Flexible, can fit complex calibration curves
   - Good for larger datasets

2. **Platt Scaling**
   - Parametric (logistic regression)
   - Good for smaller datasets
   - Assumes sigmoid-shaped calibration curve

#### Metrics

- **Expected Calibration Error (ECE)**: Average deviation between predicted and observed frequencies
- **Maximum Calibration Error (MCE)**: Worst-case deviation
- **Brier Score**: Mean squared error of probability predictions
- **Log Loss**: Cross-entropy loss

### Uncertainty Quantification

#### Beta Distribution Method

Models uncertainty using Beta distribution:

```python
from src.models import estimate_uncertainty

ci_lower, ci_upper = estimate_uncertainty(
    calibrated_probs,
    method="beta_binomial",
    confidence_level=0.90
)
```

Parameters:
- Effective sample size: ~10 (assumes 10 comparable historical props)
- Confidence level: 90% by default

#### Uncertainty Metrics

For each prediction, the system provides:
- `sigma`: Standard deviation (uncertainty measure)
- `ci_lower`: Lower bound of 90% confidence interval
- `ci_upper`: Upper bound of 90% confidence interval
- `ci_width`: Width of confidence interval (upper - lower)

### Calibration Plots

Generate reliability diagrams:

```python
from src.models import plot_calibration_curve

plot_calibration_curve(
    probs=predicted_probs,
    labels=true_labels,
    save_path="reports/calibration_curve.png",
    n_bins=10,
    title="Model Calibration"
)
```

Output includes:
- Calibration curve (predicted vs actual frequencies)
- Distribution of predicted probabilities
- Calibration metrics (ECE, Brier, Log Loss)

## 3. Unified Prediction Interface

### Main Function: `estimate_probabilities`

The primary interface for generating predictions:

```python
from src.models import estimate_probabilities

result_df = estimate_probabilities(
    props_df=props_with_features,
    models=[gbm_model, bayesian_model],  # Optional
    ensemble_method="average",            # or "median", "weighted"
    calibration_method="isotonic",        # or "platt", "none"
    include_drivers=True                  # Include feature drivers
)
```

### Output Columns

- `prob_over`: Calibrated probability of OVER hitting
- `prob_under`: Probability of UNDER (1 - prob_over)
- `sigma`: Uncertainty (standard deviation)
- `ci_lower`: Lower bound of 90% CI
- `ci_upper`: Upper bound of 90% CI
- `ci_width`: Width of confidence interval
- `drivers`: List of top feature drivers (if requested)

### Ensemble Methods

1. **Average**: Simple mean of model predictions
2. **Median**: Median of model predictions (robust to outliers)
3. **Weighted**: Weighted average by model performance

### Example Workflow

```python
from src.models import estimate_probabilities, train_gbm
from src.features import build_features

# 1. Build features
props_with_features = build_features(
    props_df=raw_props,
    context_data={
        'injuries': injuries_df,
        'weather': weather_df,
        'baseline_stats': baseline_stats
    }
)

# 2. Train model (optional - will use heuristic if None)
if historical_data_available:
    model_dict = train_gbm(historical_data, target='hit')
    models = [model_dict['model']]
else:
    models = None

# 3. Generate predictions
predictions = estimate_probabilities(
    props_df=props_with_features,
    models=models,
    ensemble_method="average",
    calibration_method="isotonic",
    include_drivers=True
)

# 4. Filter by confidence
high_confidence = predictions[predictions['ci_width'] < 0.25]

# 5. Calculate expected value
predictions['ev'] = (
    predictions['prob_over'] * payout_over -
    (1 - predictions['prob_over'])
)
```

## 4. Bayesian Models (Stub)

### Status

Currently a placeholder stub. Full implementation planned for v2.

### Planned Features

- Hierarchical modeling with partial pooling
- Player-level and team-level random effects
- Full posterior distributions for predictions
- Better uncertainty quantification
- Automatic shrinkage for sparse data

### Future Implementation

Will use PyMC for Bayesian inference:

```python
# Planned for v2
import pymc as pm

with pm.Model() as hierarchical_model:
    # Hyperpriors for population
    mu_global = pm.Normal('mu_global', mu=0, sigma=1)
    sigma_global = pm.HalfNormal('sigma_global', sigma=1)

    # Team-level parameters
    mu_team = pm.Normal('mu_team', mu=mu_global, sigma=sigma_global)

    # Player-level parameters (partial pooling)
    mu_player = pm.Normal('mu_player', mu=mu_team, sigma=sigma_team)

    # Likelihood
    p = pm.math.sigmoid(mu_player[player_idx])
    outcome = pm.Bernoulli('outcome', p=p, observed=outcomes)

    # Sample
    trace = pm.sample(2000, tune=1000)
```

## Performance Characteristics

### Model Training

- **LightGBM**: ~0.5-2s for 1000 samples
- **XGBoost**: ~1-3s for 1000 samples
- **Logistic Regression**: ~0.1-0.5s for 1000 samples

### Prediction Latency

- **Per prop**: <1ms
- **Batch of 100 props**: <50ms
- **With calibration**: +5-10ms

### Memory Usage

- **Trained model**: ~1-5 MB
- **Feature matrix (1000 props)**: ~1 MB
- **Predictions**: ~100 KB per 1000 props

## Model Monitoring

### Calibration Drift Detection

Automatically detects when model calibration degrades:

```python
from src.models import CalibrationEvaluator

evaluator = CalibrationEvaluator()
alert = evaluator.check_calibration_alert(
    recent_outcomes=recent_results_df,
    threshold=0.15  # ECE threshold
)

if alert:
    print(f"Alert: {alert['alert_type']}")
    print(f"ECE: {alert['ece']:.4f}")
    print(f"Recommendation: {alert['recommendation']}")
```

### Recommended Actions

If ECE > 0.15:
1. Retrain model with recent data
2. Refit calibration map
3. Increase uncertainty estimates
4. Consider collecting more features

## Best Practices

### Feature Engineering

1. **Normalize features**: Use z-scores for continuous variables
2. **Handle missing values**: Impute with median or mode
3. **Create interactions**: E.g., `pace * passing_volume`
4. **Time-based features**: Recency-weighted averages

### Model Training

1. **Stratified splits**: Ensure balanced target in train/val
2. **Cross-validation**: Use time-series CV for temporal data
3. **Feature selection**: Remove low-importance features
4. **Regularization**: Prevent overfitting on small datasets

### Calibration

1. **Hold-out calibration set**: Separate from training
2. **Regular recalibration**: Weekly or after 50+ new outcomes
3. **Monitor ECE**: Alert if > 0.15
4. **Visualize**: Generate calibration plots regularly

### Uncertainty

1. **Filter by CI width**: Remove high-uncertainty props
2. **Adjust for sample size**: More data = narrower CIs
3. **Communicate clearly**: Show uncertainty ranges to users
4. **Conservative estimates**: Better to underestimate confidence

## Files and Locations

```
src/models/
├── __init__.py           # Exports all functions
├── gbm.py               # Gradient boosting models
├── calibration.py       # Calibration and uncertainty
└── bayes.py            # Bayesian models (stub)

models/
└── gbm_model.pkl       # Saved trained model

reports/
└── calibration_curve.png  # Calibration plot

data/predictions/
└── demo_predictions.csv   # Example predictions
```

## Testing

Run the full test suite:

```bash
source venv/bin/activate
python -m pytest tests/test_models.py -v
```

Run the demonstration:

```bash
python scripts/demo_models.py
```

## Dependencies

Required:
- scikit-learn >= 1.3.0
- numpy >= 1.24.0
- pandas >= 2.0.0
- scipy >= 1.10.0
- matplotlib >= 3.7.0

Optional (for better performance):
- lightgbm >= 4.0.0
- xgboost >= 2.0.0

## Future Enhancements

1. **SHAP values**: For feature driver explanations
2. **Online learning**: Update models incrementally
3. **Multi-task learning**: Joint modeling of correlated props
4. **Deep learning**: Neural networks for complex patterns
5. **Bayesian optimization**: Automated hyperparameter tuning
6. **Ensemble diversity**: Train models on different feature subsets
7. **Conformal prediction**: Distribution-free uncertainty quantification

## References

- Guo et al. (2017): "On Calibration of Modern Neural Networks"
- Kuleshov et al. (2018): "Accurate Uncertainties for Deep Learning"
- Platt (1999): "Probabilistic Outputs for Support Vector Machines"
- Zadrozny & Elkan (2002): "Transforming Classifier Scores into Calibrated Probability Estimates"
