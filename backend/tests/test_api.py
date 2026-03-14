import asyncio

import httpx

from app.main import app


def client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


def test_health() -> None:
    async def _run() -> httpx.Response:
        async with client() as c:
            return await c.get('/api/v1/health')

    response = asyncio.run(_run())
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_token_and_project_tracker_flow() -> None:
    async def _token() -> httpx.Response:
        async with client() as c:
            return await c.post('/api/v1/integration/token', headers={'X-API-Key': 'change-me'}, json={'username': 'demo', 'role': 'project_manager'})

    token_resp = asyncio.run(_token())
    assert token_resp.status_code == 200
    token = token_resp.json()['access_token']

    async def _predict() -> httpx.Response:
        async with client() as c:
            return await c.post(
                '/api/v1/project-tracker/predict-delay',
                headers={'Authorization': f'Bearer {token}'},
                json={
                    'rainfall_mm': 55,
                    'temperature_c': 31,
                    'wind_speed_kmh': 22,
                    'resource_availability': 0.7,
                    'workforce_attendance': 0.78,
                    'supply_delay_days': 4,
                },
            )

    response = asyncio.run(_predict())
    assert response.status_code == 200
    assert 'delay_risk' in response.json()


def test_integration_catalog_endpoints() -> None:
    async def _token() -> httpx.Response:
        async with client() as c:
            return await c.post(
                '/api/v1/integration/token',
                headers={'X-API-Key': 'change-me'},
                json={'username': 'analyst-user', 'role': 'analyst'},
            )

    token_resp = asyncio.run(_token())
    assert token_resp.status_code == 200
    token = token_resp.json()['access_token']

    async def _module_status() -> httpx.Response:
        async with client() as c:
            return await c.get(
                '/api/v1/integration/module-status',
                headers={'Authorization': f'Bearer {token}'},
            )

    status_resp = asyncio.run(_module_status())
    assert status_resp.status_code == 200
    assert len(status_resp.json()['items']) >= 10

    async def _endpoint_catalog() -> httpx.Response:
        async with client() as c:
            return await c.get(
                '/api/v1/integration/endpoints',
                headers={'Authorization': f'Bearer {token}'},
            )

    catalog_resp = asyncio.run(_endpoint_catalog())
    assert catalog_resp.status_code == 200
    paths = [item['path'] for item in catalog_resp.json()['items']]
    assert '/api/v1/project-tracker/predict-delay' in paths
