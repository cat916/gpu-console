from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.errors import register_error_handlers
from app.ip_pool import IpPool
from app.provider import FakeProvider, Provider
from app.routes import router
from app.service import InstanceService
from app.settings import Settings


def create_app(settings: Settings | None = None, provider: Provider | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    provider = provider or FakeProvider(
        provision_delay_seconds=settings.provision_delay_seconds,
        deprovision_delay_seconds=settings.deprovision_delay_seconds,
    )
    service = InstanceService(
        provider,
        IpPool(settings.instance_network),
        settings.dns_zone,
        settings.dns_ttl_seconds,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        await service.close()

    app = FastAPI(title="GPU Console API", version="0.1.0", lifespan=lifespan)
    app.state.instance_service = service
    register_error_handlers(app)
    app.include_router(router)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app
