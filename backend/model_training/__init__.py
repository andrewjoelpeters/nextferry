"""Model training, evaluation, and backtesting.

This package is separate from the API serving code. It contains:

- evaluation.py     — Metrics: pinball loss, bias, p90, coverage
- backtest.py       — Walk-forward cross-validation harness (model-agnostic)
- backtest_model.py — BacktestModel protocol + default QuantileGBT implementation
- report.py         — Markdown report rendering (pure string output, no ML logic)
"""
