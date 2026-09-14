import httpx
import pytest

from tests.integration.conftest import ClientFactory
from tests.integration.support import launch, wait_for_status, wait_until_gone

pytestmark = pytest.mark.anyio


async def test_running_instance_has_a_record(client: httpx.AsyncClient) -> None:
    instance = await launch(client, name="train-01")
    await wait_for_status(client, instance["id"], "running")

    response = await client.get("/api/dns/records")

    assert response.status_code == 200
    assert response.json() == [
        {"name": "train-01.gpu.internal", "type": "A", "value": "10.0.0.2", "ttl": 5}
    ]


async def test_provisioning_instance_has_no_record(make_client: ClientFactory) -> None:
    client = await make_client(provision_delay_seconds=60)
    await launch(client)

    response = await client.get("/api/dns/records")

    assert response.json() == []


async def test_deleted_instance_loses_its_record(client: httpx.AsyncClient) -> None:
    instance = await launch(client)
    await wait_for_status(client, instance["id"], "running")
    await client.delete(f"/api/instances/{instance['id']}")

    records_while_deleting = (await client.get("/api/dns/records")).json()
    await wait_until_gone(client, instance["id"])

    assert records_while_deleting == []


async def test_records_use_configured_zone_and_ttl(make_client: ClientFactory) -> None:
    client = await make_client(dns_zone="console.internal", dns_ttl_seconds=30)
    instance = await launch(client, name="eval-02")
    await wait_for_status(client, instance["id"], "running")

    records = (await client.get("/api/dns/records")).json()

    assert records == [
        {"name": "eval-02.console.internal", "type": "A", "value": "10.0.0.2", "ttl": 30}
    ]
