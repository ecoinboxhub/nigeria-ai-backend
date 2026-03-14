import os
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    np.random.seed(42)
    rows = 1500

    weather = pd.DataFrame(
        {
            "rainfall_mm": np.random.gamma(3, 12, rows),
            "temperature_c": np.random.normal(30, 4, rows),
            "wind_speed_kmh": np.random.normal(20, 8, rows).clip(0),
            "resource_availability": np.random.uniform(0.5, 1.0, rows),
            "workforce_attendance": np.random.uniform(0.55, 1.0, rows),
            "supply_delay_days": np.random.randint(0, 8, rows),
        }
    )

    delay_signal = (
        (weather["rainfall_mm"] > 35).astype(int)
        + (weather["resource_availability"] < 0.75).astype(int)
        + (weather["workforce_attendance"] < 0.8).astype(int)
        + (weather["supply_delay_days"] > 3).astype(int)
    )
    weather["delay_label"] = (delay_signal >= 2).astype(int)

    suppliers = pd.DataFrame(
        {
            "date": pd.date_range("2021-01-01", periods=600, freq="D"),
            "cement_price_ngn": 10500 + np.cumsum(np.random.normal(3, 35, 600)),
            "steel_price_ngn": 850000 + np.cumsum(np.random.normal(40, 2300, 600)),
        }
    )

    costs = pd.DataFrame(
        {
            "area_sqm": np.random.uniform(100, 8000, rows),
            "floors": np.random.randint(1, 15, rows),
            "complexity_index": np.random.uniform(0.7, 1.8, rows),
            "labor_cost_index": np.random.uniform(0.8, 1.7, rows),
            "materials_cost_index": np.random.uniform(0.8, 2.1, rows),
        }
    )
    costs["total_cost_ngn"] = (
        210000
        * costs["area_sqm"]
        * costs["floors"]
        * costs["complexity_index"]
        * costs["labor_cost_index"]
        * costs["materials_cost_index"]
        * np.random.normal(1.0, 0.08, rows)
    )

    out = Path("data/raw")
    out.mkdir(parents=True, exist_ok=True)
    weather.to_csv(out / "project_delay.csv", index=False)
    suppliers.to_csv(out / "supplier_prices.csv", index=False)
    costs.to_csv(out / "project_costs.csv", index=False)

    safety_logs = pd.DataFrame(
        {
            "project_id": [f"P-{i:03d}" for i in range(1, 201)],
            "log_text": [
                "No helmet observed near scaffold and electrical extension spill risk" if i % 2 == 0 else "Daily toolbox talk completed, no incident"
                for i in range(1, 201)
            ],
            "hazard": [1 if i % 2 == 0 else 0 for i in range(1, 201)],
        }
    )
    safety_logs.to_csv(out / "safety_logs.csv", index=False)

    docs = pd.DataFrame(
        {
            "doc_id": [f"D-{i:03d}" for i in range(1, 121)],
            "text": [
                "payment terms variation termination dispute resolution health and safety" if i % 3 != 0 else "payment terms termination"
                for i in range(1, 121)
            ],
            "compliant": [1 if i % 3 != 0 else 0 for i in range(1, 121)],
        }
    )
    docs.to_csv(out / "document_labels.csv", index=False)

    print("Synthetic MVP datasets created in data/raw")


if __name__ == "__main__":
    main()
