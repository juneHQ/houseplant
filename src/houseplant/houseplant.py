"""Main module."""

import os
from rich.console import Console
from datetime import datetime
from .clickhouse_client import ClickHouseClient
import yaml


class Houseplant:
    def __init__(self):
        self.console = Console()
        self.db = ClickHouseClient()

    def init(self):
        """Initialize a new houseplant project."""
        self.console.print("Initializing new houseplant project...")

        os.makedirs("ch/migrations", exist_ok=True)
        open("ch/schema.yml", "a").close()

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

        self.console.print("\n[bold]Database migrations status:[/bold]\n")

        for migration_file in migration_files:
            version = migration_file.split("_")[0]
            status = (
                "[green]up[/green]"
                if version in applied_migrations
                else "[red]down[/red]"
            )
            name = " ".join(migration_file.split("_")[1:]).replace(".yml", "")
            self.console.print(f"{status}\t{version}\t{name}")

        self.console.print("")

    def migrate_up(self, version: str | None = None):
        """Run migrations up to specified version."""
        # Remove VERSION= prefix if present
        if version and version.startswith("VERSION="):
            version = version.replace("VERSION=", "")

        self.console.print(f"Running migration version: {version}")

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

        for migration_file in migration_files:
            migration_version = migration_file.split("_")[0]

            if version and migration_version != version:
                continue

            if migration_version in applied_migrations:
                continue

            # Load and execute migration
            with open(os.path.join(migrations_dir, migration_file), "r") as f:
                migration = yaml.safe_load(f)

            if migration.get("up", {}).get("sql"):
                self.db.execute_migration(migration["up"]["sql"])
                self.db.mark_migration_applied(migration_version)
                self.console.print(
                    f"[green]✓[/green] Applied migration {migration_file}"
                )
            else:
                self.console.print(
                    f"[yellow]⚠[/yellow] Empty migration {migration_file}"
                )

            # Stop if we've reached target version
            if version and migration_version == version:
                break

    def migrate_down(self, version: str | None = None):
        """Roll back migrations to specified version."""
        # Remove VERSION= prefix if present
        if version and version.startswith("VERSION="):
            version = version.replace("VERSION=", "")

        self.console.print(f"Rolling back to version: {version}")

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

            if migration["down"]["sql"]:
                self.db.execute_migration(migration["down"]["sql"])
                self.db.mark_migration_rolled_back(migration_version)
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

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        migration_name = name.replace(" ", "_").replace("-", "_").lower()
        migration_file = f"ch/migrations/{timestamp}_{migration_name}.yml"

        with open(migration_file, "w") as f:
            f.write(f"""version: "{timestamp}"
name: {migration_name}
up:
  sql: ""

down:
  sql: ""
""")

        self.console.print(f"✨ Generated migration: {migration_file}")
