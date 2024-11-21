import time

import pytest
from clickhouse_driver import Client

from houseplant.clickhouse_client import ClickHouseClient


def check_clickhouse_connection(host="localhost", port=9000, attempts=3):
    """Check if ClickHouse is accessible."""
    for _ in range(attempts):
        try:
            test_client = Client(host=host, port=port)
            test_client.execute("SELECT 1")
            return True
        except Exception:
            time.sleep(1)
    return False


@pytest.fixture(scope="session")
def clickhouse_service():
    """Verify ClickHouse is running and return connection details."""
    if not check_clickhouse_connection():
        raise RuntimeError(
            "ClickHouse is not running. Please start ClickHouse before running tests."
        )

    return {
        "host": "localhost",
        "port": 9000,  # Default ClickHouse port
    }


@pytest.fixture
def ch_client(clickhouse_service):
    """Create a fresh database for each test."""
    test_db = f"houseplant_test_{time.time_ns()}"

    ch_client = Client(host=clickhouse_service["host"], port=clickhouse_service["port"])

    ch_client.execute(f"CREATE DATABASE IF NOT EXISTS {test_db}")

    client = ClickHouseClient(
        host=f"{clickhouse_service['host']}:{clickhouse_service['port']}",
        database=test_db,
    )

    yield client

    ch_client.execute(f"DROP DATABASE IF EXISTS {test_db}")
