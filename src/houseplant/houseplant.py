"""Main module."""

import os
from datetime import datetime

import yaml
from rich.console import Console
from rich.table import Table

from .clickhouse_client import ClickHouseClient


class Houseplant:
    def __init__(self):
        self.console = Console()
        self.db = ClickHouseClient()
        self.env = os.getenv("RAILS_ENV", "development")

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

        # Get all local migration files
        migrations_dir = "ch/migrations"
        if not os.path.exists(migrations_dir):
            self.console.print("[red]No migrations directory found.[/red]")
            return

        migration_files = sorted(
            [f for f in os.listdir(migrations_dir) if f.endswith(".yml")]
        )

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

        migrations_dir = "ch/migrations"
        if not os.path.exists(migrations_dir):
            self.console.print("[red]No migrations directory found.[/red]")
            return

        migration_files = sorted(
            [f for f in os.listdir(migrations_dir) if f.endswith(".yml")]
        )

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
                with open(os.path.join(migrations_dir, migration_file), "r") as f:
                    migration = yaml.safe_load(f)

                # Get migration SQL based on environment
                migration_sql = migration.get(self.env, {}).get("up", {}).strip()

                table = migration.get("table", "").strip()

                if not table:
                    self.console.print(
                        "[red]✗[/red] Migration [bold red]failed[/bold red]: "
                        "'table' field is required in migration file"
                    )
                    return

                table_definition = migration.get("table_definition", "").strip()
                table_settings = migration.get("table_settings", "").strip()

                format_args = {"table": table}
                if table_definition and table_settings:
                    format_args.update(
                        {
                            "table_definition": table_definition,
                            "table_settings": table_settings,
                        }
                    )

                migration_sql = migration_sql.format(**format_args).strip()
                if migration_sql:
                    self.db.execute_migration(migration_sql)
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

        migrations_dir = "ch/migrations"
        if not os.path.exists(migrations_dir):
            self.console.print("[red]No migrations directory found.[/red]")
            return

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
                        for f in os.listdir(migrations_dir)
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
                with open(os.path.join(migrations_dir, migration_file), "r") as f:
                    migration = yaml.safe_load(f)

                # Get migration SQL based on environment
                migration_sql = migration.get(self.env, {}).get("down", {}).strip()
                table = migration.get("table", "").strip()
                if not table:
                    self.console.print(
                        "[red]✗[/red] [bold red] Migration failed[/bold red]: "
                        "'table' field is required in migration file"
                    )
                    return
                migration_sql = migration_sql.format(table=table).strip()

                if migration_sql:
                    self.db.execute_migration(migration_sql)
                    self.db.mark_migration_rolled_back(migration_version)
                    self.update_schema()
                    self.console.print(
                        f"[green]✓[/green] Rolled back migration {migration_file}"
                    )
                else:
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

development: &development
  up: |
  down: |

test:
  <<: *development

production:
  up: |
  down: |
""")

            self.console.print(f"✨ Generated migration: {migration_file}")

    def update_schema(self):
        """Update the schema file with the current database schema."""

        # Get all applied migrations in order
        applied_migrations = self.db.get_applied_migrations()
        latest_version = applied_migrations[-1][0] if applied_migrations else "0"

        # Get all database objects
        tables = self.db.get_database_tables()
        materialized_views = self.db.get_database_materialized_views()
        dictionaries = self.db.get_database_dictionaries()

        # Build schema in migration order
        schema_statements = []

        for migration_version in applied_migrations:
            # Check tables first
            for table in tables:
                table_name = table[0]
                create_stmt = self.db.client.execute(f"SHOW CREATE TABLE {table_name}")[
                    0
                ][0]
                schema_statements.append(create_stmt)

            # Then materialized views
            for mv in materialized_views:
                mv_name = mv[0]
                create_stmt = self.db.client.execute(
                    f"SHOW CREATE MATERIALIZED VIEW {mv_name}"
                )[0][0]
                schema_statements.append(create_stmt)

            # Finally dictionaries
            for dict in dictionaries:
                dict_name = dict[0]
                create_stmt = self.db.client.execute(
                    f"SHOW CREATE DICTIONARY {dict_name}"
                )[0][0]
                schema_statements.append(create_stmt)

        # Write schema file
        with open("ch/schema.sql", "w") as f:
            f.write(f"-- version: {latest_version}\n\n")
            if schema_statements:
                f.write("\n;\n\n".join(schema_statements) + ";")
