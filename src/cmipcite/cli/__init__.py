"""
Command-line interface
"""

# # Do not use this here, it breaks typer's annotations
# from __future__ import annotations
import sys
from functools import partial
from pathlib import Path
from typing import Annotated, Callable, Optional, Union

import typer
from pyhandle.handleclient import RESTHandleClient  # type: ignore

import cmipcite
from cmipcite.citations import (
    AuthorListStyle,
    get_bibtex_citation,
    get_citations,
    get_text_citation,
)
from cmipcite.tracking_id import MultiDatasetHandlingStrategy

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from backports.strenum import StrEnum

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


class FormatOption(StrEnum):
    """
    Citation format options
    """

    BIBTEX = "bibtex"
    """
    Bibtex format
    """

    TEXT = "text"
    """
    Plain text file
    """


@app.command(name="get")
def get(  # noqa: PLR0913
    in_values: Annotated[
        list[str],
        typer.Argument(
            help="Tracking IDs, PIDs or file paths for which to generate citations"
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
        typer.Option(help="Format in which to retrieve the citations"),
    ] = FormatOption.TEXT,
    author_list_style: Annotated[
        AuthorListStyle,
        typer.Option(
            help="Whether the author list should be long (all names) or short (et al.)"
        ),
    ] = AuthorListStyle.LONG,
    multi_dataset_handling: Annotated[
        Optional[MultiDatasetHandlingStrategy],
        typer.Option(
            help="Strategy to use when a given ID or file belongs to multiple datasets"
        ),
    ] = None,
    handle_server_url: Annotated[
        str,
        typer.Option(
            help="URL of the server to use for handling tracking IDs i.e. handles"
        ),
    ] = "http://hdl.handle.net/",
) -> None:
    """
    Generate citations from CMIP files or tracking IDs or PIDs
    """
    if format == FormatOption.TEXT:
        get_citation: Callable[[str, str], str] = partial(
            get_text_citation, author_list_style=author_list_style
        )

    elif format == FormatOption.BIBTEX:
        get_citation = get_bibtex_citation

    else:  # pragma: no cover
        raise NotImplementedError(FormatOption)

    client = RESTHandleClient(handle_server_url=handle_server_url)

    citations = get_citations(
        ids_or_paths=in_values,
        get_citation=get_citation,
        client=client,
        multi_dataset_handling=multi_dataset_handling,
    )

    text = "\n\n".join(citations)

    if out_path is None:
        print(text)
    else:
        with open(out_path, "w") as fh:
            fh.write(text)


if __name__ == "__main__":  # pragma: no cover
    app()
