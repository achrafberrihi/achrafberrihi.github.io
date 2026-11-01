"""Anomaly detection and short-term prediction for air-quality sensors.

Detectors are complementary, each targeting a failure mode that the others miss:

- robust z-score (rolling median / MAD)    → sudden spikes
- flatline (rolling std = 0)               → stuck sensor
- night-baseline drift                     → slow calibration drift
- Isolation Forest (multivariate)          → unusual combinations, e.g. CO2 rising off-hours
- 30-min CO2 forecast                      → early warning before a threshold is crossed
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, IsolationForest

THRESHOLDS = {"co2_ppm": 1000.0, "pm25_ugm3": 35.0, "tvoc_ppb": 500.0}  # alert levels
STEPS_PER_HOUR = 12                                                    # 5-min sampling


def robust_zscore(s: pd.Series, window: int = 6 * STEPS_PER_HOUR) -> pd.Series:
    """Trailing robust z-score: (x - rolling median) / (1.4826 · rolling MAD)."""
    med = s.rolling(window, min_periods=STEPS_PER_HOUR).median()
    mad = (s - med).abs().rolling(window, min_periods=STEPS_PER_HOUR).median()
    return (s - med) / (1.4826 * mad.replace(0, np.nan))


def flatline(s: pd.Series, window: int = STEPS_PER_HOUR) -> pd.Series:
    """True when the signal hasn't changed at all over `window` samples (stuck sensor).

    The whole frozen stretch is flagged, not only the samples after the window fills.
    """
    flat_end = s.rolling(window).std().fillna(1.0).lt(1e-6)
    return flat_end[::-1].rolling(window, min_periods=1).max()[::-1].astype(bool)


def night_baseline_drift(df: pd.DataFrame, col: str = "co2_ppm", outdoor: float = 420.0,
                         tolerance: float = 120.0) -> pd.Series:
    """Unoccupied nights should return CO2 to the outdoor level (≈420 ppm).

    If the 00:00-05:00 minimum stays well above it, the sensor is drifting.
    Flags every reading of a drifting day.
    """
    night = df[df.timestamp.dt.hour < 5]
    baseline = night.groupby(night.timestamp.dt.date)[col].min()
    drifting_days = set(baseline[baseline > outdoor + tolerance].index)
    return df.timestamp.dt.date.isin(drifting_days)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    hour = out.timestamp.dt.hour + out.timestamp.dt.minute / 60
    out["hour_sin"], out["hour_cos"] = np.sin(2 * np.pi * hour / 24), np.cos(2 * np.pi * hour / 24)
    out["is_workday"] = (out.timestamp.dt.dayofweek < 5).astype(int)
    for col in ("co2_ppm", "pm25_ugm3", "tvoc_ppb"):
        out[f"{col}_d15"] = out[col].diff(3)
        out[f"{col}_std1h"] = out[col].rolling(STEPS_PER_HOUR, min_periods=2).std()
    return out.bfill()


ISO_FEATURES = ["co2_ppm", "pm25_ugm3", "tvoc_ppb", "temp_c", "humidity_pct", "hour_sin", "hour_cos",
                "is_workday", "co2_ppm_d15", "pm25_ugm3_d15", "tvoc_ppb_d15"]


def detect_sensor(df: pd.DataFrame, contamination: float = 0.02, seed: int = 0) -> pd.DataFrame:
    """Run all detectors on one sensor's time series (sorted by timestamp)."""
    out = add_features(df.sort_values("timestamp").reset_index(drop=True))

    z_pm, z_voc = robust_zscore(out.pm25_ugm3), robust_zscore(out.tvoc_ppb)
    out["flag_spike"] = (z_pm > 8) | (z_voc > 8)
    out["flag_stuck"] = flatline(out.pm25_ugm3)
    out["flag_drift"] = night_baseline_drift(out)

    iso = IsolationForest(n_estimators=200, contamination=contamination, random_state=seed)
    iso.fit(out[ISO_FEATURES])
    out["iforest_score"] = -iso.score_samples(out[ISO_FEATURES])   # higher = more anomalous
    out["flag_iforest"] = iso.predict(out[ISO_FEATURES]) == -1

    out["flag_threshold"] = np.column_stack([out[c] > v for c, v in THRESHOLDS.items()]).any(axis=1)
    flags = ["flag_stuck", "flag_drift", "flag_spike", "flag_iforest"]
    out["is_anomaly"] = out[flags].any(axis=1)
    out["detected_type"] = np.select(
        [out.flag_stuck, out.flag_drift, out.flag_spike, out.flag_iforest],
        ["stuck", "drift", "spike", "multivariate"], default="normal")
    return out


def detect_all(df: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([detect_sensor(g) for _, g in df.groupby("sensor_id")], ignore_index=True)


def event_metrics(det: pd.DataFrame) -> dict:
    """Event-level view: share of injected incidents caught, and how fast."""
    caught, delays, total = 0, [], 0
    for _, g in det.groupby("sensor_id"):
        g = g.sort_values("timestamp")
        lab = g.true_label
        block = (lab != lab.shift()).cumsum()
        for _, ev in g[lab != "normal"].groupby(block[lab != "normal"]):
            total += 1
            hits = ev[ev.is_anomaly]
            if not hits.empty:
                caught += 1
                delays.append((hits.timestamp.iloc[0] - ev.timestamp.iloc[0]).total_seconds() / 60)
    return {"incidents": total, "incidents_detected": caught,
            "median_detection_delay_min": float(np.median(delays)) if delays else None}


def evaluate(det: pd.DataFrame) -> dict:
    truth = det.true_label != "normal"
    pred = det.is_anomaly
    tp = int((truth & pred).sum())
    precision = tp / max(int(pred.sum()), 1)
    recall = tp / max(int(truth.sum()), 1)
    per_type = {
        t: round(float(det.loc[det.true_label == t, "is_anomaly"].mean()), 3)
        for t in sorted(det.true_label.unique()) if t != "normal"
    }
    return {"precision": round(precision, 3), "recall": round(recall, 3),
            "f1": round(2 * precision * recall / max(precision + recall, 1e-9), 3),
            "recall_by_type": per_type, **event_metrics(det)}


# ── Prediction: CO2 30 minutes ahead ──────────────────────────────────────────
HORIZON = 6  # steps of 5 min


def forecast_features(g: pd.DataFrame) -> pd.DataFrame:
    f = pd.DataFrame(index=g.index)
    for lag in (0, 1, 3, 6, 12):
        f[f"co2_lag{lag}"] = g.co2_ppm.shift(lag)
    f["co2_slope30"] = g.co2_ppm.diff(6)
    f["hour_sin"], f["hour_cos"], f["is_workday"] = g.hour_sin, g.hour_cos, g.is_workday
    return f


def forecast_co2(det: pd.DataFrame, train_frac: float = 0.7) -> tuple[pd.DataFrame, dict]:
    """Train one model on all sensors (time-based split) and forecast CO2 30 min ahead."""
    rows = []
    for sid, g in det.groupby("sensor_id"):
        g = g.sort_values("timestamp").reset_index(drop=True)
        f = forecast_features(g)
        f["target"] = g.co2_ppm.shift(-HORIZON)
        f["timestamp"], f["sensor_id"], f["co2_actual"] = g.timestamp, sid, g.co2_ppm
        rows.append(f)
    data = pd.concat(rows, ignore_index=True).dropna()
    cutoff = data.timestamp.quantile(train_frac)
    train, test = data[data.timestamp <= cutoff], data[data.timestamp > cutoff].copy()

    feats = [c for c in data.columns if c not in ("target", "timestamp", "sensor_id", "co2_actual")]
    model = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
    model.fit(train[feats], train.target)
    test["co2_forecast_30min"] = model.predict(test[feats])
    test["predicted_alert"] = test.co2_forecast_30min > THRESHOLDS["co2_ppm"]

    mae = float(np.mean(np.abs(test.co2_forecast_30min - test.target)))
    naive = float(np.mean(np.abs(test.co2_actual - test.target)))  # "no change" baseline
    actual_exceed = test.target > THRESHOLDS["co2_ppm"]
    alert_precision = float((test.predicted_alert & actual_exceed).sum() / max(int(test.predicted_alert.sum()), 1))
    alert_recall = float((test.predicted_alert & actual_exceed).sum() / max(int(actual_exceed.sum()), 1))
    return test, {"mae_ppm": round(mae, 1), "naive_mae_ppm": round(naive, 1),
                  "alert_precision": round(alert_precision, 3), "alert_recall": round(alert_recall, 3),
                  "median_lead_time_min": early_warning_lead(test)}


def early_warning_lead(test: pd.DataFrame) -> float | None:
    """Median minutes between the first predicted alert and the actual crossing (looks back 90 min)."""
    leads = []
    for _, g in test.groupby("sensor_id"):
        g = g.sort_values("timestamp")
        above = g.co2_actual > THRESHOLDS["co2_ppm"]
        crossings = g.index[above & ~above.shift(1, fill_value=False)]
        for idx in crossings:
            t_cross = g.at[idx, "timestamp"]
            window = g[(g.timestamp >= t_cross - pd.Timedelta(minutes=90)) & (g.timestamp <= t_cross)]
            alerts = window[window.predicted_alert]
            if not alerts.empty:
                leads.append((t_cross - alerts.timestamp.iloc[0]).total_seconds() / 60)
    return float(np.median(leads)) if leads else None


def alert_events(det: pd.DataFrame) -> pd.DataFrame:
    """Merge consecutive anomalous readings into events (one row per incident)."""
    events = []
    for sid, g in det.groupby("sensor_id"):
        g = g.sort_values("timestamp")
        grp = (g.is_anomaly != g.is_anomaly.shift()).cumsum()
        for _, block in g[g.is_anomaly].groupby(grp[g.is_anomaly]):
            types = block.detected_type[block.detected_type != "normal"]
            events.append({
                "sensor_id": sid, "zone": block.zone.iloc[0],
                "start": block.timestamp.iloc[0], "end": block.timestamp.iloc[-1],
                "duration_min": int((block.timestamp.iloc[-1] - block.timestamp.iloc[0]).total_seconds() / 60) + 5,
                "type": types.mode().iloc[0] if not types.empty else "multivariate",
                "peak_co2_ppm": block.co2_ppm.max(), "peak_pm25_ugm3": block.pm25_ugm3.max(),
                "max_score": round(block.iforest_score.max(), 3),
            })
    return pd.DataFrame(events)
