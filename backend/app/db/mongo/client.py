from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

from app.core.config import settings


class SiteLogDoc(BaseModel):
    project_id: str
    log_text: str
    images: list[str] = Field(default_factory=list)
    weather_snapshot: dict = Field(default_factory=dict)
    created_at: str


class DocumentChunkDoc(BaseModel):
    doc_id: str
    title: str
    chunk_text: str
    embedding_id: str
    source: str
    created_at: str


class TenderDoc(BaseModel):
    tender_id: str
    title: str
    text: str
    risks: list[dict] = Field(default_factory=list)
    summary: str = ""
    compliance_score: float = 0.0
    created_at: str


_mongo_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(settings.mongo_uri)
    return _mongo_client


def get_mongo_db():
    return get_mongo_client()[settings.mongo_db]
