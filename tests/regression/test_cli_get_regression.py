"""
Regression tests of the `get` CLI
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from cmipcite.cli import app

runner = CliRunner()


TEST_PID = "hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b"
TEST_TRACKING_ID = "hdl:21.14100/be06a059-363d-47a4-97a2-d5253190fd15"


@pytest.mark.parametrize(
    "out_path, out_format, author_list_style",
    (
        pytest.param(None, None, None, id="defaults"),
        pytest.param("tmp.bib", "bibtex", "short", id="outfile-bibtex-shortauthors"),
        pytest.param("tmp.txt", "text", "long", id="outfile-text-longauthors"),
    ),
)
def test_citations_from_PID(
    out_path, out_format, author_list_style, file_regression, tmpdir
):
    args = ["get", TEST_PID]

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


# test nearly duplicated to avoid avoid more than 5 args
@pytest.mark.parametrize(
    "out_path, out_format, author_list_style",
    (
        pytest.param(None, None, None, id="defaults"),
        pytest.param("tmp.bib", "bibtex", "short", id="outfile-bibtex-shortauthors"),
        pytest.param("tmp.txt", "text", "long", id="outfile-text-longauthors"),
    ),
)
def test_citations_from_tracking(
    out_path, out_format, author_list_style, file_regression, tmpdir
):
    args = ["get", TEST_TRACKING_ID]

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
