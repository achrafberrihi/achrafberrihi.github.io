"""Linear stability analysis and step-response metrics."""
from __future__ import annotations

import numpy as np


def pid_double_integrator_poles(kp: float, ki: float, kd: float) -> np.ndarray:
    """Closed-loop poles of a PID on a double integrator (one attitude axis, linearised at hover).

    Characteristic polynomial: s³ + kd·s² + kp·s + ki = 0
    Routh-Hurwitz: stable  ⇔  kp, ki, kd > 0 and kd·kp > ki.
    """
    return np.roots([1.0, kd, kp, ki])


def is_hurwitz_stable(kp: float, ki: float, kd: float) -> bool:
    return kp > 0 and ki >= 0 and kd > 0 and kd * kp > ki


def damping_report(poles: np.ndarray) -> list[dict]:
    rows = []
    for p in poles:
        wn = abs(p)
        zeta = -p.real / wn if wn else 1.0
        pole = complex(round(p.real, 3), round(p.imag, 3))
        rows.append({"pole": pole, "wn_rad_s": round(wn, 2), "zeta": round(zeta, 3)})
    return rows


def step_metrics(t: np.ndarray, y: np.ndarray, target: float, start: float | None = None, band: float = 0.02) -> dict:
    """Rise time (10-90 %), overshoot (%), settling time (±band) and final error of a step response."""
    y0 = y[0] if start is None else start
    span = target - y0
    if abs(span) < 1e-9:
        raise ValueError("target equals initial value")
    norm = (y - y0) / span

    def first_cross(level: float) -> float:
        idx = np.argmax(norm >= level)
        return float(t[idx]) if norm[idx] >= level else float("nan")

    rise = first_cross(0.9) - first_cross(0.1)
    overshoot = max(0.0, (norm.max() - 1.0) * 100)
    outside = np.where(np.abs(norm - 1.0) > band)[0]
    if len(outside) == 0:
        settling = float(t[0])
    elif outside[-1] + 1 >= len(t):
        settling = float("nan")  # never settled within the simulation
    else:
        settling = float(t[outside[-1] + 1])
    return {
        "rise_time_s": round(rise, 3),
        "overshoot_pct": round(overshoot, 2),
        "settling_time_s": round(settling, 3),
        "final_error": round(float(target - y[-1]), 4),
    }
