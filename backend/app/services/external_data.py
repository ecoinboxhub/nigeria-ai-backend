from datetime import datetime

import pandas as pd


def fetch_supplier_prices_mock() -> pd.DataFrame:
    # Replace with AroundDeal/supplier API integrations in production.
    return pd.DataFrame(
        {
            "supplier": ["Dangote", "BUA", "African Steel"],
            "material": ["cement", "cement", "steel"],
            "price_ngn": [12000, 11850, 955000],
            "fetched_at": [datetime.utcnow()] * 3,
        }
    )
