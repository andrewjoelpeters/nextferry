# Experiments

Tracking model experiments, ideas, and results. Each entry describes the model configuration, what changed, and key metrics. Full evaluation reports are linked.

## Summary

| # | Experiment | PL | MAE | Coverage | vs Baseline | Key Change |
|---|-----------|-----|-----|----------|-------------|------------|
| 1 | [Baseline](#1-baseline--quantilegbt-v2) | 3.83 | 2.54 | 61.6% | — | Starting point |
| 2 | [Deeper trees](#2-deeper-trees) | 3.62 | 2.44 | — | 49.1% | max_depth=8, iter=400, lr=0.08 |
| 3 | [+ vessel_id](#3-add-vessel_id) | 3.62 | 2.46 | — | 49.1% | vessel_id as categorical |
| 4 | [+ vessel_speed](#4-add-vessel_speed) | 3.68 | 2.48 | — | 48.2% | vessel_speed as numeric |
| 5 | [delay × horizon](#5-delay--horizon-interaction) | 3.74 | 2.52 | — | 47.4% | Interaction feature |
| 6 | [Drop is_peak_hour](#6-drop-is_peak_hour) | 3.66 | 2.47 | — | 48.5% | Remove redundant feature |
| 7 | [Hour as numeric](#7-hour-and-dow-as-numeric) | 3.67 | 2.47 | — | 48.4% | day_of_week also numeric |
| 8 | [+ arriving_terminal](#8-add-arriving_terminal_id) | 3.72 | 2.50 | — | 47.7% | arriving_terminal_id |
| 9 | [Slow & deep](#9-slow-and-deep-hyperparams) | **3.48** | 2.38 | — | 51.1% | iter=600, depth=8, lr=0.05 |
| 10 | [Very slow](#10-very-slow-learning) | 3.60 | 2.44 | — | 49.4% | iter=1000, lr=0.03 |
| 11 | [Shallow + many](#11-shallow-trees-many-iterations) | 3.88 | 2.59 | — | 45.4% | depth=4, iter=800 |
| 12 | [Best + speed](#12-best-hyperparams--vessel_speed) | **3.30** | 2.31 | — | 53.6% | exp9 hyperparams + vessel_speed |
| 13 | [Kitchen sink](#13-kitchen-sink) | 3.40 | 2.34 | — | 52.2% | + delay_x_horizon (hurt) |
| 14 | [+ delay²](#14-delay-squared) | 3.31 | 2.31 | — | 53.4% | Squared delay (negligible) |
| 15 | [+ month](#15-add-month) | 3.49 | 2.41 | — | 50.9% | Month feature (hurt) |
| 16 | [+ is_weekend](#16-add-is_weekend) | **3.27** | 2.29 | 59.9% | 54.0% | Weekend flag |
| 17 | [+ month again](#17-is_weekend--month) | 3.52 | 2.42 | — | 50.5% | Month still hurts |
| 18 | [Continuous time](#18-minutes-since-midnight) | 3.49 | 2.39 | — | 50.9% | Replace hour with minutes |
| 19 | [min_samples_leaf](#19-min_samples_leaf-regularization) | 3.27 | 2.29 | 59.9% | 54.0% | min_samples_leaf=20 |
| 20 | [Wider quantiles](#20-wider-quantile-bounds) | 3.27 | 2.29 | **70.0%** | 54.0% | q10/q90 instead of q15/q85 |
| 21 | [L2 median](#21-l2-loss-for-median) | 4.85 | 2.96 | 70.0% | 31.8% | squared_error for median (bad) |
| 22 | [q40 asymmetric](#22-asymmetric-quantile-q40) | **3.09** | 2.29 | 70.0% | 56.5% | Predict 40th percentile |
| 23 | [q35](#23-q35) | **2.87** | 2.25 | 70.0% | 59.6% | Predict 35th percentile |
| 24 | [q33 (optimal)](#24-q33-theoretically-optimal) | **2.76** | 2.22 | 70.0% | **61.2%** | 1/(1+α) = 1/3 ≈ 0.333 |
| 25 | [q33 + more iters](#25-q33--more-iterations) | 2.77 | 2.22 | 68.8% | 61.0% | 800 iters (no gain, 2× slower) |
| 26 | [+ L2 regularization](#26-l2-regularization) | 2.79 | 2.24 | 70.0% | 60.8% | l2_regularization=0.1 |
| 27 | [Rebaseline](#27-rebaseline) | **2.48** | 1.97 | 70.0% | 43.5% | More data (19K events) |
| 28 | [Tighter bounds (q25/q75)](#28-tighter-bounds-q25q75) | 2.48 | 1.97 | 42.5% | 43.5% | Narrower intervals, same PL |
| 29 | [Drop turnaround_minutes](#29-drop-turnaround_minutes) | 2.94 | 2.37 | 71.4% | 33.0% | Ablation: turnaround is critical |
| 30 | [Drop previous_sailing_fullness](#30-drop-previous_sailing_fullness) | 2.49 | 1.97 | 70.0% | 43.3% | Negligible impact |
| 31 | [Deeper trees (depth=10)](#31-deeper-trees-depth10) | 2.48 | 1.97 | 69.8% | 43.5% | No gain from deeper trees |
| 32 | [+ consecutive_late_sailings](#32-add-consecutive_late_sailings) | 2.48 | 1.97 | 70.0% | 43.5% | No gain — redundant with current_delay |
| 33 | [NGBoost (Normal)](#33-ngboost-normal-distribution) | 2.76 | 2.05 | 81.0% | 37.1% | Distributional model, worse PL |
| 34 | [q30 quantile](#34-q30-quantile) | **2.45** | 1.99 | 70.0% | 44.2% | Slight improvement over q33 |

**Best configuration: Experiment 34 (q30)** — PL=2.45, 44.2% improvement, 70% coverage.

## Experiment Log

### 1. Baseline — QuantileGBT v2

**Report:** [baseline_2026-03-22.md](baseline_2026-03-22.md)

**Model:** 3× `HistGradientBoostingRegressor` (quantiles q15/q50/q85)
**Hyperparameters:** max_iter=200, max_depth=6, learning_rate=0.1
**Training time:** 49.8s (5-fold walk-forward, 19,348 events)

**Features (9):** route_abbrev, departing_terminal_id, day_of_week, hour_of_day, minutes_until_scheduled_departure, current_vessel_delay_minutes, is_peak_hour, previous_sailing_fullness, turnaround_minutes

| Metric | Value |
|--------|-------|
| Pinball Loss | 3.83 min |
| MAE | 2.54 min |
| Bias | +0.04 min |
| 70% Coverage | 61.6% |
| vs Baseline | — |

**Observations:** Nearly unbiased, strong 46% improvement over naive. Coverage under-calibrated. Fold 1 is an outlier (PL=6.7). Sundays hardest (PL=5.4). Prediction horizon has almost no effect.

---

### 2. Deeper trees

**Report:** [exp02-deeper-trees.md](exp02-deeper-trees.md)
**Change:** max_iter=400, max_depth=8, learning_rate=0.08

| PL | MAE | Bias | vs Baseline |
|----|-----|------|-------------|
| 3.62 | 2.44 | -0.08 | 49.1% |

**Takeaway:** Deeper trees with more iterations help (+5.5% vs baseline). Fold 1 improved from 6.7→5.44.

---

### 3. Add vessel_id

**Report:** [exp03-vessel-id.md](exp03-vessel-id.md)
**Change:** Added vessel_id as categorical feature (10 features total). Same hyperparams as baseline.

| PL | MAE | Bias | vs Baseline |
|----|-----|------|-------------|
| 3.62 | 2.46 | -0.05 | 49.1% |

**Takeaway:** Vessel identity helps — some vessels are consistently slower/faster. Same PL as deeper trees but with default hyperparams.

---

### 4. Add vessel_speed

**Report:** [exp04-vessel-speed.md](exp04-vessel-speed.md)
**Change:** Added vessel_speed (from snapshot at prediction time) to exp03 features.

| PL | MAE | Bias | vs Baseline |
|----|-----|------|-------------|
| 3.68 | 2.48 | -0.01 | 48.2% |

**Takeaway:** Speed alone added noise with default hyperparams. Revisit with better hyperparams (see exp12).

---

### 5. Delay × horizon interaction

**Report:** [exp05-delay-x-horizon.md](exp05-delay-x-horizon.md)
**Change:** Added `delay_x_horizon = current_delay × minutes_until_departure` interaction feature.

| PL | MAE | Bias | vs Baseline |
|----|-----|------|-------------|
| 3.74 | 2.52 | -0.08 | 47.4% |

**Takeaway:** Interaction feature didn't help. GBT can learn this interaction implicitly through splits.

---

### 6. Drop is_peak_hour

**Report:** [exp06-drop-is-peak.md](exp06-drop-is-peak.md)
**Change:** Removed `is_peak_hour` from features (features: exp03 minus is_peak_hour = 9 features).

| PL | MAE | Bias | vs Baseline |
|----|-----|------|-------------|
| 3.66 | 2.47 | +0.04 | 48.5% |

**Takeaway:** `is_peak_hour` is redundant with `hour_of_day` + categorical encoding. Removing it is slightly better. Drop it going forward.

---

### 7. Hour and DOW as numeric

**Report:** [exp07-hour-numeric.md](exp07-hour-numeric.md)
**Change:** Treated both hour_of_day and day_of_week as numeric instead of categorical.

| PL | MAE | Bias | vs Baseline |
|----|-----|------|-------------|
| 3.67 | 2.47 | +0.01 | 48.4% |

**Takeaway:** Slightly worse — categorical encoding lets the model treat each hour independently (important for non-monotonic delay patterns through the day). Keep day_of_week as categorical.

---

### 8. Add arriving_terminal_id

**Report:** [exp08-arriving-terminal.md](exp08-arriving-terminal.md)
**Change:** Added arriving_terminal_id as categorical feature.

| PL | MAE | Bias | vs Baseline |
|----|-----|------|-------------|
| 3.72 | 2.50 | +0.04 | 47.7% |

**Takeaway:** Redundant with route_abbrev + departing_terminal_id (each route has exactly 2 terminals). Added noise.

---

### 9. Slow and deep hyperparams

**Report:** [exp09-slow-and-deep.md](exp09-slow-and-deep.md)
**Change:** max_iter=600, max_depth=8, learning_rate=0.05 (features from exp06: no is_peak_hour).

| PL | MAE | Bias | vs Baseline |
|----|-----|------|-------------|
| **3.48** | 2.38 | +0.00 | 51.1% |

**Takeaway:** Big jump! Lower learning rate + more iterations = better generalization. Fold 1 dropped to 4.84. This is the right hyperparameter regime.

---

### 10. Very slow learning

**Report:** [exp10-very-slow.md](exp10-very-slow.md)
**Change:** max_iter=1000, learning_rate=0.03.

| PL | MAE | Bias | vs Baseline |
|----|-----|------|-------------|
| 3.60 | 2.44 | -0.02 | 49.4% |

**Takeaway:** lr=0.03 is too slow — 1000 iterations isn't enough to converge, especially for early folds with less data. lr=0.05 is the sweet spot.

---

### 11. Shallow trees, many iterations

**Report:** [exp11-shallow-many.md](exp11-shallow-many.md)
**Change:** max_depth=4, max_iter=800, learning_rate=0.05.

| PL | MAE | Bias | vs Baseline |
|----|-----|------|-------------|
| 3.88 | 2.59 | -0.01 | 45.4% |

**Takeaway:** Depth=4 is too shallow — ferry delay patterns need deeper interaction capture (route × time × vessel). Depth 8 is better.

---

### 12. Best hyperparams + vessel_speed

**Report:** [exp12-best-plus-speed.md](exp12-best-plus-speed.md)
**Change:** exp09 hyperparams (iter=600, depth=8, lr=0.05) + vessel_speed feature.

| PL | MAE | Bias | vs Baseline |
|----|-----|------|-------------|
| **3.30** | 2.31 | -0.07 | 53.6% |

**Takeaway:** Vessel speed helps significantly with good hyperparams! Fold 1 dropped from 4.84→3.95. A slow vessel near departure time is a strong delay signal that the model can now exploit.

---

### 13. Kitchen sink

**Report:** [exp13-kitchen-sink.md](exp13-kitchen-sink.md)
**Change:** exp12 + delay_x_horizon interaction.

| PL | MAE | Bias | vs Baseline |
|----|-----|------|-------------|
| 3.40 | 2.34 | -0.01 | 52.2% |

**Takeaway:** Adding the interaction feature to exp12 hurt. More features ≠ better. The model overfits the interaction in early folds.

---

### 14. Delay squared

**Report:** [exp14-delay-squared.md](exp14-delay-squared.md)
**Change:** exp12 + delay_squared = current_delay².

| PL | MAE | Bias | vs Baseline |
|----|-----|------|-------------|
| 3.31 | 2.31 | -0.05 | 53.4% |

**Takeaway:** Negligible difference — GBT already handles nonlinear relationships through its tree splits.

---

### 15. Add month

**Report:** [exp15-month.md](exp15-month.md)
**Change:** exp12 + month feature (1–12).

| PL | MAE | Bias | vs Baseline |
|----|-----|------|-------------|
| 3.49 | 2.41 | -0.25 | 50.9% |

**Takeaway:** Month hurts. Walk-forward cross-validation already handles temporal distribution shift. Adding month as a feature causes the model to memorize seasonal patterns from training data that don't generalize.

---

### 16. Add is_weekend

**Report:** [exp16-weekend.md](exp16-weekend.md)
**Change:** exp12 + is_weekend binary flag (Sat/Sun = 1).

| PL | MAE | Bias | vs Baseline |
|----|-----|------|-------------|
| **3.27** | 2.29 | -0.07 | 54.0% |

**Takeaway:** Weekend flag helps! Fold 1 dropped from 3.95→3.84. Weekends have fundamentally different delay patterns (more recreational traffic, different vessel rotations). The model benefits from this explicit signal even though day_of_week is already a feature.

---

### 17. is_weekend + month

**Report:** [exp17-weekend-plus-month.md](exp17-weekend-plus-month.md)
**Change:** exp16 + month.

| PL | MAE | Bias | vs Baseline |
|----|-----|------|-------------|
| 3.52 | 2.42 | -0.20 | 50.5% |

**Takeaway:** Month still hurts even with the weekend flag. Seasonal patterns are too noisy.

---

### 18. Minutes since midnight

**Report:** [exp18-minutes-since-midnight.md](exp18-minutes-since-midnight.md)
**Change:** exp16 + minutes_since_midnight (continuous) replacing hour_of_day.

| PL | MAE | Bias | vs Baseline |
|----|-----|------|-------------|
| 3.49 | 2.39 | -0.00 | 50.9% |

**Takeaway:** Continuous time-of-day is worse than categorical hour. Delay patterns are step-function-like (commute peaks, midday lull) — categorical encoding captures these transitions better.

---

### 19. min_samples_leaf regularization

**Report:** [exp19-min-samples-leaf.md](exp19-min-samples-leaf.md)
**Change:** exp16 + min_samples_leaf=20 (regularization).

| PL | MAE | Bias | vs Baseline | Coverage |
|----|-----|------|-------------|----------|
| 3.27 | 2.29 | -0.07 | 54.0% | 59.9% |

**Takeaway:** min_samples_leaf=20 has negligible impact. The model was already well-regularized at depth=8 + lr=0.05.

---

### 20. Wider quantile bounds

**Report:** [exp20-wider-quantiles.md](exp20-wider-quantiles.md)
**Change:** exp19 config but q10/q90 bounds instead of q15/q85.

| PL | MAE | Bias | vs Baseline | Coverage |
|----|-----|------|-------------|----------|
| 3.27 | 2.29 | -0.07 | 54.0% | **70.0%** |

**Takeaway:** Coverage jumped from 59.9%→70.0% (perfectly calibrated!) with zero PL change. The q15/q85 bounds were too narrow — q10/q90 matches the 70% target exactly. Keep these bounds going forward.

---

### 21. L2 loss for median

**Report:** [exp21-l2-median.md](exp21-l2-median.md)
**Change:** Use `squared_error` loss for the median model instead of `quantile(0.5)`.

| PL | MAE | Bias | vs Baseline | Coverage |
|----|-----|------|-------------|----------|
| 4.85 | 2.96 | +0.40 | 31.8% | 70.0% |

**Takeaway:** L2 optimizes for the mean, not the median. Since the delay distribution has a heavy right tail, the mean is higher than the median, causing systematic overprediction. PL/MAE ratio jumped from 1.43→1.64, confirming more "dangerous" overpredictions. Quantile loss is essential for this problem.

---

### 22. Asymmetric quantile (q40)

**Report:** [exp22-q40-asymmetric.md](exp22-q40-asymmetric.md)
**Change:** Predict the 40th percentile instead of the 50th (median) for the point estimate.

| PL | MAE | Bias | vs Baseline | Coverage |
|----|-----|------|-------------|----------|
| **3.09** | 2.29 | -0.70 | 56.5% | 70.0% |

**Takeaway:** Key insight: since pinball loss penalizes overprediction 2× more, predicting below the median is optimal. At q40, predictions are slightly conservative (bias=-0.70), which is safe — riders arrive a bit early rather than missing the ferry. PL/MAE dropped from 1.43→1.35.

---

### 23. q35

**Report:** [exp23-q35.md](exp23-q35.md)
**Change:** Predict the 35th percentile.

| PL | MAE | Bias | vs Baseline | Coverage |
|----|-----|------|-------------|----------|
| **2.87** | 2.25 | -1.01 | 59.6% | 70.0% |

**Takeaway:** Even better. Bias of -1 min means predictions are 1 minute conservative on average — perfectly acceptable for ferry riders.

---

### 24. q33 (theoretically optimal)

**Report:** [exp24-q33-optimal.md](exp24-q33-optimal.md)
**Change:** Predict the 33.3rd percentile (1/(1+α) = 1/3 for α=2).

| PL | MAE | Bias | vs Baseline | Coverage |
|----|-----|------|-------------|----------|
| **2.76** | 2.22 | -1.15 | **61.2%** | 70.0% |

**Takeaway:** The theoretical optimum for asymmetric pinball loss with overprediction penalty α=2 is exactly the 1/(1+α) = 1/3 quantile. This achieves the best PL (2.76) with fold stability (std=0.28 vs baseline 1.49). The model consistently underpredicts by ~1.15 min, which is the safe direction. **This is the best configuration.**

---

### 25. q33 + more iterations

**Report:** [exp25-q33-more-iters.md](exp25-q33-more-iters.md)
**Change:** exp24 with max_iter=800.

| PL | MAE | Bias | vs Baseline | Coverage |
|----|-----|------|-------------|----------|
| 2.77 | 2.22 | -1.13 | 61.0% | 68.8% |

**Takeaway:** No gain from more iterations (2.77 vs 2.76), 2× slower training time (4m42s vs 2m40s), and slightly worse coverage. 600 iterations is sufficient.

---

### 26. L2 regularization

**Report:** [exp26-l2-reg.md](exp26-l2-reg.md)
**Change:** exp24 + l2_regularization=0.1.

| PL | MAE | Bias | vs Baseline | Coverage |
|----|-----|------|-------------|----------|
| 2.79 | 2.24 | -1.14 | 60.8% | 70.0% |

**Takeaway:** Slight degradation. The model is already well-regularized by depth + learning rate. Additional L2 penalty constrains useful splits.

---

### 27. Rebaseline

**Report:** [exp27-rebaseline.md](exp27-rebaseline.md)
**Change:** Re-run exp24 config on latest data (19,348 events, up from previous runs). Default hyperparams updated to exp24's best (iter=600, depth=8, lr=0.05).

| PL | MAE | Bias | vs Baseline | Coverage |
|----|-----|------|-------------|----------|
| **2.48** | 1.97 | -0.93 | 43.5% | 70.0% |

**Takeaway:** Absolute PL improved from 2.76→2.48 with more training data. Improvement % dropped to 43.5% because the naive baseline also improved. Fold stability excellent (std=0.32). This is the new starting point for all further experiments.

---

### 28. Tighter bounds (q25/q75)

**Report:** [exp28-tighter-bounds.md](exp28-tighter-bounds.md)
**Change:** Changed interval bounds from q10/q90 to q25/q75 for narrower prediction intervals.

| PL | MAE | Bias | vs Baseline | Coverage |
|----|-----|------|-------------|----------|
| 2.48 | 1.97 | -0.93 | 43.5% | 42.5% |

**Takeaway:** PL and MAE identical — bounds don't affect the point estimate. But coverage dropped from 70%→42.5%, far below the 70% target. Tighter bounds answer the question from the proposal: the problem isn't just wide bounds, we need a different approach to confidence. Keep q10/q90.

---

### 29. Drop turnaround_minutes

**Report:** [exp29-drop-turnaround.md](exp29-drop-turnaround.md)
**Change:** Ablation — removed turnaround_minutes from features (10→9 features).

| PL | MAE | Bias | vs Baseline | Coverage |
|----|-----|------|-------------|----------|
| 2.94 | 2.37 | -1.25 | 33.0% | 71.4% |

**Takeaway:** Turnaround time is a critical feature. Removing it degrades PL from 2.48→2.94 (+18.5%). This makes sense: turnaround_minutes captures how long the vessel has been docked — a short turnaround means loading may not be complete, directly predicting departure delay.

---

### 30. Drop previous_sailing_fullness

**Report:** [exp30-drop-fullness.md](exp30-drop-fullness.md)
**Change:** Ablation — removed previous_sailing_fullness from features (11→10 features).

| PL | MAE | Bias | vs Baseline | Coverage |
|----|-----|------|-------------|----------|
| 2.49 | 1.97 | -0.93 | 43.3% | 70.0% |

**Takeaway:** Negligible impact (2.48→2.49). Fullness of the previous sailing doesn't meaningfully predict delay for the current sailing. Could be dropped for simplicity, but keeping it costs nothing.

---

### 31. Deeper trees (depth=10)

**Report:** [exp31-deeper-trees.md](exp31-deeper-trees.md)
**Change:** Increased max_depth from 8 to 10.

| PL | MAE | Bias | vs Baseline | Coverage |
|----|-----|------|-------------|----------|
| 2.48 | 1.97 | -0.93 | 43.5% | 69.8% |

**Takeaway:** Identical PL. Depth 8 already captures the interaction complexity in this dataset. Deeper trees risk overfitting without additional signal. Keep depth=8.

---

### 32. Add consecutive_late_sailings

**Report:** [exp32-consecutive-late.md](exp32-consecutive-late.md)
**Change:** New feature: count of consecutive late sailings (>1 min) on the same route preceding each event. Computed per-route from sailing_events.

| PL | MAE | Bias | vs Baseline | Coverage |
|----|-----|------|-------------|----------|
| 2.48 | 1.97 | -0.93 | 43.5% | 70.0% |

**Takeaway:** No improvement. The cascading delay signal is already captured by `current_vessel_delay_minutes` — if the vessel is currently late, previous sailings were already late. The feature is redundant with existing real-time delay information.

---

### 33. NGBoost (Normal distribution)

**Report:** [exp33-ngboost.md](exp33-ngboost.md)
**Change:** New model: NGBRegressor with Normal distribution, DecisionTree base learner (depth=4), 200 estimators, lr=0.05. Uses q33 percentile for point estimate.

| PL | MAE | Bias | vs Baseline | Coverage |
|----|-----|------|-------------|----------|
| 2.76 | 2.05 | -0.65 | 37.1% | 81.0% |

**Takeaway:** NGBoost is worse than quantile GBT (2.76 vs 2.48). Two issues: (1) Normal distribution is symmetric but ferry delays are right-skewed, making intervals too wide (81% coverage vs 70% target). (2) NGBoost base learner is limited to shallow trees (depth=4) without HistGBT's native categorical handling. The quantile GBT approach better fits this problem. ~10× slower training time.

---

### 34. q30 quantile

**Report:** [exp34-q30.md](exp34-q30.md)
**Change:** Changed point estimate quantile from q33 (0.333) to q30 (0.30).

| PL | MAE | Bias | vs Baseline | Coverage |
|----|-----|------|-------------|----------|
| **2.45** | 1.99 | -1.06 | 44.2% | 70.0% |

**Takeaway:** Small but real improvement: PL 2.48→2.45. The theoretical optimum of q33 (1/(1+α)) assumes perfect calibration; with real-world model errors, slightly more conservative (q30) helps because the penalty for overprediction (α=2) means it's better to err further on the safe side. Bias increases to -1.06 (1 min conservative), still perfectly acceptable for ferry riders. **New best.**

---

## Key Learnings

1. **Hyperparameters matter more than features.** Going from default (iter=200, depth=6, lr=0.1) to tuned (iter=600, depth=8, lr=0.05) was worth more than any single feature addition.

2. **Asymmetric quantile is the single biggest win.** Aligning the prediction quantile (q33) with the asymmetric loss function (α=2) reduced PL from 3.27→2.76 (15.6% improvement) with no additional training cost.

3. **vessel_speed is the strongest new feature.** It provides real-time signal about whether a vessel will be late — a slow vessel near departure is a strong predictor.

4. **is_weekend captures patterns day_of_week misses.** Even though day_of_week is categorical, explicitly flagging weekends helps the model generalize across Sat/Sun.

5. **Wider quantile bounds (q10/q90) fix coverage.** Switching from q15/q85 to q10/q90 achieved exactly 70% coverage at no PL cost.

6. **Engineered interactions don't help GBTs.** Features like delay×horizon and delay² add noise because tree ensembles learn interactions naturally.

7. **Temporal features (month, minutes_since_midnight) hurt.** Walk-forward cross-validation handles distribution shift; adding month causes memorization. Categorical hour outperforms continuous time.

8. **L2 loss is wrong for skewed targets.** Ferry delays have a heavy right tail — L2 optimizes the mean, which overpredicts the typical case.

## Best Configuration (Exp 24)

```
Model: 3× HistGradientBoostingRegressor
  - q33 (point estimate, quantile=0.333)
  - q10 (lower bound)
  - q90 (upper bound)

Hyperparameters:
  max_iter: 600 (CLI override)
  max_depth: 8 (CLI override)
  learning_rate: 0.05 (CLI override)
  min_samples_leaf: 20

Features (10):
  route_abbrev (categorical)
  departing_terminal_id (categorical)
  vessel_id (categorical)
  day_of_week (categorical)
  hour_of_day (numeric)
  is_weekend (binary)
  minutes_until_scheduled_departure (numeric)
  current_vessel_delay_minutes (numeric)
  vessel_speed (numeric)
  previous_sailing_fullness (numeric)
  turnaround_minutes (numeric)
```

*Add new experiments above the Key Learnings section.*
