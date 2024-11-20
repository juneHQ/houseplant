"""ClickHouse database operations module."""

from clickhouse_driver import Client
from datetime import datetime
import os


class ClickHouseClient:
    def __init__(self, host=None, database=None):
        self.client = Client(
            host=host or os.getenv('CLICKHOUSE_HOST', 'localhost'),
            database=database or os.getenv('CLICKHOUSE_DB', 'june_development')
        )

    def init_migrations_table(self):
        """Initialize the schema migrations table."""
        self.client.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version LowCardinality(String),
                active UInt8 NOT NULL DEFAULT 1,
                created_at DateTime64(6, 'UTC') NOT NULL DEFAULT now64()
            )
            ENGINE = ReplacingMergeTree(created_at)
            PRIMARY KEY(version)
            ORDER BY (version)
        """)

    def get_applied_migrations(self):
        """Get list of applied migrations."""
        return self.client.execute("""
            SELECT version
            FROM schema_migrations
            WHERE active = 1
            ORDER BY version
        """)

    def execute_migration(self, sql: str):
        """Execute a migration SQL statement."""
        return self.client.execute(sql)

    def mark_migration_applied(self, version: str):
        """Mark a migration as applied."""
        self.client.execute("""
            INSERT INTO schema_migrations (version, active)
            VALUES
        """, [{'version': version, 'active': 1}])
