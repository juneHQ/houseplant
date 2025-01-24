"""Console script for houseplant."""

import os
from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv
from rich.console import Console

from houseplant import Houseplant, __version__

# Load environment variables from .env file in current directory
load_dotenv(Path.cwd() / ".env")

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Database Migrations for ClickHouse",
)


def get_houseplant() -> Houseplant:
    houseplant = Houseplant()
    houseplant._check_migrations_dir()
    houseplant.db._check_clickhouse_connection()
    return houseplant


def version_callback(value: bool):
    if value:
        console = Console()
        console.print(f"houseplant version {__version__}")
        raise typer.Exit()


@app.callback()
def common(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
):
    pass


@app.command()
def init():
    """Initialize a new houseplant project."""
    hp = Houseplant()
    hp.init()


@app.command(name="generate")
def generate(name: str):
    """Generate a new migration."""
    hp = get_houseplant()
    hp.generate(name)


@app.command(name="migrate:status")
def migrate_status():
    """Show status of database migrations."""
    hp = get_houseplant()
    hp.migrate_status()


@app.command(name="migrate")
def migrate(version: Optional[str] = typer.Argument(None)):
    """Run migrations up to specified version."""
    hp = get_houseplant()
    hp.migrate(version)


@app.command(name="migrate:up")
def migrate_up(version: Optional[str] = typer.Argument(None)):
    """Run migrations up to specified version."""
    hp = get_houseplant()
    version = version or os.getenv("VERSION")
    hp.migrate_up(version)


@app.command(name="migrate:down")
def migrate_down(version: Optional[str] = typer.Argument(None)):
    """Roll back migrations to specified version."""
    hp = get_houseplant()
    version = version or os.getenv("VERSION")
    hp.migrate_down(version)


@app.command(name="db:schema:load")
def db_schema_load():
    """Load the schema migrations from migrations directory."""
    hp = get_houseplant()
    hp.db_schema_load()


@app.command(hidden=True)
def main():
    """Console script for houseplant."""
    console = Console()
    console.print(
        "Replace this message by putting your code into " "houseplant.cli.main"
    )
    console.print("See Typer documentation at https://typer.tiangolo.com/")


if __name__ == "__main__":
    app()
