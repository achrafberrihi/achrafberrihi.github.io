# Training the YOLO component detector

1. **Dataset (Roboflow):** collect PCB photos (top view, even lighting, several boards and angles) and annotate bounding boxes for the classes used by the analysis: `resistor`, `capacitor`, `electrolytic capacitor`, `ic`, `transistor`, `diode`, `led`, `inductor`, `connector`, `crystal`, `switch`. Public PCB component datasets on Roboflow Universe are a good starting point.
2. **Preprocessing / augmentation:** auto-orient, resize to 1024 px (components are small), rotations of 90°, flips, brightness ±20 %, slight blur.
3. **Train:** `python training/train_yolo.py --workspace <ws> --project <project> --version <n> --deploy`, or train directly in Roboflow.
4. **Evaluate:** check mAP50 per class. Small passives (0402/0603) are usually the weakest, so add close-up images for them.
5. **Serve:** the deployed version is reachable at `https://detect.roboflow.com/<project>/<version>`, which is what `inspect_board.py` and the n8n workflow call.

Class names are normalized by `pcb_inspector/analysis.py` (`CANONICAL`), so labels such as `cap`, `chip` or `oscillator` also work.
