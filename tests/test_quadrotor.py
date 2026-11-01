import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "Quadrotor_Stability_Simulation"))

from quadrotor import QuadParams, mixer  # noqa: E402
from quadrotor.analysis import is_hurwitz_stable, pid_double_integrator_poles, step_metrics  # noqa: E402
from quadrotor.model import dynamics, forces_from_rotors  # noqa: E402
from simulate import metrics, run  # noqa: E402


def test_hover_is_an_equilibrium():
    p = QuadParams()
    rotor = np.full(4, p.hover_thrust / 4)
    deriv = dynamics(np.zeros(12), rotor, p)
    assert np.allclose(deriv, 0, atol=1e-9)


def test_mixer_inverts_force_model():
    p = QuadParams()
    thrust, torques = 12.0, np.array([0.05, -0.02, 0.01])
    t_back, tau_back = forces_from_rotors(p, mixer(p, thrust, torques))
    assert np.isclose(t_back, thrust) and np.allclose(tau_back, torques)


def test_routh_condition_matches_poles():
    assert is_hurwitz_stable(144, 20, 19)
    assert np.all(pid_double_integrator_poles(144, 20, 19).real < 0)
    assert not is_hurwitz_stable(1, 50, 1)
    assert np.any(pid_double_integrator_poles(1, 50, 1).real > 0)


def test_step_metrics_on_first_order_response():
    t = np.linspace(0, 10, 2001)
    m = step_metrics(t, 1 - np.exp(-t), 1.0)
    assert abs(m["rise_time_s"] - np.log(9)) < 0.02 and m["overshoot_pct"] == 0


def test_closed_loop_reaches_target_and_rejects_gust():
    m = metrics(run(duration=10.0, dt=0.004))
    assert abs(m["altitude"]["final_error"]) < 0.05
    assert m["altitude"]["overshoot_pct"] < 10
    assert m["gust_rejection"]["final_position_error_m"] < 0.1
