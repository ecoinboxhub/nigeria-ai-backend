import logging
from app.core.security import create_access_token, create_refresh_token, refresh_access_token
from app.modules.integration_suite.catalog import ENDPOINT_CATALOG, MODULE_STATUS
from app.modules.integration_suite.schemas import (
    EndpointCatalogResponse,
    ModuleStatusResponse,
    RefreshTokenRequest,
    TokenRequest,
    TokenResponse,
)

logger = logging.getLogger(__name__)


def issue_token(payload: TokenRequest) -> TokenResponse:
    access = create_access_token(subject=payload.username, role=payload.role)
    refresh = create_refresh_token(subject=payload.username, role=payload.role)
    return TokenResponse(access_token=access, refresh_token=refresh)


def refresh_token(payload: RefreshTokenRequest) -> TokenResponse:
    try:
        access, refresh = refresh_access_token(payload.refresh_token)
        return TokenResponse(access_token=access, refresh_token=refresh)
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise


def get_module_status() -> ModuleStatusResponse:
    return ModuleStatusResponse(items=MODULE_STATUS)


def get_endpoint_catalog() -> EndpointCatalogResponse:
    return EndpointCatalogResponse(items=ENDPOINT_CATALOG)

