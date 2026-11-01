# Electrical Study of a Steam Turbo-Alternator — OCP Group, Jorf Lasfar

**Engineering internship (PFA), July – August 2026** · Supervisors: OCP and EMSI

Study of the electrical side of a 25 MVA steam turbo-alternator at the Jorf Lasfar chemical complex, which turns process steam into electricity for the site. Because a generator fault stops this self-generation, the goal was to understand the installation end to end and how it is protected.

## Context

Steam from the **sulfuric acid plant** (high pressure) and the **phosphoric acid plant** (low/medium pressure) drives the turbine. The turbine turns the alternator shaft, and a step-up transformer feeds the site network.

```
HP steam ─┐
          ├─► turbine ──► alternator 5.5 kV ──► step-up transformer 5.5/22 kV ──► site network
LP/MP steam ┘                │
                         brushless exciter + AVR
```

## Alternator construction

| Part | Design |
|---|---|
| Stator | Laminated magnetic core with a three-phase winding |
| Rotor | Smooth (cylindrical) poles, rotating magnetic field |
| Excitation | Brushless exciter controlled by an automatic voltage regulator (AVR) |

## Key calculations

Run `python turbo_alternator.py`.

| Quantity | Value | How |
|---|---|---|
| Apparent power S | 25 MVA | rating |
| Rated current, 5.5 kV side | **≈ 2,624 A** | I = S / (√3 · U) |
| Rated current, 22 kV side | ≈ 656 A | same formula on the HV side |
| Transformer ratio | 1:4 (5.5/22 kV) | rating |
| Active / reactive power at cos φ = 0.8 | 20 MW / 15 Mvar | typical power factor |
| Synchronous speed | 3,000 rpm | 2-pole smooth rotor at 50 Hz (assumed) |
| Subtransient short-circuit current | ≈ 17.5 kA | In / X''d with typical X''d = 0.15 |

## Generator protection

| ANSI | Function | Fault detected |
|---|---|---|
| 87G | Generator differential | Internal stator short circuit |
| 59/27 | Over/under-voltage | Voltage regulation (AVR) fault |
| 12 | Overspeed | Mechanical runaway after load rejection |
| 40 | Loss of excitation | Field (exciter) failure |

`turbo_alternator.py` also lists typical settings for each function, for illustration only (not plant settings).

## Synchronization and voltage regulation

Before closing the generator breaker, the synchro-check (ANSI 25) requires the same **voltage**, **frequency**, **phase angle** and **phase sequence** as the grid. Once coupled, the AVR holds the terminal voltage by acting on the exciter field current. `synchronization_check()` implements the permissive logic with typical limits (ΔU ≤ 5 %, Δf ≤ 0.1 Hz, Δφ ≤ 10°).

## Proposed improvement: AI predictive maintenance

Fixed protection thresholds trip when a fault is already present. The study proposes continuous collection of **sensor, IED (protection relay) and vibration data** feeding a machine-learning model that detects early drifts invisible to fixed thresholds, with a dashboard for the maintenance team. The approach is prototyped in [`../MoorMaster_ML_Maintenance`](../MoorMaster_ML_Maintenance) and [`../Air_Quality_Anomaly_PowerBI`](../Air_Quality_Anomaly_PowerBI).

## Takeaways

- Hands-on view of a complete industrial power chain, from steam to the site network.
- Generator protection philosophy: which relay covers which failure, and why each one matters.
- Next step: deploy the predictive model on real IED and vibration data.

> Only information suitable for public sharing is included. Plant-specific settings and drawings remain confidential to OCP Group.
