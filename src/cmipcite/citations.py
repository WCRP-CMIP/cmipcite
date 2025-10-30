"""
Citation support
"""

from __future__ import annotations

import re
import sys

import httpx
from pyhandle.handleclient import RESTHandleClient  # type: ignore

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


def get_citation_for_id(
    input_id: str,
    format: FormatOption,
    author_list_style: AuthorListStyle,
) -> str:
    """
    Get citation for tracking ID or PID.

    Parameters
    ----------
    input_id
        Tracking_id (file PID) or dataset PID for which to get citations.
        Tracking ids identify files. They are found in the tracking_id attribute.
        PIDs identify datasets (a grouping of files).
        Paths should point to a CMIP file with a tracking_id attribute.

    format
        Format in which to get the citation

    author_list_style
        Style to use for the author list

    Returns
    -------
    :
        Citation for the given `tracking_id` or PID
    """
    client = RESTHandleClient(handle_server_url="http://hdl.handle.net/")

    id_query = input_id.replace("hdl:", "")

    agg_lev = client.get_value_from_handle(id_query, "AGGREGATION_LEVEL")

    if agg_lev == "DATASET":
        # the input is a pid (associated to a dataset), the is_part_of is a doi.
        doi = client.get_value_from_handle(id_query, "IS_PART_OF")
        version = client.get_value_from_handle(id_query, "VERSION_NUMBER")

    elif agg_lev == "FILE":
        # the input is a tracking_id (associated to a file),
        # the is_part_of is a pid of the dataset.
        # and we need an extra step to get the doi.
        pid = client.get_value_from_handle(id_query, "IS_PART_OF")
        doi = client.get_value_from_handle(pid, "IS_PART_OF")
        version = client.get_value_from_handle(pid, "VERSION_NUMBER")

    else:
        raise NotImplementedError(
            f"The id {input_id} has an unknown AGGREGATION_LEVEL: {agg_lev}"
        )

    doi = doi.replace("doi:", "")

    if format == FormatOption.TEXT:
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

    elif format == FormatOption.BIBTEX:
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

    else:  # pragma: no cover
        raise NotImplementedError(format)

    return citation


def get_citations(
    ids_or_paths: list[str],
    format: FormatOption,
    author_list_style: AuthorListStyle,
) -> list[str]:
    """
    Get citations

    Parameters
    ----------
    ids_or_paths
        Tracking id (file PID), dataset PID or paths for which to get citations.
        Tracking ids identify files.
        To date, they can be found
        in the `tracking_id` global attribute of CMIP netCDF files.
        PIDs identify datasets (a group of files).
        Paths should point to a CMIP file with a `tracking_id` global attribute.

    format
        Format in which to get the citations

    author_list_style
        Style to use for the author list

    Returns
    -------
    :
        Citations for the given `ids_or_paths`

    Notes
    -----
     Citation can be retrieved with the help of the Persistent IDentifiers (PIDs).
     In the CMIP world, there are two types of PIDs:
       * file PID (also called tracking_id)
       * dataset PID (often referred to as just PID).
     A dataset is a collection of files from a single variable sampled at a single
     frequency from a single model running a single experiment.
     All datasets from a single model and a single experiment are grouped under a DOI.
     There exist DOIs associated to single model, but including all the experiments,
     but they are not used by this package.
    """
    res = []
    for input_id in ids_or_paths:
        # TODO: add checking for and support for paths
        res.append(
            get_citation_for_id(
                input_id, format=format, author_list_style=author_list_style
            )
        )

    return res
