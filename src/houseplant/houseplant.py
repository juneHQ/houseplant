"""Main module."""

import os
from datetime import datetime

import yaml
from rich.console import Console
from rich.table import Table

from .clickhouse_client import ClickHouseClient
from .utils import MIGRATIONS_DIR, get_migration_files


class EnvVars:
    """Helper class to access environment variables via attribute syntax."""

    def __getattr__(self, name: str) -> str:
        return os.getenv(name, "")


class Houseplant:
    def __init__(self):
        self.console = Console()
        self.db = ClickHouseClient()
        self.env = os.getenv("HOUSEPLANT_ENV", "development")

    def _check_migrations_dir(self):
        """Check if migrations directory exists and raise formatted error if not."""
        if not os.path.exists(MIGRATIONS_DIR):
            self.console.print("[red]Error:[/red] Migrations directory not found")
            self.console.print(
                "\nPlease run [bold]houseplant init[/bold] to create a new project "
                "or ensure you're in the correct directory."
            )
            raise SystemExit(1)

    def init(self):
        """Initialize a new houseplant project."""
        with self.console.status("[bold green]Initializing new houseplant project..."):
            os.makedirs("ch/migrations", exist_ok=True)
            open("ch/schema.sql", "a").close()

            self.db.init_migrations_table()

        self.console.print("✨ Project initialized successfully!")

    def migrate_status(self):
        """Show status of database migrations."""
        # Get applied migrations from database
        applied_migrations = {
            version[0] for version in self.db.get_applied_migrations()
        }

        migration_files = get_migration_files()
        if not migration_files:
            self.console.print("[yellow]No migrations found.[/yellow]")
            return

        self.console.print(f"\nDatabase: {self.db.client.connection.database}\n")

        table = Table()
        table.add_column("Status", justify="center", style="cyan", no_wrap=True)
        table.add_column("Migration ID", justify="left", style="magenta")
        table.add_column("Migration Name", justify="left", style="green")

        for migration_file in migration_files:
            version = migration_file.split("_")[0]
            status = (
                "[green]up[/green]"
                if version in applied_migrations
                else "[red]down[/red]"
            )
            name = " ".join(migration_file.split("_")[1:]).replace(".yml", "")
            table.add_row(status, version, name)

        self.console.print(table)
        self.console.print("")

    def migrate_up(self, version: str | None = None):
        """Run migrations up to specified version."""
        # Remove VERSION= prefix if present
        if version and version.startswith("VERSION="):
            version = version.replace("VERSION=", "")

        migration_files = get_migration_files()
        if not migration_files:
            self.console.print("[yellow]No migrations found.[/yellow]")
            return

        # Get applied migrations from database
        applied_migrations = {
            version[0] for version in self.db.get_applied_migrations()
        }

        # If specific version requested, verify it exists
        if version:
            matching_files = [f for f in migration_files if f.split("_")[0] == version]
            if not matching_files:
                self.console.print(f"[red]Migration version {version} not found[/red]")
                return

        with self.console.status(
            f"[bold green]Running migration version: {version}..."
        ):
            for migration_file in migration_files:
                migration_version = migration_file.split("_")[0]

                if version and migration_version != version:
                    continue

                if migration_version in applied_migrations:
                    continue

                # Load and execute migration
                with open(os.path.join(MIGRATIONS_DIR, migration_file), "r") as f:
                    migration = yaml.safe_load(f)

                table = migration.get("table", "").strip()
                if not table:
                    self.console.print(
                        "[red]✗[/red] Migration [bold red]failed[/bold red]: "
                        "'table' field is required in migration file"
                    )
                    return

                table_definition = migration.get("table_definition", "").strip()
                table_settings = migration.get("table_settings", "").strip()

                format_args = {"table": table, "env": EnvVars()}
                if table_definition and table_settings:
                    format_args.update(
                        {
                            "table_definition": table_definition,
                            "table_settings": table_settings,
                        }
                    )

                sink_table = migration.get("sink_table", "").strip()
                view_definition = migration.get("view_definition", "").strip()
                view_query = migration.get("view_query", "").strip()
                if sink_table and view_definition and view_query:
                    format_args.update(
                        {
                            "sink_table": sink_table,
                            "view_definition": view_definition,
                            "view_query": view_query,
                        }
                    )

                # Get migration SQL based on environment
                migration_env: dict = migration.get(self.env, {})
                migration_sql = (
                    migration_env.get("up", "").format(**format_args).strip()
                )

                if migration_sql:
                    self.db.execute_migration(
                        migration_sql, migration_env.get("query_settings")
                    )
                    self.db.mark_migration_applied(migration_version)
                    self.console.print(
                        f"[green]✓[/green] Applied migration {migration_file}"
                    )
                else:
                    self.console.print(
                        f"[yellow]⚠[/yellow] Empty migration {migration_file}"
                    )

                if version and migration_version == version:
                    self.update_schema()
                    break

    def migrate_down(self, version: str | None = None):
        """Roll back migrations to specified version."""
        # Remove VERSION= prefix if present
        if version and version.startswith("VERSION="):
            version = version.replace("VERSION=", "")

        # Get applied migrations from database
        applied_migrations = sorted(
            [version[0] for version in self.db.get_applied_migrations()], reverse=True
        )

        if not applied_migrations:
            self.console.print("[yellow]No migrations to roll back.[/yellow]")
            return

        with self.console.status(f"[bold green]Rolling back to version: {version}..."):
            for migration_version in applied_migrations:
                if version and migration_version < version:
                    break

                # Find corresponding migration file
                migration_file = next(
                    (
                        f
                        for f in os.listdir(MIGRATIONS_DIR)
                        if f.startswith(migration_version) and f.endswith(".yml")
                    ),
                    None,
                )

                if not migration_file:
                    self.console.print(
                        f"[red]Warning: Migration file for version {migration_version} not found[/red]"
                    )
                    continue

                # Load and execute down migration
                with open(os.path.join(MIGRATIONS_DIR, migration_file), "r") as f:
                    migration = yaml.safe_load(f)

                table = migration.get("table", "").strip()
                if not table:
                    self.console.print(
                        "[red]✗[/red] [bold red] Migration failed[/bold red]: "
                        "'table' field is required in migration file"
                    )
                    return

                # Get migration SQL based on environment
                migration_env = migration.get(self.env, {})
                migration_sql = (
                    migration_env.get("down", {})
                    .format(table=table, env=EnvVars())
                    .strip()
                )

                if migration_sql:
                    self.db.execute_migration(
                        migration_sql, migration_env.get("query_settings")
                    )
                    self.db.mark_migration_rolled_back(migration_version)
                    self.update_schema()
                    self.console.print(
                        f"[green]✓[/green] Rolled back migration {migration_file}"
                    )

                    return

                self.console.print(
                    f"[yellow]⚠[/yellow] Empty down migration {migration_file}"
                )

    def migrate(self, version: str | None = None):
        """Run migrations up to specified version."""
        self.migrate_up(version)

    def generate(self, name: str):
        """Generate a new migration."""
        with self.console.status("[bold green]Generating migration..."):
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

            migration_name = name.replace(" ", "_").replace("-", "_").lower()
            migration_file = f"ch/migrations/{timestamp}_{migration_name}.yml"

            with open(migration_file, "w") as f:
                f.write(f"""version: "{timestamp}"
name: {migration_name}
table:

development: &development
  up: |
  down: |
    DROP TABLE {{table}}

test:
  <<: *development

production:
  up: |
  down: |
    DROP TABLE {{table}}
""")

            self.console.print(f"✨ Generated migration: {migration_file}")

    def db_schema_load(self):
        """Load schema migrations from migration files without applying them."""
        migration_files = get_migration_files()
        if not migration_files:
            self.console.print("[yellow]No migrations found.[/yellow]")
            return

        with self.console.status("[bold green]Loading schema migrations..."):
            for migration_file in migration_files:
                migration_version = migration_file.split("_")[0]
                self.db.mark_migration_applied(migration_version)
                self.console.print(
                    f"[green]✓[/green] Loaded migration {migration_file}"
                )

        self.console.print("✨ Schema migrations loaded successfully!")

    def update_schema(self):
        """Update the schema file with the current database schema."""

        # Get all applied migrations in order
        applied_migrations = self.db.get_applied_migrations()
        migration_files = get_migration_files()
        latest_version = applied_migrations[-1][0] if applied_migrations else "0"

        # Get all database objects
        tables = self.db.get_database_tables()
        materialized_views = self.db.get_database_materialized_views()
        dictionaries = self.db.get_database_dictionaries()

        # Track processed tables to ensure first migration takes precedence
        processed_tables = set()

        # Group statements by type
        table_statements = []
        mv_statements = []
        dict_statements = []

        for migration_version in applied_migrations:
            matching_file = next(
                (f for f in migration_files if f.startswith(migration_version[0])), None
            )

            if not matching_file:
                continue

            migration_file = f"ch/migrations/{matching_file}"
            with open(migration_file) as f:
                migration_data = yaml.safe_load(f)

            # Extract table name from migration
            table_name = migration_data.get("table")
            if not table_name:
                continue

            # Skip if we've already processed this table
            if table_name in processed_tables:
                continue

            # Check tables first
            for table in tables:
                if table[0] == table_name:
                    create_stmt = self.db.client.execute(
                        f"SHOW CREATE TABLE {table_name}"
                    )[0][0]
                    table_statements.append(create_stmt)
                    processed_tables.add(table_name)

            # Then materialized views
            for mv in materialized_views:
                if mv[0] == table_name:
                    mv_name = mv[0]
                    create_stmt = self.db.client.execute(f"SHOW CREATE VIEW {mv_name}")[
                        0
                    ][0]
                    mv_statements.append(create_stmt)
                    processed_tables.add(table_name)

            # Finally dictionaries
            for ch_dict in dictionaries:
                if ch_dict[0] == table_name:
                    dict_name = ch_dict[0]
                    create_stmt = self.db.client.execute(
                        f"SHOW CREATE DICTIONARY {dict_name}"
                    )[0][0]
                    dict_statements.append(create_stmt)
                    processed_tables.add(table_name)

        # Write schema file
        with open("ch/schema.sql", "w") as f:
            f.write(f"-- version: {latest_version}\n\n")
            if table_statements:
                f.write("-- TABLES\n\n")
                f.write("\n;\n\n".join(table_statements) + ";")
            if mv_statements:
                f.write("\n\n-- MATERIALIZED VIEWS\n\n")
                f.write("\n;\n\n".join(mv_statements) + ";")
            if dict_statements:
                f.write("\n\n-- DICTIONARIES\n\n")
                f.write("\n;\n\n".join(dict_statements) + ";")
