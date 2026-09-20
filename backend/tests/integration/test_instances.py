from ipaddress import IPv4Network

import httpx
import pytest

from tests.integration.conftest import ClientFactory
from tests.integration.support import (
    ControllableProvider,
    error_fields,
    launch,
    wait_for_status,
    wait_until_gone,
)

pytestmark = pytest.mark.anyio


async def test_launch_returns_accepted_provisioning_instance_with_reserved_ip(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/instances",
        json={"name": "train-01", "instance_type": "1x-h100", "image": "ubuntu-24.04-cuda-12.8"},
    )

    assert response.status_code == 202
    instance = response.json()
    assert instance["id"].startswith("inst_")
    assert instance["hostname"] == "train-01.gpu.internal"
    assert instance["status"] == "provisioning"
    assert instance["ip"] == "10.0.0.2"
    assert instance["failure_reason"] is None
    assert response.headers["location"] == f"/api/instances/{instance['id']}"


async def test_instance_becomes_running_with_its_reserved_ip(
    client: httpx.AsyncClient,
) -> None:
    created = await launch(client)

    running = await wait_for_status(client, created["id"], "running")

    assert running["ip"] == "10.0.0.2"
    assert running["updated_at"] >= created["updated_at"]


async def test_lists_instances_in_launch_order(client: httpx.AsyncClient) -> None:
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


async def test_rejects_launch_when_network_is_full(make_client: ClientFactory) -> None:
    client = await make_client(instance_network=IPv4Network("10.0.0.0/30"))
    await launch(client, name="train-01")

    response = await client.post(
        "/api/instances",
        json={"name": "train-02", "instance_type": "1x-h100", "image": "ubuntu-24.04-cuda-12.8"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "network_full"
    assert [instance["name"] for instance in (await client.get("/api/instances")).json()] == [
        "train-01"
    ]


async def test_provisioning_instance_already_holds_its_ip(make_client: ClientFactory) -> None:
    client = await make_client(
        instance_network=IPv4Network("10.0.0.0/30"), provision_delay_seconds=60
    )
    await launch(client, name="train-01")

    response = await client.post(
        "/api/instances",
        json={"name": "train-02", "instance_type": "1x-h100", "image": "ubuntu-24.04-cuda-12.8"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "network_full"


async def test_failed_launch_keeps_ip_and_explains_why(make_client: ClientFactory) -> None:
    provider = ControllableProvider()
    provider.fail_create = True
    client = await make_client(provider=provider)
    instance = await launch(client)

    failed = await wait_for_status(client, instance["id"], "failed")

    assert failed["ip"] == "10.0.0.2"
    assert failed["failure_reason"] == (
        "Launch did not complete. Delete this instance and try again."
    )
    assert (await client.get("/api/dns/records")).json() == []


async def test_deleting_failed_instance_clears_reason_and_frees_ip(
    make_client: ClientFactory,
) -> None:
    provider = ControllableProvider()
    provider.fail_create = True
    client = await make_client(provider=provider)
    instance = await launch(client, name="train-01")
    await wait_for_status(client, instance["id"], "failed")

    response = await client.delete(f"/api/instances/{instance['id']}")
    await wait_until_gone(client, instance["id"])
    provider.fail_create = False
    relaunched = await launch(client, name="train-01")

    assert response.status_code == 202
    assert response.json()["status"] == "deleting"
    assert response.json()["failure_reason"] is None
    assert relaunched["ip"] == "10.0.0.2"


async def test_failed_delete_keeps_ip_and_can_be_retried(make_client: ClientFactory) -> None:
    provider = ControllableProvider()
    provider.fail_delete = True
    client = await make_client(provider=provider)
    instance = await launch(client)
    await wait_for_status(client, instance["id"], "running")
    await client.delete(f"/api/instances/{instance['id']}")

    failed = await wait_for_status(client, instance["id"], "failed")
    provider.fail_delete = False
    retry = await client.delete(f"/api/instances/{instance['id']}")

    assert failed["ip"] == "10.0.0.2"
    assert failed["failure_reason"] == "Delete did not complete. Try deleting this instance again."
    assert retry.status_code == 202
    await wait_until_gone(client, instance["id"])
