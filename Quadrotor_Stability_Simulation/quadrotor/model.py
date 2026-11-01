"""Nonlinear 6-DOF rigid-body model of an X-configuration quadrotor.

State vector (12):
    [x, y, z, vx, vy, vz, phi, theta, psi, p, q, r]
    position (m) and velocity (m/s) in the inertial frame (z up),
    Z-Y-X Euler angles (rad) and body angular rates (rad/s).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

G = 9.81


@dataclass(frozen=True)
class QuadParams:
    mass: float = 1.0            # kg
    arm: float = 0.17            # m, centre to rotor
    ixx: float = 0.0082          # kg·m²
    iyy: float = 0.0082
    izz: float = 0.0149
    kf: float = 6.1e-6           # thrust coefficient, N/(rad/s)²
    km: float = 1.5e-7           # drag-torque coefficient, N·m/(rad/s)²
    max_rotor_speed: float = 1100.0   # rad/s
    drag: float = 0.10           # linear translational drag, N/(m/s)

    @property
    def inertia(self) -> np.ndarray:
        return np.diag([self.ixx, self.iyy, self.izz])

    @property
    def max_thrust_per_rotor(self) -> float:
        return self.kf * self.max_rotor_speed**2

    @property
    def hover_thrust(self) -> float:
        return self.mass * G


def rotation_matrix(phi: float, theta: float, psi: float) -> np.ndarray:
    """Body-to-inertial rotation for Z-Y-X Euler angles."""
    cf, sf = np.cos(phi), np.sin(phi)
    ct, st = np.cos(theta), np.sin(theta)
    cp, sp = np.cos(psi), np.sin(psi)
    return np.array([
        [ct * cp, sf * st * cp - cf * sp, cf * st * cp + sf * sp],
        [ct * sp, sf * st * sp + cf * cp, cf * st * sp - sf * cp],
        [-st, sf * ct, cf * ct],
    ])


def euler_rates(phi: float, theta: float, pqr: np.ndarray) -> np.ndarray:
    """Convert body rates (p, q, r) into Euler-angle rates."""
    p, q, r = pqr
    ct = np.cos(theta)
    if abs(ct) < 1e-6:
        ct = 1e-6
    return np.array([
        p + np.sin(phi) * np.tan(theta) * q + np.cos(phi) * np.tan(theta) * r,
        np.cos(phi) * q - np.sin(phi) * r,
        (np.sin(phi) * q + np.cos(phi) * r) / ct,
    ])


def mixer(params: QuadParams, thrust: float, torques: np.ndarray) -> np.ndarray:
    """Map total thrust and body torques to the four rotor thrusts (X layout).

    Rotor order: front-right (CCW), rear-left (CCW), front-left (CW), rear-right (CW).
    Each rotor thrust is clipped to [0, max], which models actuator saturation.
    """
    tx, ty, tz = torques
    d = params.arm / np.sqrt(2)
    c = params.km / params.kf
    allocation = np.array([
        [1, 1, 1, 1],
        [-d, d, d, -d],
        [d, -d, d, -d],
        [c, c, -c, -c],
    ])
    rotor = np.linalg.solve(allocation, np.array([thrust, tx, ty, tz]))
    return np.clip(rotor, 0.0, params.max_thrust_per_rotor)


def forces_from_rotors(params: QuadParams, rotor: np.ndarray) -> tuple[float, np.ndarray]:
    d = params.arm / np.sqrt(2)
    c = params.km / params.kf
    f1, f2, f3, f4 = rotor
    thrust = rotor.sum()
    torques = np.array([d * (-f1 + f2 + f3 - f4), d * (f1 - f2 + f3 - f4), c * (f1 + f2 - f3 - f4)])
    return thrust, torques


def dynamics(state: np.ndarray, rotor: np.ndarray, params: QuadParams,
             disturbance: np.ndarray | None = None) -> np.ndarray:
    """Time derivative of the state for given rotor thrusts.

    `disturbance` is an optional body-torque vector (N·m), e.g. a wind gust.
    """
    vel = state[3:6]
    phi, theta, psi = state[6:9]
    pqr = state[9:12]

    thrust, torques = forces_from_rotors(params, rotor)
    if disturbance is not None:
        torques = torques + disturbance

    accel = rotation_matrix(phi, theta, psi) @ np.array([0.0, 0.0, thrust]) / params.mass
    accel += np.array([0.0, 0.0, -G]) - params.drag * vel / params.mass

    inertia = params.inertia
    ang_accel = np.linalg.solve(inertia, torques - np.cross(pqr, inertia @ pqr))

    return np.concatenate([vel, accel, euler_rates(phi, theta, pqr), ang_accel])


def rk4_step(state, rotor, params, dt, disturbance=None):
    k1 = dynamics(state, rotor, params, disturbance)
    k2 = dynamics(state + 0.5 * dt * k1, rotor, params, disturbance)
    k3 = dynamics(state + 0.5 * dt * k2, rotor, params, disturbance)
    k4 = dynamics(state + dt * k3, rotor, params, disturbance)
    return state + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
