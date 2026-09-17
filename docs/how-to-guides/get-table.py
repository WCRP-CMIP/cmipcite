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
# # How to get a table ?
#
# To show the data that you are using in your research,
# you can use table created by cmipcite.


# %% [markdown]
# ## Imports

# %%

from cmipcite.citations import get

# %% [markdown]
#
# cmipcite can get you a latex table with information on the data and the reference.


# %%
table = get(["hdl:21.14107/4caada9a-697f-4cfb-a898-94eedbd25dee"], format="latextable")
print(table)

# %% [markdown]
# The citation links to the label in the bibtex file.

# %%
bib = get(["hdl:21.14107/4caada9a-697f-4cfb-a898-94eedbd25dee"], format="bibtex")
print(bib)


# %% [markdown]
# Or you can also put the DOI directly, by changing the `table_columns` arg.
# This arg also allows you to choose the other column from all the dataset global attrs.

# %%
table = get(
    ["hdl:21.14107/4caada9a-697f-4cfb-a898-94eedbd25dee"],
    format="latextable",
    table_columns=["source_id", "variant_label", "version", "doi"],
)
print(table)

# %%
