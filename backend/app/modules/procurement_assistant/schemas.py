from pydantic import BaseModel, Field

class ProcurementQuery(BaseModel):
    material: str
    location: str = "Lagos"
    horizon_days: int = Field(default=30, ge=7, le=180)

class SupplierQuote(BaseModel):
    supplier: str
    latest_price_ngn: float
    forecast_price_ngn: float
    reliability_score: float

class ProcurementResponse(BaseModel):
    material: str
    quotes: list[SupplierQuote]
    best_supplier: str

class MaterialSchema(BaseModel):
    id: str | None = None
    name: str
    category: str
    sub_category: str | None = None
    unit: str | None = None
