from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.config import get_settings

from app.models import *

from app.models.base import Base

print(Base.metadata.tables.keys())

target_metadata = Base.metadata

config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _sync_database_url() -> str:
    url = get_settings().database_url
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    return url


config.set_main_option("sqlalchemy.url", _sync_database_url())

print(config.get_main_option("sqlalchemy.url"))

def _include_object():
    import importlib.util
    from pathlib import Path

    helpers_path = Path(__file__).resolve().parent / "env_helpers.py"
    if not helpers_path.is_file():
        return None

    spec = importlib.util.spec_from_file_location("migration_env_helpers", helpers_path)
    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.get_include_object()


def _configure_context(**kwargs) -> None:
    include_object = _include_object()
    if include_object is not None:
        kwargs["include_object"] = include_object

    context.configure(
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        **kwargs,
    )


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    _configure_context(
        url=url,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        _configure_context(connection=connection)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
