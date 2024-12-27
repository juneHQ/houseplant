Houseplant: Database Migrations for ClickHouse
==============================================

.. image:: https://img.shields.io/pypi/v/houseplant.svg
   :target: https://pypi.python.org/pypi/houseplant

.. image:: https://img.shields.io/pypi/l/houseplant.svg
   :target: https://pypi.org/project/houseplant/

.. image:: https://img.shields.io/pypi/pyversions/houseplant.svg
   :target: https://pypi.org/project/houseplant/

Houseplant is a CLI tool that helps you manage database migrations for ClickHouse.

Here's how you can manage your ClickHouse migrations:

.. code-block:: console

   $ houseplant init
   ✨ Project initialized successfully!

   $ houseplant generate "add events"
   ✨ Generated migration: ch/migrations/20240101000000_add_events.yml

   $ houseplant migrate:status
   Database: june_development

   ┏━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
   ┃ Status ┃ Migration ID   ┃ Migration Name ┃
   ┡━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
   │   up   │ 20240101000000 │ add events     │
   └────────┴────────────────┴────────────────┘

   $ houseplant migrate
   ✓ Applied migration 20241121003230_add_events.yml

   $ houseplant migrate:up VERSION=20241121003230
   ✓ Applied migration 20241121003230_add_events.yml

   $ houseplant migrate:down VERSION=20241121003230
   ✓ Rolled back migration 20241121003230_add_events.yml

Why Houseplant?
---------------

- **Schema Management**: Houseplant automatically tracks and manages your ClickHouse schema changes, making it easy to evolve your data model over time
- **Developer Experience**: Write migrations in YAML format, making them easy to read, review, and maintain
- **Environment Support**: Different configurations for development, testing, and production environments
- **Rich CLI**: Comes with an intuitive command-line interface for all migration operations

The User Guide
--------------

.. toctree::
   :maxdepth: 2

   install
   usage

Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
