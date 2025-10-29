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
    tracking_id: str,
    format: FormatOption,
    author_list_style: AuthorListStyle,
) -> str:
    """
    Get citation for tracking ID or PID.

    Parameters
    ----------
    tracking_id
        Tracking ID or PID for which to get the citation.

    format
        Format in which to get the citation

    author_list_style
        Style to use for the author list

    Returns
    -------
    :
        Citation for the given `tracking_id`
    """
    client = RESTHandleClient(handle_server_url="http://hdl.handle.net/")

    tracking_id_query = tracking_id.replace("hdl:", "")

    # tracking_id are associated to a file. pid are associated to a dataset.
    ispartof = client.get_value_from_handle(tracking_id_query, "IS_PART_OF")

    # if the input is a pid (associated to a dataset), the is_part_of is a doi.
    if "doi" in ispartof:
        doi = ispartof
        version = client.get_value_from_handle(tracking_id_query, "VERSION_NUMBER")
    # if the input is a tracking_id (associated to a file),
    # the is_part_of is a pid of the dataset.
    # and we need an extra step to get the doi.
    else:
        pid = client.get_value_from_handle(tracking_id_query, "IS_PART_OF")
        doi = client.get_value_from_handle(pid, "IS_PART_OF")
        version = client.get_value_from_handle(pid, "VERSION_NUMBER")

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
        Tracking IDs PID or paths for which to get citations.
        Tracking ids identify files. They are found in the tracking_id attribute.
        PIDs identify datasets (a grouping of files).
        Paths should point to a CMIP file with a tracking_id attribute.

    format
        Format in which to get the citations

    author_list_style
        Style to use for the author list

    Returns
    -------
    :
        Citations for the given `tracking_ids_or_paths`
    """
    res = []
    for v in ids_or_paths:
        # TODO: add checking for and support for paths
        tracking_id = v
        res.append(
            get_citation_for_id(
                tracking_id, format=format, author_list_style=author_list_style
            )
        )

    return res
