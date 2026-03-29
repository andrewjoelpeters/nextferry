"""Markdown report rendering for backtest results.

Pure string output — no ML logic, no pandas, no numpy. Takes dicts of
metrics and renders them as markdown tables. This module never imports
sklearn or touches DataFrames.
"""

import json
import re
from datetime import datetime

from .evaluation import OVERPREDICTION_PENALTY


def _natural_sort_key(key: str):
    """Sort key that orders leading numbers numerically (e.g. '2–4m' before '10–14m')."""
    match = re.match(r"(\d+)", key)
    if match:
        return (0, int(match.group(1)), key)
    return (1, 0, key)


def _metric_table(data: dict, key_label: str) -> list:
    """Render a dict of {label: metrics} as a markdown table."""
    has_width = any("mean_interval_width" in m for m in data.values())
    lines = []
    if has_width:
        lines.append(f"| {key_label} | Pinball Loss | Bias | p90 | Interval Width | N |")
        lines.append("|---|---|---|---|---|---|")
    else:
        lines.append(f"| {key_label} | Pinball Loss | Bias | p90 | N |")
        lines.append("|---|---|---|---|---|")
    for label, m in sorted(data.items(), key=lambda x: _natural_sort_key(x[0])):
        if has_width:
            width = m.get("mean_interval_width", "—")
            lines.append(
                f"| {label} | {m['pinball_loss']} | {m['bias']:+.2f} | "
                f"{m['error_p90']:+.2f} | {width} | {m['n']} |"
            )
        else:
            lines.append(
                f"| {label} | {m['pinball_loss']} | {m['bias']:+.2f} | "
                f"{m['error_p90']:+.2f} | {m['n']} |"
            )
    return lines


def _delta_str(prev_val, curr_val, lower_is_better=True):
    d = curr_val - prev_val
    if d == 0:
        return "0.00 (no change)"
    sign = "+" if d > 0 else ""
    better = (d < 0) if lower_is_better else (d > 0)
    return f"{sign}{d:.2f} ({'better' if better else 'worse'})"


def generate_markdown_report(
    backtest_results: dict,
    experiment_name: str = "unnamed",
    description: str = "",
    comparison: dict | None = None,
) -> str:
    """Generate a markdown report from backtest results dicts."""
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    agg = backtest_results["aggregate"]
    stab = backtest_results["stability"]

    # ---- Header ----
    lines.append(f"# Backtest Report: {experiment_name}")
    lines.append("")
    if description:
        lines.append(f"> {description}")
        lines.append("")
    lines.append(f"**Date:** {now}  ")
    lines.append(f"**Sailing events:** {backtest_results['n_total_events']}  ")
    lines.append(f"**Walk-forward folds:** {backtest_results['n_folds']}  ")
    training_time = backtest_results.get("training_time_seconds")
    if training_time is not None:
        minutes, seconds = divmod(training_time, 60)
        if minutes >= 1:
            lines.append(f"**Training time:** {int(minutes)}m {int(seconds)}s")
        else:
            lines.append(f"**Training time:** {training_time}s")
    lines.append("")

    # ---- TOP-LINE ----
    pl = agg["overall_pinball_loss"]
    mae = agg["overall_mae"]
    bias = agg["overall_bias"]
    pl_ratio = round(pl / max(mae, 0.01), 2)

    lines.append("## Top-Line Results")
    lines.append("")
    lines.append(
        f"> **Pinball Loss** is an asymmetric MAE (α={OVERPREDICTION_PENALTY}): "
        f"overprediction is penalized {OVERPREDICTION_PENALTY}× more than underprediction.  "
    )
    lines.append(
        f"> PL / MAE = {pl_ratio}× — closer to 1.0 means errors are mostly safe "
        f"(underprediction); closer to {OVERPREDICTION_PENALTY}.0 means mostly dangerous."
    )
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| **Pinball Loss** | **{pl} min** (PL/MAE = {pl_ratio}×) |")
    lines.append(f"| MAE | {mae} min |")
    lines.append(f"| Bias | {bias:+.2f} min |")
    lines.append(f"| p90 (tail risk) | {agg['overall_error_p90']:+.2f} min |")
    lines.append(
        f"| 70% Interval Coverage | {agg['overall_coverage_70pct']}% (target: 70%) |"
    )
    if "overall_mean_interval_width" in agg:
        lines.append(
            f"| Interval Width (mean) | {agg['overall_mean_interval_width']} min |"
        )
        lines.append(
            f"| Interval Width (median) | {agg['overall_median_interval_width']} min |"
        )
    if "overall_baseline_pinball_loss" in agg:
        lines.append(
            f"| Baseline Pinball Loss | {agg['overall_baseline_pinball_loss']} min |"
        )
        lines.append(f"| Improvement vs baseline | {agg['overall_improvement_pct']}% |")
    lines.append("")

    # ---- Comparison ----
    if comparison:
        lines.extend(_comparison_section(agg, comparison))

    # ---- Stability ----
    lines.append("## Walk-Forward Stability")
    lines.append("")
    lines.append("| Fold | Train | Test | Pinball Loss | Bias | p90 |")
    lines.append("|------|-------|------|--------------|------|-----|")
    for f in backtest_results["fold_results"]:
        lines.append(
            f"| {f['fold']} | {f['n_train_events']} | {f.get('n_test_events', '?')} | "
            f"{f['overall_pinball_loss']} | {f['overall_bias']:+.2f} | "
            f"{f['overall_error_p90']:+.2f} |"
        )
    lines.append("")

    lines.append("| Metric | Mean | Std Dev |")
    lines.append("|--------|------|---------|")
    for key, label in [
        ("pinball_loss", "Pinball Loss"),
        ("bias", "Bias"),
        ("error_p90", "p90"),
    ]:
        s = stab.get(key)
        if s:
            lines.append(f"| {label} | {s['mean']} | ±{s['std']} |")
    lines.append("")

    # ---- Breakdowns ----
    for section_key, section_title, key_label in [
        ("by_route", "By Route", "Route"),
        ("by_day_of_week", "By Day of Week", "Day"),
        ("by_time_of_day", "By Time of Day", "Period"),
        ("by_month", "By Month", "Month"),
        ("by_horizon", "By Prediction Horizon", "Horizon"),
        ("by_route_x_peak", "Route x Peak vs Off-Peak", "Route (period)"),
    ]:
        data = agg.get(section_key)
        if data:
            lines.append(f"## {section_title}")
            lines.append("")
            lines.extend(_metric_table(data, key_label))
            lines.append("")

    # ---- Feature Importance ----
    feature_importance = backtest_results.get("feature_importance")
    if feature_importance:
        lines.extend(_feature_importance_section(feature_importance))

    # ---- Raw JSON ----
    lines.append("## Raw Results (JSON)")
    lines.append("")
    lines.append("<details>")
    lines.append("<summary>Click to expand</summary>")
    lines.append("")
    lines.append("```json")
    exportable = {
        "aggregate": agg,
        "stability": stab,
        "n_total_events": backtest_results["n_total_events"],
        "n_folds": backtest_results["n_folds"],
    }
    lines.append(json.dumps(exportable, indent=2))
    lines.append("```")
    lines.append("")
    lines.append("</details>")
    lines.append("")

    return "\n".join(lines)


def _comparison_section(agg: dict, prev: dict) -> list:
    lines = []
    lines.append("## Comparison vs Previous Run")
    lines.append("")
    lines.append("| Metric | Previous | Current | Delta |")
    lines.append("|--------|----------|---------|-------|")

    for label, key, suffix, lower_is_better in [
        ("Pinball Loss", "overall_pinball_loss", " min", True),
        ("MAE", "overall_mae", " min", True),
        ("p90", "overall_error_p90", " min", True),
        ("Coverage", "overall_coverage_70pct", "%", False),
        ("Interval Width", "overall_mean_interval_width", " min", True),
        ("Improvement %", "overall_improvement_pct", "%", False),
    ]:
        p, c = prev.get(key), agg.get(key)
        if p is not None and c is not None:
            lines.append(
                f"| {label} | {p}{suffix} | {c}{suffix} | "
                f"{_delta_str(p, c, lower_is_better)} |"
            )

    # Per-route comparison
    prev_routes = prev.get("by_route", {})
    curr_routes = agg.get("by_route", {})
    all_routes = sorted(set(prev_routes) | set(curr_routes))
    if all_routes:
        lines.append("")
        lines.append("### Per-Route Comparison")
        lines.append("")
        lines.append("| Route | Prev PL | Curr PL | Prev p90 | Curr p90 | PL Delta |")
        lines.append("|-------|---------|---------|----------|----------|----------|")
        for r in all_routes:
            pp = prev_routes.get(r, {}).get("pinball_loss", "—")
            cp = curr_routes.get(r, {}).get("pinball_loss", "—")
            pp90 = prev_routes.get(r, {}).get("error_p90", "—")
            cp90 = curr_routes.get(r, {}).get("error_p90", "—")
            delta = (
                _delta_str(pp, cp)
                if isinstance(pp, (int, float)) and isinstance(cp, (int, float))
                else "—"
            )
            pp90_s = f"{pp90:+.2f}" if isinstance(pp90, (int, float)) else pp90
            cp90_s = f"{cp90:+.2f}" if isinstance(cp90, (int, float)) else cp90
            lines.append(f"| {r} | {pp} | {cp} | {pp90_s} | {cp90_s} | {delta} |")

    lines.append("")
    return lines


def _feature_importance_section(feature_importance: dict) -> list:
    """Render permutation importance tables (overall + per route)."""
    lines = []
    lines.append("## Feature Importance (Permutation)")
    lines.append("")

    overall = feature_importance.get("overall", [])
    if overall:
        max_imp = max(f["importance"] for f in overall) if overall else 1
        lines.append("| Feature | Importance | |")
        lines.append("|---|---|---|")
        for f in overall:
            bar_len = int(f["importance"] / max_imp * 20) if max_imp > 0 else 0
            bar = "█" * bar_len
            lines.append(f"| {f['feature']} | {f['importance']:.4f} | {bar} |")
        lines.append("")

    # Per-route tables
    route_keys = [k for k in sorted(feature_importance) if k != "overall"]
    if route_keys:
        lines.append("### By Route")
        lines.append("")
        # Side-by-side header
        lines.append("| Feature | " + " | ".join(route_keys) + " |")
        lines.append("|---|" + "|".join(["---"] * len(route_keys)) + "|")

        # Build lookup: route -> {feature: importance}
        route_maps = {}
        for route in route_keys:
            route_maps[route] = {
                f["feature"]: f["importance"] for f in feature_importance[route]
            }

        # Use overall ordering
        for f in overall:
            feat = f["feature"]
            vals = []
            for route in route_keys:
                v = route_maps[route].get(feat, 0.0)
                vals.append(f"{v:.4f}")
            lines.append(f"| {feat} | " + " | ".join(vals) + " |")
        lines.append("")

    return lines


def parse_previous_report(report_path: str) -> dict | None:
    """Parse the JSON block from a previous markdown report for comparison."""
    from pathlib import Path

    try:
        content = Path(report_path).read_text()
        start = content.find("```json\n")
        if start == -1:
            return None
        start += len("```json\n")
        end = content.find("\n```", start)
        if end == -1:
            return None
        raw = content[start:end]
        data = json.loads(raw)
        return data.get("aggregate", data)
    except Exception:
        return None
