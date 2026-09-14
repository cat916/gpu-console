import asyncio
import logging
import secrets
from collections.abc import Coroutine
from datetime import UTC, datetime
from typing import Any

from app.catalog import IMAGES_BY_ID, INSTANCE_TYPES_BY_ID
from app.errors import invalid_state, name_taken, not_found, validation_failed
from app.models import CreateInstanceRequest, DnsRecord, FieldError, Instance, InstanceStatus
from app.provider import Provider, ProvisioningFailed

logger = logging.getLogger(__name__)

DELETABLE_STATUSES = {InstanceStatus.RUNNING, InstanceStatus.ERROR}


class InstanceService:
    def __init__(self, provider: Provider, dns_zone: str, dns_ttl_seconds: int) -> None:
        self._provider = provider
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

    def create_instance(self, request: CreateInstanceRequest) -> Instance:
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

        now = datetime.now(UTC)
        instance = Instance(
            id=self._new_instance_id(),
            name=request.name,
            hostname=f"{request.name}.{self._dns_zone}",
            instance_type=request.instance_type,
            image=request.image,
            status=InstanceStatus.PROVISIONING,
            ip=None,
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
        deleting = self._update(instance_id, status=InstanceStatus.DELETING)
        self._run_in_background(self._deprovision(deleting))
        return deleting

    def dns_records(self) -> list[DnsRecord]:
        return [
            DnsRecord(name=instance.hostname, value=instance.ip, ttl=self._dns_ttl_seconds)
            for instance in self.list_instances()
            if instance.status is InstanceStatus.RUNNING and instance.ip is not None
        ]

    async def close(self) -> None:
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)

    async def _provision(self, instance_id: str) -> None:
        try:
            ip = await self._provider.create(self._instances[instance_id])
        except ProvisioningFailed as exc:
            logger.warning("Provisioning %s failed: %s", instance_id, exc)
            self._update(instance_id, status=InstanceStatus.ERROR)
        except Exception:
            logger.exception("Provisioning %s crashed", instance_id)
            self._update(instance_id, status=InstanceStatus.ERROR)
        else:
            self._update(instance_id, status=InstanceStatus.RUNNING, ip=ip)

    async def _deprovision(self, instance: Instance) -> None:
        try:
            await self._provider.delete(instance)
        except Exception:
            logger.exception("Deprovisioning %s crashed", instance.id)
            self._update(instance.id, status=InstanceStatus.ERROR)
        else:
            self._instances.pop(instance.id, None)

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
