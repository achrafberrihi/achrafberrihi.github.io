"""Electrical calculations for a steam turbo-alternator (OCP Jorf Lasfar internship study).

Rated values from the study: 25 MVA, generator 5.5 kV, step-up to 22 kV.
Values marked "typical" are textbook assumptions used to illustrate the method,
not plant settings.

    python turbo_alternator.py
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Generator:
    s_rated_va: float = 25e6          # apparent power (study)
    u_gen_v: float = 5.5e3            # generator line voltage (study)
    u_grid_v: float = 22e3            # step-up transformer HV side (study)
    frequency_hz: float = 50.0
    power_factor: float = 0.8         # typical for industrial turbo-alternators
    poles: int = 2                    # smooth-pole (cylindrical) rotor, 2 poles
    xd_subtransient_pu: float = 0.15  # typical X''d


def rated_current(s_va: float, u_v: float) -> float:
    """Three-phase line current: I = S / (√3 · U)."""
    return s_va / (math.sqrt(3) * u_v)


def synchronous_speed_rpm(frequency_hz: float, poles: int) -> float:
    """n = 60 · f / p, with p = pole pairs."""
    return 60 * frequency_hz / (poles / 2)


def study(g: Generator | None = None) -> dict:
    g = g or Generator()
    i_gen = rated_current(g.s_rated_va, g.u_gen_v)
    i_grid = rated_current(g.s_rated_va, g.u_grid_v)
    return {
        "apparent_power_MVA": g.s_rated_va / 1e6,
        "rated_current_generator_A": round(i_gen, 1),
        "rated_current_22kV_A": round(i_grid, 1),
        "transformer_ratio": f"1:{g.u_grid_v / g.u_gen_v:g} ({g.u_gen_v / 1e3:g}/{g.u_grid_v / 1e3:g} kV)",
        "active_power_MW_at_pf": round(g.s_rated_va * g.power_factor / 1e6, 2),
        "reactive_power_Mvar_at_pf": round(g.s_rated_va * math.sin(math.acos(g.power_factor)) / 1e6, 2),
        "synchronous_speed_rpm": synchronous_speed_rpm(g.frequency_hz, g.poles),
        "subtransient_short_circuit_kA_typical": round(i_gen / g.xd_subtransient_pu / 1e3, 1),
    }


# Generator protection functions (ANSI codes) from the study, with typical settings for illustration
PROTECTIONS = [
    {"ansi": "87G", "function": "Generator differential", "detects": "Internal stator short circuit",
     "typical_setting": "10 % In minimum pickup, dual slope, instantaneous trip"},
    {"ansi": "59/27", "function": "Over/under-voltage", "detects": "Voltage regulation (AVR) fault",
     "typical_setting": "59: 110 % Un, 1 s  |  27: 85 % Un, 2 s"},
    {"ansi": "12", "function": "Overspeed", "detects": "Mechanical runaway after load rejection",
     "typical_setting": "110 % of rated speed, trips turbine stop valves"},
    {"ansi": "40", "function": "Loss of excitation", "detects": "Field (exciter) failure",
     "typical_setting": "Offset mho impedance zones, 0.5 s / instantaneous"},
]


def synchronization_check(u_gen_v: float, u_grid_v: float, f_gen_hz: float, f_grid_hz: float,
                          phase_diff_deg: float, max_dv_pct: float = 5.0, max_df_hz: float = 0.1,
                          max_dphi_deg: float = 10.0) -> dict:
    """Synchro-check (ANSI 25): close the breaker only if voltage, frequency and phase match.

    Phase sequence must also be identical, which is verified once at commissioning.
    """
    dv = abs(u_gen_v - u_grid_v) / u_grid_v * 100
    df = abs(f_gen_hz - f_grid_hz)
    dphi = abs((phase_diff_deg + 180) % 360 - 180)
    checks = {"voltage": dv <= max_dv_pct, "frequency": df <= max_df_hz, "phase": dphi <= max_dphi_deg}
    return {"delta_v_pct": round(dv, 2), "delta_f_hz": round(df, 3), "delta_phi_deg": round(dphi, 1),
            "checks": checks, "permit_close": all(checks.values())}


if __name__ == "__main__":
    print(json.dumps(study(), indent=2))
    print("\nSynchro-check example (5.45 kV / 50.05 Hz / 6°):")
    print(json.dumps(synchronization_check(5450, 5500, 50.05, 50.0, 6.0), indent=2))
