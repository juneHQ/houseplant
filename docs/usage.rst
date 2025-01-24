=====
Usage
=====

Houseplant is a CLI tool that helps you manage database migrations for ClickHouse.

Basic Commands
--------------

Initialize a New Project
~~~~~~~~~~~~~~~~~~~~~~~~

To create a new Houseplant project::

    $ houseplant init

This will create the following structure::

    ch/
    ├── migrations/
    └── schema.sql

Generate a Migration
~~~~~~~~~~~~~~~~~~~~

To generate a new migration::

    $ houseplant generate "create users table"

This will create a new migration file in ``ch/migrations/`` with a timestamp prefix, for example::

    ch/migrations/20240320123456_create_users_table.yml

Migration File Structure
~~~~~~~~~~~~~~~~~~~~~~~~

Migration files use YAML format and support different environments::

    version: "20240320123456"
    name: create_users_table
    table: users

    development: &development
      up: |
        CREATE TABLE {table} (
          id UInt64,
          name String
        ) ENGINE = MergeTree()
        ORDER BY id
      down: |
        DROP TABLE {table}

    test:
      <<: *development

    production:
      up: |
        CREATE TABLE ON CLUSTER '{cluster}' {table} (
          id UInt64,
          name String
        ) ENGINE = ReplicatedMergeTree()
        ORDER BY id
      down: |
        DROP TABLE ON CLUSTER '{cluster}' {table}

Running Migrations
------------------

Check Migration Status
~~~~~~~~~~~~~~~~~~~~~~

To see the status of all migrations::

    $ houseplant migrate:status

This will show which migrations have been applied and which are pending.

Apply Migrations
~~~~~~~~~~~~~~~~

To run all pending migrations::

    $ houseplant migrate:up

To migrate to a specific version::

    $ houseplant migrate:up VERSION=20240320123456

Rollback Migrations
~~~~~~~~~~~~~~~~~~~

To roll back the last migration::

    $ houseplant migrate:down

To roll back to a specific version::

    $ houseplant migrate:down VERSION=20240320123456

Schema Management
-----------------

Load Schema
~~~~~~~~~~~

To load existing schema migrations into the database without applying them::

    $ houseplant db:schema:load

This is useful when setting up a new environment where the database and tables already exist.

Update Schema
~~~~~~~~~~~~~

The schema file (``ch/schema.sql``) is automatically updated after each migration. It contains:

- Table definitions
- Materialized view definitions
- Dictionary definitions

Environment Support
-------------------

Houseplant supports different environments through the ``HOUSEPLANT_ENV`` environment variable:

- development (default)
- test
- production

Set the environment before running commands::

    $ HOUSEPLANT_ENV=production houseplant migrate

Configuration
-------------

Houseplant uses the following environment variables:

- ``HOUSEPLANT_ENV``: The current environment (default: "development")
- ``CLICKHOUSE_HOST``: ClickHouse server host
- ``CLICKHOUSE_PORT``: ClickHouse server port
- ``CLICKHOUSE_USER``: ClickHouse username
- ``CLICKHOUSE_PASSWORD``: ClickHouse password
- ``CLICKHOUSE_DB``: ClickHouse database name
