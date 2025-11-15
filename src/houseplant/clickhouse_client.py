"""ClickHouse database operations module."""

import os

from clickhouse_driver import Client
from clickhouse_driver.errors import NetworkError, ServerException
from rich.console import Console


class RichFormattedError:
    """Mixin for exceptions that use Rich formatting."""

    def __init__(self, message, error_type="Error"):
        super().__init__(message)
        self.message = message
        console = Console(stderr=True)
        console.print(f"[red bold]ClickHouse {error_type}:[/] {message}")


class ClickHouseConnectionError(RichFormattedError, Exception):
    """Raised when ClickHouse connection fails."""

    def __init__(self, message):
        super().__init__(message, error_type="Connection Error")


class ClickHouseAuthenticationError(RichFormattedError, Exception):
    """Raised when ClickHouse authentication fails."""

    def __init__(self, message):
        super().__init__(message, error_type="Authentication Error")


class ClickHouseDatabaseNotFoundError(RichFormattedError, Exception):
    """Raised when ClickHouse database does not exist."""

    def __init__(self, database):
        message = f"Database '{database}' does not exist"
        super().__init__(message, error_type="Database Error")


class ClickHouseClient:
    def __init__(
        self, host=None, port=None, database=None, user=None, password=None, secure=None
    ):
        self.host = host or os.getenv("CLICKHOUSE_HOST", "localhost")
        # Parse port from host:port string if present, otherwise use port parameter or default
        if ":" in self.host:
            self.host, port_str = self.host.split(":")
            self.port = int(port_str)
        else:
            self.port = int(port or os.getenv("CLICKHOUSE_PORT", 9000))

        self.database = database or os.getenv("CLICKHOUSE_DB", "development")

        self.user = user or os.getenv("CLICKHOUSE_USER", "default")
        self.password = password or os.getenv("CLICKHOUSE_PASSWORD", "")

        # Use SSL port by default if secure
        self.secure = secure or os.getenv("CLICKHOUSE_SECURE", "n").lower()
        self.secure = self.secure in ("true", "t", "yes", "y", "1")
        self.port = 9440 if self.secure else self.port

        # Disable verification unless specified otherwise
        self.verify = os.getenv("CLICKHOUSE_VERIFY", "n").lower()
        self.verify = self.verify in ("true", "t", "yes", "y", "1")

        self.client = Client(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            secure=self.secure,
            verify=self.verify,
        )

        self._cluster = None

    def _check_clickhouse_connection(self):
        """Check connection to ClickHouse and raise appropriate errors."""
        try:
            self.client.execute("SELECT 1")
        except NetworkError:
            raise ClickHouseConnectionError(
                f"Could not connect to database at {self.host}:{self.port}"
            )
        except ServerException as e:
            if "Authentication failed" in str(e):
                raise ClickHouseAuthenticationError(
                    f"Authentication failed for user {os.getenv('CLICKHOUSE_USER', 'default')}"
                )
            elif "Database" in str(e) and "does not exist" in str(e):
                raise ClickHouseDatabaseNotFoundError(self.database)
            else:
                raise e

    @property
    def cluster(self):
        if self._cluster is None:
            self._cluster = os.getenv("CLICKHOUSE_CLUSTER")
        return self._cluster

    @cluster.setter
    def cluster(self, value):
        self._cluster = value

    def init_migrations_table_query(self):
        """Initialize the schema migrations table."""
        table_definition = """
            CREATE TABLE IF NOT EXISTS schema_migrations {cluster} (
                version LowCardinality(String),
                active UInt8 NOT NULL DEFAULT 1,
                created_at DateTime64(6, 'UTC') NOT NULL DEFAULT now64()
            )
            ENGINE = {engine}
            PRIMARY KEY(version)
            ORDER BY (version)
        """

        cluster_clause = "ON CLUSTER '{cluster}'" if self.cluster is not None else ""
        engine = (
            "ReplicatedReplacingMergeTree(created_at)"
            if self.cluster is not None
            else "ReplacingMergeTree(created_at)"
        )

        return table_definition.format(cluster=cluster_clause, engine=engine)

    def init_migrations_table(self):
        self.client.execute(self.init_migrations_table_query())

    def get_database_schema(self):
        """Get the database schema organized by object type and sorted by migration date."""
        # Get all applied migrations in order
        applied_migrations = self.get_applied_migrations()
        latest_version = applied_migrations[-1][0] if applied_migrations else "0"

        # Initialize schema structure
        schema = {
            "version": latest_version,
            "tables": [],
            "materialized_views": [],
            "dictionaries": [],
        }

        # Get all database objects
        tables = self.get_database_tables()
        materialized_views = self.get_database_materialized_views()
        dictionaries = self.get_database_dictionaries()

        for table in tables:
            table_name = table[0]
            create_stmt = self.client.execute(f"SHOW CREATE TABLE {table_name}")[0][0]
            schema["tables"].append(create_stmt)

        for materialized_view in materialized_views:
            materialized_view_name = materialized_view[0]
            create_stmt = self.client.execute(
                f"SHOW CREATE MATERIALIZED VIEW {materialized_view_name}"
            )[0][0]
            schema["materialized_views"].append(create_stmt)

        for dictionary in dictionaries:
            dictionary_name = dictionary[0]
            create_stmt = self.client.execute(
                f"SHOW CREATE DICTIONARY {dictionary_name}"
            )[0][0]
            schema["dictionaries"].append(create_stmt)

        # Sort each category by migration date
        for category in ["tables", "materialized_views", "dictionaries"]:
            schema[category].sort()

        return schema

    def get_latest_migration(self):
        """Get the latest migration version."""
        # First check if the table exists
        table_exists = self.client.execute("""
            SELECT name
            FROM system.tables
            WHERE database = currentDatabase()
            AND name = 'schema_migrations'
        """)

        if not table_exists:
            return None

        result = self.client.execute("""
            SELECT MAX(version) FROM schema_migrations WHERE active = 1
        """)
        return result[0][0] if result else None

    def get_database_tables(self, database=None):
        """Get the database tables with their engines, indexes and partitioning."""
        database_expr = f"'{database}'" if database else "currentDatabase()"
        return self.client.execute(f"""
            SELECT
                name
            FROM system.tables
            WHERE database = {database_expr}
                AND position('MergeTree' IN engine) > 0
                AND engine NOT IN ('MaterializedView', 'Dictionary')
                AND name != 'schema_migrations'
            ORDER BY name
        """)

    def get_database_materialized_views(self, database=None):
        """Get the database materialized views."""
        database_expr = f"'{database}'" if database else "currentDatabase()"
        return self.client.execute(f"""
            SELECT
                name
            FROM system.tables
            WHERE database = {database_expr}
                AND engine = 'MaterializedView'
                AND name != 'schema_migrations'
            ORDER BY name
        """)

    def get_database_dictionaries(self, database=None):
        """Get the database dictionaries."""
        database_expr = f"'{database}'" if database else "currentDatabase()"
        return self.client.execute(f"""
            SELECT
                name
            FROM system.tables
            WHERE database = {database_expr}
                AND engine = 'Dictionary'
                AND name != 'schema_migrations'
            ORDER BY name
        """)

    def get_applied_migrations(self):
        """Get list of applied migrations."""
        return self.client.execute("""
            SELECT version
            FROM schema_migrations FINAL
            WHERE active = 1
            ORDER BY version
        """)

    def execute_migration(self, sql: str, query_settings: dict = None):
        """Execute a migration SQL statement."""
        # Split multiple statements and execute them separately
        statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
        for statement in statements:
            self.client.execute(statement, settings=query_settings)

    def mark_migration_applied(self, version: str):
        """Mark a migration as applied."""
        self.client.execute(
            """
            INSERT INTO schema_migrations (version, active)
            VALUES (%(version)s, 1)
            """,
            {"version": version},
        )

        self.client.execute(
            """
            OPTIMIZE TABLE schema_migrations FINAL
            """
        )

    def mark_migration_rolled_back(self, version: str):
        """Mark a migration as rolled back."""
        self.client.execute(
            """
            INSERT INTO schema_migrations (version, active, created_at)
            VALUES (
                %(version)s,
                0,
                now64()
            )
            """,
            {"version": version},
        )

        self.client.execute(
            """
            OPTIMIZE TABLE schema_migrations FINAL
            """
        )
