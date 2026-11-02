# Unity digital twin

Builds a 3D model of the inspected board from the `pcb-digital-twin/1` JSON: board outline, one object per detected component at its real position, coloured by status (green ok, amber review, red issue). Click a component in Play mode to see its designator, confidence and notes.

## Setup (Unity 2021 LTS or newer)

1. Copy `Scripts/` into `Assets/Scripts/` and `StreamingAssets/` into `Assets/StreamingAssets/`.
2. Create an empty GameObject, add **PcbDigitalTwin**, press Play: the sample board is built from `digital_twin_sample.json`.
3. Optional: add component prefabs in the **Prefabs** list using the names from the JSON (`IC_QFP`, `Resistor_0805`, `Capacitor_0805`, `Crystal_HC49`…). Without prefabs, scaled cubes are used.
4. **Live mode:** set **n8n Webhook Url** to your `pcb-inspect` webhook and **Image Url** to a board photo. The twin is then built from a fresh inspection, and the LLM explanation is available in `PcbDigitalTwin.Explanation`.

Units: 1 Unity unit = 1 cm. The JSON origin is the bottom-left corner of the board, the Unity board is centred on its GameObject.
