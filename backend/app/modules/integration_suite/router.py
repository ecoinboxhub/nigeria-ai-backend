from fastapi import APIRouter, Depends

from app.core.rbac import Role, require_role
from app.core.security import verify_api_key
from app.modules.integration_suite.schemas import (
    EndpointCatalogResponse,
    ModuleStatusResponse,
    RefreshTokenRequest,
    TokenRequest,
    TokenResponse,
)
from app.modules.integration_suite.service import (
    get_endpoint_catalog,
    get_module_status,
    issue_token,
    refresh_token,
)

router = APIRouter()


@router.post('/token', response_model=TokenResponse, dependencies=[Depends(verify_api_key)])
def issue_token_endpoint(payload: TokenRequest) -> TokenResponse:
    return issue_token(payload)


@router.post('/refresh', response_model=TokenResponse)
def refresh_token_endpoint(payload: RefreshTokenRequest) -> TokenResponse:
    return refresh_token(payload)


@router.get(
    '/module-status',
    response_model=ModuleStatusResponse,
    dependencies=[Depends(require_role([Role.ADMIN, Role.PM, Role.ANALYST]))],
)
def module_status_endpoint() -> ModuleStatusResponse:
    return get_module_status()


@router.get(
    '/endpoints',
    response_model=EndpointCatalogResponse,
    dependencies=[Depends(require_role([Role.ADMIN, Role.PM, Role.ANALYST]))],
)
def endpoint_catalog_endpoint() -> EndpointCatalogResponse:
    return get_endpoint_catalog()
