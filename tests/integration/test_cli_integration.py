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


def test_multiple_error_message():
    args = ["get", "hdl:21.14100/cfb3c24b-921a-49af-8b7b-1346c764e750"]

    result = runner.invoke(app, args)

    assert result.exit_code == 1, result.stdout

    assert str(result.exception) == (
        "One of your input values is a member of more than one dataset. "
        "You can resolve this by passing a value for the "
        "`--multi-dataset-handling` option. "
        "In most cases, passing `--multi-dataset-handling latest` "
        "is what you will want "
        "(this will give you the reference to the last published dataset "
        "that includes your ID)"
    )
