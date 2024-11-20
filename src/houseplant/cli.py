"""Console script for houseplant."""

import houseplant
import os

import typer
from rich.console import Console

app = typer.Typer()
console = Console()


@app.command()
def init():
    """Initialize a new houseplant project."""
    console.print("Initializing new houseplant project...")


@app.command(name="migrate:status")
def migrate_status():
    """Show status of database migrations."""
    console.print("Checking migration status...")


@app.command(name="migrate:up")
def migrate_up(version: str | None = None):
    """Run migrations up to specified version."""
    version = version or os.getenv("VERSION")
    if version:
        console.print(f"Running migrations up to version {version}...")
    else:
        console.print("Running all pending migrations...")


@app.command(name="migrate:down")
def migrate_down(version: str | None = None):
    """Roll back migrations to specified version."""
    version = version or os.getenv("VERSION")
    if version:
        console.print(f"Rolling back migrations to version {version}...")
    else:
        console.print("Rolling back all migrations...")


@app.command(name="migrate")
def migrate(version: str | None = None):
    """Run migrations up to specified version."""
    migrate_up(version)


@app.command(hidden=True)
def main():
    """Console script for houseplant."""
    console.print(
        "Replace this message by putting your code into " "houseplant.cli.main"
    )
    console.print("See Typer documentation at https://typer.tiangolo.com/")


if __name__ == "__main__":
    app()
