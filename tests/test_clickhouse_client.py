import pytest


@pytest.fixture
def migrations_table(ch_client):
    """Fixture to initialize migrations table."""
    ch_client.init_migrations_table()
    return ch_client


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

    schema = ch_client.get_database_schema()

    assert "test_table" in schema
    assert schema["test_table"]["engine"] == "MergeTree"
    assert schema["test_table"]["primary_key"] == "id"
    assert schema["test_table"]["sorting_key"] == "id"

    columns = schema["test_table"]["columns"]
    assert "id" in columns
    assert columns["id"]["type"] == "UInt32"
    assert not columns["id"]["has_default"]

    assert "name" in columns
    assert columns["name"]["type"] == "String"
    assert not columns["name"]["has_default"]
