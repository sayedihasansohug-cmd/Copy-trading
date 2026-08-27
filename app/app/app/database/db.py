from __future__ import annotations

import logging
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import DATABASE_URL
from app.database.models import Base


logger = logging.getLogger(__name__)


def normalize_database_url(url: str) -> str:
    """
    Convert common PostgreSQL URLs into an async SQLAlchemy URL.

    Render may provide:
        postgres://...
        postgresql://...

    asyncpg requires:
        postgresql+asyncpg://...
    """

    url = url.strip()

    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[
            len("postgresql://"):
        ]

    return url


def create_engine() -> AsyncEngine:
    """
    Create the SQLAlchemy asynchronous database engine.
    """

    database_url = normalize_database_url(
        DATABASE_URL
    )

    if database_url.startswith(
        "sqlite+aiosqlite://"
    ):
        return create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
        )

    return create_async_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
    )


engine: AsyncEngine = create_engine()


SessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_session() -> AsyncGenerator[
    AsyncSession,
    None,
]:
    """
    Provide a database session.

    Automatically commits successful operations
    and rolls back failed operations.
    """

    async with SessionFactory() as session:

        try:
            yield session

            await session.commit()

        except Exception:
            await session.rollback()
            raise


async def check_database_connection() -> bool:
    """
    Check whether the database is reachable.
    """

    try:

        async with engine.connect() as connection:

            await connection.execute(
                text("SELECT 1")
            )

        return True

    except Exception:

        logger.exception(
            "DATABASE_CONNECTION_FAILED"
        )

        return False


async def initialize_database() -> None:
    """
    Create database tables if they do not already exist.

    This is useful for the initial deployment.

    For larger production deployments, proper migrations
    can be added later without changing the repository layer.
    """

    try:

        async with engine.begin() as connection:

            await connection.run_sync(
                Base.metadata.create_all
            )

        logger.info(
            "DATABASE_INITIALIZED"
        )

    except Exception:

        logger.exception(
            "DATABASE_INITIALIZATION_FAILED"
        )

        raise


async def dispose_database() -> None:
    """
    Gracefully close the database connection pool.
    """

    try:

        await engine.dispose()

        logger.info(
            "DATABASE_POOL_DISPOSED"
        )

    except Exception:

        logger.exception(
            "DATABASE_DISPOSE_FAILED"
        )


async def health_check() -> dict[str, object]:
    """
    Return database health information.
    """

    healthy = await check_database_connection()

    return {
        "database": "postgresql"
        if "postgresql" in DATABASE_URL
        else "sqlite",
        "healthy": healthy,
    }
