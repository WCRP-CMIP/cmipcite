"""
Integration tests of the CLI
"""

from __future__ import annotations

import pytest
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


def test_handle_path_equivalence(test_data_dir):
    pytest.importorskip("netCDF4")

    args_id = ["get", "hdl:21.14100/90f93a05-357c-4ea2-b61f-bf2418700791"]

    result_id = runner.invoke(app, args_id)

    assert result_id.exit_code == 0, result_id.stdout

    args_path = [
        "get",
        str(test_data_dir / "sftlf_fx_CanESM5_historical_r1i1p1f1_gn.nc"),
    ]

    result_path = runner.invoke(app, args_path)

    assert result_path.exit_code == 0, result_path.stdout

    assert result_id.stdout == result_path.stdout
