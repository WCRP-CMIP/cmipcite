"""
Unit tests of `cmipcite.citations`
"""

import re
import sys
from unittest.mock import patch

import pytest

from cmipcite.citations import get_tracking_id_from_cmip_netcdf
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
