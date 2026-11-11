<!-- docs_check: historical -->
<!-- Public README. Source: publish/public/README.md in the private lab; validated by publish.py in the export. -->
<p align="center">
  <img src="assets/project_logo.svg" alt="Career Overhaul for Forza Motorsport" width="620">
</p>

<p align="center">
  <b>A career mod for Forza Motorsport (2023, Steam), in the making</b><br>
  Forza Motorsport 4 meets Gran Turismo 4 — and the tools to build it on your machine, from the game you own
</p>

<p align="center">
  <a href="docs/en/PROGRESS.md">Progress</a> ·
  <a href="docs/guides/CAREER_MOD.md">The career mod</a> ·
  <a href="docs/en/GETTING_STARTED.md">Build your own</a> ·
  <a href="docs/en/MOD_TOOLKIT.md">What the mod can do</a> ·
  <a href="docs/INDICE.md">All docs</a> ·
  <a href="docs/pt-br/PROGRESS.md">Português</a>
</p>

---

## What this is

**The career mod.** The goal is a career that takes the best of two games: the
**permanent event list**, the right car for each event and one-make series of
**Forza Motorsport 4**, and the **climb from the entry classes** of **Gran Turismo
4**, with short cheap races in ordinary cars first. It is built piece by piece, and
each piece is tested in game before it counts. Nothing is distributed ready to
install: you generate your own changes with the tools here.

**The toolkit.** Rename, reorder and unlock the career, create new series (several
events each) from a short JSON spec, and build AI grids: one roster per class, per
make, or a closed pool of hand-picked models. Everything works by editing the
game's content cache **on your machine**, with your copy of the game, and every
change is reproducible and reversible: lint, mandatory dry-run, automatic backup,
post-write verification and rollback.

> Independent fan project, not affiliated with Microsoft, Turn 10 or the Forza
> brand. This repository contains **our own code and documentation only** — no
> game files, no game text, no mod payloads. See [NOTICE](NOTICE.md).

## Where we are

Phase by phase, with the evidence: [PROGRESS](docs/en/PROGRESS.md).

**New since v0.2.0**

- **The game reads the AI roster from the cache**, so AI grids are rebuilt with the
  normal apply tool, with no install edits.
- **Series with several events** run in sequence, add up points and close at the last
  event.
- **Class and make grids**: one roster per class keeps the AI in your class; a closed
  pool of chosen models gives a grid of only those models.
- **Own pools at scale**: a vanilla roster document with an identical copy can be freed
  and reused (313 candidates).
- **A first season of our own** ("German Ovals", 6 series in 3 groups, in a cup of its
  own) is in game; the first group is played.
- **Prizes belong to the server.** Credits and cars are granted against the server's
  own challenges; editing payout tables or challenge conditions changes only what the
  screens show. The career pays through race length, unlocks by progression and live
  vanilla challenges ([ECONOMY_MAP](docs/reference/ECONOMY_MAP.md)).

| stage | what the player gets | state |
|---|---|---|
| Own place in the career | a cup and ladder of our own; renamed, reordered, unlocked | verified in game |
| Spec races | 23 AI of one model against you | verified in game |
| Trackday | pick a circuit, any class, rolling start | verified in game |
| Start type and start slot per event | standing or rolling; a free pick or last on the grid | verified / observed |
| Honest multi-class AI | a pool that follows your PI, or a fixed list D to R | verified in game |
| AI per class or make | a roster per class; a closed pool of chosen models | verified in game |
| Series with several events | a season-like series with accumulated points | verified in game |
| Progression gates | a series or group opens only after another is done | verified in game |
| Race weekend | practice orders the AI's grid; the generator decides where you start | observed |
| Practice length, weather, time of day, pit stop, field size | set per event | observed |
| A first own season | cup of our own, groups that unlock in order | in progress |
| Entry ladder (E and D) | short series for the cars the career never lists | planned |
| One-make and period series | one manufacturer, decade or country | planned (the pool mechanism is proven) |
| Wear, fuel, tyre compound | the career's own wear, fuel and compound | to test |
| Prizes of our own, real qualifying | — | closed: the server grants prizes; no data field selects a qualifying |

## At a glance

| you want to… | status | start here |
|---|---|---|
| rename, reorder or unlock cups, ladders and series | verified | [tutorial 01](docs/tutorials/01_rename.md) · [tutorial 02](docs/tutorials/02_reorder.md) |
| create a new series from a spec | verified | [tutorial 03](docs/tutorials/03_new_series.md) · [SERIES_CHECKLIST](docs/reference/SERIES_CHECKLIST.md) |
| build an AI grid (class, make, chosen models) | verified | [tutorial 04](docs/tutorials/04_ai_grid.md) · [AI_GRIDS](docs/guides/AI_GRIDS.md) |
| race against 23 cars of one model | verified | [AI_GRIDS](docs/guides/AI_GRIDS.md) §6 |
| let practice set the starting grid, choose where you start | verified / observed | [RACE_SYSTEM](docs/reference/RACE_SYSTEM.md) |
| set practice length, weather, start type per event | observed | [RACE_SYSTEM](docs/reference/RACE_SYSTEM.md) |
| understand how the career pays | mapped | [ECONOMY_MAP](docs/reference/ECONOMY_MAP.md) |
| see every lever and how sure we are | mapped | [MOD_TOOLKIT](docs/en/MOD_TOOLKIT.md) · [MODDING_SURFACE](docs/reference/MODDING_SURFACE.md) |

Every finding is tested in game, not guessed from file names; the evidence and its
status (verified, observed, to test) are in [DISCOVERIES](docs/project/DISCOVERIES.md).

**What this does not do.** It does not touch online play, physics or the account
economy. Steam's *verify files* or a new server snapshot can undo edits; run the
tools again (kits are reproducible). A new CMS file with an invented id is rejected
by the game, so custom content reuses existing slots. Findings marked *observed*
rest on one or two runs: if yours differs, open an issue with the numbers
([CONTRIBUTING](CONTRIBUTING.md)).

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
| [`docs/en/`](docs/en/GETTING_STARTED.md) · [`docs/pt-br/`](docs/pt-br/GETTING_STARTED.md) | **Start**: getting started, concepts, the apply pipeline, the mod toolkit, progress |
| [`docs/tutorials/`](docs/tutorials/01_rename.md) | **Step by step**: rename, reorder, new series, AI grid |
| [`docs/guides/`](docs/guides/CAREER_MOD.md) | **By goal**: the career mod, career basics, AI grids, custom multi-class races, a trackday series, troubleshooting |
| [`docs/reference/`](docs/reference/MODDING_SURFACE.md) | **The format**: what can be modded, career model, race system, cars and PI, schema, economy, glossary |
| [`docs/data/`](docs/data/ENUMS.md) | **Tables** generated from your game: cars, tracks, classes and enums |
| [`docs/project/`](docs/project/PROJECT_STATUS.md) | **The project**: status, discoveries, open questions, career audit, decisions, third-party material |

The full map, by task: [docs/INDICE.md](docs/INDICE.md). The role of each script:
[_tools/TOOLS.md](_tools/TOOLS.md).

**For AI agents:** start at [okf/index.md](okf/index.md), an
[Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf)
bundle of the rules, tools, specs and docs, with one index per folder. It is
generated; do not edit it by hand.

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
