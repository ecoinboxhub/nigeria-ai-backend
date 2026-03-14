import mlflow
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA


def main() -> None:
    df = pd.read_csv("data/raw/supplier_prices.csv")
    # Proxy equipment utilization signal from steel prices for MVP.
    signal = df["steel_price_ngn"]
    train = signal[:-20]
    test = signal[-20:]

    model = ARIMA(train, order=(2, 1, 2)).fit()
    pred = model.forecast(steps=len(test))
    mape = (abs((test - pred) / test)).mean()

    mlflow.set_experiment("maintenance_predictor")
    with mlflow.start_run(run_name="equipment_failure_proxy"):
        mlflow.log_metric("mape", float(mape))

    print(f"Maintenance predictor proxy MAPE: {mape:.4f}")


if __name__ == "__main__":
    main()
