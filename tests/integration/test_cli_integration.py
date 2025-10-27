"""
Integration tests of the CLI
"""

from __future__ import annotations

from typer.testing import CliRunner

import cmipcite
from cmipcite.cli import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0, result.exc_info
    assert result.stdout == f"cmipcite {cmipcite.__version__}\n"
