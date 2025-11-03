"""
Citation support
"""

from __future__ import annotations

import re
import sys
from functools import partial
from pathlib import Path
from typing import Any, Callable

import httpx
from pyhandle.handleclient import RESTHandleClient  # type: ignore

from cmipcite.tracking_id import (
    MultiDatasetHandlingStrategy,
    MultipleDatasetMemberError,
    get_dataset_pid,
)

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from backports.strenum import StrEnum


class AuthorListStyle(StrEnum):
    """
    Author list style
    """

    SHORT = "short"
    """
    Short i.e. use "et al."
    """

    LONG = "long"
    """
    Long i.e. list all names
    """


def get_text_citation(
    doi: str, version: str, author_list_style: AuthorListStyle
) -> str:
    """
    Get text citation

    Parameters
    ----------
    doi
        DOI for which to get the citation

    version
        Version of the dataset associated with `doi`

    author_list_style
        Style to use for the author list

    Returns
    -------
    :
        Plain text citation
    """
    r = httpx.get(f"https://api.datacite.org/dois/{doi}", follow_redirects=True)
    data = r.raise_for_status().json()["data"]["attributes"]

    if author_list_style == AuthorListStyle.SHORT:
        if len(data["creators"]) == 1:
            creators = data["creators"][0]["name"]

        else:
            creators = f"{data['creators'][0]['familyName']} et al."

    elif author_list_style == AuthorListStyle.LONG:
        creators = "; ".join([c["name"] for c in data["creators"]])

    else:  # pragma: no cover
        raise NotImplementedError(author_list_style)

    citation = (
        f"{creators} ({data['publicationYear']}): {data['titles'][0]['title']}. "
        f"Version {version}. {data['publisher']}. https://doi.org/{doi}."
    )

    return citation


def get_bibtex_citation(doi: str, version: str) -> str:
    """
    Get bibtex citation

    Parameters
    ----------
    doi
        DOI for which to get the citation

    version
        Version of the dataset associated with `doi`

    Returns
    -------
    :
        Bibtex citation
    """
    url = "http://dx.doi.org/" + doi
    headers = {"accept": "application/x-bibtex"}
    r = httpx.get(url, headers=headers, follow_redirects=True)

    bib = r.raise_for_status().text

    # add version to title
    citation = re.sub(
        r"title = {(.*?)}",
        lambda m: f"title = {{{m.group(1)}. Version {version}.}}",
        bib,
    )

    return citation


# Turn on in future PR
# def get_tracking_id_from_cmip_netcdf(nc_path: Path) -> str:
#     with netCDF4.Dataset(in_value) as ds:
#         tracking_id = ds.getncattr("tracking_id")
#
#     return tracking_id


def get_doi_and_version(  # type: ignore
    in_value: str,
    client: RESTHandleClient | None = None,
    # # Turn on in future PR
    # get_tracking_id_from_path: Callable[
    #     [Path], str
    # ] = get_tracking_id_from_cmip_netcdf,
    multi_dataset_handling: MultiDatasetHandlingStrategy | None = None,
) -> tuple[str, str]:
    """
    Get DOI and version for a given ID or path to a netCDF file

    Parameters
    ----------
    in_value
        Input ID or path to a netCDF file

    client
        Client to use for interacting with pyhandle's REST API

        If not supplied, a new client with a default handle server URL
        is instantiated.

    multi_dataset_handling
        What to do in the case that the tracking ID belongs to multiple datasets
        i.e. is associated with more than one PID.

        Passed to [get_dataset_pid][(p).tracking_id.get_dataset_pid].

    Returns
    -------
    doi :
        DOI that applies to `in_value`

    version :
        Version that applies to `in_value`
    """
    if client is None:  # pragma: no cover
        client = RESTHandleClient(handle_server_url="http://hdl.handle.net/")

    if Path(in_value).exists():  # pragma: no cover
        # Turn on in future PR and remove no cover
        raise NotImplementedError
        # tracking_id = get_tracking_id_from_path(Path(in_value))
        # Can get the version from the full path too if available
        # id_in_value = tracking_id.replace("hdl:", "")
        # id_is_tracking_id = True

    else:
        id_in_value = in_value.replace("hdl:", "")

        agg_lev = client.get_value_from_handle(id_in_value, "AGGREGATION_LEVEL")
        if agg_lev == "DATASET":
            id_is_tracking_id = False

        elif agg_lev == "FILE":
            id_is_tracking_id = True

        else:  # pragma: no cover
            msg = f"The id {id_in_value} has an unknown AGGREGATION_LEVEL: {agg_lev}"
            raise NotImplementedError(msg)

    if id_is_tracking_id:
        pid = get_dataset_pid(
            tracking_id=id_in_value,
            multi_dataset_handling=multi_dataset_handling,
            client=client,
        )

    else:
        pid = id_in_value

    doi_raw = client.get_value_from_handle(pid, "IS_PART_OF")
    doi = doi_raw.replace("doi:", "")
    version = client.get_value_from_handle(pid, "VERSION_NUMBER")

    return (doi, version)


def get_citations(  # type: ignore
    ids_or_paths: list[str],
    get_citation: Callable[[str, str], str],
    client: RESTHandleClient | None = None,
    multi_dataset_handling: MultiDatasetHandlingStrategy | None = None,
) -> list[str]:
    """
    Get citations that apply to the given IDs or paths

    IDs don't apply at the file level.
    Hence, if your IDs are tracking IDs or paths,
    then two or more IDs/paths can share the same citation.
    This function returns the minimum set of citations required
    i.e. any duplicate citations are removed.

    Parameters
    ----------
    ids_or_paths
        Tracking ids (file PID), dataset PIDs and paths for which to get citations.

        Tracking ids identify files.
        To date, they can be found
        in the `tracking_id` global attribute of CMIP netCDF files.

        PIDs identify datasets (a group of files).

        Paths should point to a CMIP file with a `tracking_id` global attribute.

    get_citation
        Function which, given a DOI and a version, produces a citation

        For example, [get_bibtex_citation][(m).].

    client
        Client to use for interacting with pyhandle's REST API

        If not supplied, a new client with a default handle server URL
        is instantiated.

    multi_dataset_handling
        What to do in the case that the tracking ID belongs to multiple datasets
        i.e. is associated with more than one PID.

        Passed to [get_dataset_pid][(p).tracking_id.get_dataset_pid].

    Returns
    -------
    :
        Citations for the given `ids_or_paths`

    Notes
    -----
    Citations can be retrieved with the help of the Persistent IDentifiers (PIDs).
    In the CMIP world, there are two types of PIDs:

       * file PID (normally referred to as a tracking ID)
       * dataset PID (normally simply referred to as PID).

    A dataset is a collection of files
    (for CMIP, this collection of files
    is for a single variable sampled at a single frequency and spatial sampling
    from a single model running a single experiment).
    All datasets from a single model and a single experiment
    are grouped under a DOI, associated with the dataset's PID.
    There also exist DOIs associated to a single model,
    that include all the experiments performed by that model,
    but they are not used by this package at the moment.

    Examples
    --------
    >>> citations = get_citations(
    ...     ["hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b"],
    ...     get_citation=get_bibtex_citation,
    ... )
    >>> print(citations[0])
    @misc{https://doi.org/10.22033/esgf/cmip6.6595,
      doi = {10.22033/ESGF/CMIP6.6595},
      url = {http://cera-www.dkrz.de/WDCC/meta/CMIP6/CMIP6.CMIP.MPI-M.MPI-ESM1-2-LR.historical},
      author = {Wieners, Karl-Hermann and Giorgetta, Marco and Jungclaus, Johann and Reick, Christian and Esch, Monika and Bittner, Matthias and Legutke, Stephanie and Schupfner, Martin and Wachsmann, Fabian and Gayler, Veronika and Haak, Helmuth and de Vrese, Philipp and Raddatz, Thomas and Mauritsen, Thorsten and von Storch, Jin-Song and Behrens, Jörg and Brovkin, Victor and Claussen, Martin and Crueger, Traute and Fast, Irina and Fiedler, Stephanie and Hagemann, Stefan and Hohenegger, Cathy and Jahns, Thomas and Kloster, Silvia and Kinne, Stefan and Lasslop, Gitta and Kornblueh, Luis and Marotzke, Jochem and Matei, Daniela and Meraner, Katharina and Mikolajewicz, Uwe and Modali, Kameswarrao and Müller, Wolfgang and Nabel, Julia and Notz, Dirk and Peters-von Gehlen, Karsten and Pincus, Robert and Pohlmann, Holger and Pongratz, Julia and Rast, Sebastian and Schmidt, Hauke and Schnur, Reiner and Schulzweida, Uwe and Six, Katharina and Stevens, Bjorn and Voigt, Aiko and Roeckner, Erich},
      keywords = {CMIP6, climate, CMIP6.CMIP.MPI-M.MPI-ESM1-2-LR.historical},
      language = {en},
      title = {MPI-M MPI-ESM1.2-LR model output prepared for CMIP6 CMIP historical. Version 20211412.},
      publisher = {Earth System Grid Federation},
      year = {2019},
      copyright = {Creative Commons Attribution 4.0 International}
    }
    """  # noqa: E501
    if client is None:  # pragma: no cover
        client = RESTHandleClient(handle_server_url="http://hdl.handle.net/")

    doi_versions = [
        get_doi_and_version(
            v, client=client, multi_dataset_handling=multi_dataset_handling
        )
        for v in ids_or_paths
    ]

    doi_versions_unique = set(doi_versions)

    res = [get_citation(doi, version) for doi, version in doi_versions_unique]

    return res


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


def translate_get_args_to_get_citations_kwargs(
    format: FormatOption,
    author_list_style: AuthorListStyle,
    handle_server_url: str = "http://hdl.handle.net/",
) -> dict[str, Any]:
    """
    Translate the arguments of [(m).get][] to arguments needed by [(m).get_citations][]

    [(m).get_citations][] is a lower-level function that supports dependency injection.
    [(m).get][] is meant to mirror the equivalent command-line interface command,
    therefore has to work with more primitive types and does not support
    (direct) dependency injection.

    Parameters
    ----------
    format
        Format in which to retrieve the citations

    author_list_style
        Whether, if the format is text,
        the author list should be long (all names) or short (et al.)

    handle_server_url
        URL of the server to use for handling tracking IDs i.e. handles

    Returns
    -------
    :
        Keyword arguments which can be passed to [(m).get_citations][]
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

    return dict(
        get_citation=get_citation,
        client=client,
    )


def get(
    in_values: list[str],
    format: FormatOption = FormatOption.TEXT,
    author_list_style: AuthorListStyle = AuthorListStyle.LONG,
    multi_dataset_handling: MultiDatasetHandlingStrategy | None = None,
    handle_server_url: str = "http://hdl.handle.net/",
) -> list[str]:
    """
    Get citations from CMIP files or tracking IDs or PIDs

    This function mirrors the CLI `get` command as closely as possible.

    Parameters
    ----------
    in_values
        Tracking IDs, PIDs or file paths for which to generate citations

    format
        Format in which to retrieve the citations

    author_list_style
        Whether, if the format is text,
        the author list should be long (all names) or short (et al.)

    multi_dataset_handling
        Strategy to use when a given ID or file belongs to multiple datasets

    handle_server_url
        URL of the server to use for handling tracking IDs i.e. handles

    Returns
    -------
    :
        Retrieved citations for `in_values`
    """
    get_citations_kwargs = translate_get_args_to_get_citations_kwargs(
        format=format,
        author_list_style=author_list_style,
        handle_server_url=handle_server_url,
    )

    try:
        citations = get_citations(
            ids_or_paths=in_values,
            multi_dataset_handling=multi_dataset_handling,
            **get_citations_kwargs,
        )
    except MultipleDatasetMemberError as exc:
        msg = (
            "One of your input values is a member of more than one dataset. "
            "You can resolve this by passing a value for the "
            "`multi_dataset_handling` argument. "
            "In most cases, adding "
            "`from cmipcite.tracking_id import MultiDatasetHandlingStrategy` "
            "and then using "
            "`multi_dataset_handling=MultiDatasetHandlingStrategy.LATEST` "
            "is what you will want "
            "(this will give you the reference to the last published dataset "
            "that includes your ID)."
        )
        raise ValueError(msg) from exc

    return citations
