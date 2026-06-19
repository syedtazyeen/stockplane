import asyncio
from collections.abc import Awaitable, Callable

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_db
from app.main import app


async def run_concurrent_session_requests(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    workers: int,
    request_factory: Callable[[AsyncClient, AsyncSession], Awaitable[int]],
) -> list[int]:
    """Run the same HTTP request concurrently, each with its own DB session."""
    return await run_mixed_concurrent_session_requests(
        session_factory,
        request_factories=[request_factory] * workers,
    )


async def run_mixed_concurrent_session_requests(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    request_factories: list[Callable[[AsyncClient, AsyncSession], Awaitable[int]]],
) -> list[int]:
    """Run different HTTP requests concurrently, each with its own DB session."""
    transport = ASGITransport(app=app)

    async def run_one(
        request_factory: Callable[[AsyncClient, AsyncSession], Awaitable[int]],
    ) -> int:
        async with AsyncClient(transport=transport, base_url="") as client:
            async with session_factory() as session:
                async def override_get_db():
                    try:
                        yield session
                    except Exception:
                        await session.rollback()
                        raise

                app.dependency_overrides[get_db] = override_get_db
                try:
                    status_code = await request_factory(client, session)
                    if status_code < 400:
                        await session.commit()
                    else:
                        await session.rollback()
                    return status_code
                finally:
                    app.dependency_overrides.clear()

    return list(await asyncio.gather(*(run_one(factory) for factory in request_factories)))
