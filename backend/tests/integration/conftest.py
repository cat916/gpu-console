from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import AsyncExitStack
from typing import Any

import httpx
import pytest

from app.main import create_app
from app.provider import Provider
from app.settings import Settings

ClientFactory = Callable[..., Awaitable[httpx.AsyncClient]]


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def make_client() -> AsyncIterator[ClientFactory]:
    async with AsyncExitStack() as stack:

        async def factory(
            provider: Provider | None = None, **settings_overrides: Any
        ) -> httpx.AsyncClient:
            settings = Settings(
                **{
                    "provision_delay_seconds": 0,
                    "deprovision_delay_seconds": 0,
                    **settings_overrides,
                }
            )
            app = create_app(settings, provider)
            stack.push_async_callback(app.state.instance_service.close)
            transport = httpx.ASGITransport(app=app)
            return await stack.enter_async_context(
                httpx.AsyncClient(transport=transport, base_url="http://test")
            )

        yield factory


@pytest.fixture
async def client(make_client: ClientFactory) -> httpx.AsyncClient:
    return await make_client()
