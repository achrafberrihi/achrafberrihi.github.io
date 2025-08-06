"""
Example predictive maintenance script for the MoorMaster™ NXG system.

This script demonstrates how to load sensor data, preprocess it, train a logistic regression model,
and evaluate its performance. Replace the file paths and column names with those specific to your dataset.
"""
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler


def load_data(csv_path: str) -> pd.DataFrame:
    """Load the maintenance dataset from a CSV file."""
    data = pd.read_csv(csv_path)
    return data


def preprocess_data(df: pd.DataFrame, target_col: str):
    """Split features and target, then scale the features."""
    X = df.drop(columns=[target_col])
    y = df[target_col]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    return X_scaled, y


def train_model(X, y) -> LogisticRegression:
    """Train a logistic regression classifier."""
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    print("Classification Report:")
    print(classification_report(y_test, y_pred))
    return clf


def main():
    # Path to your dataset CSV
    csv_path = "./your_dataset.csv"
    target_column = "failure"

    df = load_data(csv_path)
    X, y = preprocess_data(df, target_column)
    train_model(X, y)


if __name__ == "__main__":
    main()