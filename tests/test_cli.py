from typing import Generator

import pytest
from typer.testing import CliRunner

from houseplant import Houseplant, __version__
from houseplant.cli import app

runner = CliRunner()


@pytest.fixture
def mock_houseplant(mocker) -> Generator[None, None, None]:
    """Mock the Houseplant class to avoid actual operations during testing."""
    mock = mocker.patch("houseplant.cli.get_houseplant", autospec=True)
    mock_instance = mocker.Mock(spec=Houseplant)
    mock.return_value = mock_instance
    yield mock_instance


def test_version_flag():
    """Test the version flag."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"houseplant version {__version__}" in result.stdout


def test_init_command(mock_houseplant):
    """Test the init command."""
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    mock_houseplant.init.assert_called_once()


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
