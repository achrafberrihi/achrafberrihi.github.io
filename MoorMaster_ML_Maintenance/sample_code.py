import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score


def load_data(path):
    data = pd.read_csv(path)
    return data


def preprocess_data(data):
    # Example preprocessing
    X = data.drop('target', axis=1)
    y = data['target']
    # train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    # scaling
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)
    return X_train, X_test, y_train, y_test


def train_model(X_train, y_train, model='logistic'):
    if model == 'logistic':
        clf = LogisticRegression()
    elif model == 'decision_tree':
        clf = DecisionTreeClassifier()
    else:
        raise ValueError('Unsupported model type')
    clf.fit(X_train, y_train)
    return clf


def evaluate_model(model, X_test, y_test):
    preds = model.predict(X_test)
    return accuracy_score(y_test, preds)


def main():
    # path to your dataset
    data = load_data('data.csv')
    X_train, X_test, y_train, y_test = preprocess_data(data)
    model = train_model(X_train, y_train, model='logistic')
    accuracy = evaluate_model(model, X_test, y_test)
    print(f'Accuracy: {accuracy:.2f}')


if __name__ == '__main__':
    main()
