import csv
import logging
import re
from datetime import UTC, datetime
from pathlib import Path

import mlflow

from data_pipeline.suppliers.common import fetch_with_retries, parse_html

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scrape_jiji")

BASE_URL = "https://jiji.ng/building-materials"
MATERIALS = ["cement", "reinforcement-bars", "blocks", "roofing-sheet", "tiles"]
OUT = Path("data/raw/supplier_prices/jiji_raw.csv")


def extract_price(text: str) -> float | None:
    m = re.search(r"([\d,]+(?:\.\d+)?)", text.replace("₦", ""))
    if not m:
        return None
    return float(m.group(1).replace(",", ""))


def scrape() -> list[dict]:
    rows: list[dict] = []
    for mat in MATERIALS:
        url = f"{BASE_URL}/{mat}"
        try:
            res = fetch_with_retries(url)
            soup = parse_html(res.html)
            cards = soup.select("article, div.b-list-advert-base")[:40]
            for card in cards:
                txt = card.get_text(" ", strip=True)
                price = extract_price(txt)
                if price is None:
                    continue
                rows.append(
                    {
                        "supplier": "Jiji Marketplace",
                        "material": mat.replace("-", " "),
                        "price_ngn": price,
                        "location": "Nigeria",
                        "unit": "unit",
                        "scraped_at": datetime.now(UTC).isoformat(),
                        "source_url": url,
                    }
                )
        except Exception as exc:
            logger.exception("failed to scrape %s: %s", url, exc)

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
    with mlflow.start_run(run_name="scrape_jiji"):
        mlflow.log_metric("rows", len(rows))
        mlflow.log_param("source", BASE_URL)

    logger.info("saved %s rows to %s", len(rows), OUT)


if __name__ == "__main__":
    main()
