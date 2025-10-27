"""
Command-line interface
"""

# # Do not use this here, it breaks typer's annotations
# from __future__ import annotations
from pathlib import Path
from typing import Annotated, Optional

import typer

import cmipcite
from cmipcite.citations import AuthorListStyle, FormatOption, get_citations

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
def get(
    in_values: Annotated[
        list[str],
        typer.Argument(
            help="Tracking IDs or file paths for which to generate citations"
        ),
    ],
    out_path: Annotated[
        Path | None,
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
) -> None:
    """
    Generate citations from CMIP files or tracking IDs
    """
    citations = get_citations(
        tracking_ids_or_paths=in_values,
        format=format,
        author_list_style=author_list_style,
    )

    text = "\n\n".join(citations)

    if out_path is None:
        print(text)
    else:
        with open(out_path, "w") as fh:
            fh.write(text)


if __name__ == "__main__":
    app()
