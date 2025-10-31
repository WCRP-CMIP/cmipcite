"""
Tests of `cmipcite.citations`
"""

import re
from contextlib import nullcontext as does_not_raise

import pytest

from cmipcite.tracking_id import (
    MultiDatasetHandlingStrategy,
    MultipleDatasetMemberError,
    get_dataset_pid,
)


@pytest.mark.parametrize(
    "handling_strategy,exp_res,exp_error",
    (
        pytest.param(
            None,
            None,
            pytest.raises(
                MultipleDatasetMemberError,
                match=re.escape(
                    "tracking_id='hdl:21.14100/cfb3c24b-921a-49af-8b7b-1346c764e750' "
                    "is associated with multiple versions (therefore PIDs): "
                    "20210205 "
                    "(PID: hdl:21.14100/3a3497e8-759b-368d-8615-91aebcd67abd), "
                    "20190903 "
                    "(PID: hdl:21.14100/2a375e38-5e60-3fe1-bf79-accadaed10d3)"
                ),
            ),
            id="default-no-handling-strategy-supplied",
        ),
        pytest.param(
            MultiDatasetHandlingStrategy.LATEST,
            # PID of the 20210205 i.e. latest version.
            "hdl:21.14100/3a3497e8-759b-368d-8615-91aebcd67abd",
            does_not_raise(),
            id="get-latest",
        ),
        pytest.param(
            MultiDatasetHandlingStrategy.FIRST,
            # PID of the 20190903 i.e. first version.
            "hdl:21.14100/2a375e38-5e60-3fe1-bf79-accadaed10d3",
            does_not_raise(),
            id="get-first",
        ),
    ),
)
def test_file_in_multiple_datasets_handling(handling_strategy, exp_res, exp_error):
    # The 2040-2049 file appears in both the
    # 20210205 and 20190903 versions.
    #
    # Search URL to see these datasets:
    # https://aims2.llnl.gov/search?project=CMIP6&versionType=all&activeFacets=%7B%22variable_id%22%3A%22tas%22%2C%22table_id%22%3A%22Amon%22%2C%22source_id%22%3A%22UKESM1-0-LL%22%2C%22experiment_id%22%3A%22ssp534-over%22%2C%22variant_label%22%3A%22r4i1p1f2%22%7D
    kwargs = {}
    if handling_strategy is not None:
        kwargs["multi_dataset_handling"] = handling_strategy

    with exp_error:
        res = get_dataset_pid(
            tracking_id="hdl:21.14100/cfb3c24b-921a-49af-8b7b-1346c764e750",
            **kwargs,
        )

    if exp_res is not None:
        assert res == exp_res
