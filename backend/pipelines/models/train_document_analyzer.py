import mlflow
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


def main() -> None:
    df = pd.read_csv("data/raw/document_labels.csv")
    X = df["text"]
    y = df["compliant"]

    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    clf = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
            ("lr", LogisticRegression(max_iter=500)),
        ]
    )
    clf.fit(x_train, y_train)
    y_pred = clf.predict(x_test)
    accuracy = accuracy_score(y_test, y_pred)

    mlflow.set_experiment("document_analyzer")
    with mlflow.start_run(run_name="doc_compliance"):
        mlflow.log_metric("accuracy", float(accuracy))

    print(f"Document compliance accuracy: {accuracy:.4f}")


if __name__ == "__main__":
    main()
