"""
Unit tests of `cmipcite.citations`
"""

import re
import sys
from unittest.mock import patch

import pytest

from cmipcite.citations import (
    get_info_from_STAC,
    get_mip_era,
    get_tracking_id_from_cmip_netcdf,
)
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


def test_get_mip_era_from_tracking_id():
    assert get_mip_era("hdl:21.14100/90f93a05-357c-4ea2-b61f-bf2418700791") == "CMIP6"
    assert get_mip_era("hdl:21.14107/eee87809-8c47-4b80-9104-fdd5ee85c8c4") == "CMIP7"
    with pytest.raises(
        ValueError,
        match=re.escape("Could not determine mip_era for"),
    ):
        get_mip_era("hdl:21.14108/eee87809-8c47-4b80-9104-fdd5ee85c8c4")


def test_get_info_from_STAC():
    # catch warning for property that does not exist
    with pytest.warns(
        UserWarning,
        match=re.escape(
            "model not found in STAC for "
            "hdl:21.14107/eee87809-8c47-4b80-9104-fdd5ee85c8c4. "
            "Setting to empty string."
        ),
    ):
        out = get_info_from_STAC(
            "hdl:21.14107/eee87809-8c47-4b80-9104-fdd5ee85c8c4", ["source_id", "model"]
        )
        assert out == {"source_id": "UKCM2a-0-HH", "model": ""}
