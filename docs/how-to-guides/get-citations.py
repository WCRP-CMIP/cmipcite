# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown] editable=true slideshow={"slide_type": ""}
# # How to get citations
#
# Here, we show how you can get citations for CMIP data.
# Citation can be retrieved with the help of the Persistent IDentifiers (PIDs).
# In the CMIP world, there are two types of PIDs:
#   * file PID (also called tracking_id)
#   * dataset PID (often referred to as just PID).
# A dataset is a collection of files from a single variable sampled at a single
# frequency from a single model running a single experiment.
# All the datasets from a single model and a single experiment are grouped under a DOI.
# There also exist DOIs associated to single model, but including all the experiments,
#  but they are not used by this package.

# %% [markdown]
# ## Imports

# %%
import traceback
from functools import partial

from cmipcite.citations import (
    AuthorListStyle,
    get_bibtex_citation,
    get_citations,
    get_text_citation,
)
from cmipcite.tracking_id import (
    MultiDatasetHandlingStrategy,
    MultipleDatasetMemberError,
)

# %% [markdown]
# ## Python API
#
# First we show how to do this via the Python API.

# %% [markdown]
# Bibtex
#
# A single citation for a single tracking ID or PID can be retrieved as shown.

# %%
bibtex_citations = get_citations(
    ["hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b"],
    get_citation=get_bibtex_citation,
)
print(f"{len(bibtex_citations)=}")
print(bibtex_citations[0])

# %% [markdown]
# Multiple citations can also be retrieved.

# %%
bibtex_citations_multi = get_citations(
    [
        "hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b",
        "hdl:21.14100/a31d6f22-4066-3e30-913f-501509086357",
        "hdl:21.14100/f821d2df-4b10-3afc-a17d-119b9c24ba3c",
    ],
    get_citation=get_bibtex_citation,
)
print(f"Retrieved {len(bibtex_citations_multi)} citations")
print()
print("\n\n".join(bibtex_citations_multi))

# %% [markdown]
# Plain text

# %%
plaintex_citations = get_citations(
    ["hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b"],
    get_citation=partial(get_text_citation, author_list_style=AuthorListStyle.LONG),
)

print(plaintex_citations[0])

# %% [markdown]
# Plain text with a short author list

# %%
plaintex_citations = get_citations(
    ["hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b"],
    get_citation=partial(get_text_citation, author_list_style=AuthorListStyle.SHORT),
)

print(plaintex_citations[0])

# %% [markdown]
# ## Command-line interface
#
# More or less the same as the above, but from the command line instead.

# %%
# !cmipcite get 'hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b'

# %%
# !cmipcite get 'hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b' \
#   --author-list-style short

# %%
# !cmipcite get 'hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b' --format bibtex

# %% [markdown]
# If you wish, you can save the output directly to a file.

# %%
# !cmipcite get 'hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b' --out-path demo.txt

# %%
with open("demo.txt") as fh:
    print(fh.read())

# %% [markdown]
# ## Files associated with multiple datasets
#
# On ESGF, a file can be part of multiple datasets.
# In such a case, the citation to use is ambiguous.

# %%
# Trying to get the citation for a dataset
# that is part of multiple datasets gives an error.
try:
    get_citations(
        ["hdl:21.14100/cfb3c24b-921a-49af-8b7b-1346c764e750"],
        get_citation=get_bibtex_citation,
    )
except MultipleDatasetMemberError:
    traceback.print_exc(limit=0, chain=False)

# %% [markdown]
# In this case, you as the user have to specify the strategy
# you would like to use to pick a specific dataset.

# %%
multi_member_cite = get_citations(
    ["hdl:21.14100/cfb3c24b-921a-49af-8b7b-1346c764e750"],
    get_citation=get_bibtex_citation,
    # Get the latest dataset
    multi_dataset_handling=MultiDatasetHandlingStrategy.LATEST,
)
print(multi_member_cite[0])

# %% [markdown]
# The same behaviour can be specified via the CLI.

# %%
# !cmipcite get 'hdl:21.14100/cfb3c24b-921a-49af-8b7b-1346c764e750' \
#     --multi-dataset-handling latest
