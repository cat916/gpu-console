import httpx
import pytest

pytestmark = pytest.mark.anyio


async def test_lists_instance_types(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/instance-types")

    assert response.status_code == 200
    h100 = next(item for item in response.json() if item["id"] == "1x-h100")
    assert h100 == {
        "id": "1x-h100",
        "gpu_model": "H100 80GB",
        "gpu_count": 1,
        "vcpus": 22,
        "memory_gb": 185,
        "price_per_hour": 2.29,
    }


async def test_lists_images(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/images")

    assert response.status_code == 200
    assert {"id": "ubuntu-24.04-cuda-12.8", "name": "Ubuntu 24.04 + CUDA 12.8"} in response.json()


async def test_health_check(client: httpx.AsyncClient) -> None:
    response = await client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_unknown_route_uses_error_format(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/nope")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
