<!-- docs_check: historical -->
<!-- Public README. Source: publish/public/README.md in the private lab; validated by publish.py in the export. -->
<p align="center">
  <img src="assets/project_logo.svg" alt="Career Overhaul for Forza Motorsport" width="620">
</p>

<p align="center">
  <b>Build your own career mod for Forza Motorsport (2023, Steam)</b><br>
  modelled on the career of Forza Motorsport 4 — generated on your machine, from the game you own
</p>

<p align="center">
  <a href="docs/en/GETTING_STARTED.md">Get started</a> ·
  <a href="docs/reference/MODDING_SURFACE.md">What can be changed</a> ·
  <a href="docs/project/PROJECT_STATUS.md">Project status</a> ·
  <a href="docs/INDICE.md">All docs</a> ·
  <a href="docs/pt-br/GETTING_STARTED.md">Português</a>
</p>

---

## What this is

Tools and documentation to reshape the career of Forza Motorsport (2023): a
**permanent event list**, the **right car for each event**, a denser **entry
path** at classes E and D, a **race weekend** where practice sets the grid, and
**multi-class AI grids** that race honestly. Rename, reorder and unlock the
career, create new series from a short JSON spec, and build AI grids.

Everything works by editing the game's content cache (and, for AI grids, one
install archive) **on your machine**, with your copy of the game. Every change
is reproducible and reversible: lint, mandatory dry-run, automatic backup,
post-write verification and rollback.

> Independent fan project, not affiliated with Microsoft, Turn 10 or the Forza
> brand. This repository contains **our own code and documentation only** — no
> game files, no game text, no mod payloads. See [NOTICE](NOTICE.md).

## At a glance

| you want to… | status | start here |
|---|---|---|
| rename, reorder or unlock cups, ladders and series | verified in game | [tutorial 01](docs/tutorials/01_rename.md) · [tutorial 02](docs/tutorials/02_reorder.md) |
| create a new series from a spec | verified in game | [tutorial 03](docs/tutorials/03_new_series.md) · [SERIES_CHECKLIST](docs/reference/SERIES_CHECKLIST.md) |
| build a multi-class AI grid that follows the player | verified in game | [tutorial 04](docs/tutorials/04_ai_grid.md) · [AI_GRIDS](docs/guides/AI_GRIDS.md) |
| let practice set the starting grid | verified in game | [RACE_SYSTEM](docs/reference/RACE_SYSTEM.md) |
| change weather, time of day, tyres or fuel per event | mapped, to test | [MODDING_SURFACE](docs/reference/MODDING_SURFACE.md) |
| know what is career-only, global or out of reach | mapped | [MODDING_SURFACE](docs/reference/MODDING_SURFACE.md) |

## Start in three steps

1. **Look** — build the two oracles and read your own career data on a *copy*
   of the cache: [GETTING_STARTED](docs/en/GETTING_STARTED.md) (about 15
   minutes, never touches the game).
2. **Describe** — write a short JSON spec for the series or grid you want
   ([specs/README.md](specs/README.md), [specs/_TEMPLATE.json](specs/_TEMPLATE.json)).
3. **Apply** — `--dry-run`, then apply with `--verify` with the game closed;
   undo with `rollback_cache.py` ([PIPELINE](docs/en/PIPELINE.md)).

```powershell
python _tools\inventory.py                                   # your own game data, read-only
python _tools\build_series.py --spec specs\<name>.json       # spec -> kit
python _tools\cache_edit.py --dry-run --plan patches\<kit>\plan.json
python _tools\cache_edit.py --plan patches\<kit>\plan.json --verify
python _tools\rollback_cache.py                              # undo the last apply
```

### Prerequisites

- Windows, with the game launched at least once (it creates the CmsCache).
- Python 3.10+ (`pip install -r requirements.txt`) and the .NET 10 SDK (the two
  oracles target `net10.0`).
- The CMS key and the third-party files the cache oracle needs, obtained by you
  and kept git-ignored: [THIRD_PARTY](docs/project/THIRD_PARTY.md). A fresh clone
  cannot run `cache_edit.py` until you supply them.

## Documentation

| folder | what is inside |
|---|---|
| [`docs/en/`](docs/en/GETTING_STARTED.md) · [`docs/pt-br/`](docs/pt-br/GETTING_STARTED.md) | **Start**: getting started, concepts (cache, Strategy S, career model), the apply pipeline |
| [`docs/tutorials/`](docs/tutorials/01_rename.md) | **Step by step**: rename, reorder, new series, AI grid |
| [`docs/guides/`](docs/guides/CAREER_BASICS.md) | **By goal**: career basics, AI grids, custom multi-class races, a worked trackday series, troubleshooting |
| [`docs/reference/`](docs/reference/MODDING_SURFACE.md) | **The format**: what can be modded, career model, race system, cars and PI, field-by-field schema, data reference, series checklist, glossary |
| [`docs/data/`](docs/data/ENUMS.md) | **Tables** generated from your game: cars, tracks, classes and enum values |
| [`docs/project/`](docs/project/PROJECT_STATUS.md) | **The project**: status and roadmap, discoveries, open questions, career audit, decision records, third-party material |

The full map, by task: [docs/INDICE.md](docs/INDICE.md). The role of each
script: [_tools/TOOLS.md](_tools/TOOLS.md).

## Golden rules

1. **Game closed** before any cache write. The game locks the files; a write
   while it is open leaves the cache inconsistent.
2. The runtime source is the **CmsCache**
   (`%LOCALAPPDATA%\Microsoft.ForzaMotorsport\CmsCache\`), not the install
   folder.
3. Always `--dry-run` first, then apply with `--verify`. Every apply backs up
   first; the tools refuse to run if you skip these.
4. Never commit the key, third-party tools or copies of game files.
5. Nothing here changes online play: the project only touches what the career
   reads. Global switches, physics and the account economy are out of scope.

Modding violates the game's Terms of Use and may get you banned from online
features. Use it at your own risk.

## What is not in this repository

- Game files, game text or mod payloads: you generate your own kits from the
  game you own.
- The CMS key and any part of the
  [Forza Mod Tool](https://github.com/HTTPJXRDN/Forza-Mod-Tool) (it declares no
  license, so nothing of it is redistributed): [THIRD_PARTY](docs/project/THIRD_PARTY.md).
- The maintainer's private research log, applied-kit history and one-off
  generators. The method they produced is what is documented here.

## Contributing

Run the pipeline on a copy and report what breaks, build a series nobody tried,
or settle an [open question](docs/project/OPEN_QUESTIONS.md) — each names the
experiment that decides it. See [CONTRIBUTING](CONTRIBUTING.md), the
[CODE_OF_CONDUCT](CODE_OF_CONDUCT.md) and [SECURITY](SECURITY.md) (what never to
post). History: [CHANGELOG](CHANGELOG.md).

This repository is a filtered publication of a private lab; accepted changes
are ported there by the maintainer.

## License

Code: [MIT](LICENSE). Documentation: [CC BY 4.0](LICENSE-DOCS.md). Third-party
material is not covered and not distributed: [THIRD_PARTY](docs/project/THIRD_PARTY.md).
