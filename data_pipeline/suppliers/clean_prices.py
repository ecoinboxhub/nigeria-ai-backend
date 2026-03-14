import logging
import os
from pathlib import Path

import pandas as pd
from pymongo import MongoClient
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("clean_prices")

RAW_DIR = Path("data/raw/supplier_prices")
OUT = RAW_DIR / "supplier_prices_clean.csv"


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["supplier", "material", "location", "unit", "source_url"]:
        df[col] = df[col].astype(str).str.strip()
    df["price_ngn"] = pd.to_numeric(df["price_ngn"], errors="coerce")
    df = df[df["price_ngn"].notna()]
    df = df[df["price_ngn"] > 0]
    df = df.drop_duplicates(subset=["supplier", "material", "price_ngn", "scraped_at"])
    return df


def _persist_postgres(df: pd.DataFrame) -> None:
    database_url = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/construction_ai")
    engine = create_engine(database_url)
    with engine.begin() as conn:
        for _, row in df.iterrows():
            conn.execute(
                text(
                    """
                    INSERT INTO supplier_quotes
                    (supplier, material, location, price_ngn, unit, reliability_score, forecast_price_ngn, source_url, scraped_at)
                    VALUES (:supplier, :material, :location, :price_ngn, :unit, :reliability_score, :forecast_price_ngn, :source_url, :scraped_at)
                    """
                ),
                {
                    "supplier": row["supplier"],
                    "material": row["material"],
                    "location": row["location"],
                    "price_ngn": float(row["price_ngn"]),
                    "unit": row.get("unit", "unit"),
                    "reliability_score": None,
                    "forecast_price_ngn": None,
                    "source_url": row.get("source_url", ""),
                    "scraped_at": row["scraped_at"],
                },
            )


def _persist_mongo(df: pd.DataFrame) -> None:
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db = os.getenv("MONGO_DB", "construction_ai")
    client = MongoClient(mongo_uri)
    col = client[mongo_db]["supplier_prices"]
    records = df.to_dict(orient="records")
    if records:
        col.insert_many(records)


def main() -> None:
    files = list(RAW_DIR.glob("*_raw.csv"))
    if not files:
        logger.warning("no raw supplier files found")
        return

    frames = [pd.read_csv(f) for f in files]
    combined = pd.concat(frames, ignore_index=True)
    cleaned = _normalize(combined)
    cleaned.to_csv(OUT, index=False)

    try:
        _persist_postgres(cleaned)
    except Exception as exc:
        logger.warning("postgres persist failed: %s", exc)

    try:
        _persist_mongo(cleaned)
    except Exception as exc:
        logger.warning("mongo persist failed: %s", exc)

    logger.info("cleaned %s supplier rows", len(cleaned))


if __name__ == "__main__":
    main()
