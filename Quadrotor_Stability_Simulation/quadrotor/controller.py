"""Cascaded PID controller: position → attitude → rotor thrusts.

Outer loop (slow): position and altitude errors give a desired acceleration,
converted into a total thrust and desired roll/pitch angles.
Inner loop (fast): attitude PID gives body torques.
The inner loop is tuned roughly 5-10x faster than the outer loop, which is
what keeps the cascade stable.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .model import G, QuadParams, mixer


@dataclass
class Gains:
    # attitude (per axis: roll, pitch, yaw) — torque = I * (kp*e + ki*∫e - kd*rate)
    att_kp: tuple = (144.0, 144.0, 36.0)
    att_ki: tuple = (20.0, 20.0, 4.0)
    att_kd: tuple = (19.0, 19.0, 10.0)
    # altitude
    z_kp: float = 6.0
    z_ki: float = 0.8
    z_kd: float = 4.5
    # horizontal position
    xy_kp: float = 1.2
    xy_kd: float = 1.8
    max_tilt_deg: float = 25.0


@dataclass
class CascadedController:
    params: QuadParams
    gains: Gains = field(default_factory=Gains)
    _att_int: np.ndarray = field(default_factory=lambda: np.zeros(3))
    _z_int: float = 0.0

    def reset(self) -> None:
        self._att_int[:] = 0.0
        self._z_int = 0.0

    def __call__(self, state: np.ndarray, ref: np.ndarray, dt: float) -> tuple[np.ndarray, np.ndarray]:
        """Return (rotor thrusts, desired attitude) for reference [x, y, z, psi]."""
        g, p = self.gains, self.params
        x, y, z, vx, vy, vz = state[:6]
        phi, theta, psi = state[6:9]
        rates = state[9:12]
        x_ref, y_ref, z_ref, psi_ref = ref

        # Altitude → collective thrust (with tilt compensation)
        ez = z_ref - z
        if abs(ez) < 0.3:  # conditional integration: no wind-up during large climbs
            self._z_int = np.clip(self._z_int + ez * dt, -2.0, 2.0)
        az = g.z_kp * ez + g.z_ki * self._z_int - g.z_kd * vz
        tilt = max(np.cos(phi) * np.cos(theta), 0.5)
        thrust = p.mass * (G + az) / tilt

        # Horizontal position → desired roll / pitch (small-angle inversion, yaw-aware)
        ax = g.xy_kp * (x_ref - x) - g.xy_kd * vx
        ay = g.xy_kp * (y_ref - y) - g.xy_kd * vy
        max_tilt = np.radians(g.max_tilt_deg)
        theta_des = np.clip((ax * np.cos(psi) + ay * np.sin(psi)) / G, -max_tilt, max_tilt)
        phi_des = np.clip((ax * np.sin(psi) - ay * np.cos(psi)) / G, -max_tilt, max_tilt)
        att_des = np.array([phi_des, theta_des, psi_ref])

        # Attitude PID → torques
        err = att_des - np.array([phi, theta, psi])
        err[2] = (err[2] + np.pi) % (2 * np.pi) - np.pi  # shortest yaw error
        self._att_int = np.clip(self._att_int + err * dt, -0.5, 0.5)
        accel = np.array(g.att_kp) * err + np.array(g.att_ki) * self._att_int - np.array(g.att_kd) * rates
        torques = p.inertia @ accel

        return mixer(p, thrust, torques), att_des
