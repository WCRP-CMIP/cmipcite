"""
Unit tests of `cmipcite.citations`
"""

import re
import sys
from unittest.mock import patch

import pytest

from cmipcite.citations import get_doi_and_version, get_tracking_id_from_cmip_netcdf
from cmipcite.exceptions import MissingOptionalDependencyError


def test_get_tracking_id_from_cmip_netcdf_no_netcdf4():
    with patch.dict(sys.modules, {"netCDF4": None}):
        with pytest.raises(
            MissingOptionalDependencyError,
            match=re.escape(
                "`get_tracking_id_from_cmip_netcdf` requires netCDF4 to be installed"
            ),
        ):
            get_tracking_id_from_cmip_netcdf("junk")


def test_id_with_no_doi():
    with pytest.raises(
        ValueError,
        match=re.escape("Could not find a DOI for"),
    ):
        get_doi_and_version(
            "hdl:21.14100/da9cc03a-3b05-4dee-9b7a-5c9b9435bf2b", "experiment"
        )


def test_id_doi_in_old_pid():
    doi, version = get_doi_and_version(
        "hdl:21.14100/c4eac79c-5c22-44a3-9a67-03b5959046e1", "experiment"
    )
    assert doi == "10.22033/ESGF/CMIP6.8321"
    assert version == "20230616"
