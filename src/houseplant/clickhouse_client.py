"""ClickHouse database operations module."""

from clickhouse_driver import Client
import os


class ClickHouseClient:
    def __init__(self, host=None, database=None, port=None):
        host = host or os.getenv("CLICKHOUSE_HOST", "localhost")
        if ":" in host:
            host, port = host.split(":")

        self.client = Client(
            host=host,
            port=port or os.getenv("CLICKHOUSE_PORT", 9000),
            database=database or os.getenv("CLICKHOUSE_DB", "june_development"),
            user=os.getenv("CLICKHOUSE_USER", "default"),
            password=os.getenv("CLICKHOUSE_PASSWORD", ""),
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

    def get_database_schema(self):
        """Get the database schema organized by table."""
        result = self.client.execute("""
            SELECT 
                table,
                name,
                type,
                default_expression,
                compression_codec,
                is_nullable
            FROM system.columns
            WHERE database = currentDatabase()
            ORDER BY table, name
        """)

        schema = {}
        for table, column, type_, default, codec, nullable in result:
            if table not in schema:
                schema[table] = {}
            schema[table][column] = {
                "type": type_,
                "default": default if default else None,
                "compression_codec": codec,
                "is_nullable": nullable,
            }

        return schema

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
        self.client.execute(
            """
            INSERT INTO schema_migrations (version, active)
            VALUES
        """,
            [{"version": version, "active": 1}],
        )
