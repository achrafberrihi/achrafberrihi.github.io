"""Synthetic indoor air-quality sensor data with labelled anomalies.

Each sensor node reports CO2 (ppm), PM2.5 (µg/m³), TVOC (ppb), temperature (°C)
and relative humidity (%) every 5 minutes. Occupancy drives daily cycles.
Four realistic anomaly types are injected and labelled so detectors can be scored:

- spike        short pollution burst (dust, combustion)          → PM2.5, TVOC
- ventilation  ventilation failure, CO2 builds up for hours      → CO2
- drift        slow sensor calibration drift                     → CO2
- stuck        sensor freezes on a constant value                → PM2.5
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SENSORS = {
    "S1": {"zone": "Workshop", "occupancy": 1.4, "dust": 1.8},
    "S2": {"zone": "Office", "occupancy": 1.0, "dust": 0.7},
    "S3": {"zone": "Warehouse", "occupancy": 0.6, "dust": 1.2},
}
POLLUTANTS = ["co2_ppm", "pm25_ugm3", "tvoc_ppb", "temp_c", "humidity_pct"]


def _occupancy(ts: pd.DatetimeIndex) -> np.ndarray:
    hour = ts.hour + ts.minute / 60
    workday = (ts.dayofweek < 5).astype(float)
    day_shape = np.clip(np.sin((hour - 7) / 11 * np.pi), 0, None)  # 07:00-18:00
    return np.asarray(day_shape * (0.25 + 0.75 * workday), dtype=float)


def generate(days: int = 30, freq: str = "5min", seed: int = 7, start: str = "2026-03-01") -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    ts = pd.date_range(start, periods=int(pd.Timedelta(days=days) / pd.Timedelta(freq)), freq=freq)
    n = len(ts)
    occ = _occupancy(ts)
    frames = []

    for sid, cfg in SENSORS.items():
        o = occ * cfg["occupancy"]
        co2 = 420 + 430 * o + rng.normal(0, 18, n)
        pm25 = 6 + 9 * o * cfg["dust"] + rng.gamma(2, 1.2, n)
        tvoc = 80 + 220 * o + rng.normal(0, 15, n)
        temp = 21 + 2.5 * o + 1.2 * np.sin(2 * np.pi * (np.asarray(ts.hour) - 15) / 24) + rng.normal(0, 0.15, n)
        hum = 48 - 6 * o + rng.normal(0, 1.0, n)
        label = np.array(["normal"] * n, dtype=object)

        def window(hours_min: float, hours_max: float) -> slice:
            length = int(rng.uniform(hours_min, hours_max) * 12)
            start_i = int(rng.integers(288, n - length - 1))
            return slice(start_i, start_i + length)

        for _ in range(6):                                   # pollution spikes
            w = window(0.25, 1.0)
            k = w.stop - w.start
            shape = np.hanning(k) if k > 2 else np.ones(k)
            pm25[w] += rng.uniform(60, 140) * shape
            tvoc[w] += rng.uniform(400, 900) * shape
            label[w] = "spike"
        for _ in range(2):                                   # ventilation failure
            w = window(3, 6)
            co2[w] += np.linspace(0, rng.uniform(900, 1400), w.stop - w.start)
            label[w] = "ventilation"
        w = window(48, 72)                                   # calibration drift
        co2[w] += np.linspace(0, 380, w.stop - w.start)
        label[w] = "drift"
        w = window(4, 8)                                     # stuck sensor
        pm25[w] = round(float(pm25[w.start]), 1)
        label[w] = "stuck"

        frames.append(pd.DataFrame({
            "timestamp": ts, "sensor_id": sid, "zone": cfg["zone"],
            "co2_ppm": co2.round(1), "pm25_ugm3": np.clip(pm25, 0, None).round(1),
            "tvoc_ppb": np.clip(tvoc, 0, None).round(1), "temp_c": temp.round(2),
            "humidity_pct": hum.round(1), "true_label": label,
        }))

    return pd.concat(frames, ignore_index=True)
