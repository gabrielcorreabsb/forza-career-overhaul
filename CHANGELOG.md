<!-- docs_check: historical -->
# Changelog

User-facing history of the tools and docs in this repository. Mod payloads are
not published here: you generate your own kits from your copy of the game.

## Unreleased

- **Docs reframed around the Forza Motorsport 4 career structure** (permanent
  event list, the right car for each event, denser entry classes, a more honest
  AI). New [PROJECT_STATUS](docs/PROJECT_STATUS.md): what works, what we learned,
  what is next.
- **Guides renamed**: `guides/DISCOVERIES.md` (findings with status) and
  `guides/CAREER_BASICS.md` (the common career).
- **GETTING_STARTED** now lists every prerequisite (.NET 10 SDK, key and Mod Tool
  sourcing, `FM_INSTALL`), shows the expected output of each step and ends with a
  before/after example. The four tutorials were re-run on a cache copy.
- **PIPELINE** is operational only: golden rules, `--dry-run` then `--verify`,
  rollback.
- **GLOSSARY** opens with a one-line-per-term table.

## Tooling

- **`build_series.py`**: new series from a JSON spec (ladder, optional cup,
  events, overrides, selectable cars, text keys).
- **`install_edit.py`**: edits one entry of the install archive and keeps the
  archive and every manifest consistent (needed for AI grids).
- **`build_aifield.py`**: AI grids in both modes, a PI-window pool or a fixed list.
- **`inventory.py`** and **`audit_career.py`**: inventories and the read-only
  career audit from your own game.
- **Safety locks**: `cache_edit.py` refuses to write with the game running,
  without a recent clean `--dry-run` or with a failing plan lint; every apply
  backs up first; `rollback_cache.py` restores the newest backup.
- **`docs_check.py`**: cited paths exist, EN/PT pairs match, the index lists
  every doc.
