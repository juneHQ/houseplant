<p align="center">
   <img src="./houseplant.png" width="300">
</p>

# Houseplant: Database Migrations for ClickHouse

[![PyPI version](https://img.shields.io/pypi/v/houseplant.svg)](https://pypi.python.org/pypi/houseplant)
[![image](https://img.shields.io/pypi/l/houseplant.svg)](https://pypi.org/project/houseplant/)
[![image](https://img.shields.io/pypi/pyversions/houseplant.svg)](https://pypi.org/project/houseplant/)

**Houseplant** is a CLI tool that helps you manage database migrations for ClickHouse!

---

**Here's how you can manage your ClickHouse migrations.**

<pre>
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
</pre>

## Why Houseplant?

- **Schema Tracking**: Automatically tracks and updates your database schema
- **YAML Format**: Migrations are written in YAML format, making them easy to read and maintain
- **Environment Support**: Houseplant supports different environments (development, test, production) with different migration configurations for each
- **Rich CLI**: Comes with an intuitive command-line interface for all migration operations

## Installation

You can install Houseplant using pip:

<pre>
$ pip install houseplant
</pre>

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
