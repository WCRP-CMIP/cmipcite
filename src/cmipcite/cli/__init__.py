"""
Command-line interface
"""

# # Do not use this here, it breaks typer's annotations
# from __future__ import annotations
from pathlib import Path
from typing import Annotated, Optional, Union

import typer

import cmipcite
from cmipcite.citations import (
    AuthorListStyle,
    DatasetPIDLookupStrategy,
    DOIGranularity,
    FormatOption,
    get_citations,
    get_latex_table,
    translate_get_args_to_get_citations_kwargs,
)
from cmipcite.tracking_id import (
    MultiDatasetHandlingStrategy,
    MultipleDatasetMemberError,
)

app = typer.Typer()


def version_callback(version: Optional[bool]) -> None:
    """
    If requested, print the version string and exit
    """
    if version:
        print(f"cmipcite {cmipcite.__version__}")
        raise typer.Exit(code=0)


@app.callback()
def cli(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            help="Print the version number and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """
    Entrypoint for the command-line interface
    """


@app.command(name="get")
def get(  # noqa: PLR0913
    in_values: Annotated[
        list[str],
        typer.Argument(
            help="Tracking IDs, PIDs or file paths for which to generate citations."
        ),
    ],
    out_path: Annotated[
        Union[Path, None],
        typer.Option(
            help="Path in which to write the output. If not provided, it is printed."
        ),
    ] = None,
    format: Annotated[
        FormatOption,
        typer.Option(help="Format in which to retrieve the citations."),
    ] = FormatOption.TEXT,
    author_list_style: Annotated[
        AuthorListStyle,
        typer.Option(
            help="Whether the author list should be long (all names) or short (et al.)."
        ),
    ] = AuthorListStyle.LONG,
    doi_granularity: Annotated[
        DOIGranularity,
        typer.Option(
            help="Only valid for CMIP6 data. Desired granularity of the retrieved DOIs."
        ),
    ] = DOIGranularity.MODEL,
    multi_dataset_handling: Annotated[
        Optional[MultiDatasetHandlingStrategy],
        typer.Option(
            help="Strategy to use when a given ID or file belongs to multiple datasets."
        ),
    ] = None,
    handle_server_url: Annotated[
        str,
        typer.Option(
            help="Only valid for CMIP6 data. URL of the server to use for handling"
            " tracking IDs i.e. handles"
        ),
    ] = "http://hdl.handle.net/",
    dataset_pid_lookup: Annotated[
        DatasetPIDLookupStrategy,
        typer.Option(
            help="Whether to only look at the current dataset PID or allow looking at "
            "the previous dataset PID (if it exists)"
            " if the current one does not have a DOI."
        ),
    ] = DatasetPIDLookupStrategy.ALLOWPREVIOUS,
    table_columns: Annotated[
        list[str],
        typer.Option(
            help="Only valid for LaTeX table format. List of columns to include in"
            " the table."
        ),
    ] = [
        "source_id",
        "institution_id",
        "experiment_id",
        "variable_id",
        "version",
        "reference",
    ],
) -> None:
    """
    Generate citations from CMIP files or tracking IDs or PIDs
    """
    if format == FormatOption.LATEXTABLE:
        table = get_latex_table(
            ids_or_paths=in_values,
            table_columns=table_columns,
            multi_dataset_handling=multi_dataset_handling,
            doi_granularity=doi_granularity,
            dataset_pid_lookup=dataset_pid_lookup,
        )
        return table
    else:
        get_citations_kwargs = translate_get_args_to_get_citations_kwargs(
            format=format,
            author_list_style=author_list_style,
            handle_server_url=handle_server_url,
        )

        try:
            citations = get_citations(
                ids_or_paths=in_values,
                doi_granularity=doi_granularity,
                multi_dataset_handling=multi_dataset_handling,
                dataset_pid_lookup=dataset_pid_lookup,
                **get_citations_kwargs,
            )

        except MultipleDatasetMemberError as exc:
            msg = (
                "One of your input values is a member of more than one dataset. "
                "You can resolve this by passing a value for the "
                "`--multi-dataset-handling` option. "
                "In most cases, passing `--multi-dataset-handling latest` "
                "is what you will want "
                "(this will give you the reference to the last published dataset "
                "that includes your ID)"
            )
            raise ValueError(msg) from exc

        text = "\n\n".join(citations)

        if out_path is None:
            print(text)
        else:
            with open(out_path, "w") as fh:
                fh.write(text)


if __name__ == "__main__":  # pragma: no cover
    app()
