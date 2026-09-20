import asyncio
from typing import Protocol

from app.models import Instance


class Provider(Protocol):
    async def create(self, instance: Instance) -> None: ...

    async def delete(self, instance: Instance) -> None: ...


class FakeProvider:
    def __init__(self, provision_delay_seconds: float, deprovision_delay_seconds: float) -> None:
        self._provision_delay_seconds = provision_delay_seconds
        self._deprovision_delay_seconds = deprovision_delay_seconds

    async def create(self, instance: Instance) -> None:
        await asyncio.sleep(self._provision_delay_seconds)

    async def delete(self, instance: Instance) -> None:
        await asyncio.sleep(self._deprovision_delay_seconds)
