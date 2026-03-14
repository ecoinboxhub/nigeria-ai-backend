import warnings

import mlflow
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

warnings.filterwarnings("ignore")


def main() -> None:
    df = pd.read_csv("data/raw/supplier_prices.csv")
    series = df["cement_price_ngn"]

    train = series[:-30]
    test = series[-30:]

    model = ARIMA(train, order=(3, 1, 2)).fit()
    forecast = model.forecast(steps=len(test))

    mape = (abs((test - forecast) / test)).mean()

    mlflow.set_experiment("procurement_assistant")
    with mlflow.start_run(run_name="arima_cement"):
        mlflow.log_param("order", "(3,1,2)")
        mlflow.log_metric("mape", float(mape))

    print(f"Procurement ARIMA MAPE: {mape:.4f}")


if __name__ == "__main__":
    main()
