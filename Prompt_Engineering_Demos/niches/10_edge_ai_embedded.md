# Edge AI & Embedded Systems

Prompts for on-device ML, firmware and IoT.

## 1. Model compression planner

```text
I need to deploy a {model_type} model ({params} parameters, {accuracy} accuracy) on a
{target_hardware} with {ram} RAM, {flash} flash and a {latency_ms} ms latency budget.

Propose a compression plan (quantization type, pruning, distillation, architecture changes),
the expected size, latency and accuracy impact of each step, and the toolchain
(TFLite Micro, ONNX Runtime, TensorRT…). Order steps from least to most accuracy loss.
```

> **Why it works:** hard constraints up front force realistic, ordered trade-offs.

## 2. Embedded C reviewer

```text
Review this embedded C code for a {microcontroller}:

{code}

Check for: buffer overflows, integer overflow, blocking calls in ISRs, missing volatile,
race conditions with interrupts, dynamic allocation, and power consumption issues.
For each issue give the line, the risk, and the fix.
```

> **Why it works:** an embedded-specific checklist catches bugs general reviewers miss.

## 3. Sensor fusion explainer and implementation

```text
I have {sensors} (e.g. accelerometer + gyroscope at 100 Hz) on a {platform}.
Goal: {goal} (e.g. stable orientation estimate).

1. Recommend a fusion method (complementary filter, Kalman, Madgwick) and justify it for this hardware.
2. Give a C implementation with fixed-size arrays and no dynamic memory.
3. Explain how to tune its parameters with real data.
```

> **Why it works:** asking for justification relative to hardware avoids over-engineered solutions.

## 4. IoT telemetry design

```text
Design the telemetry for {device_count} battery-powered {device_type} devices.

Specify: which signals to send and at what rate, on-device aggregation, payload format
(size in bytes), protocol (MQTT/LoRaWAN/BLE), what triggers an immediate alert,
and estimated battery life impact. Target: {battery_target}.
```

> **Why it works:** payload size and battery impact keep the design grounded in real constraints.

## 5. On-device anomaly detection

```text
Design a lightweight anomaly detector running on a {mcu} for {signal}
(e.g. motor vibration at 1 kHz).

Give: features to compute on-device (with memory cost), the detection method
(threshold, z-score, tiny autoencoder…), how to calibrate it per device, and how to avoid
false alarms. Include pseudocode that fits in {ram} RAM.
```

> **Why it works:** per-device calibration and false-alarm handling are what make edge detectors usable.
