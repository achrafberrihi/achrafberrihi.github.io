"""Train a YOLOv8 component detector on a Roboflow PCB dataset and deploy it back to Roboflow.

    pip install ultralytics roboflow
    export ROBOFLOW_API_KEY=...
    python training/train_yolo.py --workspace my-ws --project pcb-components --version 3 --epochs 80

Steps: download the dataset in YOLOv8 format → fine-tune a pretrained model → report mAP →
upload the weights so the hosted endpoint (used by n8n and inspect_board.py) serves the new model.
"""
import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", type=int, required=True)
    parser.add_argument("--model", default="yolov8s.pt", help="pretrained checkpoint to fine-tune")
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--imgsz", type=int, default=1024, help="PCB parts are small, so use a large input size")
    parser.add_argument("--deploy", action="store_true", help="upload trained weights to Roboflow")
    args = parser.parse_args()

    from roboflow import Roboflow
    from ultralytics import YOLO

    rf = Roboflow(api_key=os.environ["ROBOFLOW_API_KEY"])
    version = rf.workspace(args.workspace).project(args.project).version(args.version)
    dataset = version.download("yolov8")

    model = YOLO(args.model)
    model.train(data=f"{dataset.location}/data.yaml", epochs=args.epochs, imgsz=args.imgsz,
                patience=20, mosaic=1.0, degrees=10, flipud=0.5, fliplr=0.5)  # boards can be photographed any way up
    metrics = model.val()
    print(f"mAP50: {metrics.box.map50:.3f}  mAP50-95: {metrics.box.map:.3f}")

    if args.deploy:
        version.deploy(model_type="yolov8", model_path=str(model.trainer.save_dir))
        print("Weights uploaded: the hosted endpoint now serves this model.")


if __name__ == "__main__":
    main()
