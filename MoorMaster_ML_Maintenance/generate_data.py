"""Generate a synthetic sensor dataset for the predictive-maintenance demo.

Real mooring-system telemetry is confidential, so this script simulates
plausible readings for a vacuum-pad mooring unit. Failure risk rises with
vibration, hydraulic-pressure drop, temperature and accumulated cycles, with
noise so the problem isn't trivially separable. About 8% of rows are failures,
reflecting the class imbalance of real maintenance data.

    python generate_data.py --rows 5000 --out data.csv
"""
import argparse

import numpy as np
import pandas as pd


def generate(rows: int = 5000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "vibration_rms_mm_s": rng.gamma(2.0, 1.2, rows),
        "hydraulic_pressure_bar": rng.normal(180, 12, rows),
        "vacuum_kpa": rng.normal(-80, 4, rows),
        "oil_temp_c": rng.normal(45, 6, rows),
        "pad_load_kn": rng.normal(200, 35, rows).clip(0),
        "cycles_since_service": rng.integers(0, 4000, rows),
        "wave_height_m": rng.gamma(1.5, 0.6, rows),
    })
    risk = (
        0.9 * (df.vibration_rms_mm_s - 2.4)
        - 0.12 * (df.hydraulic_pressure_bar - 180)
        + 0.10 * (df.oil_temp_c - 45)
        + 0.0009 * (df.cycles_since_service - 2000)
        + 0.15 * (df.vacuum_kpa + 80)
        + 0.6 * (df.wave_height_m - 0.9)
        + rng.normal(0, 1.2, rows)
    )
    df["failure"] = (risk > np.quantile(risk, 0.92)).astype(int)
    return df.round(3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic mooring sensor data.")
    parser.add_argument("--rows", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="data.csv")
    args = parser.parse_args()
    data = generate(args.rows, args.seed)
    data.to_csv(args.out, index=False)
    print(f"Wrote {len(data)} rows to {args.out} ({data.failure.mean():.1%} failures)")
