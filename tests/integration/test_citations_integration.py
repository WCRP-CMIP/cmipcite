"""
Integration tests of `cmipcite.citations`
"""

import re

import pytest

from cmipcite.citations import get


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
