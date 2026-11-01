import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "MoorMaster_ML_Maintenance"))

from generate_data import generate  # noqa: E402
from sample_code import MODELS, train_and_evaluate  # noqa: E402


def test_generated_data_shape_and_imbalance():
    df = generate(rows=2000, seed=1)
    assert len(df) == 2000 and "failure" in df
    assert 0.05 < df.failure.mean() < 0.12


def test_every_model_beats_chance():
    df = generate(rows=2000, seed=1)
    X, y = df.drop(columns="failure"), df.failure
    for name in MODELS:
        metrics = train_and_evaluate(X, y, name, verbose=False)
        assert metrics["roc_auc"] > 0.75, name
