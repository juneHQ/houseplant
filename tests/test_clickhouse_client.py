import pytest
from clickhouse_driver.errors import NetworkError, ServerException

from houseplant.clickhouse_client import (
    ClickHouseAuthenticationError,
    ClickHouseConnectionError,
    ClickHouseDatabaseNotFoundError,
)


@pytest.fixture
def migrations_table(ch_client):
    """Fixture to initialize migrations table."""
    ch_client.init_migrations_table()
    return ch_client


def test_port_parsing_from_host():
    """Test port parsing from host string."""
    from houseplant.clickhouse_client import ClickHouseClient

    client = ClickHouseClient(host="localhost:1234")
    assert client.host == "localhost"
    assert client.port == 1234


def test_default_port(monkeypatch):
    """Test default port selection."""
    from houseplant.clickhouse_client import ClickHouseClient

    # Test default non-secure port
    client = ClickHouseClient()
    assert client.port == 9000

    # Test default secure port
    monkeypatch.setenv("CLICKHOUSE_SECURE", "true")
    client = ClickHouseClient()
    assert client.port == 9440


def test_port_precedence(monkeypatch):
    """Test port parameter precedence."""
    from houseplant.clickhouse_client import ClickHouseClient

    # Host:port should override port parameter and env var
    monkeypatch.setenv("CLICKHOUSE_PORT", "8000")
    client = ClickHouseClient(host="localhost:7000", port=6000)
    assert client.port == 7000

    # Host:port should override env var
    client = ClickHouseClient(host="localhost:7000")
    assert client.port == 7000

    # Port parameter should override env var
    client = ClickHouseClient(host="localhost", port=7000)
    assert client.port == 7000

    # Env var should be used if no other port specified
    client = ClickHouseClient(host="localhost")
    assert client.port == 8000

    # Secure port should be used if secure is true
    monkeypatch.setenv("CLICKHOUSE_SECURE", "true")
    client = ClickHouseClient(host="localhost:7000", port=6000)
    assert client.port == 9440


def test_connection_error(monkeypatch):
    """Test connection error handling."""
    monkeypatch.setenv("CLICKHOUSE_HOST", "invalid_host")

    with pytest.raises(ClickHouseConnectionError) as exc_info:
        from houseplant.clickhouse_client import ClickHouseClient

        client = ClickHouseClient()

        def mock_execute(*args, **kwargs):
            raise NetworkError("Connection refused")

        monkeypatch.setattr(client.client, "execute", mock_execute)
        client._check_clickhouse_connection()

    assert "Could not connect to database at invalid_host" in str(exc_info.value)


def test_authentication_error(monkeypatch):
    """Test authentication error handling."""
    monkeypatch.setenv("CLICKHOUSE_USER", "invalid_user")

    with pytest.raises(ClickHouseAuthenticationError) as exc_info:
        from houseplant.clickhouse_client import ClickHouseClient

        client = ClickHouseClient()

        def mock_execute(*args, **kwargs):
            raise ServerException("Authentication failed")

        monkeypatch.setattr(client.client, "execute", mock_execute)
        client._check_clickhouse_connection()

    assert "Authentication failed for user invalid_user" in str(exc_info.value)


def test_database_not_found_error(monkeypatch):
    """Test database not found error handling."""
    monkeypatch.setenv("CLICKHOUSE_DB", "nonexistent_db")

    with pytest.raises(ClickHouseDatabaseNotFoundError) as exc_info:
        from houseplant.clickhouse_client import ClickHouseClient

        client = ClickHouseClient()

        def mock_execute(*args, **kwargs):
            raise ServerException(
                "Code: None. Database 'nonexistent_db' does not exist"
            )

        monkeypatch.setattr(client.client, "execute", mock_execute)
        client._check_clickhouse_connection()

    assert "Database 'nonexistent_db' does not exist" in str(exc_info.value)


def test_migrations_table_structure(migrations_table):
    """Test that migrations table is created with correct structure."""
    result = migrations_table.client.execute("""
        SELECT name, type, default_expression
        FROM system.columns
        WHERE database = currentDatabase() AND table = 'schema_migrations'
    """)

    columns = {row[0]: {"type": row[1], "default": row[2]} for row in result}

    assert "version" in columns
    assert "LowCardinality(String)" in columns["version"]["type"]
    assert "active" in columns
    assert columns["active"]["type"] == "UInt8"
    assert columns["active"]["default"] == "1"
    assert "created_at" in columns
    assert "DateTime64" in columns["created_at"]["type"]


def test_migrations_table_structure_with_cluster(ch_client, monkeypatch):
    """Test that migrations table is created with correct structure when using cluster."""
    monkeypatch.setenv("CLICKHOUSE_CLUSTER", "test_cluster")

    create_statement = ch_client.init_migrations_table_query()

    assert "ON CLUSTER '{cluster}'" in create_statement
    assert "ENGINE = ReplicatedReplacingMergeTree" in create_statement


def test_migrations_table_structure_without_cluster(ch_client):
    """Test that migrations table is created with correct structure when using cluster."""
    create_statement = ch_client.init_migrations_table_query()

    assert "ON CLUSTER '{cluster}'" not in create_statement
    assert "ENGINE = ReplacingMergeTree" in create_statement


@pytest.mark.parametrize("test_versions", [["20240101000000", "20240102000000"]])
def test_get_applied_migrations(migrations_table, test_versions):
    """Test retrieving applied migrations."""
    for version in test_versions:
        migrations_table.mark_migration_applied(version)

    applied = migrations_table.get_applied_migrations()
    applied_versions = [row[0] for row in applied]

    assert applied_versions == test_versions


def test_execute_migration(ch_client):
    """Test executing a migration SQL statement."""
    test_sql = """
        CREATE TABLE test_table (
            id UInt32,
            name String
        ) ENGINE = MergeTree()
        ORDER BY id
    """

    ch_client.execute_migration(test_sql)

    result = ch_client.client.execute("""
        SELECT name
        FROM system.tables
        WHERE database = currentDatabase() AND name = 'test_table'
    """)

    assert len(result) == 1
    assert result[0][0] == "test_table"


def test_mark_migration_applied(migrations_table):
    """Test marking a migration as applied."""
    test_version = "20240101000000"
    migrations_table.mark_migration_applied(test_version)

    result = migrations_table.client.execute(
        """
        SELECT version, active
        FROM schema_migrations
        WHERE version = %(version)s
    """,
        {"version": test_version},
    )

    assert len(result) == 1
    assert result[0][0] == test_version
    assert result[0][1] == 1


def test_get_database_schema(ch_client):
    """Test getting database schema."""
    test_sql = """
        CREATE TABLE test_table (
            id UInt32,
            name String
        ) ENGINE = MergeTree()
        ORDER BY id
    """

    ch_client.execute_migration(test_sql)
    ch_client.init_migrations_table()

    schema = ch_client.get_database_schema()

    assert schema["version"] == "0"
    assert len(schema["tables"]) == 1
    assert schema["tables"][0].startswith("CREATE TABLE houseplant_test_")
    assert "test_table" in schema["tables"][0]
    assert "ENGINE = MergeTree" in schema["tables"][0]
