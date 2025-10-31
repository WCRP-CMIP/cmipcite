"""
Handling of tracking IDs
"""

from __future__ import annotations

import sys

from pyhandle.handleclient import RESTHandleClient  # type: ignore

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from backports.strenum import StrEnum


class MultiDatasetHandlingStrategy(StrEnum):
    """
    Strategy for handling the case when a tracking ID appears in multiple datasets

    In other words, is associated with more than one dataset PID
    """

    LATEST = "latest"
    """
    Get the PID for the latest dataset
    """

    FIRST = "first"
    """
    Get the PID for the first dataset
    """

    # Could imagine also having first-published
    # vs. first-including-retracted etc.
    # Not doing this for now as not clear we actually need/want these


class MultipleDatasetMemberError(KeyError):
    """
    Raised to indicate that a tracking ID is associated with multiple datasets i.e. PIDs

    Usually only raised if no strategy for handling such a clash is given.
    """

    def __init__(self, tracking_id: str, version_pids: dict[str, str]) -> None:
        """
        Initialise the error

        Parameters
        ----------
        tracking_id
            Tracking ID

        version_pids
            Version strings and associated PIDs with which `tracking_id` is associated
        """
        version_pid_info = ", ".join(
            f"{version} (PID: {version_pids[version]})"
            for version in sorted(version_pids)[::-1]
        )
        error_msg = (
            f"{tracking_id=} is associated with "
            f"multiple versions (therefore PIDs): {version_pid_info}"
        )
        super().__init__(error_msg)


def get_dataset_pids(  # type: ignore
    tracking_id: str,
    client: RESTHandleClient | None = None,
) -> list[str]:
    """
    Get the PID(s) of the dataset(s) with which a tracking ID is associated

    Parameters
    ----------
    tracking_id
        Tracking ID for which to get associated PIDs

    client
        Client to use for interacting with pyhandle's REST API

        If not supplied, a new client with a default handle server URL
        is instantiated.

    Returns
    -------
    :
        PID(s) of the dataset(s) with which `tracking_id` is associated
    """
    if client is None:  # pragma: no cover
        client = RESTHandleClient(handle_server_url="http://hdl.handle.net/")

    id_query = tracking_id.replace("hdl:", "")
    pids_raw: str = client.get_value_from_handle(id_query, "IS_PART_OF")
    pids = pids_raw.split(";")

    return pids


def get_dataset_pid(  # type: ignore
    tracking_id: str,
    multi_dataset_handling: MultiDatasetHandlingStrategy | None = None,
    client: RESTHandleClient | None = None,
) -> str:
    """
    Get dataset PID to which a given tracking ID belongs

    Parameters
    ----------
    tracking_id
        Tracking ID

    multi_dataset_handling
        What to do in the case that the tracking ID belongs to multiple datasets
        i.e. is associated with more than one PID.

        If not supplied, an error is raised if `tracking_id`
        is associated with more than one PID.

    client
        Client to use for interacting with pyhandle's REST API

        If not supplied, a new client with a default handle server URL
        is instantiated.

    Returns
    -------
    :
        `tracking_id`'s dataset PID.

    Raises
    ------
    MultipleDatasetMemberError
        `multi_dataset_handling` is `None` and the tracking ID
        appears in multiple datasets.
    """
    if client is None:
        client = RESTHandleClient(handle_server_url="http://hdl.handle.net/")

    pids = get_dataset_pids(tracking_id, client=client)
    if len(pids) == 1:
        # Only found one, fast return
        return pids[0]

    # Have to do more work to get metadata in this case.
    # We could imagine adding more complicated picking strategies here.
    # For now, this is fine.
    versions = {
        client.get_value_from_handle(pid, "VERSION_NUMBER"): pid for pid in pids
    }
    if multi_dataset_handling is None:
        raise MultipleDatasetMemberError(tracking_id=tracking_id, version_pids=versions)

    if multi_dataset_handling == MultiDatasetHandlingStrategy.LATEST:
        pid_selected = versions[max(versions)]

    elif multi_dataset_handling == MultiDatasetHandlingStrategy.FIRST:
        pid_selected = versions[min(versions)]

    else:  # pragma: no cover
        raise NotImplementedError(multi_dataset_handling)

    return pid_selected
