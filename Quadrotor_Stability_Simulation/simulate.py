"""Run the quadrotor stability scenario and produce figures + metrics.

Scenario: take off from the ground, fly to (1, 1, 2) m while yawing to 30°,
then reject a wind-gust torque at t = 7 s.

    python simulate.py                 # metrics + figures in ./figures
    python simulate.py --no-plots      # metrics only
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from quadrotor import CascadedController, Gains, QuadParams, rk4_step
from quadrotor.analysis import damping_report, is_hurwitz_stable, pid_double_integrator_poles, step_metrics

HERE = Path(__file__).parent
DEFAULT_REF = (1.0, 1.0, 2.0, float(np.radians(30)))
DEFAULT_GUST = (7.0, 7.2, (0.05, -0.03, 0.0))  # start (s), end (s), body torque (N·m)


def run(duration: float = 12.0, dt: float = 0.002, ref=DEFAULT_REF, gust=DEFAULT_GUST,
        params: QuadParams | None = None, gains: Gains | None = None) -> dict:
    params = params or QuadParams()
    ctrl = CascadedController(params, gains or Gains())
    steps = int(duration / dt)
    state = np.zeros(12)
    ref = np.asarray(ref, dtype=float)

    t = np.arange(steps) * dt
    states = np.zeros((steps, 12))
    att_des = np.zeros((steps, 3))
    rotors = np.zeros((steps, 4))

    for k in range(steps):
        rotor, des = ctrl(state, ref, dt)
        disturbance = np.asarray(gust[2]) if gust and gust[0] <= t[k] < gust[1] else None
        states[k], att_des[k], rotors[k] = state, des, rotor
        state = rk4_step(state, rotor, params, dt, disturbance)
        if state[2] < 0:            # ground contact
            state[2], state[5] = 0.0, max(state[5], 0.0)

    return {"t": t, "states": states, "att_des": att_des, "rotors": rotors, "ref": ref, "params": params}


def metrics(sim: dict) -> dict:
    t, s, ref = sim["t"], sim["states"], sim["ref"]
    before_gust = t < 7.0
    out = {
        "altitude": step_metrics(t[before_gust], s[before_gust, 2], ref[2], start=0.0),
        "x_position": step_metrics(t[before_gust], s[before_gust, 0], ref[0], start=0.0),
        "yaw": step_metrics(t[before_gust], s[before_gust, 8], ref[3], start=0.0),
    }
    after = t >= 7.0
    roll_dev = np.degrees(np.abs(s[after, 6] - sim["att_des"][after, 0]))
    out["gust_rejection"] = {
        "peak_roll_error_deg": round(float(roll_dev.max()), 2),
        "final_position_error_m": round(float(np.linalg.norm(s[-1, :3] - ref[:3])), 4),
    }
    out["rotor_saturation_pct"] = round(float(
        np.mean(sim["rotors"] >= sim["params"].max_thrust_per_rotor - 1e-9) * 100), 2)
    return out


def linear_stability(gains: Gains | None = None) -> dict:
    g = gains or Gains()
    report = {}
    for name, i in (("roll", 0), ("yaw", 2)):
        kp, ki, kd = g.att_kp[i], g.att_ki[i], g.att_kd[i]
        poles = damping_report(pid_double_integrator_poles(kp, ki, kd))
        report[name] = {"stable": is_hurwitz_stable(kp, ki, kd), "poles": poles}
    report["altitude"] = {"stable": is_hurwitz_stable(g.z_kp, g.z_ki, g.z_kd),
                          "poles": damping_report(pid_double_integrator_poles(g.z_kp, g.z_ki, g.z_kd))}
    return report


def plot(sim: dict, out_dir: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    t, s, ref, des = sim["t"], sim["states"], sim["ref"], sim["att_des"]
    out_dir.mkdir(exist_ok=True)

    fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    for ax, i, label in zip(axes, (0, 1, 2), ("x (m)", "y (m)", "z (m)"), strict=True):
        ax.plot(t, s[:, i], label="response")
        ax.axhline(ref[i], ls="--", c="gray", label="reference")
        ax.axvspan(7.0, 7.2, color="orange", alpha=0.25, label="wind gust")
        ax.set_ylabel(label)
        ax.grid(alpha=0.3)
    axes[0].legend(loc="lower right")
    axes[-1].set_xlabel("time (s)")
    fig.suptitle("Quadrotor position tracking and gust rejection")
    fig.tight_layout()
    fig.savefig(out_dir / "position.png", dpi=130)

    fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    for ax, i, label in zip(axes, (0, 1, 2), ("roll φ (°)", "pitch θ (°)", "yaw ψ (°)"), strict=True):
        ax.plot(t, np.degrees(s[:, 6 + i]), label="actual")
        ax.plot(t, np.degrees(des[:, i]), "--", label="commanded")
        ax.axvspan(7.0, 7.2, color="orange", alpha=0.25)
        ax.set_ylabel(label)
        ax.grid(alpha=0.3)
    axes[0].legend(loc="upper right")
    axes[-1].set_xlabel("time (s)")
    fig.suptitle("Attitude loop: commanded vs actual")
    fig.tight_layout()
    fig.savefig(out_dir / "attitude.png", dpi=130)

    fig = plt.figure(figsize=(7, 6))
    ax = fig.add_subplot(projection="3d")
    ax.plot(s[:, 0], s[:, 1], s[:, 2])
    ax.scatter(*ref[:3], c="red", label="target")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_zlabel("z (m)")
    ax.legend()
    ax.set_title("3D flight path")
    fig.tight_layout()
    fig.savefig(out_dir / "trajectory_3d.png", dpi=130)
    plt.close("all")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--duration", type=float, default=12.0)
    args = parser.parse_args()

    sim = run(duration=args.duration)
    result = {"linear_stability": linear_stability(), "simulation": metrics(sim)}
    print(json.dumps(result, indent=2, default=str))
    if not args.no_plots:
        plot(sim, HERE / "figures")
        print(f"Figures saved to {HERE / 'figures'}")


if __name__ == "__main__":
    main()
