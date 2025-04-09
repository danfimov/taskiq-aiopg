import os
import random
import string
from collections.abc import AsyncGenerator
from typing import TypeVar

import pytest

from taskiq_aiopg.result_backend import AiopgResultBackend


_ReturnType = TypeVar("_ReturnType")


@pytest.fixture
def postgres_table() -> str:
    """
    Name of a postgresql table for current test.

    :return: random string.
    """
    return "".join(random.choice(string.ascii_uppercase) for _ in range(10))


@pytest.fixture
def postgresql_dsn() -> str:
    """
    DSN to PostgreSQL.

    :return: dsn to PostgreSQL.
    """
    return os.environ.get("POSTGRESQL_URL") or "postgresql://postgres:postgres@localhost:5432/taskiqaiopg"


@pytest.fixture
async def result_backend(
    postgresql_dsn: str,
    postgres_table: str,
) -> AsyncGenerator[AiopgResultBackend[_ReturnType], None]:
    backend: AiopgResultBackend[_ReturnType] = AiopgResultBackend(
        dsn=postgresql_dsn,
        table_name=postgres_table,
    )
    await backend.startup()
    yield backend

    async with backend._database_pool.acquire() as connection, connection.cursor() as cursor:  # noqa: SLF001
        await cursor.execute(
            f"DROP TABLE {postgres_table}",
        )
    await backend.shutdown()
