"""Console script for houseplant."""

import os
import typer
from rich.console import Console
from houseplant import Houseplant

app = typer.Typer()
hp = Houseplant()


@app.command()
def init():
    """Initialize a new houseplant project."""
    hp.init()


@app.command(name="migrate:status")
def migrate_status():
    """Show status of database migrations."""
    hp.migrate_status()


@app.command(name="migrate:up")
def migrate_up(version: str | None = None):
    """Run migrations up to specified version."""
    version = version or os.getenv("VERSION")
    hp.migrate_up(version)


@app.command(name="migrate:down")
def migrate_down(version: str | None = None):
    """Roll back migrations to specified version."""
    version = version or os.getenv("VERSION")
    hp.migrate_down(version)


@app.command(name="migrate")
def migrate(version: str | None = None):
    """Run migrations up to specified version."""
    hp.migrate(version)


@app.command(name="generate")
def generate(name: str):
    """Generate a new migration."""
    hp.generate(name)


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
