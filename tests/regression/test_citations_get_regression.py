"""
Regression tests of the `get` CLI
"""

from __future__ import annotations

import pytest

from cmipcite.citations import get


@pytest.mark.parametrize(
    "in_values",
    (
        pytest.param("hdl:21.14100/90f93a05-357c-4ea2-b61f-bf2418700791", id="CMIP6"),
        pytest.param("hdl:21.14107/eee87809-8c47-4b80-9104-fdd5ee85c8c4", id="CMIP7"),
    ),
)
@pytest.mark.parametrize(
    "out_format, author_list_style, doi_granularity, table_columns",
    (
        pytest.param(None, None, None, None, id="defaults"),
        pytest.param("bibtex", "short", "experiment", None, id="bib-short-exp"),
        pytest.param("bibtex", "long", "model", None, id="bib-long-bib"),
        pytest.param("text", "long", "model", None, id="text-long-model"),
        pytest.param("text", "short", "experiment", None, id="text-short-exp"),
        pytest.param("latextable", None, None, None, id="table-default"),
        pytest.param(
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
    out_format,
    author_list_style,
    doi_granularity,
    table_columns,
    file_regression,
    tmpdir,
):
    kwargs = dict(
        format=out_format,
        author_list_style=author_list_style,
        doi_granularity=doi_granularity,
        table_columns=table_columns,
    )
    args = {k: v for k, v in kwargs.items() if v is not None}

    if "hdl:21.14100" in in_values and out_format == "latextable":
        with pytest.raises(
            NotImplementedError,
        ):
            result = get([in_values], **args)
    else:
        result = get([in_values], **args)

        file_regression.check(str(result), encoding="utf-8")
