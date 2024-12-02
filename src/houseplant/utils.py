import os

MIGRATIONS_DIR = "ch/migrations"


def get_migration_files():
    # Get all local migration files
    return sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith(".yml")])
