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
# # How to get citations ?  (Advanced version)
#
# Here, we show how you can get citations for CMIP data
# with a fine-level of user control.
# For the basic intro, please see
# [How to get citations ? (Basic version)](../get-citations-basic).

# %% [markdown]
# ## Imports

# %%
from functools import partial

import httpx

from cmipcite.citations import (
    AuthorListStyle,
    DOIGranularity,
    get_bibtex_citation,
    get_citations,
    get_text_citation,
)

# %% [markdown]
#
# The `get_citations` function allows for more control over how citations are retrieved.
# It supports dependency injection which allows you to pass function that defined the
# behavior. A few such functions are provided out-of-the-box.


# %% [markdown]
# ### Bibtex
#
# This support is built-in.
# Simply pass `get_bibtex_citation` to `get_citation`.

# %%
bibtex_citations = get_citations(
    ["hdl:21.14100/90f93a05-357c-4ea2-b61f-bf2418700791"],
    doi_granularity=DOIGranularity.EXPERIMENT,
    get_citation=get_bibtex_citation,
)
print(f"{len(bibtex_citations)=}")
print(bibtex_citations[0])


# %% [markdown]
# ### Plain text
#
# A specific implementation of this is built-in.
# You can pass in `get_text_citation`
# with a 'pre-loaded' value for `author_list_style`
# using [`functools.partial`](https://docs.python.org/3/library/functools.html#functools.partial).

# %%
plaintex_citations = get_citations(
    ["hdl:21.14100/90f93a05-357c-4ea2-b61f-bf2418700791"],
    doi_granularity=DOIGranularity.EXPERIMENT,
    get_citation=partial(get_text_citation, author_list_style=AuthorListStyle.LONG),
)

print(plaintex_citations[0])

# %% [markdown]
# Plain text with a short author list
# If you need a different value for `author_list_style`,
# just change it in the call to `partial`.

# %%
plaintex_citations = get_citations(
    ["hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b"],
    doi_granularity=DOIGranularity.MODEL,
    get_citation=partial(get_text_citation, author_list_style=AuthorListStyle.SHORT),
)

print(plaintex_citations[0])


# %% [markdown]
# ### Inject your own function
#
# You can also inject your own, custom function.


# %%
def get_my_citation(doi: str, version: str) -> str:
    """
    Get custom citation
    """
    r = httpx.get(f"https://api.datacite.org/dois/{doi}", follow_redirects=True)
    data = r.raise_for_status().json()["data"]["attributes"]

    creators = ", ".join(
        [
            f"{c['name'].split(',')[1].strip()} {c['name'].split(',')[0]}"
            for c in data["creators"]
        ]
    )

    citation = f"{version} {data['titles'][0]['title']} by {creators}. DOI: https://doi.org/{doi}"

    return citation


# %%
custom_citations = get_citations(
    ["hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b"],
    doi_granularity=DOIGranularity.MODEL,
    get_citation=get_my_citation,
)

print(custom_citations[0])
