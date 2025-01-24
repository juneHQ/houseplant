import os
from typing import Generator

import pytest
from typer.testing import CliRunner

from houseplant import Houseplant, __version__
from houseplant.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def mock_clickhouse(mocker):
    """Mock ClickHouse connection and client for all tests."""
    # Mock the clickhouse_driver.Client
    mock_client = mocker.patch("houseplant.clickhouse_client.Client", autospec=True)

    # Create a mock instance with required methods and attributes
    client_instance = mocker.Mock()
    client_instance.execute.return_value = [[1]]  # Default successful response
    client_instance.connection = mocker.Mock()
    client_instance.connection.database = "test_db"
    mock_client.return_value = client_instance

    return client_instance


@pytest.fixture
def mock_houseplant(mocker, mock_clickhouse) -> Generator[None, None, None]:
    """Mock the Houseplant class to avoid actual operations during testing."""
    # Create a real instance to get access to the original init method
    real_instance = Houseplant()

    # Create mock instance
    mock_instance = mocker.Mock(spec=Houseplant)
    mock_instance.db = mocker.Mock()
    mock_instance.db.client = mock_clickhouse
    mock_instance.db._check_clickhouse_connection.return_value = None
    mock_instance.db.init_migrations_table.return_value = None
    mock_instance.console = real_instance.console

    # Create a mock that wraps the real init method
    mock_instance.init = mocker.Mock(side_effect=real_instance.init)

    # Mock both the constructor and get_houseplant
    mocker.patch("houseplant.cli.Houseplant", return_value=mock_instance)
    mocker.patch("houseplant.cli.get_houseplant", return_value=mock_instance)

    yield mock_instance


def test_dotenv_loading(tmp_path, monkeypatch):
    """Test that .env file is loaded."""
    assert os.getenv("CLICKHOUSE_HOST") is None

    # Create a temporary .env file
    env_file = tmp_path / ".env"
    env_file.write_text("CLICKHOUSE_HOST=test.host")

    # Set current working directory to tmp_path
    monkeypatch.chdir(tmp_path)

    # Import cli module to trigger .env loading
    import importlib

    import houseplant.cli

    importlib.reload(houseplant.cli)

    assert os.getenv("CLICKHOUSE_HOST") == "test.host"


def test_version_flag():
    """Test the version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"houseplant version {__version__}" in result.stdout


def test_init_command(tmp_path, mock_houseplant, monkeypatch):
    """Test the init command."""
    # Change to temp directory safely using monkeypatch
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    mock_houseplant.init.assert_called_once()

    # Verify directories were created using absolute paths
    migrations_dir = tmp_path / "ch" / "migrations"
    schema_file = tmp_path / "ch" / "schema.sql"

    assert migrations_dir.exists()
    assert schema_file.exists()


def test_migrate_status_command(mock_houseplant):
    """Test the migrate:status command."""
    result = runner.invoke(app, ["migrate:status"])
    assert result.exit_code == 0
    mock_houseplant.migrate_status.assert_called_once()


def test_migrate_up_command(mock_houseplant):
    """Test the migrate:up command with and without version."""
    # Test without version
    result = runner.invoke(app, ["migrate:up"])
    assert result.exit_code == 0
    mock_houseplant.migrate_up.assert_called_with(None)

    # Test with version
    mock_houseplant.reset_mock()
    result = runner.invoke(app, ["migrate:up", "1.0"])
    assert result.exit_code == 0
    mock_houseplant.migrate_up.assert_called_with("1.0")


def test_migrate_down_command(mock_houseplant):
    """Test the migrate:down command with and without version."""
    # Test without version
    result = runner.invoke(app, ["migrate:down"])
    assert result.exit_code == 0
    mock_houseplant.migrate_down.assert_called_with(None)

    # Test with version
    mock_houseplant.reset_mock()
    result = runner.invoke(app, ["migrate:down", "1.0"])
    assert result.exit_code == 0
    mock_houseplant.migrate_down.assert_called_with("1.0")


def test_migrate_command(mock_houseplant):
    """Test the migrate command with and without version."""
    # Test without version
    result = runner.invoke(app, ["migrate"])
    assert result.exit_code == 0
    mock_houseplant.migrate.assert_called_with(None)

    # Test with version
    mock_houseplant.reset_mock()
    result = runner.invoke(app, ["migrate", "1.0"])
    assert result.exit_code == 0
    mock_houseplant.migrate.assert_called_with("1.0")


def test_generate_command(mock_houseplant):
    """Test the generate command."""
    result = runner.invoke(app, ["generate", "new_migration"])
    assert result.exit_code == 0
    mock_houseplant.generate.assert_called_with("new_migration")


def test_main_command():
    """Test the main command."""
    result = runner.invoke(app, ["main"])
    assert result.exit_code == 0
    assert "Replace this message" in result.stdout


def test_cli_entrypoint():
    """Test the CLI entrypoint."""
    import houseplant.cli

    assert hasattr(houseplant.cli, "app")
