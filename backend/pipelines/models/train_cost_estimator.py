import mlflow
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error
from sklearn.model_selection import train_test_split


def main() -> None:
    df = pd.read_csv("data/raw/project_costs.csv")
    X = df.drop(columns=["total_cost_ngn"])
    y = df["total_cost_ngn"]

    # Deterministic baseline from engineering quantity take-off equation.
    base_cost = (
        210000
        * X["area_sqm"]
        * X["floors"]
        * X["complexity_index"]
        * X["labor_cost_index"]
        * X["materials_cost_index"]
    )
    X = X.copy()
    X["base_cost"] = base_cost

    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    rf = RandomForestRegressor(n_estimators=350, random_state=42)
    rf.fit(x_train, y_train)

    pred = 0.7 * x_test["base_cost"].to_numpy() + 0.3 * rf.predict(x_test)

    rmse = mean_squared_error(y_test, pred, squared=False)
    mape = mean_absolute_percentage_error(y_test, pred)

    mlflow.set_experiment("cost_estimator")
    with mlflow.start_run(run_name="cost_ensemble"):
        mlflow.log_metric("rmse", float(rmse))
        mlflow.log_metric("mape", float(mape))

    print(f"Cost model RMSE: {rmse:.2f}")
    print(f"Cost model MAPE: {mape:.4f}")
    print(f"RMSE ratio to mean target: {rmse / np.mean(y_test):.4f}")


if __name__ == "__main__":
    main()
