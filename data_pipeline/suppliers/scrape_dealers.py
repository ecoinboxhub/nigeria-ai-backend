import csv
import logging
import re
from datetime import UTC, datetime
from pathlib import Path

import mlflow

from data_pipeline.suppliers.common import fetch_with_retries, parse_html

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scrape_dealers")

SUPPLIER_URLS = {
    "Dangote": "https://www.dangote.com",
    "BUA": "https://www.buagroup.com",
    "Lafarge Africa": "https://www.lafarge.com.ng",
    "African Steel": "https://africanindustries.com",
    "UniCem Nigeria": "https://unitedcement.com",
    "Eagle Paints": "https://eaglepaints.com.ng",
    "First Aluminium Nigeria PLC": "https://firstaluminium.com",
    "Inland Doors Nigeria LTD": "https://inlanddoors.com",
    "QMB Builders MART": "https://qmbbuildersmart.com",
    "Oiltools Africa Limited": "https://oiltoolsafrica.com",
    "KPI Construction Services LTD": "https://kpi.com.ng",
    "Atlantic Infinity Limited": "https://atlanticinfinity.com",
}

MATERIAL_HINTS = ["cement", "steel", "paint", "aluminium", "doors", "roof", "tiles", "blocks"]
OUT = Path("data/raw/supplier_prices/dealers_raw.csv")


def extract_prices(text: str) -> list[float]:
    return [float(x.replace(",", "")) for x in re.findall(r"(?:₦|NGN)?\s*([\d,]{4,}(?:\.\d+)?)", text)]


def infer_material(text: str) -> str:
    t = text.lower()
    for m in MATERIAL_HINTS:
        if m in t:
            return m
    return "construction material"


def scrape() -> list[dict]:
    rows: list[dict] = []
    for supplier, url in SUPPLIER_URLS.items():
        try:
            res = fetch_with_retries(url)
            soup = parse_html(res.html)
            body = soup.get_text(" ", strip=True)
            material = infer_material(body)
            prices = extract_prices(body)[:5]
            for price in prices:
                rows.append(
                    {
                        "supplier": supplier,
                        "material": material,
                        "price_ngn": price,
                        "location": "Nigeria",
                        "unit": "unit",
                        "scraped_at": datetime.now(UTC).isoformat(),
                        "source_url": url,
                    }
                )
        except Exception as exc:
            logger.warning("skipping %s due to %s", supplier, exc)

    return rows


def main() -> None:
    rows = scrape()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["supplier", "material", "price_ngn", "location", "unit", "scraped_at", "source_url"],
        )
        writer.writeheader()
        writer.writerows(rows)

    mlflow.set_experiment("procurement_scraping")
    with mlflow.start_run(run_name="scrape_dealers"):
        mlflow.log_metric("rows", len(rows))

    logger.info("saved %s rows to %s", len(rows), OUT)


if __name__ == "__main__":
    main()
