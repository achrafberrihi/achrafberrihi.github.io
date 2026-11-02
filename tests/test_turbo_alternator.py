import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "OCP_TurboAlternator_Study"))

from turbo_alternator import rated_current, study, synchronization_check  # noqa: E402


def test_rated_current_matches_study():
    assert round(rated_current(25e6, 5.5e3)) == 2624
    assert study()["transformer_ratio"].startswith("1:4")


def test_synchro_check():
    assert synchronization_check(5450, 5500, 50.05, 50.0, 6.0)["permit_close"]
    blocked = synchronization_check(5500, 5500, 50.0, 50.0, 25.0)
    assert not blocked["permit_close"] and not blocked["checks"]["phase"]
    assert synchronization_check(5500, 5500, 50.0, 50.0, 355.0)["checks"]["phase"]  # wraps around 360°
