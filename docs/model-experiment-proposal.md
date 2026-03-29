# ML Model Experiment Proposal: Confidence Scores & Distributional Models

## Problem

The current delay prediction uses three independent quantile regressors (q10/q50/q90) to produce a point estimate and confidence interval. Two problems:

1. **Intervals are too wide to be useful.** The q10–q90 bounds span an 80% prediction interval. For a typical "2 min delay" prediction, bounds might be "-3 to +12m" — not actionable for users.
2. **The three models don't know about each other.** They can produce incoherent intervals (bounds crossing at edge cases), and there's no principled way to derive a confidence score.

The real-world problem has natural structure the current approach doesn't capture: there's a **floor** (the boat can't leave before time X), then a monotonically increasing probability of departure after that. This is a survival/time-to-event problem.

## Current State

- `backtest_model.py:125` trains q50 (actually at quantile=0.333), q10, q90
- `predict_single()` returns `{predicted_delay, lower_bound, upper_bound}`
- `display_processing.py` computes `confidence_text` (e.g., "(+1 to +5m)") but **no template renders it**
- `evaluation.py` tracks pinball loss, bias, p90, coverage, and interval width

## Models to Test

Each model implements the existing `BacktestModel` protocol (`fit(train_df)` → `predict(test_df)` returning `predicted_delay`, `lower_bound`, `upper_bound`), so the harness, evaluation, and reporting stay untouched.

### Model D: Tighter Quantile GBT (Incremental Baseline)

Change quantiles from q10/q90 to q25/q75. Minimal code change, immediately narrower intervals. Answers the question: "Is the problem just that our bounds are too wide, or do we need a different model class?"

### Model A: Log-Normal AFT (Accelerated Failure Time)

Models `time_from_floor_to_departure` as a log-normal distribution. Produces a full CDF per prediction — `sigma` is a direct confidence measure. Highly explainable (feature coefficients). May underfit nonlinear patterns. Library: `lifelines`.

### Model B: NGBoost (Natural Gradient Boosting)

Gradient boosting that fits a log-normal distribution per prediction, jointly optimizing location and scale. Best of both worlds — nonlinear power of GBT + coherent distributional output. The strongest candidate. Library: `ngboost`.

### Model C: Survival GBT (scikit-survival)

Full survival analysis — models the hazard function directly. Most theoretically correct for "hasn't departed yet → departs at time T", but most complex to integrate. Only pursue if NGBoost doesn't capture the survival framing's benefits.

### Feature Ideas

| Feature | Rationale | Source |
|---------|-----------|--------|
| `consecutive_late_sailings` | Cascading delays are the #1 cause of large delays | `sailing_events` table |
| `time_since_last_departure` | Previous sailing left late → turnaround behind | `sailing_events` + `vessel_snapshots` |
| `is_holiday` | Different traffic patterns | Static calendar |

Test features independently from model changes — one variable at a time.

## How to Run Experiments

### Key Rule: One Experiment = One Backtest + One Report + One Commit

Every experiment must be self-contained and traceable. Do not combine model changes, feature changes, or hyperparameter changes in a single run.

### Experiment Workflow

```bash
# 1. Make your change (new model class, feature, or hyperparam tweak)
#    Edit backtest_model.py (or a new file imported there)

# 2. Run the backtest
uv run python -m backend.model_training.backtest \
  --name "experiment_name" \
  --description "What changed and why" \
  --compare reports/baseline.md \
  --output-dir reports

# 3. Review the report
#    Check: pinball loss, coverage, interval width, stability across folds
#    The --compare flag produces delta tables vs the baseline

# 4. Commit the model change + report together
git add backend/model_training/your_changes.py reports/experiment_name_*.md
git commit -m "Experiment: description of what changed"

# 5. Repeat from step 1 for the next experiment
```

### Experiment Sequence

Run these in order. Each step builds on the previous and compares against the baseline.

| # | Experiment | What to change | Compare against |
|---|-----------|----------------|-----------------|
| 0 | **Baseline** | Nothing — run current `QuantileGBTModel` as-is | — |
| 1 | **Tighter quantiles (Model D)** | Change q10/q90 → q25/q75 in `backtest_model.py:125` | `reports/baseline.md` |
| 2 | **Log-Normal AFT (Model A)** | New `LogNormalAFTModel` class | `reports/baseline.md` |
| 3 | **NGBoost (Model B)** | New `NGBoostModel` class | `reports/baseline.md` |
| 4 | **Best model + `consecutive_late_sailings`** | Add feature to winner from 1-3 | Winner's report |

### What Files to Change vs. Leave Alone

**Change per experiment:**

| File | What to change |
|------|---------------|
| `backend/model_training/backtest_model.py` | New model class implementing `BacktestModel` protocol |
| `backend/model_training/at_dock_model.py` | At-dock variant (if applicable) |

**Never change during experiments:**

| File | Why |
|------|-----|
| `backend/model_training/backtest.py` | Walk-forward CV harness — model-agnostic |
| `backend/model_training/evaluation.py` | Metrics framework — shared across all experiments |
| `backend/model_training/report.py` | Report rendering — shared across all experiments |
| `backend/ml_predictor.py` | Serving layer — only touch when wiring in the winning model |
| `backend/dock_predictor.py` | At-dock serving layer — same |

### Implementing a New Model

Each model is a class that implements the `BacktestModel` protocol:

```python
class MyNewModel:
    def fit(self, train_df: pd.DataFrame) -> None:
        """Train on raw training data. All feature engineering happens here."""
        ...

    def predict(self, test_df: pd.DataFrame) -> pd.DataFrame:
        """Return test_df with three new columns added:
        predicted_delay, lower_bound, upper_bound (all in minutes)."""
        ...
```

Pass it to the backtest via a factory:

```python
# In backtest_model.py or a new module
from backend.model_training.backtest import run_backtest

run_backtest(
    model_factory=MyNewModel,
    experiment_name="my_experiment",
    description="Testing NGBoost with log-normal distribution",
    compare_path="reports/baseline.md",
    output_dir="reports",
)
```

Or from the CLI by modifying `backtest.py`'s `__main__` to accept a `--model` flag (but don't change the harness logic).

### Metrics to Watch

| Metric | What it tells you | Good value |
|--------|------------------|------------|
| **Pinball Loss** | Accuracy with 2x penalty for overprediction | Lower is better |
| **Bias** | Systematic direction of errors | ~0, slightly negative = safe |
| **Coverage** | % of actuals within [lower, upper] | Should match quantile spread |
| **Mean Interval Width** | How wide the bounds are | Narrower is better (given coverage) |
| **Fold Stability (std)** | Consistency across time periods | Low std = robust model |

The winning model should improve interval width without degrading pinball loss.

## End State for Users

Once we have a model with coherent, narrow confidence intervals:

1. **Confidence label:** "High / Medium / Low confidence" based on sigma or interval width
2. **Probability statement:** "80% chance the boat departs by 3:47 PM" (from the CDF)
3. **Fallback rule:** If confidence is low, show flat propagation instead of a misleading ML prediction
4. **Explainability:** "Predicted late because the previous sailing departed 8 minutes behind schedule" — feasible with SHAP or AFT coefficients
