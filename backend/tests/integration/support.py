import asyncio
from typing import Any

import httpx

from app.models import Instance

WAIT_TIMEOUT_SECONDS = 2


class ProviderCrash(Exception):
    pass


class ControllableProvider:
    def __init__(self) -> None:
        self.fail_create = False
        self.fail_delete = False

    async def create(self, instance: Instance) -> None:
        if self.fail_create:
            raise ProviderCrash("create exploded")

    async def delete(self, instance: Instance) -> None:
        if self.fail_delete:
            raise ProviderCrash("delete exploded")


async def launch(
    client: httpx.AsyncClient,
    name: str = "train-01",
    instance_type: str = "1x-h100",
    image: str = "ubuntu-24.04-cuda-12.8",
) -> dict[str, Any]:
    response = await client.post(
        "/api/instances", json={"name": name, "instance_type": instance_type, "image": image}
    )
    assert response.status_code == 202, response.text
    return response.json()


async def wait_for_status(
    client: httpx.AsyncClient, instance_id: str, expected_status: str
) -> dict[str, Any]:
    async with asyncio.timeout(WAIT_TIMEOUT_SECONDS):
        while True:
            response = await client.get(f"/api/instances/{instance_id}")
            if response.status_code == 200 and response.json()["status"] == expected_status:
                return response.json()
            await asyncio.sleep(0.01)


async def wait_until_gone(client: httpx.AsyncClient, instance_id: str) -> None:
    async with asyncio.timeout(WAIT_TIMEOUT_SECONDS):
        while True:
            response = await client.get(f"/api/instances/{instance_id}")
            if response.status_code == 404:
                return
            await asyncio.sleep(0.01)


def error_fields(response: httpx.Response) -> set[str]:
    return {field["field"] for field in response.json()["error"]["fields"]}
