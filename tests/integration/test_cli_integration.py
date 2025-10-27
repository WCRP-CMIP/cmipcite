"""
Integration tests of the CLI
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

import cmipcite
from cmipcite.cli import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0, result.exc_info
    assert result.stdout == f"cmipcite {cmipcite.__version__}\n"


@pytest.mark.parametrize(
    "out_path, out_format, author_list_style",
    (
        pytest.param(None, None, None, id="defaults"),
        pytest.param("tmp.bib", "bibtex", "short", id="outfile-bibtex-shortauthors"),
        pytest.param("tmp.txt", "text", "long", id="outfile-text-longauthors"),
    ),
)
def test_citations(out_path, out_format, author_list_style, file_regression, tmpdir):
    args = ["get", "hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b"]

    if out_path is not None:
        out_path_full = Path(tmpdir) / out_path
        args.extend(["--out-path", str(out_path_full)])

    if out_format is not None:
        args.extend(["--format", out_format])

    if author_list_style is not None:
        args.extend(["--author-list-style", author_list_style])

    result = runner.invoke(app, args)

    assert result.exit_code == 0, result.stdout

    if out_path is None:
        res = result.stdout
        suffix = ".txt"
    else:
        suffix = out_path_full.suffix
        with open(out_path_full) as fh:
            res = fh.read()

    file_regression.check(res, extension=suffix)
