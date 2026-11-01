"""Predictive-maintenance baseline for industrial sensor data (MoorMaster NXG case study).

Loads a CSV of sensor features with a binary failure label, splits it with
stratification, fits a classifier inside a pipeline (so no test data leaks
into the scaler) and reports the metrics that matter for maintenance:
recall on failures (missed failures are expensive), precision, and ROC-AUC.

    python generate_data.py                      # synthetic demo data -> data.csv
    python sample_code.py data.csv --model all   # compare models
"""
import argparse

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

# class_weight="balanced": failures are rare, so weight them up instead of
# letting the model score well by predicting "no failure" everywhere.
MODELS = {
    "logistic": lambda: LogisticRegression(max_iter=1000, class_weight="balanced"),
    "decision_tree": lambda: DecisionTreeClassifier(max_depth=6, class_weight="balanced", random_state=42),
    "random_forest": lambda: RandomForestClassifier(n_estimators=300, min_samples_leaf=3, class_weight="balanced",
                                                    n_jobs=-1, random_state=42),
}


def load_data(path: str, target: str):
    df = pd.read_csv(path).dropna(subset=[target])
    X = df.drop(columns=[target]).select_dtypes("number")
    X = X.fillna(X.median())
    return X, df[target].astype(int)


def train_and_evaluate(X, y, model_name: str = "logistic", test_size: float = 0.2, verbose: bool = True) -> dict:
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, stratify=y, random_state=42)
    model = make_pipeline(StandardScaler(), MODELS[model_name]())
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = {
        "model": model_name,
        "failure_recall": recall_score(y_test, y_pred),
        "failure_precision": precision_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_prob),
    }
    if verbose:
        print(f"\n=== {model_name}  (train={len(X_train)}, test={len(X_test)}) ===")
        print(classification_report(y_test, y_pred, digits=3, target_names=["normal", "failure"]))
        print("Confusion matrix [rows=actual, cols=predicted]:\n", confusion_matrix(y_test, y_pred))
        if model_name in ("decision_tree", "random_forest"):
            importances = pd.Series(model[-1].feature_importances_, index=X.columns).sort_values(ascending=False)
            print("\nTop features:\n", importances.head(5).round(3).to_string())
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv", help="path to the sensor dataset")
    parser.add_argument("--target", default="failure", help="name of the binary label column")
    parser.add_argument("--model", choices=[*MODELS, "all"], default="logistic")
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()

    X, y = load_data(args.csv, args.target)
    names = list(MODELS) if args.model == "all" else [args.model]
    results = [train_and_evaluate(X, y, n, args.test_size) for n in names]

    if len(results) > 1:
        print("\n=== Comparison ===")
        print(pd.DataFrame(results).set_index("model").round(3).to_string())


if __name__ == "__main__":
    main()
