import os

import pytest
import yaml

from houseplant.houseplant import Houseplant


@pytest.fixture
def houseplant():
    return Houseplant()


@pytest.fixture
def test_migration(tmp_path):
    # Set up test environment
    migrations_dir = tmp_path / "ch/migrations"
    migrations_dir.mkdir(parents=True)
    migration_file = migrations_dir / "20240101000000_test_migration.yml"

    migration_content = """version: "20240101000000"
name: test_migration
table: events

development: &development
  up: |
    CREATE TABLE {table} (
        id UInt32,
        name String
    ) ENGINE = MergeTree()
    ORDER BY id
  down: |
    DROP TABLE {table}

test:
  <<: *development

production:
  up: |
    CREATE TABLE {table} (
        id UInt32,
        name String
    ) ENGINE = ReplicatedMergeTree()
    ORDER BY id
  down: |
    DROP TABLE {table}
"""

    migration_file.write_text(migration_content)
    os.chdir(tmp_path)
    return migration_content


@pytest.fixture
def test_migration_with_settings(tmp_path):
    # Set up test environment
    migrations_dir = tmp_path / "ch/migrations"
    migrations_dir.mkdir(parents=True)
    migration_file = migrations_dir / "20240101000000_test_settings.yml"

    migration_content = """version: "20240101000000"
name: test_settings
table: settings_table

table_definition: |
    id UInt32,
    name String,
    created_at DateTime
table_settings: |
    ORDER BY (id, created_at)
    PARTITION BY toYYYYMM(created_at)

development: &development
  up: |
    CREATE TABLE {table} (
        {table_definition}
    ) ENGINE = MergeTree()
    {table_settings}
  down: |
    DROP TABLE {table}

test:
  <<: *development

production:
  up: |
    CREATE TABLE {table} ON CLUSTER '{{cluster}}' (
        {table_definition}
    ) ENGINE = MergeTree()
    {table_settings}
  down: |
    DROP TABLE {table}
"""

    migration_file.write_text(migration_content)
    os.chdir(tmp_path)
    return migration_content


def test_migrate_up_development(houseplant, test_migration, mocker):
    # Mock environment and database calls
    houseplant.env = "development"
    mock_execute = mocker.patch.object(houseplant.db, "execute_migration")
    mock_mark_applied = mocker.patch.object(houseplant.db, "mark_migration_applied")
    mock_get_applied = mocker.patch.object(
        houseplant.db, "get_applied_migrations", return_value=[]
    )

    # Run migration
    houseplant.migrate_up()

    # Verify correct SQL was executed
    expected_sql = """CREATE TABLE events (
    id UInt32,
    name String
) ENGINE = MergeTree()
ORDER BY id"""
    mock_execute.assert_called_once_with(expected_sql)
    mock_mark_applied.assert_called_once_with("20240101000000")
    mock_get_applied.assert_called_once()


def test_migrate_up_production(houseplant, test_migration, mocker):
    # Mock environment and database calls
    houseplant.env = "production"
    mock_execute = mocker.patch.object(houseplant.db, "execute_migration")
    mock_mark_applied = mocker.patch.object(houseplant.db, "mark_migration_applied")
    mock_get_applied = mocker.patch.object(
        houseplant.db, "get_applied_migrations", return_value=[]
    )

    # Run migration
    houseplant.migrate_up()

    # Verify correct SQL was executed
    expected_sql = """CREATE TABLE events (
    id UInt32,
    name String
) ENGINE = ReplicatedMergeTree()
ORDER BY id"""
    mock_execute.assert_called_once_with(expected_sql)
    mock_mark_applied.assert_called_once_with("20240101000000")
    mock_get_applied.assert_called_once()


def test_migrate_up_with_development_table_settings(
    houseplant, test_migration_with_settings, mocker
):
    # Mock database calls
    houseplant.env = "development"
    mock_execute = mocker.patch.object(houseplant.db, "execute_migration")
    mock_mark_applied = mocker.patch.object(houseplant.db, "mark_migration_applied")
    mock_get_applied = mocker.patch.object(
        houseplant.db, "get_applied_migrations", return_value=[]
    )

    # Run migration
    houseplant.migrate_up()

    # Verify correct SQL was executed with table_definition and table_settings
    expected_sql = """CREATE TABLE settings_table (
    id UInt32,
name String,
created_at DateTime
) ENGINE = MergeTree()
ORDER BY (id, created_at)
PARTITION BY toYYYYMM(created_at)"""
    mock_execute.assert_called_once_with(expected_sql)
    mock_mark_applied.assert_called_once_with("20240101000000")
    mock_get_applied.assert_called_once()


def test_migrate_up_with_production_table_settings(
    houseplant, test_migration_with_settings, mocker
):
    # Mock database calls
    houseplant.env = "production"
    mock_execute = mocker.patch.object(houseplant.db, "execute_migration")
    mock_mark_applied = mocker.patch.object(houseplant.db, "mark_migration_applied")
    mock_get_applied = mocker.patch.object(
        houseplant.db, "get_applied_migrations", return_value=[]
    )

    # Run migration
    houseplant.migrate_up()

    # Verify correct SQL was executed with table_definition and table_settings
    expected_sql = """CREATE TABLE settings_table ON CLUSTER '{cluster}' (
    id UInt32,
name String,
created_at DateTime
) ENGINE = MergeTree()
ORDER BY (id, created_at)
PARTITION BY toYYYYMM(created_at)"""
    mock_execute.assert_called_once_with(expected_sql)
    mock_mark_applied.assert_called_once_with("20240101000000")
    mock_get_applied.assert_called_once()


@pytest.mark.skip
def test_migrate_down(houseplant, test_migration, mocker):
    # Mock database calls
    mock_execute = mocker.patch.object(houseplant.db, "execute_migration")
    mock_mark_rolled_back = mocker.patch.object(
        houseplant.db, "mark_migration_rolled_back"
    )
    mock_get_applied = mocker.patch.object(
        houseplant.db, "get_applied_migrations", return_value=[("20240101000000",)]
    )

    # Roll back migration
    houseplant.migrate_down()

    # Verify correct SQL was executed
    mock_execute.assert_called_once_with("DROP TABLE events")
    mock_mark_rolled_back.assert_called_once_with("20240101000000")
    mock_get_applied.assert_called_once()
