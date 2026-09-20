import asyncio
import logging
import secrets
from collections.abc import Coroutine
from datetime import UTC, datetime
from ipaddress import IPv4Address
from typing import Any

from app.catalog import IMAGES_BY_ID, INSTANCE_TYPES_BY_ID
from app.errors import invalid_state, name_taken, network_full, not_found, validation_failed
from app.ip_pool import IpPool, IpPoolExhausted
from app.models import DnsRecord, FieldError, Instance, InstanceStatus, LaunchInstanceRequest
from app.provider import Provider

logger = logging.getLogger(__name__)

DELETABLE_STATUSES = {InstanceStatus.RUNNING, InstanceStatus.FAILED}
LAUNCH_FAILURE_REASON = "Launch did not complete. Delete this instance and try again."
DELETE_FAILURE_REASON = "Delete did not complete. Try deleting this instance again."


class InstanceService:
    def __init__(
        self, provider: Provider, ip_pool: IpPool, dns_zone: str, dns_ttl_seconds: int
    ) -> None:
        self._provider = provider
        self._ip_pool = ip_pool
        self._dns_zone = dns_zone
        self._dns_ttl_seconds = dns_ttl_seconds
        self._instances: dict[str, Instance] = {}
        self._tasks: set[asyncio.Task[None]] = set()

    def list_instances(self) -> list[Instance]:
        return sorted(self._instances.values(), key=lambda instance: instance.created_at)

    def get_instance(self, instance_id: str) -> Instance:
        instance = self._instances.get(instance_id)
        if instance is None:
            raise not_found(instance_id)
        return instance

    def launch_instance(self, request: LaunchInstanceRequest) -> Instance:
        unknown_fields = []
        if request.instance_type not in INSTANCE_TYPES_BY_ID:
            unknown_fields.append(
                FieldError(
                    field="instance_type",
                    message=f"Unknown instance type {request.instance_type}",
                )
            )
        if request.image not in IMAGES_BY_ID:
            unknown_fields.append(
                FieldError(field="image", message=f"Unknown image {request.image}")
            )
        if unknown_fields:
            raise validation_failed(unknown_fields)
        if any(instance.name == request.name for instance in self._instances.values()):
            raise name_taken(request.name)
        try:
            ip = self._ip_pool.allocate()
        except IpPoolExhausted as exc:
            raise network_full() from exc

        now = datetime.now(UTC)
        instance = Instance(
            id=self._new_instance_id(),
            name=request.name,
            hostname=f"{request.name}.{self._dns_zone}",
            instance_type=request.instance_type,
            image=request.image,
            status=InstanceStatus.PROVISIONING,
            ip=str(ip),
            failure_reason=None,
            created_at=now,
            updated_at=now,
        )
        self._instances[instance.id] = instance
        self._run_in_background(self._provision(instance.id))
        return instance

    def delete_instance(self, instance_id: str) -> Instance:
        instance = self.get_instance(instance_id)
        if instance.status not in DELETABLE_STATUSES:
            raise invalid_state(instance, "delete")
        deleting = self._update(instance_id, status=InstanceStatus.DELETING, failure_reason=None)
        self._run_in_background(self._deprovision(deleting))
        return deleting

    def dns_records(self) -> list[DnsRecord]:
        return [
            DnsRecord(name=instance.hostname, value=instance.ip, ttl=self._dns_ttl_seconds)
            for instance in self.list_instances()
            if instance.status is InstanceStatus.RUNNING
        ]

    async def close(self) -> None:
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def _provision(self, instance_id: str) -> None:
        try:
            await self._provider.create(self._instances[instance_id])
        except Exception:
            logger.exception("Provisioning %s crashed", instance_id)
            self._update(
                instance_id, status=InstanceStatus.FAILED, failure_reason=LAUNCH_FAILURE_REASON
            )
        else:
            self._update(instance_id, status=InstanceStatus.RUNNING)

    async def _deprovision(self, instance: Instance) -> None:
        try:
            await self._provider.delete(instance)
        except Exception:
            logger.exception("Deprovisioning %s crashed", instance.id)
            self._update(
                instance.id, status=InstanceStatus.FAILED, failure_reason=DELETE_FAILURE_REASON
            )
        else:
            self._instances.pop(instance.id, None)
            self._ip_pool.release(IPv4Address(instance.ip))

    def _update(self, instance_id: str, **changes: Any) -> Instance:
        updated = self._instances[instance_id].model_copy(
            update={**changes, "updated_at": datetime.now(UTC)}
        )
        self._instances[instance_id] = updated
        return updated

    def _run_in_background(self, coroutine: Coroutine[Any, Any, None]) -> None:
        task = asyncio.get_running_loop().create_task(coroutine)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    def _new_instance_id(self) -> str:
        while True:
            candidate = f"inst_{secrets.token_hex(4)}"
            if candidate not in self._instances:
                return candidate
