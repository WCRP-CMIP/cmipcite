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
# Here we show how you can get citations for CMIP data.

# %% [markdown]
# ## Imports

# %%
from cmipcite.citations import AuthorListStyle, FormatOption, get_citations

# %% [markdown]
# ## Python API
#
# First we show how to do this via the Python API.

# %% [markdown]
# Bibtex
#
# A single citation for a single tracking ID can be retrieved as shown.

# %%
bibtex_citations = get_citations(
    ["hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b"],
    format=FormatOption.BIBTEX,
    author_list_style=AuthorListStyle.LONG,
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
    format=FormatOption.BIBTEX,
    author_list_style=AuthorListStyle.LONG,
)
print(f"Retrieved {len(bibtex_citations_multi)} citations")
print()
print("\n\n".join(bibtex_citations_multi))

# %% [markdown]
# Plain text

# %%
plaintex_citations = get_citations(
    ["hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b"],
    format=FormatOption.TEXT,
    author_list_style=AuthorListStyle.LONG,
)

print(plaintex_citations[0])

# %% [markdown]
# Plain text with a short author list

# %%
plaintex_citations = get_citations(
    ["hdl:21.14100/f2f502c9-9626-31c6-b016-3f7c0534803b"],
    format=FormatOption.TEXT,
    author_list_style=AuthorListStyle.SHORT,
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
