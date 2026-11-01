import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Air_Quality_Anomaly_PowerBI"))

from airq.detect import detect_all, evaluate, flatline, forecast_co2, robust_zscore  # noqa: E402
from airq.simulate import generate  # noqa: E402


def test_robust_zscore_flags_spike():
    s = pd.Series(np.r_[np.random.default_rng(0).normal(10, 1, 200), 60, np.random.default_rng(1).normal(10, 1, 20)])
    z = robust_zscore(s)
    assert z.iloc[200] > 8 and z.iloc[150:200].abs().max() < 5


def test_flatline_marks_whole_frozen_stretch():
    s = pd.Series(np.r_[np.arange(20.0), np.full(15, 5.0), np.arange(20.0)])
    flags = flatline(s, window=12)
    assert flags.iloc[20:35].all() and not flags.iloc[:19].any()


def test_pipeline_detects_most_incidents_and_forecast_beats_naive():
    det = detect_all(generate(days=14, seed=3))
    metrics = evaluate(det)
    assert metrics["incidents_detected"] / metrics["incidents"] >= 0.8
    _, fc = forecast_co2(det)
    assert fc["mae_ppm"] < fc["naive_mae_ppm"]
