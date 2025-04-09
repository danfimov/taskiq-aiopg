import uuid
from typing import Any, TypeVar

import pytest
from pydantic import BaseModel
from taskiq import TaskiqResult

from taskiq_aiopg.exceptions import ResultIsMissingError
from taskiq_aiopg.result_backend import AiopgResultBackend


_ReturnType = TypeVar("_ReturnType")
pytestmark = pytest.mark.anyio


class ResultForTest(BaseModel):
    """Just test class for testing."""

    test_arg: str = uuid.uuid4().hex


@pytest.fixture
def task_id() -> str:
    """
    Generate ID for taskiq result.

    :returns: uuid as string.
    """
    return str(uuid.uuid4())


@pytest.fixture
def default_taskiq_result() -> TaskiqResult[Any]:
    """
    Generate default TaskiqResult.

    :returns: TaskiqResult with generic result.
    """
    return TaskiqResult(
        is_err=False,
        log=None,
        return_value="Best test ever.",
        execution_time=0.1,
    )


@pytest.fixture
def custom_taskiq_result() -> TaskiqResult[Any]:
    """
    Generate custom TaskiqResult.

    :returns: TaskiqResult with custom class result.
    """
    return TaskiqResult(
        is_err=False,
        log=None,
        return_value=ResultForTest(),
        execution_time=0.1,
    )


async def test_failure_backend_result(
    result_backend: AiopgResultBackend[_ReturnType],
    task_id: str,
) -> None:
    """Test exception raising in `get_result` method."""
    with pytest.raises(expected_exception=ResultIsMissingError):
        await result_backend.get_result(task_id=task_id)


async def test_success_backend_default_result_delete_res(
    postgresql_dsn: str,
    postgres_table: str,
    default_taskiq_result: TaskiqResult[_ReturnType],
    task_id: str,
) -> None:
    backend: AiopgResultBackend[_ReturnType] = AiopgResultBackend(
        dsn=postgresql_dsn,
        table_name=postgres_table,
        keep_results=False,
    )
    await backend.startup()

    await backend.set_result(
        task_id=task_id,
        result=default_taskiq_result,
    )
    await backend.get_result(task_id=task_id)

    with pytest.raises(expected_exception=ResultIsMissingError):
        await backend.get_result(task_id=task_id)

    async with backend._database_pool.acquire() as connection, connection.cursor() as cursor:  # noqa: SLF001
        await cursor.execute(
            f"DROP TABLE {postgres_table}",
        )

    await backend.shutdown()


async def test_success_backend_default_result(
    result_backend: AiopgResultBackend[_ReturnType],
    default_taskiq_result: TaskiqResult[_ReturnType],
    task_id: str,
) -> None:
    """
    Tests normal behavior with default result in TaskiqResult.

    :param default_taskiq_result: TaskiqResult with default result.
    :param task_id: ID for task.
    :param nats_urls: urls to NATS.
    """
    await result_backend.set_result(
        task_id=task_id,
        result=default_taskiq_result,
    )
    result = await result_backend.get_result(task_id=task_id)

    assert result == default_taskiq_result


async def test_success_backend_custom_result(
    result_backend: AiopgResultBackend[_ReturnType],
    custom_taskiq_result: TaskiqResult[_ReturnType],
    task_id: str,
) -> None:
    """
    Tests normal behavior with custom result in TaskiqResult.

    :param custom_taskiq_result: TaskiqResult with custom result.
    :param task_id: ID for task.
    :param redis_url: url to redis.
    """
    await result_backend.set_result(
        task_id=task_id,
        result=custom_taskiq_result,
    )
    result = await result_backend.get_result(task_id=task_id)

    assert result.return_value.test_arg == custom_taskiq_result.return_value.test_arg
    assert result.is_err == custom_taskiq_result.is_err
    assert result.execution_time == custom_taskiq_result.execution_time
    assert result.log == custom_taskiq_result.log


async def test_success_backend_is_result_ready(
    result_backend: AiopgResultBackend[_ReturnType],
    custom_taskiq_result: TaskiqResult[_ReturnType],
    task_id: str,
) -> None:
    """Tests `is_result_ready` method."""
    assert not await result_backend.is_result_ready(task_id=task_id)
    await result_backend.set_result(
        task_id=task_id,
        result=custom_taskiq_result,
    )

    assert await result_backend.is_result_ready(task_id=task_id)


async def test_test_success_backend_custom_result_set_same_task_id(
    result_backend: AiopgResultBackend[_ReturnType],
    custom_taskiq_result: TaskiqResult[_ReturnType],
    task_id: str,
) -> None:
    await result_backend.set_result(
        task_id=task_id,
        result=custom_taskiq_result,
    )
    result = await result_backend.get_result(task_id=task_id)

    assert result.return_value.test_arg == custom_taskiq_result.return_value.test_arg

    await result_backend.set_result(
        task_id=task_id,
        result=custom_taskiq_result,
    )

    another_taskiq_res_uuid = uuid.uuid4().hex
    another_taskiq_res = TaskiqResult(
        is_err=False,
        log=None,
        return_value=ResultForTest(test_arg=another_taskiq_res_uuid),
        execution_time=0.1,
    )

    await result_backend.set_result(
        task_id=task_id,
        result=another_taskiq_res,  # type: ignore[arg-type]
    )
    result = await result_backend.get_result(task_id=task_id)

    assert result.return_value.test_arg == another_taskiq_res_uuid
