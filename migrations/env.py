"""Alembic environment configuration for async SQLAlchemy + SQLModel.

Используется асинхронный движок (asyncpg), поэтому миграции
запускаются через alembic.run_async().

Для работы требуется установленный psycopg2-binary (синхронный драйвер),
который alembic использует под капотом для выполнения DDL-команд.
"""

# pylint: disable=no-member,unused-import,wrong-import-position

import asyncio
import sys
from pathlib import Path
from logging.config import fileConfig

# Добавляем корень проекта в sys.path, чтобы импорты app.* работали
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

# ---------- Импортируем модели, чтобы они попали в SQLModel.metadata ----------
from app.core.config import settings
from app.features.auth.models import User          # noqa: F401
from app.features.movies.models import Movie, Genre, MovieGenre  # noqa: F401
from app.features.ratings.models import Rating      # noqa: F401
# -----------------------------------------------------------------------------

# Конфигурация Alembic (из alembic.ini)
config = context.config

# Переопределяем URL на синхронный (Alembic работает синхронно)
# Берём настройки из проекта и заменяем asyncpg на psycopg2
SYNC_URL = settings.database_url.replace("+asyncpg", "+psycopg2")
config.set_main_option("sqlalchemy.url", SYNC_URL)

# Настройка логирования (если в alembic.ini есть секция [loggers])
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для autogenerate
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Запуск миграций в 'offline' режиме (генерирует SQL-скрипт без подключения к БД)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Выполнение миграций через переданное соединение."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Запуск миграций в async-режиме.

    Alembic поддерживает асинхронный движок через run_async().
    """
    configuration = config.get_section(config.config_ini_section)
    assert configuration is not None, "Missing alembic configuration section"

    # Используем async движок (asyncpg)
    async_url = settings.database_url
    configuration["sqlalchemy.url"] = async_url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Запуск миграций в 'online' режиме (подключение к реальной БД)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
