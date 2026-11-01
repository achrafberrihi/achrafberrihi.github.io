# MoorMaster™ NXG — Predictive Maintenance

Predicting component failures on an automated vacuum-pad mooring system from sensor telemetry, so maintenance can be scheduled before a breakdown instead of after it.

The original work used confidential operational data. This folder contains a reproducible version of the workflow on **synthetic data** with the same structure: vibration, hydraulic pressure, vacuum, oil temperature, pad load, cycles since service and sea state.

## Quick start

```bash
pip install -r ../requirements.txt
python generate_data.py                       # writes data.csv (5,000 rows, ~8% failures)
python sample_code.py data.csv --model all    # trains and compares 3 models
```

## Approach

- **Leak-free pipeline:** scaling is fitted on the training split only (`make_pipeline`), with a stratified split to keep the failure rate identical in train and test.
- **Class imbalance:** failures are rare, so models use `class_weight="balanced"` rather than learning to always predict "normal".
- **Metrics that match the cost:** a missed failure is far more expensive than an extra inspection, so the report leads with **recall on failures**, then precision and ROC-AUC, plus a confusion matrix and feature importances.

## Sample results (synthetic data)

| Model | Failure recall | Failure precision | ROC-AUC |
|---|---|---|---|
| Logistic regression | 0.938 | 0.503 | 0.974 |
| Decision tree | 0.750 | 0.364 | 0.868 |
| Random forest | 0.675 | 0.540 | 0.954 |

On this dataset the failure signal is close to linear, so logistic regression wins — a good reminder to benchmark a simple baseline before reaching for heavier models. On real telemetry, add time-window features (rolling means, trends since last service) and validate with a time-based split.

## Files

- `generate_data.py` — synthetic sensor dataset generator
- `sample_code.py` — training, evaluation and model comparison (`--model logistic|decision_tree|random_forest|all`)
