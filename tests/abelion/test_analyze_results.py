"""Tests for analyze_results module."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "docs/abelion/research/scripts")

from analyze_results import load_results, compute_aggregates, compare_conditions


SAMPLE_CSV = """task_id,category,condition,condition_name,run,completed,failed,error,iterations,total_tokens,input_tokens,output_tokens,cost_usd,elapsed_seconds
debug-01,debugging,A,control,1,True,False,,5,1000,500,500,0.002,10.5
debug-01,debugging,B,raw_rsi,1,True,False,,4,900,450,450,0.0018,9.2
debug-01,debugging,C,validated_rsi,1,True,False,,3,800,400,400,0.0016,8.1
debug-02,debugging,A,control,1,False,True,import error,6,1200,600,600,0.0024,12.0
debug-02,debugging,B,raw_rsi,1,True,False,,5,1100,550,550,0.0022,11.0
debug-02,debugging,C,validated_rsi,1,True,False,,4,1000,500,500,0.002,10.0
"""


def _write_sample_csv() -> str:
    """Write sample CSV to temp file and return path."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(SAMPLE_CSV)
        return f.name


def test_load_results():
    tmp_path = _write_sample_csv()
    try:
        df = load_results(tmp_path)
        assert len(df) == 6
        cols = list(df.columns)
        for required in [
            "task_id", "category", "condition", "run",
            "completed", "failed", "iterations", "total_tokens",
        ]:
            assert required in cols
    finally:
        Path(tmp_path).unlink()


def test_compute_aggregates():
    tmp_path = _write_sample_csv()
    try:
        df = load_results(tmp_path)
        agg = compute_aggregates(df)
        assert "A" in agg.index
        assert "B" in agg.index
        assert "C" in agg.index
        assert "completion_rate" in agg.columns
        assert "avg_iterations" in agg.columns
        assert "avg_total_tokens" in agg.columns
    finally:
        Path(tmp_path).unlink()


def test_compare_conditions():
    tmp_path = _write_sample_csv()
    try:
        df = load_results(tmp_path)
        comp = compare_conditions(df, "A", "B")
        assert "pair" in comp.columns
        assert len(comp) >= 1
    finally:
        Path(tmp_path).unlink()
