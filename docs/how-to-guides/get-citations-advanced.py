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

# %% [markdown]
# ## Imports

# %%
from functools import partial

from cmipcite.citations import (
    AuthorListStyle,
    DOILevel,
    get_bibtex_citation,
    get_citations,
    get_text_citation,
)

# %% [markdown]
#
# The `get_citations` function allows for more control over how citations are retrieved.
# It supports dependency injection which allows you to pass function that defined the
# behavior. A few such functions are provided out-of-the-box.


# %%


# %% [markdown]
# ### Bibtex
#
# A single citation for a single tracking ID or PID can be retrieved as shown.

# %%
bibtex_citations = get_citations(
    ["hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b"],
    doi_level=DOILevel.MODEL,
    get_citation=get_bibtex_citation,
)
print(f"{len(bibtex_citations)=}")
print(bibtex_citations[0])


# %% [markdown]
# ### Plain text

# %%
plaintex_citations = get_citations(
    ["hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b"],
    doi_level=DOILevel.EXPERIMENT,
    get_citation=partial(get_text_citation, author_list_style=AuthorListStyle.LONG),
)

print(plaintex_citations[0])

# %% [markdown]
# Plain text with a short author list

# %%
plaintex_citations = get_citations(
    ["hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b"],
    doi_level=DOILevel.MODEL,
    get_citation=partial(get_text_citation, author_list_style=AuthorListStyle.SHORT),
)

print(plaintex_citations[0])
