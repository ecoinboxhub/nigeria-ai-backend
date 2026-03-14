import logging
from sqlalchemy import text
from app.db.session import SessionLocal
from app.modules.procurement_assistant.schemas import ProcurementQuery, ProcurementResponse, SupplierQuote

logger = logging.getLogger(__name__)


def _load_last_prices(material: str) -> list[tuple[str, float, str]]:
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                """
                SELECT supplier, price_ngn, location
                FROM supplier_quotes
                WHERE LOWER(material) LIKE :material
                ORDER BY scraped_at DESC
                LIMIT 5
                """
            ),
            {"material": f"%{material.lower()}%"},
        ).fetchall()
        return [(r[0], float(r[1]), r[2]) for r in rows]
    except Exception as e:
        logger.error(f"Failed to load last prices for {material} from DB: {e}")
        return []
    finally:
        db.close()


def supplier_intelligence(query: ProcurementQuery) -> ProcurementResponse:
    live = _load_last_prices(query.material)

    if live:
        source = live
    else:
        base = {
            "cement": [("Dangote", 12000, query.location), ("BUA", 11850, query.location), ("African Steel", 12200, query.location)],
            "steel": [("African Steel", 955000, query.location), ("Dangote", 948000, query.location), ("BUA", 962000, query.location)],
            "paint": [("Eagle Paints", 14500, query.location), ("QMB Builders MART", 14100, query.location), ("Atlantic Infinity Limited", 14900, query.location)],
        }
        source = base.get(query.material.lower(), [("QMB Builders MART", 50000, query.location)])

    quotes: list[SupplierQuote] = []
    for idx, (supplier, latest, _loc) in enumerate(source):
        forecast = latest * (1 + 0.015 * (query.horizon_days / 30))
        reliability = max(0.5, min(0.98, 0.75 + ((idx + 1) * 0.04) - 0.01 * (query.horizon_days / 30)))
        quotes.append(
            SupplierQuote(
                supplier=supplier,
                latest_price_ngn=round(latest, 2),
                forecast_price_ngn=round(forecast, 2),
                reliability_score=round(reliability, 3),
            )
        )

    best = min(quotes, key=lambda x: x.forecast_price_ngn / max(x.reliability_score, 0.01))
    return ProcurementResponse(material=query.material, quotes=quotes, best_supplier=best.supplier)
