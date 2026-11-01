"""End-to-end pipeline: sensor data → anomaly detection → CO2 forecast → Power BI tables.

    python run_pipeline.py                     # synthetic data, 30 days, 3 sensors
    python run_pipeline.py --input my.csv      # your own readings (same columns, no true_label needed)

Outputs (data/powerbi/): fact_readings.csv, fact_alerts.csv, fact_forecast.csv,
dim_sensor.csv, plus metrics.json and figures/.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from airq.detect import THRESHOLDS, alert_events, detect_all, evaluate, forecast_co2
from airq.simulate import SENSORS, generate

HERE = Path(__file__).parent
READING_COLS = ["timestamp", "sensor_id", "co2_ppm", "pm25_ugm3", "tvoc_ppb", "temp_c", "humidity_pct",
                "iforest_score", "flag_spike", "flag_stuck", "flag_drift", "flag_iforest", "flag_threshold",
                "is_anomaly", "detected_type"]


def export_powerbi(det: pd.DataFrame, forecast: pd.DataFrame, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    det[READING_COLS].to_csv(out / "fact_readings.csv", index=False)
    alert_events(det).to_csv(out / "fact_alerts.csv", index=False)
    forecast[["timestamp", "sensor_id", "co2_actual", "co2_forecast_30min", "predicted_alert"]].to_csv(
        out / "fact_forecast.csv", index=False)
    dim = pd.DataFrame([{"sensor_id": k, "zone": v["zone"]} for k, v in SENSORS.items()])
    dim = dim[dim.sensor_id.isin(det.sensor_id.unique())]
    dim.assign(co2_limit_ppm=THRESHOLDS["co2_ppm"], pm25_limit_ugm3=THRESHOLDS["pm25_ugm3"]).to_csv(
        out / "dim_sensor.csv", index=False)


def plot(det: pd.DataFrame, forecast: pd.DataFrame, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out.mkdir(exist_ok=True)
    s1 = det[det.sensor_id == "S1"].set_index("timestamp")
    fig, axes = plt.subplots(2, 1, figsize=(11, 6), sharex=True)
    for ax, col, label in ((axes[0], "pm25_ugm3", "PM2.5 (µg/m³)"), (axes[1], "co2_ppm", "CO2 (ppm)")):
        ax.plot(s1.index, s1[col], lw=0.7, label=label)
        hits = s1[s1.is_anomaly]
        ax.scatter(hits.index, hits[col], s=6, c="red", label="detected anomaly", zorder=3)
        ax.axhline(THRESHOLDS[col], ls="--", c="gray", lw=1, label="alert level")
        ax.set_ylabel(label)
        ax.grid(alpha=0.3)
        ax.legend(loc="upper left", fontsize=8)
    axes[0].set_title("Sensor S1 (Workshop): readings and detected anomalies")
    fig.tight_layout()
    fig.savefig(out / "anomalies_s1.png", dpi=120)

    f = forecast[forecast.sensor_id == "S1"].set_index("timestamp").iloc[: 12 * 24 * 3]
    fig, ax = plt.subplots(figsize=(11, 3.5))
    ax.plot(f.index, f.co2_actual, lw=0.9, label="actual CO2")
    ax.plot(f.index, f.co2_forecast_30min, lw=0.9, label="forecast made 30 min earlier", alpha=0.8)
    ax.axhline(THRESHOLDS["co2_ppm"], ls="--", c="gray", lw=1, label="1000 ppm")
    ax.set_ylabel("CO2 (ppm)")
    ax.set_title("30-minute CO2 forecast on unseen test days (S1)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out / "forecast_s1.png", dpi=120)
    plt.close("all")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, help="CSV of sensor readings (default: synthetic data)")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()

    if args.input:
        raw = pd.read_csv(args.input, parse_dates=["timestamp"])
        raw["true_label"] = raw.get("true_label", "normal")
        raw["zone"] = raw.get("zone", raw.sensor_id)
    else:
        raw = generate(days=args.days)

    det = detect_all(raw)
    forecast, fc_metrics = forecast_co2(det)
    metrics = {"rows": len(det), "sensors": det.sensor_id.nunique(), "forecast": fc_metrics}
    if args.input is None:
        metrics["detection"] = evaluate(det)

    export_powerbi(det, forecast, HERE / "data" / "powerbi")
    (HERE / "data" / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
    if not args.no_plots:
        plot(det, forecast, HERE / "figures")


if __name__ == "__main__":
    main()
