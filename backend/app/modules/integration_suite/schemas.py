from pydantic import BaseModel


class TokenRequest(BaseModel):
    username: str
    role: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ModuleStatusItem(BaseModel):
    module: str
    completion_pct: int
    algorithms: list[str]
    metric_name: str
    metric_value: float | None
    target: str
    blockers: str


class ModuleStatusResponse(BaseModel):
    items: list[ModuleStatusItem]


class EndpointItem(BaseModel):
    method: str
    path: str
    module: str


class EndpointCatalogResponse(BaseModel):
    items: list[EndpointItem]
