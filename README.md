<p align="center">
   <img src="https://raw.githubusercontent.com/juneHQ/houseplant/refs/heads/master/houseplant.png" width="300">
</p>

# Houseplant: Database Migrations for ClickHouse

[![PyPI version](https://img.shields.io/pypi/v/houseplant.svg)](https://pypi.python.org/pypi/houseplant)
[![image](https://img.shields.io/pypi/l/houseplant.svg)](https://pypi.org/project/houseplant/)
[![image](https://img.shields.io/pypi/pyversions/houseplant.svg)](https://pypi.org/project/houseplant/)

**Houseplant** is a CLI tool that helps you manage database migrations for ClickHouse.

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

- **Schema Management**: Houseplant automatically tracks and manages your ClickHouse schema changes, making it easy to evolve your data model over time
- **Developer Experience**: Write migrations in YAML format, making them easy to read, review, and maintain
- **Environment Support**: Different configurations for development, testing, and production environments
- **Rich CLI**: Comes with an intuitive command-line interface for all migration operations

## Installation

You can install Houseplant using pip:

<pre>
$ pip install houseplant
</pre>

## Configuration

Houseplant uses the following environment variables to connect to your ClickHouse instance:

- `HOUSEPLANT_ENV`: The current environment
- `CLICKHOUSE_HOST`: Host address of your ClickHouse server (default: "localhost")
- `CLICKHOUSE_PORT`: Port number for ClickHouse (default: 9000)
- `CLICKHOUSE_DB`: Database name (default: "development")
- `CLICKHOUSE_USER`: Username for authentication (default: "default")
- `CLICKHOUSE_PASSWORD`: Password for authentication (default: "")
- `CLICKHOUSE_SECURE`: Enable secure connection via the `secure` flag of ClickHouse client (default: False)
- `CLICKHOUSE_VERIFY`: Enable certificate verifiaction `verify` flag of ClickHouse client (default: False)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
