"""Console script for houseplant."""

import os
import typer
from rich.console import Console
from houseplant import Houseplant
from typing import Optional

app = typer.Typer()

def get_houseplant() -> Houseplant:
    return Houseplant()

@app.command()
def init():
    """Initialize a new houseplant project."""
    hp = get_houseplant()
    hp.init()

@app.command(name="migrate:status")
def migrate_status():
    """Show status of database migrations."""
    hp = get_houseplant()
    hp.migrate_status()

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

@app.command(name="migrate")
def migrate(version: Optional[str] = typer.Argument(None)):
    """Run migrations up to specified version."""
    hp = get_houseplant()
    hp.migrate(version)

@app.command(name="generate")
def generate(name: str):
    """Generate a new migration."""
    hp = get_houseplant()
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
