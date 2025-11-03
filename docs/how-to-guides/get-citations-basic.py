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
# # How to get citations ? (Basic version)
#
# Here, we show how you can get citations for CMIP data.
# Citation can be retrieved with the help of the Persistent IDentifiers (PIDs).
# In the CMIP world, there are two types of PIDs:
#   * file PID (also called tracking_id)
#   * dataset PID (often referred to as just PID).
# A dataset is a collection of files from a single variable sampled at a single
# frequency from a single model running a single experiment.
# All the datasets from a single model or a single experiment (and model) are grouped
# under a DOI.


# %% [markdown]
# ## Imports

# %%
import traceback

from cmipcite.citations import get

# %% [markdown]
# ## Python API
#
# First, we show how to do this via the Python API.
# There is a simple  `get` function that allows the user to easily get a citation.
# This function has sensible defaults and the same argument as the CLI api (see below).


# %%
citations = get(["hdl:21.14100/90f93a05-357c-4ea2-b61f-bf2418700791"])
print(citations[0])

# %% [markdown]
# Instead of an id, you can also pass a path to a file.

# %%
# root_dir = Path.cwd().resolve().parents[1]  # adjust depth if needed
# data_file = root_dir / "tests/test-data/sftlf_fx_CanESM5_historical_r1i1p1f1_gn.nc"
data_file = "tests/test-data/sftlf_fx_CanESM5_historical_r1i1p1f1_gn.nc"
citations = get([data_file])
print(citations[0])


# %% [markdown]
# You can specify author list style.

# %%
citations = get(
    ["hdl:21.14100/90f93a05-357c-4ea2-b61f-bf2418700791"],
    author_list_style="short",
)
print(citations[0])

# %% [markdown]
# You can specify the output format.

# %%
citations = get(
    ["hdl:21.14100/90f93a05-357c-4ea2-b61f-bf2418700791"],
    format="bibtex",
)
print(citations[0])


# %% [markdown]
# You can specify the level of the DOI (model or experiment)

# %%
citations = get(
    ["hdl:21.14100/90f93a05-357c-4ea2-b61f-bf2418700791"],
    doi_level="experiment",
)
print(citations[0])


# %% [markdown]
# Multiple citations can also be retrieved.

# %%
citations = get(
    [
        "hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b",
        "hdl:21.14100/a31d6f22-4066-3e30-913f-501509086357",
        "hdl:21.14100/f821d2df-4b10-3afc-a17d-119b9c24ba3c",
    ],
)
print(f"Retrieved {len(citations)} citations")
print()
print("\n\n".join(citations))


# %% [markdown]
# On ESGF, a file can be part of multiple datasets.
# In such a case, the citation to use is ambiguous.

# %%
# Trying to get the citation for a dataset
# that is part of multiple datasets gives an error.
try:
    get(["hdl:21.14100/cfb3c24b-921a-49af-8b7b-1346c764e750"])
except ValueError:
    traceback.print_exc(limit=0, chain=False)

# %% [markdown]
# In this case, you as the user have to specify the strategy
# you would like to use to pick a specific dataset.

# %%
multi_member_cite = get(
    ["hdl:21.14100/cfb3c24b-921a-49af-8b7b-1346c764e750"],
    # Get the latest dataset
    multi_dataset_handling="latest",
)
print(multi_member_cite)


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
# !cmipcite get 'hdl:21.14100/cfb3c24b-921a-49af-8b7b-1346c764e750' \
#     --multi-dataset-handling latest --format bibtex

# %% [markdown]
# If you wish, you can save the output directly to a file.

# %%
# !cmipcite get 'hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b' --out-path demo.txt

# %%
with open("demo.txt") as fh:
    print(fh.read())
