import pytest
from clickhouse_driver import Client
from houseplant.clickhouse_client import ClickHouseClient

@pytest.fixture
def ch_client():
    """Create a test ClickHouse client with a temporary test database."""

    client = Client(host='localhost')
    
    test_db = 'test_houseplant'
    client.execute(f'DROP DATABASE IF EXISTS {test_db}')
    client.execute(f'CREATE DATABASE {test_db}')
    

    ch = ClickHouseClient(host='localhost', database=test_db)
    
    yield ch
    
    client.execute(f'DROP DATABASE IF EXISTS {test_db}') 