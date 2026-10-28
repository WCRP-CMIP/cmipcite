"""
Regression tests of the `get` CLI
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from cmipcite.cli import app

runner = CliRunner()


@pytest.mark.parametrize(
    "in_values",
    (
        pytest.param("hdl:21.14100/90f93a05-357c-4ea2-b61f-bf2418700791", id="CMIP6"),
        pytest.param("hdl:21.14107/eee87809-8c47-4b80-9104-fdd5ee85c8c4", id="CMIP7"),
    ),
)
@pytest.mark.parametrize(
    "out_path, out_format, author_list_style, doi_granularity, table_columns",
    (
        pytest.param(None, None, None, None, None, id="defaults"),
        pytest.param(
            "tmp.bib", "bibtex", "short", "experiment", None, id="bib-short-exp"
        ),
        pytest.param("tmp.txt", "text", "long", "model", None, id="text-long-model"),
        pytest.param("table.txt", "latextable", None, None, None, id="table-default"),
        pytest.param(
            "table2.txt",
            "latextable",
            None,
            None,
            ["source_id", "variant_label", "version", "doi"],
            id="table-columns",
        ),
    ),
)
def test_citations_args(  # noqa: PLR0913
    in_values,
    out_path,
    out_format,
    author_list_style,
    doi_granularity,
    table_columns,
    file_regression,
    tmpdir,
):
    args = ["get", in_values]

    if out_path is not None:
        out_path_full = Path(tmpdir) / out_path
        args.extend(["--out-path", str(out_path_full)])

    if out_format is not None:
        args.extend(["--format", out_format])

    if author_list_style is not None:
        args.extend(["--author-list-style", author_list_style])

    if doi_granularity is not None:
        args.extend(["--doi-granularity", doi_granularity])

    if table_columns is not None:
        for x in table_columns:
            args.extend(["--table-columns", x])

    result = runner.invoke(app, args)

    assert result.exit_code == 0, result.stdout

    if out_path is None:
        res = result.stdout
        suffix = ".txt"
    else:
        suffix = out_path_full.suffix
        with open(out_path_full) as fh:
            res = fh.read()

    file_regression.check(res, extension=suffix, encoding="utf-8")


@pytest.mark.parametrize(
    "input_id, extra_args",
    (
        pytest.param("hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b", [], id="pid"),
        pytest.param(
            "hdl:21.14100/be06a059-363d-47a4-97a2-d5253190fd15", [], id="tracking"
        ),
        pytest.param(
            "hdl:21.14100/2e216556-472e-4d88-a414-42b0c0944d36", [], id="consortium"
        ),
        pytest.param(
            "hdl:21.14100/cfb3c24b-921a-49af-8b7b-1346c764e750",
            ["--multi-dataset-handling", "latest"],
            id="in-multiple-datasets-latest",
        ),
        pytest.param(
            "hdl:21.14100/cfb3c24b-921a-49af-8b7b-1346c764e750",
            ["--multi-dataset-handling", "first"],
            id="in-multiple-datasets-first",
        ),
    ),
)
def test_types_of_id(input_id, extra_args, file_regression, tmpdir):
    args = ["get", input_id, "--author-list-style", "short", *extra_args]

    result = runner.invoke(app, args)

    assert result.exit_code == 0, result.stdout

    res = result.stdout

    suffix = ".txt"
    file_regression.check(res, extension=suffix, encoding="utf-8")
