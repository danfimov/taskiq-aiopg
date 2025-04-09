# taskiq + aiopg

[![Python](https://img.shields.io/badge/python-3.10_|_3.11_|_3.12_|_3.13-blue)](https://www.python.org/)
[![Linters](https://github.com/danfimov/taskiq-aiopg/actions/workflows/code-check.yml/badge.svg)](https://github.com/danfimov/taskiq-aiopg/actions/workflows/code-check.yml)


Plugin for taskiq that adds a new result backend based on PostgreSQL and [aiopg](https://github.com/aio-libs/aiopg).

## Installation

This project can be installed using pip/poetry/uv (choose your preferred package manager):

```bash
pip install taskiq-aiopg
```

## Usage

Let's see the example with the redis broker and PostgreSQL aiopg result backend (run as is):

```python
# broker.py
import asyncio

import taskiq_redis

from taskiq_aiopg import AiopgResultBackend

result_backend = AiopgResultBackend(
    dsn="postgres://postgres:postgres@localhost:5432/postgres",
)

# Or you can use PubSubBroker if you need broadcasting
broker = taskiq_redis.ListQueueBroker(
    url="redis://localhost:6379",
).with_result_backend(result_backend)


@broker.task(task_name="best_task_ever")
async def best_task_ever() -> None:
    """Solve all problems in the world."""
    print("Start to solve all problems...")
    await asyncio.sleep(2.0)
    print("All problems are solved!")


async def main():
    print("Starting the application")
    await broker.startup()
    task = await best_task_ever.kiq()
    print(await task.wait_result())
    await broker.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

- `dsn`: connection string to PostgreSQL;
- `keep_results`: flag to not remove results from Redis after reading;
- `table_name`: name of the table in PostgreSQL to store TaskIQ results;
- `field_for_task_id`: type of a field for `task_id`, you may need it if you want to have length of task_id more than 255 symbols;
- `serializer`: type of `TaskiqSerializer` default is `PickleSerializer`;
- `**connect_kwargs`: additional connection parameters, you can read more about it in [aiopg repository](https://github.com/aio-libs/aiopg).
