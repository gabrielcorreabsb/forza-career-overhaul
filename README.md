<!-- docs_check: historical -->
<!-- Public README. Source: publish/public/README.md in the private lab; validated by publish.py in the export. -->
# Forza Career Overhaul

Tools and documentation to **build your own career mod** for **Forza
Motorsport (2023, Steam)**, inspired by Gran Turismo's league progression: rename,
reorder and unlock the career, create new series from a spec, and build AI grids
that are dynamic and multi-class. It works by editing the game's content cache
(CMS) and one install archive, on **your** machine, with **your** copy of the game.
Every change is reproducible and reversible (backup before every write, rollback,
post-write verification).

> Independent fan project, not affiliated with Microsoft or Turn 10. This
> repository contains **our own code and documentation only**. See
> [NOTICE](NOTICE.md).

## What is NOT in this repository

- No game files or game text, and no mod payloads. Nothing here is a ready-made
  mod you can drop in: you generate your own from the game you own.
- No CMS key and none of the [Forza Mod Tool](https://github.com/HTTPJXRDN/Forza-Mod-Tool)
  (it declares no license, so we do not redistribute any of it). You obtain both
  yourself: [THIRD_PARTY](docs/THIRD_PARTY.md).
- The maintainer's private research log, applied-kit history and frozen one-off
  generators. The method they produced is what is documented here.

## Prerequisites

- Windows, the game launched at least once (it creates the CmsCache).
- Python 3.10+ (`pip install -r requirements.txt`) and the .NET SDK named in the
  `.csproj` files (currently .NET 10).
- The Forza Mod Tool v1.3.0 and the CMS key, kept locally and git-ignored.
- Note: the cache oracle needs third-party files you must supply yourself, so a
  fresh clone cannot run `cache_edit.py` until you do
  ([THIRD_PARTY](docs/THIRD_PARTY.md)).

## Golden rules

1. **Game CLOSED** before any cache write. The game locks the files; a write
   while it is open leaves the cache inconsistent.
2. The runtime source is the **CmsCache** under
   `%LOCALAPPDATA%\Microsoft.ForzaMotorsport\CmsCache\`, not the install folder.
3. Always `--dry-run` first, then apply with `--verify`. Every apply backs up
   first. Tools refuse to run if you skip these.
4. Never commit the key, the Forza Mod Tool or copies of game files.

Modding violates the game's Terms of Use and may get you banned from online
features. Use it at your own risk.

## Create your own mod

1. Read [GETTING_STARTED](docs/en/GETTING_STARTED.md) (15 minutes, on a **copy**
   of the cache), then [CONCEPTS](docs/en/CONCEPTS.md) and [PIPELINE](docs/en/PIPELINE.md).
   Portuguese versions are in `docs/pt-br/`.
2. Generate your inventories from your own game: `python _tools\inventory.py`.
3. Write a series spec (`specs/README.md`, start from `specs/_TEMPLATE.json`) and run
   `python _tools\build_series.py --spec specs\<name>.json` to produce your kit.
4. Apply it: `python _tools\cache_edit.py --dry-run --plan patches\<kit>\plan.json`, then
   the same without `--dry-run` and with `--verify`. Undo with `python _tools\rollback_cache.py`.
5. AI grids live in the install: see the AI grid tutorial and
   [AIFIELD_GRIDS](docs/AIFIELD_GRIDS.md), applied with `_tools\install_edit.py`.

Everything is mapped in [docs/INDICE.md](docs/INDICE.md); the role of each script is in
[_tools/TOOLS.md](_tools/TOOLS.md).

## What we learned

The findings (the CmsCache is what the game runs; AI grids are pinned by an `AIField`
XML; the AI's PI follows the player through a progression band that can be widened to
span D to P; real class scale; hidden caps on events) are in
[GT_CAFE](docs/guides/GT_CAFE.md), with evidence and status. Guides by area:
[GT_MODE](docs/guides/GT_MODE.md), [CUSTOM_RACE](docs/guides/CUSTOM_RACE.md),
[CIRCUIT_EXPERIENCE](docs/guides/CIRCUIT_EXPERIENCE.md).
Kit ids such as `mc58` that appear in the docs are experiment labels from the
maintainer's lab; you do not need them.

## Contributing

See [CONTRIBUTING](CONTRIBUTING.md). Pull requests are welcome for tools and docs.
This repository is a filtered publication of a private lab, so accepted changes are
ported there by the maintainer.

## License

Code: [MIT](LICENSE). Documentation: [CC BY 4.0](LICENSE-DOCS.md). Third-party
material is not covered and not distributed: [THIRD_PARTY](docs/THIRD_PARTY.md).
