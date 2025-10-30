"""
Citation support
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Callable

import httpx
from pyhandle.handleclient import RESTHandleClient  # type: ignore

from cmipcite.tracking_id import MultiDatasetHandlingStrategy, get_dataset_pid

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


def get_doi_and_version(
    in_value: str | Path,
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
    if client is None:
        client = RESTHandleClient(handle_server_url="http://hdl.handle.net/")

    if isinstance(in_value, Path):
        # Turn on in future PR
        raise NotImplementedError
        # tracking_id = get_tracking_id_from_path(in_value)
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

        else:
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


def get_citations(
    ids_or_paths: list[str | Path],
    get_citation: Callable[[str, str], str],
    client: RESTHandleClient | None = None,
    multi_dataset_handling: MultiDatasetHandlingStrategy | None = None,
) -> list[str]:
    """
    Get citations that apply to the given IDs or paths

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
    """
    if client is None:
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
