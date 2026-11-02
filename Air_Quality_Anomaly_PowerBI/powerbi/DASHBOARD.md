# Power BI dashboard — build guide

The pipeline writes a small star schema to `data/powerbi/`. This guide rebuilds the report in about 20 minutes.

## 1. Load and model

1. **Get data → Blank query → Advanced editor**, paste [`load_data.pq`](load_data.pq) and set `DataFolder`.
2. Load `fact_readings`, `fact_alerts`, `fact_forecast`, `dim_sensor`.
3. **Modeling → New table:** `Date = CALENDAR ( MIN ( fact_readings[date] ), MAX ( fact_readings[date] ) )`, mark it as a date table.
4. Relationships (single direction): `dim_sensor[sensor_id]` → each fact table, `Date[Date]` → `fact_readings[date]`.
5. Create the measures from [`measures.dax`](measures.dax) in a dedicated `_Measures` table.

## 2. Pages

### Overview
- **Cards:** Avg CO2, Avg PM2.5, Anomaly Rate %, Incidents, CO2 Compliance %.
- **Card with conditional colour:** `Air Status` (background = `Status Color`).
- **Line chart:** Avg CO2 and Avg PM2.5 by hour, legend = zone.
- **Slicers:** zone, date range.

### Anomalies
- **Line chart:** co2_ppm / pm25_ugm3 over timestamp, with `is_anomaly` as a red scatter overlay (or a conditional marker).
- **Stacked bar:** Spike / Stuck / Drift / Multivariate flags by sensor.
- **Table:** fact_alerts (start, zone, type, duration, peak values), sorted by max_score.
- **Heatmap (matrix):** rows = zone, columns = hour of day, values = Anomaly Rate % with colour scale.

### Prediction
- **Line chart:** co2_actual vs co2_forecast_30min, constant line at 1000 ppm.
- **Cards:** Forecast MAE, Predicted Alerts.
- **Tooltip page:** latest readings and forecast for the hovered sensor.

## 3. Refresh

Re-run `python run_pipeline.py` (or point `--input` at real sensor exports) and click **Refresh**. For live data, schedule the script and publish the report with a gateway.
