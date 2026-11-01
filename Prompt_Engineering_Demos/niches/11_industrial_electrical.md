# Industrial Maintenance & Electrical Engineering

Prompts for maintenance, automation and electrical systems. Outputs support engineers — they don't replace on-site safety procedures or certified checks.

## 1. Fault diagnosis assistant

```text
Equipment: {equipment} (model, age, operating conditions)
Symptoms: {symptoms}
Recent maintenance: {history}
Sensor readings: {readings}

List the 5 most likely causes, ranked. For each: why the symptoms point to it, the
check to confirm it (with tools needed), and the corrective action. Flag any cause that
requires lockout/tagout or a certified technician.
```

> **Why it works:** ranked causes with confirmation steps speed up troubleshooting; safety flags stay explicit.

## 2. Preventive maintenance plan

```text
Create a preventive maintenance plan for {asset_list} in a {industry} plant running {hours} hours/day.

For each asset: tasks, frequency (daily/weekly/monthly/yearly), estimated duration,
skills required, spare parts to stock, and the failure mode each task prevents.
Return as a table sorted by criticality.
```

> **Why it works:** linking each task to a failure mode justifies the plan and helps prioritize.

## 3. PLC logic generator

```text
Write IEC 61131-3 Structured Text for this control sequence:
{sequence_description}
(e.g. "Start pump P1 when tank level < 20%, stop at 80%, alarm if running > 30 min").

Inputs/outputs: {io_list}
Include: interlocks, an emergency stop that overrides everything, alarm handling and comments.
Then list the test cases to validate it on the simulator before commissioning.
```

> **Why it works:** E-stop priority and a test list keep generated logic safe to validate.

## 4. Root cause analysis (5 Whys + Ishikawa)

```text
Incident: {incident_description}
Impact: {downtime_cost}
Data available: {data}

1. Build an Ishikawa diagram as a list (Man, Machine, Method, Material, Measurement, Environment).
2. Run a 5 Whys on the most probable branch.
3. Propose corrective and preventive actions with owners and deadlines.
```

> **Why it works:** combines breadth (Ishikawa) and depth (5 Whys) in one structured analysis.

## 5. Low-voltage installation sizing check

```text
Check this LV circuit design:
Load: {load_kw} kW, cos φ = {pf}, {phases}-phase, {voltage} V
Cable: {cable} ({section} mm², {length} m, installation method {method})
Protection: {breaker}

Compute: design current, voltage drop (%), and check the cable and breaker selection
against {standard} (e.g. NF C 15-100 / IEC 60364). Show each formula and value.
Conclude "compliant" or "not compliant" with the fix.
```

> **Why it works:** showing formulas makes the calculation verifiable by an engineer.
