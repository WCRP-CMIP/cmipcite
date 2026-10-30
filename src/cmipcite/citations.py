"""
Citation support
"""

from __future__ import annotations

import re
import sys
import warnings
from functools import partial
from pathlib import Path
from typing import Any, Callable

import httpx
import numpy as np
import requests
from pyhandle.handleclient import RESTHandleClient  # type: ignore

from cmipcite.exceptions import MissingOptionalDependencyError
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


class DOIGranularity(StrEnum):
    """
    DOI granularity

    This is only valid for CMIP6. All CMIP7 citations are at the experiment granularity.
    CMIP6 data can be aggregated at different granularities.
    Data citations are designated on data aggregations belonging to a model
    contribution to a MIP (or activity_id) and on data belonging to an experiment
    contributed by a specific model:
    model: <mip_era>/<activity_id>/<institution_id>/<source_id>
    experiment: <mip_era>/<activity_id>/<institution_id>/<source_id>/<experiment_id>.
    """

    EXPERIMENT = "experiment"
    """
    mip-model-experiment granularity of DOI.
    """

    MODEL = "model"
    """
    mip-model granularity of DOI.
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

    LATEXTABLE = "latextable"
    """
    Text file with latex table
    """


class DatasetPIDLookupStrategy(StrEnum):
    """
    Dataset PID lookup strategy

    Strategy for handling the case when dataset PID does not have a DOI but the
    previous PID (linked to the dataset PID with "REPLACES") does.
    """

    CURRENTONLY = "current_only"
    """
    Only get the DOI for the the current dataset PID.
    """

    ALLOWPREVIOUS = "allow_previous"
    """
    If the current dataset PID does not have a DOI, look for a DOI in the previous
    dataset PID (if it exists in the 'REPLACES' field).
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

        elif "familyName" in data["creators"][0]:
            creators = f"{data['creators'][0]['familyName']} et al."
        elif "," in data["creators"][0]["name"]:
            creators = f"{data['creators'][0]['name'].split(',')[0]} et al."
        else:
            creators = f"{data['creators'][0]['name'].split(' ')[-1]} et al."

    elif author_list_style == AuthorListStyle.LONG:
        creators = "; ".join([c["name"] for c in data["creators"]])

    else:  # pragma: no cover
        raise NotImplementedError(author_list_style)

    if "CMIP6" in data["titles"][0]["title"]:
        citation = (
            f"{creators} ({data['publicationYear']}): {data['titles'][0]['title']}. "
            f"Version {version}. {data['publisher']}. https://doi.org/{doi}."
        )
    else:
        if "CMIP7" not in data["titles"][0]["title"]:
            warnings.warn(
                "Unable to identify the mip era from the title"
                f"({data['titles'][0]['title']}). The textual citation"
                " will follow the CMIP7 format (no dataset version).",
                UserWarning,
            )
        citation = (
            f"{creators} ({data['publicationYear']}): {data['titles'][0]['title']}. "
            f"{data['publisher']}. https://doi.org/{doi}."
        )

    return citation


def get_bibtex_citation(doi: str, version: str) -> str:
    """
    Get bibtex citation

    The version is added to the title field.

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

    # add version to title in CMIP6 only
    if "CMIP6" in bib:
        bib = re.sub(
            r"title = {(.*?)}",
            lambda m: f"title = {{{m.group(1)}. Version {version}.}}",
            bib,
        )

    return bib


def get_tracking_id_from_cmip_netcdf(nc_path: Path) -> str:
    """
    Get tracking ID from a CMIP netCDF file

    Parameters
    ----------
    nc_path
        Path to the CMIP netCDF file.

        The file must have a `tracking_id` global attribute.

    Returns
    -------
    :
        Tracking ID
    """
    try:
        import netCDF4
    except ImportError as exc:
        raise MissingOptionalDependencyError(
            "get_tracking_id_from_cmip_netcdf", requirement="netCDF4"
        ) from exc

    with netCDF4.Dataset(nc_path) as ds:
        tracking_id = ds.getncattr("tracking_id")

    return str(tracking_id)


def get_mip_era(
    in_value: str,
    get_tracking_id_from_path: Callable[[Path], str] = get_tracking_id_from_cmip_netcdf,
):
    """
    Get the mip_era for a given ID or path to a netCDF file

    Parameters
    ----------
    in_value
        Input ID or path to a netCDF file

    Returns
    -------
    :
        mip_era that applies to `in_value`
    """
    if Path(in_value).exists():
        in_value = get_tracking_id_from_path(Path(in_value))

    in_value = in_value.replace("hdl:", "")

    if in_value.startswith("21.14100/"):
        mip_era = "CMIP6"
    elif in_value.startswith("21.14107/"):
        mip_era = "CMIP7"
    else:
        message = f"Could not determine mip_era for {in_value}. "
        raise ValueError(message)

    return mip_era


def _in_value_CMIP6_2_pid(  # type: ignore
    in_value: str,
    CMIP6client: RESTHandleClient | None = None,
    get_tracking_id_from_path: Callable[[Path], str] = get_tracking_id_from_cmip_netcdf,
    multi_dataset_handling: MultiDatasetHandlingStrategy | None = None,
) -> str:
    """Get the dataset PID from the in_value.

    Parameters
    ----------
    in_value
        Input ID or path to a netCDF file

    CMIP6client
        Client to use for interacting with pyhandle's REST API

        If not supplied, a new client with a default handle server URL
        is instantiated.

    get_tracking_id_from_path
        Function which, given a path outputs the tracking ID

    multi_dataset_handling
        What to do in the case that the tracking ID belongs to multiple datasets
        i.e. is associated with more than one PID.

        Passed to [get_dataset_pid][(p).tracking_id.get_dataset_pid].

    Returns
    -------
    pid :
        Dataset PID associated with the in_value

    """
    if CMIP6client is None:  # pragma: no cover
        CMIP6client = RESTHandleClient(handle_server_url="http://hdl.handle.net/")

    if Path(in_value).exists():
        tracking_id = get_tracking_id_from_path(Path(in_value))
        id_in_value = tracking_id.replace("hdl:", "")
        id_is_tracking_id = True

    else:
        id_in_value = in_value.replace("hdl:", "")

        agg_lev = CMIP6client.get_value_from_handle(id_in_value, "AGGREGATION_LEVEL")
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
            CMIP6client=CMIP6client,
        )

    else:
        pid = id_in_value
    return pid


# we can't use the CMIP6 STAC like CMIP7 because some of the data seems to be missing
# (ex. hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b)
# doi_granularity default to experiment to fit with CMIP7
def _get_doi_and_version_CMIP6(  # noqa: PLR0913
    in_value: str,
    doi_granularity: DOIGranularity | None = DOIGranularity.EXPERIMENT,
    CMIP6client: RESTHandleClient | None = None,
    get_tracking_id_from_path: Callable[[Path], str] = get_tracking_id_from_cmip_netcdf,
    multi_dataset_handling: MultiDatasetHandlingStrategy | None = None,
    dataset_pid_lookup: DatasetPIDLookupStrategy
    | None = DatasetPIDLookupStrategy.ALLOWPREVIOUS,
) -> tuple[str, str]:
    """
    Get DOI and version for a given ID or path to a netCDF file

    Parameters
    ----------
    in_value
        Input ID or path to a netCDF file

    doi_granularity
        Granularity of DOI to retrieve.

        We use the 'lowest-level' from the DRS as a short-hand.
        "experiment" is short for mip-model-experiment.
        "model" is short for mip-model.

        See [DOIGranularity][(m).] for details.

    CMIP6client
        Client to use for interacting with pyhandle's REST API

        If not supplied, a new client with a default handle server URL
        is instantiated.

    get_tracking_id_from_path
        Function which, given a path outputs the tracking ID

    multi_dataset_handling
        What to do in the case that the tracking ID belongs to multiple datasets
        i.e. is associated with more than one PID.

        Passed to [get_dataset_pid][(p).tracking_id.get_dataset_pid].

    dataset_pid_lookup
        Whether to only look at the current dataset PID or allow looking at the
        previous dataset PID if the current one does not have a DOI.


    Returns
    -------
    doi :
        DOI that applies to `in_value`

    version :
        Version that applies to `in_value`
    """
    if CMIP6client is None:  # pragma: no cover
        CMIP6client = RESTHandleClient(handle_server_url="http://hdl.handle.net/")

    # default to Experiment if None
    doi_granularity = doi_granularity or DOIGranularity.EXPERIMENT

    pid = _in_value_CMIP6_2_pid(
        in_value, CMIP6client, get_tracking_id_from_path, multi_dataset_handling
    )

    doi_raw = CMIP6client.get_value_from_handle(pid, "IS_PART_OF")

    # try to see if there is a previous version of the PID that is linked to a DOI
    if doi_raw is None and dataset_pid_lookup == DatasetPIDLookupStrategy.ALLOWPREVIOUS:
        previous_pid = CMIP6client.get_value_from_handle(pid, "REPLACES")

        if previous_pid is not None:
            doi_raw = CMIP6client.get_value_from_handle(previous_pid, "IS_PART_OF")

        warnings.warn(
            f"No DOI found for {in_value} (pid: {pid}). "
            f"Using the DOI from the previous PID version ({previous_pid}).",
            UserWarning,
        )

    if doi_raw is None:
        msg = f"Could not find a DOI for {in_value} (pid: {pid})"
        raise ValueError(msg)

    doi = doi_raw.replace("doi:", "")

    if doi_granularity == DOIGranularity.MODEL:
        # get model doi
        r = httpx.get(
            f"https://api.datacite.org/dois/{doi}",
            follow_redirects=True,
        )
        doi = r.raise_for_status().json()["data"]["attributes"]["container"][
            "identifier"
        ]

    elif doi_granularity == DOIGranularity.EXPERIMENT:
        # doi is already in the desired form
        pass

    else:  # pragma: no cover
        raise NotImplementedError(doi_granularity)

    version = CMIP6client.get_value_from_handle(pid, "VERSION_NUMBER")

    return (doi, version)


def _get_doi_and_version_CMIP7(  # type: ignore
    in_value: str,
    get_tracking_id_from_path: Callable[[Path], str] = get_tracking_id_from_cmip_netcdf,
    multi_dataset_handling: MultiDatasetHandlingStrategy | None = None,
) -> tuple[str, str]:
    """
    Get DOI and version for a given ID or path to a netCDF file

    Parameters
    ----------
    in_value
        Input ID or path to a netCDF file

    get_tracking_id_from_path
        Function which, given a path outputs the tracking ID

    multi_dataset_handling
        DOESN'T WORK FOR CMIP7 YET
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
    info = get_info_from_STAC(
        in_value,
        ["doi", "version"],
        get_tracking_id_from_path,
        multi_dataset_handling,
    )

    return (info["doi"], info["version"])


def get_doi_and_version(  # type: ignore # noqa: PLR0913
    in_value: str,
    get_tracking_id_from_path: Callable[[Path], str] = get_tracking_id_from_cmip_netcdf,
    multi_dataset_handling: MultiDatasetHandlingStrategy | None = None,
    doi_granularity: DOIGranularity | None = None,
    CMIP6client: RESTHandleClient | None = None,
    dataset_pid_lookup: DatasetPIDLookupStrategy | None = None,
) -> tuple[str, str]:
    """
    Get DOI and version for a given ID or path to a netCDF file

    Parameters
    ----------
    in_value
        Input ID or path to a netCDF file

    get_tracking_id_from_path
        Function which, given a path outputs the tracking ID

    multi_dataset_handling
        What to do in the case that the tracking ID belongs to multiple datasets
        i.e. is associated with more than one PID.

    doi_granularity
        Only valid for CMIP6.
        Granularity of DOI to retrieve.

        We use the 'lowest-level' from the DRS as a short-hand.
        "experiment" is short for mip-model-experiment.
        "model" is short for mip-model.
        All CMIP7 dois are at the experiment level.

        See [DOIGranularity][(m).] for details.

    CMIP6client
        Only valid for CMIP6.
        Client to use for interacting with pyhandle's REST API

        If not supplied, a new client with a default handle server URL
        is instantiated.

    dataset_pid_lookup
        Only valid for CMIP6.
        Whether to only look at the current dataset PID or allow looking at the
        previous dataset PID if the current one does not have a DOI.


    Returns
    -------
    doi :
        DOI that applies to `in_value`

    version :
        Version that applies to `in_value`
    """
    if get_mip_era(in_value, get_tracking_id_from_path) == "CMIP6":
        (doi, version) = _get_doi_and_version_CMIP6(
            in_value,
            doi_granularity=doi_granularity,
            CMIP6client=CMIP6client,
            get_tracking_id_from_path=get_tracking_id_from_path,
            multi_dataset_handling=multi_dataset_handling,
            dataset_pid_lookup=dataset_pid_lookup,
        )

    else:  # CMIP7
        if CMIP6client is not None:
            warnings.warn(
                "CMIP6client is not used for CMIP7. Ignoring the client parameter.",
                UserWarning,
            )
        if doi_granularity is not None:
            warnings.warn(
                "doi_granularity is not used for CMIP7. "
                "All dois are at the experiment level."
                " Ignoring the doi_granularity parameter.",
                UserWarning,
            )
        if dataset_pid_lookup is not None:
            warnings.warn(
                "dataset_pid_lookup is not used for CMIP7. "
                " Ignoring the dataset_pid_lookup parameter.",
                UserWarning,
            )
        (doi, version) = _get_doi_and_version_CMIP7(
            in_value,
            get_tracking_id_from_path=get_tracking_id_from_path,
            multi_dataset_handling=multi_dataset_handling,
        )

    return (doi, version)


def get_citations(  # type: ignore # noqa: PLR0913
    ids_or_paths: list[str],
    get_citation: Callable[[str, str], str],
    doi_granularity: DOIGranularity,
    CMIP6client: RESTHandleClient | None = None,
    multi_dataset_handling: MultiDatasetHandlingStrategy | None = None,
    dataset_pid_lookup: DatasetPIDLookupStrategy | None = None,
) -> list[str]:
    """
    Get citations that apply to the given IDs or paths

    If your IDs are tracking IDs or paths,
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
        Function which, given a DOI and a version, produces a citation or a table.

        For example, [get_bibtex_citation][(m).].

    doi_granularity
        Only valid for CMIP6 data. Granularity of DOI to retrieve.

        See [DOIGranularity][(m).] for details.

    CMIP6client
        Only valid for CMIP6 data.
        Client to use for interacting with pyhandle's REST API

        If not supplied, a new client with a default handle server URL
        is instantiated.

    multi_dataset_handling
        What to do in the case that the tracking ID belongs to multiple datasets
        i.e. is associated with more than one PID.

        Passed to [get_dataset_pid][(p).tracking_id.get_dataset_pid].

    dataset_pid_lookup
        Whether to only look at the current dataset PID orallow looking at the
        previous dataset PID if the current one does not have a DOI.


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
    Both PID types can be passed to `ids_or_paths`.

    For a given PID, we can retrieve an associated DOI.
    However, for CMIP6, there are multiple possibilities for the retrieved DOI.
    These vary based on the granularity of the DOI.
    At the moment, as far as we know, there are two granularities:
        * model (capturing all submissions to a given MIP by a given model)
        * experiment (capturing all submissions to a given MIP by a given model for a
        given experiment.
    This is controlled by `doi_granularity`.
    CMIP7 only has one granularity (experiment).

    Examples
    --------
    >>> citations = get_citations(
    ...     ["hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b"],
    ...     doi_granularity=DOIGranularity.MODEL,
    ...     get_citation=get_bibtex_citation,
    ... )
    >>> print(citations[0])
    @misc{https://doi.org/10.22033/esgf/cmip6.742,
      doi = {10.22033/ESGF/CMIP6.742},
      url = {http://cera-www.dkrz.de/WDCC/meta/CMIP6/CMIP6.CMIP.MPI-M.MPI-ESM1-2-LR},
      author = {Wieners, Karl-Hermann and Giorgetta, Marco and Jungclaus,
      Johann and Reick, Christian and Esch, Monika and Bittner, Matthias and Legutke,
      Stephanie and Schupfner, Martin and Wachsmann, Fabian and Gayler,
      Veronika and Haak, Helmuth and de Vrese, Philipp and Raddatz,
      Thomas and Mauritsen, Thorsten and von Storch, Jin-Song and Behrens,
      Jörg and Brovkin, Victor and Claussen, Martin and Crueger, Traute and Fast,
      Irina and Fiedler, Stephanie and Hagemann, Stefan and Hohenegger, Cathy and Jahns,
      Thomas and Kloster, Silvia and Kinne, Stefan and Lasslop, Gitta and Kornblueh,
      Luis and Marotzke, Jochem and Matei, Daniela and Meraner, Katharina and
      Mikolajewicz, Uwe and Modali, Kameswarrao and Müller, Wolfgang and Nabel, Julia
      and Notz, Dirk and Peters-von Gehlen, Karsten and Pincus, Robert and Pohlmann,
      Holger and Pongratz, Julia and Rast, Sebastian and Schmidt, Hauke and Schnur,
      Reiner and Schulzweida, Uwe and Six, Katharina and Stevens, Bjorn and Voigt, Aiko
      and Roeckner, Erich},
      keywords = {CMIP6, climate, CMIP6.CMIP.MPI-M.MPI-ESM1-2-LR},
      language = {en},
      title = {MPI-M MPIESM1.2-LR model output prepared for CMIP6 CMIP.
        Version 20211412.},
      publisher = {Earth System Grid Federation},
      year = {2019},
      copyright = {Creative Commons Attribution 4.0 International}
    }
    """
    doi_versions = [
        get_doi_and_version(
            v,
            CMIP6client=CMIP6client,
            multi_dataset_handling=multi_dataset_handling,
            doi_granularity=doi_granularity,
            dataset_pid_lookup=dataset_pid_lookup,
        )
        for v in ids_or_paths
    ]

    doi_versions_unique = set(doi_versions)

    res = [get_citation(doi, version) for doi, version in doi_versions_unique]

    return res


# TODO: do other formats also, md ?
def get_latex_table(
    ids_or_paths: list[str],
    table_columns: list[str] | None = None,
    get_tracking_id_from_path: Callable[[Path], str] = get_tracking_id_from_cmip_netcdf,
    multi_dataset_handling: MultiDatasetHandlingStrategy | None = None,
) -> str:
    """Get a LaTeX table of metadata.

    If your IDs are tracking IDs or paths,
    then two or more IDs/paths can share the same citation.
    This function returns the minimum a table only with unique columns.
    Warning: Only works for CMIP7 at the moment.

    Parameters
    ----------
    ids_or_paths
        Tracking ids (file PID), dataset PIDs and paths for which to get citations.

        Tracking ids identify files.
        To date, they can be found
        in the `tracking_id` global attribute of CMIP netCDF files.

        PIDs identify datasets (a group of files).

        Paths should point to a CMIP file with a `tracking_id` global attribute.

    table_columns
        List of columns to include in the table.
        Possible values are the CMIP global attributes,
          "reference" (to get the bibtex label), "doi" and "version".

    get_tracking_id_from_path
        Function which, given a path outputs the tracking ID

    multi_dataset_handling
        What to do in the case that the tracking ID belongs to multiple datasets
        i.e. is associated with more than one PID.

    """
    columns_title = [
        x.capitalize().replace("_id", "").replace("Doi", "DOI") for x in table_columns
    ]
    ncol = len(table_columns)

    table = (
        "\\begin{center}\n\\begin{tabular}{ "
        + "c " * ncol
        + "}\n"
        + " & ".join(columns_title)
        + " \\\\\n\\hline\n"
    )

    attrs_col = ["doi" if c == "reference" else c for c in table_columns]

    in_attrs = [
        get_info_from_STAC(
            v, attrs_col, get_tracking_id_from_path, multi_dataset_handling
        )
        for v in ids_or_paths
    ]

    # get the bibtex entry (which happens to have doi_url as a label)
    bibtex_ref = [
        {"reference": "\\cite{https://doi.org/" + x["doi"].lower() + "}"}
        for x in in_attrs
    ]

    combined = [{**a, **b} for a, b in zip(in_attrs, bibtex_ref)]

    # only keep the columns wanted
    combined_tuple = [tuple(d[k] for k in table_columns) for d in combined]

    # only keep unique rows
    combined_tuple = set(combined_tuple)

    # build table
    for row in combined_tuple:
        table += " & ".join(row)
        table += " \\\\\n"
    table += "\\end{tabular}\n\\end{center}"

    return table


def get_info_from_STAC(
    in_value: str,
    properties: list[str],
    get_tracking_id_from_path: Callable[[Path], str] = get_tracking_id_from_cmip_netcdf,
    multi_dataset_handling: MultiDatasetHandlingStrategy | None = None,
) -> dict[str, Any]:
    """
    Get listed properties from the STAC API based on in_value.

    It is also possible to get the doi.

    Parameters
    ----------
    in_value
        Input ID or path to a netCDF file
    properties
        List of properties to retrieve from STAC.
        These can be CMIP global attributes, "version" or "doi".
    get_tracking_id_from_path
        Function which, given a path outputs the tracking ID
    multi_dataset_handling
        What to do in the case that the tracking ID belongs to multiple datasets
        i.e. is associated with more than one PID.

        Passed to [get_dataset_pid][(p).tracking_id.get_dataset_pid].

    Returns
    -------
    info:
        Dictionary of properties retrieved from STAC
    """
    if Path(in_value).exists():
        in_value = get_tracking_id_from_path(Path(in_value))

    mip_era = get_mip_era(in_value)
    if mip_era == "CMIP6":
        message = "CMIP6 STAC is incomplete. A workaround has not yet been implemented."
        raise NotImplementedError(message)

    url = (
        f"https://transaction.east.esgf.io/collections/{mip_era}/items?filter="
        f"{mip_era.lower()}:tracking_id='{in_value}' OR"
        f"{mip_era.lower()}:pid='{in_value}'&"
        "filter-lang=cql2-text&limit=1"
    )
    r = requests.get(url, timeout=5)
    r.raise_for_status()
    STACdata = r.json()

    STACfeatures = _get_right_STACfeature(in_value, STACdata, multi_dataset_handling)

    info = {}
    for x in properties:
        if f"{mip_era.lower()}:{x}" in STACfeatures["properties"]:
            info[x] = STACfeatures["properties"][f"{mip_era.lower()}:{x}"]
        elif x in STACfeatures["properties"]:
            info[x] = STACfeatures["properties"][x]
        elif x == "doi":
            info["doi"] = _get_doi_from_STACfeatures(in_value, STACfeatures)
        else:
            warnings.warn(
                f"{x} not found in STAC for {in_value}. Setting to empty string.",
                UserWarning,
            )
            info[x] = ""

    return info


def _get_right_STACfeature(in_value, STACdata, multi_dataset_handling):
    """Choose the right STAC feature based on the multi_dataset_handling strategy."""
    if len(STACdata["features"]) == 0:
        message = f"No CMIP7 dataset found for {in_value}"
        raise ValueError(message)
    elif len(STACdata["features"]) == 1:
        STACfeatures = STACdata["features"][0]
    else:
        # TODO: find a CMIP7 case to test this
        warnings.warn(
            f"More than one feature found for {in_value}. Using the first one.",
            UserWarning,
        )

        versions = [int(f["properties"]["version"]) for f in STACdata["features"]]

        if multi_dataset_handling is None:
            raise MultipleDatasetMemberError(
                tracking_id=in_value, version_pids=versions
            )

        if multi_dataset_handling == MultiDatasetHandlingStrategy.LATEST:
            STACfeatures = STACdata["features"][np.argmax(versions)]

        elif multi_dataset_handling == MultiDatasetHandlingStrategy.FIRST:
            STACfeatures = STACdata["features"][np.argmin(versions)]

        else:  # pragma: no cover
            raise NotImplementedError(multi_dataset_handling)
    return STACfeatures


def _get_doi_from_STACfeatures(in_value, STACfeatures):
    """Extract the DOI from the STAC features and Citation Service."""
    # get the citation service url from STAC
    # and  get the doi_urlfrom the the citation service
    cite_as_links = [x for x in STACfeatures["links"] if x["rel"] == "cite-as"]
    if len(cite_as_links) == 0:
        message = f"No cite-as link found for {in_value}"
        raise ValueError(message)
    # TODO: is it possible that there would be more than one cite-as link?
    elif len(cite_as_links) > 1:
        warnings.warn(
            f"More than one cite-as link found for {in_value}.Using the first one.",
            UserWarning,
        )
    cite_as_link = cite_as_links[0]
    responsecitation = requests.get(cite_as_link["href"], timeout=5)
    responsecitation.raise_for_status()
    CITEdata = responsecitation.json()

    doi = CITEdata["doi_url"]
    doi = doi.replace("https://doi.org/", "").upper()
    return doi


def translate_get_args_to_get_citations_kwargs(
    format: FormatOption,
    author_list_style: AuthorListStyle,
    handle_server_url: str | None = None,
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

    if handle_server_url is None:
        CMIP6client = None
    else:
        CMIP6client = RESTHandleClient(handle_server_url=handle_server_url)

    return dict(
        get_citation=get_citation,
        CMIP6client=CMIP6client,
    )


TABLE_COLUMNS_DEFAULT = [
    "source_id",
    "institution_id",
    "experiment_id",
    "variable_id",
    "version",
    "reference",
]


def get(  # noqa: PLR0913
    in_values: list[str],
    format: FormatOption = FormatOption.TEXT,
    author_list_style: AuthorListStyle = AuthorListStyle.LONG,
    multi_dataset_handling: MultiDatasetHandlingStrategy | None = None,
    table_columns: list[str] | None = TABLE_COLUMNS_DEFAULT,
    doi_granularity: DOIGranularity | None = None,
    dataset_pid_lookup: DatasetPIDLookupStrategy | None = None,
    handle_server_url: str | None = None,
) -> list[str]:
    """
    Get citations without duplicates from CMIP files or tracking IDs or PIDs

    This function mirrors the CLI `get` command as closely as possible.

    Parameters
    ----------
    in_values
        Tracking IDs, PIDs or file paths for which to generate citations.
        Paths should point to a CMIP file with a `tracking_id` global attribute.

    format
        Format in which to retrieve the citations

    author_list_style
        Whether, if the format is text,
        the author list should be long (all names) or short (et al.)

    multi_dataset_handling
        Strategy to use when a given ID or file belongs to multiple datasets

    table_columns
        Columns to include in the table if format is "latextable".

    doi_granularity
        Only valid for CMIP6 data (where it defaults to experiment).
        Granularity of DOI to retrieve.

        See [DOIGranularity][(m).] for details.

    dataset_pid_lookup
        Only valid for CMIP6 data (where it defaults to allow previous).
        Whether to only look at the current dataset PID or allow looking at the
          previous dataset PID (if it exists) if the current one does not have a DOI.
        See [DatasetPIDLookupStrategy][(m).] for details.

    handle_server_url
        Only valid for CMIP6 data (where it defaults to https://hdl.handle.net).
        URL of the server to use for handling tracking IDs i.e. handles
        If not supplied, a new client with a default handle server URL
        is instantiated.

    Returns
    -------
    :
        Retrieved citations for `in_values`

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
    Both PID types can be passed to `in_values`.
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
                multi_dataset_handling=multi_dataset_handling,
                doi_granularity=doi_granularity,
                dataset_pid_lookup=dataset_pid_lookup,
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
