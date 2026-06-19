import os
import subprocess
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from faker import Faker
from httpx import ASGITransport, AsyncClient
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings
from app.core.database import get_db
from app.main import app
from tests.factories import DataFactory


def _database_url() -> str:
    return os.getenv("TEST_DATABASE_URL") or get_settings().database_url


@pytest.fixture(scope="session")
def apply_migrations() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=Path(__file__).resolve().parent.parent,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"Could not apply migrations: {result.stderr}")


@pytest.fixture
def faker() -> Faker:
    fake = Faker()
    yield fake
    fake.unique.clear()


@pytest.fixture
def factory(faker: Faker) -> DataFactory:
    return DataFactory(faker)


@pytest.fixture(scope="session")
async def engine(apply_migrations) -> AsyncGenerator[AsyncEngine, None]:
    url = make_url(_database_url()).update_query_dict({"prepared_statement_cache_size": "0"})
    test_engine = create_async_engine(
        url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=0,
        connect_args={"statement_cache_size": 0},
    )
    try:
        async with test_engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception as exc:
        await test_engine.dispose()
        pytest.skip(f"Database unavailable for integration tests: {exc}")

    yield test_engine
    await test_engine.dispose()


@pytest.fixture
async def db_session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        try:
            yield db_session
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        yield http_client
    app.dependency_overrides.clear()


@pytest.fixture
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
