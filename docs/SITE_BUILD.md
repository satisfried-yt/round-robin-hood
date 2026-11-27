# Build the multilingual RRH handbook

The Markdown sources are available in `docs/site/{de,en,fr,es,pt,it}/`. Each locale has 16 articles. RRH already includes corresponding offline HTML pages under `custom_components/round_robin_hood/frontend/guides/` with local full-text search.

To build a standalone MkDocs documentation site:

```sh
python -m pip install 'mkdocs>=1.6,<2' 'mkdocs-material>=9.7,<10' 'mkdocs-static-i18n>=1.2,<2'
python -m mkdocs build --strict
python -m mkdocs serve
```

Review all language navigation menus, cross-article links, search, responsive layout and safety notes before hosting the output. Site hosting or deployment requires the repository owner's approval.

Markdown sources are generator-neutral; choose a maintained generator before setting up long-term publishing.


## Keeping the release handbook in sync

For every feature release, update both the Markdown sources in `docs/site/{de,en,fr,es,pt,it}/` and the bundled, offline HTML pages and `search-index.js` files in `custom_components/round_robin_hood/frontend/guides/{lang}/`. They are distinct published copies: a website build does not automatically regenerate the integration's embedded handbook. Run `python tests/docs_093_check.py`, `python -m unittest discover -s tests -p 'test_*.py' -q`, and `python -m mkdocs build --strict` before release. Version 0.9.5 updates the setup, consumer, profile, condition, FAQ, installation and troubleshooting guides in all six languages.
