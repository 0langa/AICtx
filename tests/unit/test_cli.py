"""Unit tests for CLI behavior."""

from __future__ import annotations

from typer.testing import CliRunner

from aictx.cli import app

runner = CliRunner()


def test_cli_version_exits_successfully() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "aictx" in result.output
    assert "0.1.0" in result.output


def test_verify_command_exits_nonzero_on_failure(tmp_path) -> None:
    result = runner.invoke(app, ["verify", "--project", str(tmp_path), "--strict"])
    assert result.exit_code != 0
