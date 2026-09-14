import asyncio
from ipaddress import IPv4Address
from typing import Protocol

from app.ip_pool import IpPool, IpPoolExhausted
from app.models import Instance


class ProvisioningFailed(Exception):
    pass


class Provider(Protocol):
    async def create(self, instance: Instance) -> str: ...

    async def delete(self, instance: Instance) -> None: ...


class FakeProvider:
    def __init__(
        self,
        ip_pool: IpPool,
        provision_delay_seconds: float,
        deprovision_delay_seconds: float,
    ) -> None:
        self._ip_pool = ip_pool
        self._provision_delay_seconds = provision_delay_seconds
        self._deprovision_delay_seconds = deprovision_delay_seconds

    async def create(self, instance: Instance) -> str:
        await asyncio.sleep(self._provision_delay_seconds)
        try:
            return str(self._ip_pool.allocate())
        except IpPoolExhausted as exc:
            raise ProvisioningFailed("No free IP addresses in the instance network") from exc

    async def delete(self, instance: Instance) -> None:
        await asyncio.sleep(self._deprovision_delay_seconds)
        if instance.ip is not None:
            self._ip_pool.release(IPv4Address(instance.ip))
