#!/usr/bin/env python3
"""Analyze RSI experiment results from CSV.

Usage:
    python3 analyze_results.py results.csv [--output summary.md]
"""

import argparse
import sys
from pathlib import Path

# scipy and pandas are imported inside functions that use them


def load_results(csv_path: str) -> "pd.DataFrame":
    """Load experiment CSV into a DataFrame."""
    import pandas as pd
    df = pd.read_csv(csv_path)
    for col in ["completed", "failed"]:
        if col in df.columns:
            df[col] = df[col].astype(bool)
    return df


def compute_aggregates(df: "pd.DataFrame") -> "pd.DataFrame":
    """Compute per-condition aggregate metrics.

    Returns DataFrame with conditions as rows, metrics as columns.
    """
    import pandas as pd
    grouped = df.groupby("condition")

    agg = pd.DataFrame({
        "completion_rate": grouped["completed"].mean(),
        "avg_iterations": grouped["iterations"].mean(),
        "avg_total_tokens": grouped["total_tokens"].mean(),
        "avg_input_tokens": grouped["input_tokens"].mean(),
        "avg_output_tokens": grouped["output_tokens"].mean(),
        "avg_cost_usd": grouped["cost_usd"].mean(),
        "avg_elapsed_seconds": grouped["elapsed_seconds"].mean(),
        "total_tasks": grouped["completed"].count(),
        "failed_count": grouped["failed"].sum(),
    })

    return agg.round(2)


def compare_conditions(
    df: "pd.DataFrame",
    cond_a: str,
    cond_b: str,
) -> "pd.DataFrame":
    """Statistical comparison between two conditions using paired t-test.

    Matches by (task_id, run) for pairing.
    """
    import pandas as pd
    import scipy.stats as stats
    a = df[df["condition"] == cond_a].set_index(["task_id", "run"])
    b = df[df["condition"] == cond_b].set_index(["task_id", "run"])

    common_idx = a.index.intersection(b.index)
    if len(common_idx) < 2:
        return pd.DataFrame([{
            "pair": f"{cond_a}_vs_{cond_b}",
            "metric": "insufficient_data",
            "p_value": float("nan"),
            "mean_diff": 0.0,
        }])

    a_aligned = a.loc[common_idx]
    b_aligned = b.loc[common_idx]

    metrics = ["completed", "iterations", "total_tokens", "elapsed_seconds"]
    results = []

    for metric in metrics:
        if metric not in df.columns:
            continue
        a_vals = a_aligned[metric].astype(float).values
        b_vals = b_aligned[metric].astype(float).values

        mask = ~(pd.isna(a_vals) | pd.isna(b_vals))
        a_clean = a_vals[mask]
        b_clean = b_vals[mask]

        if len(a_clean) < 2:
            continue

        try:
            t_stat, p_value = stats.ttest_rel(a_clean, b_clean)
            mean_diff = (b_clean - a_clean).mean()
            results.append({
                "pair": f"{cond_a}_vs_{cond_b}",
                "metric": metric,
                "mean_a": round(a_clean.mean(), 4),
                "mean_b": round(b_clean.mean(), 4),
                "mean_diff": round(mean_diff, 4),
                "t_statistic": round(t_stat, 4),
                "p_value": round(p_value, 4),
                "n_pairs": len(a_clean),
            })
        except Exception as exc:
            results.append({
                "pair": f"{cond_a}_vs_{cond_b}",
                "metric": metric,
                "error": str(exc),
            })

    return pd.DataFrame(results)


def _sig_stars(p: float) -> str:
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


def main():
    import pandas as pd
    parser = argparse.ArgumentParser(description="Analyze RSI experiment results")
    parser.add_argument("csv_path", help="Path to experiment CSV")
    parser.add_argument("--output", default="", help="Output summary path")
    args = parser.parse_args()

    print(f"Loading results from {args.csv_path}...")
    df = load_results(args.csv_path)
    print(f"  {len(df)} rows, {df['condition'].nunique()} conditions, "
          f"{df['run'].nunique()} runs")
    print()

    # Per-condition aggregates
    print("=== Per-Condition Aggregates ===")
    agg = compute_aggregates(df)
    print(agg.to_string())
    print()

    # Pairwise comparisons
    conditions = sorted(df["condition"].unique())
    print("=== Pairwise Comparisons (paired t-test) ===")
    comparisons: list[pd.DataFrame] = []
    for i, cond_a in enumerate(conditions):
        for cond_b in conditions[i + 1:]:
            comp = compare_conditions(df, cond_a, cond_b)
            comparisons.append(comp)
            print(f"\n{cond_a} vs {cond_b}:")
            if "error" in comp.columns and comp["error"].notna().any():
                for _, row in comp.iterrows():
                    err = row.get("error", "unknown")
                    print(f"  {row['metric']}: ERROR - {err}")
            else:
                for _, row in comp.iterrows():
                    print(
                        f"  {row['metric']}: Δ={row['mean_diff']:+.4f}, "
                        f"p={row['p_value']:.4f} {_sig_stars(row['p_value'])}"
                    )

    # Summary interpretation
    print()
    print("=== RQ1: Does RSI work? ===")
    if "A" in conditions and "B" in conditions:
        comp = compare_conditions(df, "A", "B")
        rate_a = agg.loc["A", "completion_rate"]
        rate_b = agg.loc["B", "completion_rate"]
        print(f"  Control (A):   {rate_a:.1%} completion")
        print(f"  Raw RSI (B):   {rate_b:.1%} completion")
        p_vals = comp[comp["metric"] == "completed"]["p_value"].values
        if len(p_vals) > 0:
            p = p_vals[0]
            print(f"  p-value: {p:.4f}")
            if p < 0.05 and rate_b > rate_a:
                print("  → RSI significantly improves performance")
            elif p < 0.05 and rate_b < rate_a:
                print("  → RSI significantly degrades performance")
            else:
                print("  → No significant effect detected")

    print()
    print("=== RQ4: Does validation help? ===")
    if "B" in conditions and "C" in conditions:
        comp = compare_conditions(df, "B", "C")
        rate_b = agg.loc["B", "completion_rate"]
        rate_c = agg.loc["C", "completion_rate"]
        print(f"  Raw RSI (B):       {rate_b:.1%} completion")
        print(f"  Validated RSI (C): {rate_c:.1%} completion")
        p_vals = comp[comp["metric"] == "completed"]["p_value"].values
        if len(p_vals) > 0:
            p = p_vals[0]
            print(f"  p-value: {p:.4f}")
            if p < 0.05 and rate_c > rate_b:
                print("  → Validation significantly improves RSI")
            elif p < 0.05 and rate_c < rate_b:
                print("  → Raw RSI outperforms validated (unexpected)")
            else:
                print("  → No significant difference between raw and validated")

    # Save if output specified
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            f.write("# RSI Experiment Analysis\n\n")
            f.write("## Per-Condition Aggregates\n")
            f.write(agg.to_csv() + "\n\n")
            f.write("## Pairwise Comparisons\n")
            c = sorted(df["condition"].unique())
            for i, cond_a in enumerate(c):
                for cond_b in c[i + 1:]:
                    comp = compare_conditions(df, cond_a, cond_b)
                    f.write(f"### {cond_a} vs {cond_b}\n")
                    f.write(comp.to_csv() + "\n\n")
        print(f"\nSummary saved to: {args.output}")


if __name__ == "__main__":
    main()
