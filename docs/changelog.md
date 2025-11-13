# Changelog

Versions follow [Semantic Versioning](https://semver.org/) (`<major>.<minor>.<patch>`).

Backward incompatible (breaking) changes will only be introduced in major versions
with advance notice in the **Deprecations** section of releases.

<!--
You should *NOT* be adding new changelog entries to this file,
this file is managed by towncrier.
See `changelog/README.md`.

You *may* edit previous changelogs to fix problems like typo corrections or such.
To add a new changelog entry, please see
`changelog/README.md`
and https://pip.pypa.io/en/latest/development/contributing/#news-entries,
noting that we use the `changelog` directory instead of news,
markdown instead of restructured text and use slightly different categories
from the examples given in that link.
-->

<!-- towncrier release notes start -->

## CMIP Cite v0.3.0 (2025-11-13)

### ⚠️ Breaking Changes

- Changed default citations to be 'model' granularity citations rather than 'model-experiment' granularity citations.
  In practice, this means that you will get fewer citations and they will be the ones that apply to all submissions for a given model, rather than one citation for each model-experiment combination that is found. ([#7](https://github.com/WCRP-CMIP/cmipcite/pull/7))

### 🆕 Features

- - Added support for taking paths to CMIP netCDF files as input
  - Added `doi_granularity` option so users can specify whether they want citations at the model or experiment granularity

  ([#7](https://github.com/WCRP-CMIP/cmipcite/pull/7))

### 📚 Improved Documentation

- Split how-to get citations docs into basic and advanced ([#7](https://github.com/WCRP-CMIP/cmipcite/pull/7))

### 🔧 Trivial/Internal Changes

- [#10](https://github.com/WCRP-CMIP/cmipcite/pull/10)


## CMIP Cite v0.2.0 (2025-11-03)

### ⚠️ Breaking Changes

- - Changed the input arguments expected by [cmipcite.citations.get_citations][]. The old `format` and `author_list_style` should now be handled when creating the value to pass to the new `get_citation` argument. This provides finer-grained control over how citations are generated (once the DOIs and versions have been determined). For an API that closely mirrors the command-line `cmipcite get` API, see [cmipcite.citations.get][].
  - Split `cmipcite.citations.get_citation_for_id` into [cmipcite.citations.get_text_citation][], [cmipcite.citations.get_bibtex_citation][] and [cmipcite.citations.get_doi_and_version][]. This allows the process of retrieving relevant DOIs and versions to be separated from how the citations for those DOIs and versions are retrieved and formatted.

  ([#5](https://github.com/WCRP-CMIP/cmipcite/pull/5))

### 🆕 Features

- `get_citations` now works with tracking_id and PID. ([#3](https://github.com/WCRP-CMIP/cmipcite/pull/3))
- - Added [cmipcite.citations.get][] to provide a Python API which closely mirrors the command-line `cmipcite get` command ([cmipcite.citations.get_citations][] is a lower-level function which provides more flexibility to Python users looking for greater control)
  - Added the [cmipcite.tracking_id][] module to support handling of tracking IDs specifically (as opposed to PIDs)

  ([#5](https://github.com/WCRP-CMIP/cmipcite/pull/5))

### 🎉 Improvements

- - Added support for getting citations for files that are members of multiple datasets i.e. associated with multiple PIDs
  - Added the `--multi-dataset-handling` and `--handle-server-url` arguments to the `cmipcite get` CLI to add the support above and avoid hard-coding the server URL used throughout

  ([#5](https://github.com/WCRP-CMIP/cmipcite/pull/5))


## CMIP Cite v0.1.3 (2025-10-28)

No significant changes.


## CMIP Cite v0.1.2 (2025-10-27)

No significant changes.


## CMIP Cite v0.1.1 (2025-10-27)

### 🆕 Features

- Add basic `cmipcite get` command-line interface and associated Python API ([#1](https://github.com/WCRP-CMIP/cmipcite/pull/1))
