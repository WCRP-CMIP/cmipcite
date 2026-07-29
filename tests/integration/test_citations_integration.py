"""
Integration tests of `cmipcite.citations`
"""

import re

import pytest

from cmipcite.citations import get, get_doi_and_version


def test_multiple_error_message():
    with pytest.raises(
        ValueError,
        match=re.escape(
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
        ),
    ):
        get(["hdl:21.14100/cfb3c24b-921a-49af-8b7b-1346c764e750"])


def test_handle_path_equivalence(test_data_dir):
    pytest.importorskip("netCDF4")

    out_id = get(
        ["hdl:21.14100/90f93a05-357c-4ea2-b61f-bf2418700791"],
    )
    out_path = get([test_data_dir / "sftlf_fx_CanESM5_historical_r1i1p1f1_gn.nc"])

    assert out_id == out_path


def test_id_with_no_doi():
    with pytest.raises(
        ValueError,
        match=re.escape("Could not find a DOI for"),
    ):
        get(
            ["hdl:21.14100/da9cc03a-3b05-4dee-9b7a-5c9b9435bf2b"],
            multi_dataset_handling="latest",
            dataset_pid_lookup="allow_previous",
        )


def test_id_doi_in_old_pid():
    doi, version = get_doi_and_version(
        "hdl:21.14100/c4eac79c-5c22-44a3-9a67-03b5959046e1",
        "experiment",
        dataset_pid_lookup="allow_previous",
    )
    assert doi == "10.22033/ESGF/CMIP6.8321"
    assert version == "20230616"

    out = get(
        ["hdl:21.14100/c4eac79c-5c22-44a3-9a67-03b5959046e1"],
        multi_dataset_handling="latest",
        dataset_pid_lookup="allow_previous",
    )
    assert len(out) == 1

    with pytest.raises(
        ValueError,
        match=re.escape("Could not find a DOI for"),
    ):
        out = get(
            ["hdl:21.14100/c4eac79c-5c22-44a3-9a67-03b5959046e1"],
            multi_dataset_handling="latest",
            dataset_pid_lookup="current_only",
        )
