"""Predictive-maintenance baseline for industrial sensor data (MoorMaster NXG case study).

Loads a CSV of sensor features with a binary failure label, splits it with
stratification, fits a scaled classifier inside a pipeline (so no test data
leaks into the scaler), and prints a classification report.

Usage:
    python sample_code.py data.csv --target failure --model logistic
"""
import argparse

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

MODELS = {
    # class_weight="balanced": failures are usually rare
    "logistic": lambda: LogisticRegression(max_iter=1000, class_weight="balanced"),
    "decision_tree": lambda: DecisionTreeClassifier(max_depth=6, class_weight="balanced", random_state=42),
}


def load_data(path: str, target: str):
    df = pd.read_csv(path).dropna(subset=[target])
    X = df.drop(columns=[target]).select_dtypes("number")
    X = X.fillna(X.median())
    return X, df[target]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", help="path to the sensor dataset")
    parser.add_argument("--target", default="failure", help="name of the binary label column")
    parser.add_argument("--model", choices=MODELS, default="logistic")
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()

    X, y = load_data(args.csv, args.target)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, stratify=y, random_state=42
    )

    model = make_pipeline(StandardScaler(), MODELS[args.model]())
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(f"Model: {args.model}  |  train={len(X_train)}  test={len(X_test)}\n")
    print(classification_report(y_test, y_pred, digits=3))
    print("Confusion matrix:\n", confusion_matrix(y_test, y_pred))


if __name__ == "__main__":
    main()
