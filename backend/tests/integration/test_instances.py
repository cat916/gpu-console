from ipaddress import IPv4Network

import httpx
import pytest

from tests.integration.conftest import ClientFactory
from tests.integration.support import error_fields, launch, wait_for_status, wait_until_gone

pytestmark = pytest.mark.anyio


async def test_create_returns_accepted_provisioning_instance(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/instances",
        json={"name": "train-01", "instance_type": "1x-h100", "image": "ubuntu-24.04-cuda-12.8"},
    )

    assert response.status_code == 202
    instance = response.json()
    assert instance["id"].startswith("inst_")
    assert instance["hostname"] == "train-01.gpu.internal"
    assert instance["status"] == "provisioning"
    assert instance["ip"] is None
    assert response.headers["location"] == f"/api/instances/{instance['id']}"


async def test_instance_becomes_running_with_first_assignable_ip(
    client: httpx.AsyncClient,
) -> None:
    created = await launch(client)

    running = await wait_for_status(client, created["id"], "running")

    assert running["ip"] == "10.0.0.2"
    assert running["updated_at"] >= created["updated_at"]


async def test_lists_instances_in_creation_order(client: httpx.AsyncClient) -> None:
    first = await launch(client, name="train-01")
    second = await launch(client, name="eval-02")

    response = await client.get("/api/instances")

    assert [instance["id"] for instance in response.json()] == [first["id"], second["id"]]


async def test_rejects_duplicate_name(client: httpx.AsyncClient) -> None:
    await launch(client, name="train-01")

    response = await client.post(
        "/api/instances",
        json={"name": "train-01", "instance_type": "1x-a100", "image": "ubuntu-24.04-cuda-12.8"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "name_taken"
    assert error_fields(response) == {"name"}


@pytest.mark.parametrize(
    "name", ["", "Train-01", "train_01", "train.01", "-train", "train-", "a" * 64]
)
async def test_rejects_names_that_are_not_dns_labels(client: httpx.AsyncClient, name: str) -> None:
    response = await client.post(
        "/api/instances",
        json={"name": name, "instance_type": "1x-h100", "image": "ubuntu-24.04-cuda-12.8"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_failed"
    assert error_fields(response) == {"name"}


async def test_accepts_longest_valid_name(client: httpx.AsyncClient) -> None:
    instance = await launch(client, name="a" * 63)

    assert instance["hostname"] == f"{'a' * 63}.gpu.internal"


async def test_rejects_unknown_instance_type_and_image(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/instances",
        json={"name": "train-01", "instance_type": "16x-h100", "image": "windows-95"},
    )

    assert response.status_code == 422
    assert error_fields(response) == {"instance_type", "image"}


async def test_rejects_missing_fields(client: httpx.AsyncClient) -> None:
    response = await client.post("/api/instances", json={})

    assert response.status_code == 422
    assert error_fields(response) == {"name", "instance_type", "image"}


async def test_get_unknown_instance_returns_not_found(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/instances/inst_missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_cannot_delete_while_provisioning(make_client: ClientFactory) -> None:
    client = await make_client(provision_delay_seconds=60)
    instance = await launch(client)

    response = await client.delete(f"/api/instances/{instance['id']}")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "invalid_state"


async def test_cannot_delete_twice(make_client: ClientFactory) -> None:
    client = await make_client(deprovision_delay_seconds=60)
    instance = await launch(client)
    await wait_for_status(client, instance["id"], "running")
    await client.delete(f"/api/instances/{instance['id']}")

    response = await client.delete(f"/api/instances/{instance['id']}")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "invalid_state"


async def test_delete_running_instance_removes_it(client: httpx.AsyncClient) -> None:
    instance = await launch(client)
    await wait_for_status(client, instance["id"], "running")

    response = await client.delete(f"/api/instances/{instance['id']}")

    assert response.status_code == 202
    assert response.json()["status"] == "deleting"
    await wait_until_gone(client, instance["id"])
    assert (await client.get("/api/instances")).json() == []


async def test_deleted_instance_frees_its_ip_and_name(client: httpx.AsyncClient) -> None:
    first = await launch(client, name="train-01")
    first_running = await wait_for_status(client, first["id"], "running")
    await client.delete(f"/api/instances/{first['id']}")
    await wait_until_gone(client, first["id"])

    second = await launch(client, name="train-01")
    second_running = await wait_for_status(client, second["id"], "running")

    assert second_running["ip"] == first_running["ip"]


async def test_instance_errors_when_no_ip_is_free_and_can_be_deleted(
    make_client: ClientFactory,
) -> None:
    client = await make_client(instance_network=IPv4Network("10.0.0.0/30"))
    first = await launch(client, name="train-01")
    await wait_for_status(client, first["id"], "running")
    second = await launch(client, name="train-02")

    errored = await wait_for_status(client, second["id"], "error")
    response = await client.delete(f"/api/instances/{second['id']}")

    assert errored["ip"] is None
    assert response.status_code == 202
    await wait_until_gone(client, second["id"])
