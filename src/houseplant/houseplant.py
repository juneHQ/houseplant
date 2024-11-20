"""Main module."""

import os
from rich.console import Console
from datetime import datetime
from .clickhouse_client import ClickHouseClient


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
        # TODO: Implement migration status check
        pass

    def migrate_up(self, version: str | None = None):
        """Run migrations up to specified version."""
        # TODO: Implement migration up logic
        pass

    def migrate_down(self, version: str | None = None):
        """Roll back migrations to specified version."""
        # TODO: Implement migration down logic
        pass

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
