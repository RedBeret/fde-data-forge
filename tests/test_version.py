"""Version consistency tests."""

from click.testing import CliRunner

from fde import __version__
from fde.cli import cli


def test_cli_and_package_versions_match():
    result = CliRunner().invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert __version__ == "1.1.0"
    assert "1.1.0" in result.output
