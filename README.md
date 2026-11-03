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
  <a href="docs/guides/CAREER_MOD.md">The career mod</a> ·
  <a href="docs/en/GETTING_STARTED.md">Build your own</a> ·
  <a href="docs/reference/MODDING_SURFACE.md">What can be changed</a> ·
  <a href="docs/project/PROJECT_STATUS.md">Project status</a> ·
  <a href="docs/INDICE.md">All docs</a> ·
  <a href="docs/pt-br/GETTING_STARTED.md">Português</a>
</p>

---

## What this is

**The career mod.** The goal is a career that takes the best of two games: the
**permanent event list**, the right car for each event and one-make series of
**Forza Motorsport 4**, and the **climb from the entry classes** of **Gran Turismo
4**, with short cheap races in ordinary cars first. It is built piece by piece, and
each piece is tested in game before it counts. Where it stands, stage by stage, is
below; the full picture is in [CAREER_MOD](docs/guides/CAREER_MOD.md). Nothing is
distributed ready to install: you generate your own changes with the tools here.

**The toolkit.** Tools and documentation to reshape the career of Forza Motorsport (2023): a
**permanent event list**, the **right car for each event**, a denser **entry
path** at classes E and D, a **race weekend** where practice sets the grid, and
**multi-class AI grids** that race honestly. Rename, reorder and unlock the
career, create new series from a short JSON spec, and build AI grids.

Everything works by editing the game's content cache (and, for AI grids, one
install archive) **on your machine**, with your copy of the game. Every change
is reproducible and reversible: lint, mandatory dry-run, automatic backup,
post-write verification and rollback.

**Why it might interest you.** We opened up how the career really works, and
tested it in game:

- a **23-car spec race** (all Porsche 911 GT3 RS '23, or all Subaru BRZ '22) is
  a data edit away;
- the **AI's pace and class follow rules you can set**, per series, instead of
  one recipe for the whole career;
- **practice can set the AI starting grid**, and the Challenge the Grid wager
  sets yours, since the career has no real qualifying;
- **209 of 711 cars are in no event** — the entry classes (E, D) are the
  emptiest part of the career, and a series can be built to fill them.

What we found and how it changes what you play:
[below](#what-we-have-found-and-what-it-changes-when-you-play).

> Independent fan project, not affiliated with Microsoft, Turn 10 or the Forza
> brand. This repository contains **our own code and documentation only** — no
> game files, no game text, no mod payloads. See [NOTICE](NOTICE.md).

## The career mod: where we are

| stage | what the player gets | state |
|---|---|---|
| Own place in the career | a cup and ladder of our own; renamed, reordered, unlocked | verified in game |
| Spec races | 23 AI of one model against you | verified in game |
| Trackday | pick a circuit, any class, rolling start | verified in game |
| Start type per event | standing or rolling, chosen event by event | verified in game |
| Honest multi-class AI | a pool that follows your PI, or a fixed list D to R | verified in game |
| Race weekend | practice orders the AI's grid; the generator decides where you start | observed |
| Start slot per event | a free pick of your slot, or a forced start at the back of the grid | observed |
| Practice length per event | 1 to 5 practice laps, apart from the race laps | observed |
| Entry ladder (E and D) | short series for the cars the career never lists | planned |
| One-make and period series | one manufacturer, decade or country | planned |
| Weather and time of day per event | a set forecast and start hour for the race (heavy rain, a night start) | observed |
| Mandatory pit stop | demanded of the AI and of you when the event asks for it | observed |
| Small and mid-size fields | races with 8, 12 and 16 cars run | observed |
| How the career pays | payout, bonus and prizes mapped; no per-series payout field | mapped |
| Wear, fuel, tyre compound | the career's own wear, fuel and compound | to test |

Series that already run, with what each proves:
[CAREER_MOD](docs/guides/CAREER_MOD.md) §3.

## At a glance

| you want to… | status | start here |
|---|---|---|
| rename, reorder or unlock cups, ladders and series | verified in game | [tutorial 01](docs/tutorials/01_rename.md) · [tutorial 02](docs/tutorials/02_reorder.md) |
| create a new series from a spec | verified in game | [tutorial 03](docs/tutorials/03_new_series.md) · [SERIES_CHECKLIST](docs/reference/SERIES_CHECKLIST.md) |
| build a multi-class AI grid that follows the player | verified in game | [tutorial 04](docs/tutorials/04_ai_grid.md) · [AI_GRIDS](docs/guides/AI_GRIDS.md) |
| let practice set the starting grid | verified in game | [RACE_SYSTEM](docs/reference/RACE_SYSTEM.md) |
| race against 23 cars of one model (spec races) | verified in game | [AI_GRIDS](docs/guides/AI_GRIDS.md) §6 |
| point an event at a different AI roster | verified in game (one run) | [DISCOVERIES](docs/project/DISCOVERIES.md) D37 |
| choose a standing or rolling start | observed | [RACE_SYSTEM](docs/reference/RACE_SYSTEM.md) §2.8 |
| choose where you start: a free pick, or last on the grid | observed | [RACE_SYSTEM](docs/reference/RACE_SYSTEM.md) §2.17 · [ADR-006](docs/project/decisions/ADR-006_grid_start_shapes.md) |
| set the practice length of an event | observed | [RACE_SYSTEM](docs/reference/RACE_SYSTEM.md) §2.4 |
| change weather and time of day for the race | observed | [RACE_SYSTEM](docs/reference/RACE_SYSTEM.md) §2.16 |
| understand how the career pays credits and prizes | mapped | [ECONOMY_MAP](docs/reference/ECONOMY_MAP.md) |
| change tyres or fuel per event | mapped, to test | [MODDING_SURFACE](docs/reference/MODDING_SURFACE.md) |
| know what is career-only, global or out of reach | mapped | [MODDING_SURFACE](docs/reference/MODDING_SURFACE.md) |

## What we have found, and what it changes when you play

Every row is something we tested in the game, not guessed from file names. The
evidence and the status of each finding (verified, observed, to test) are in
[DISCOVERIES](docs/project/DISCOVERIES.md); the full lever map is
[MOD_TOOLKIT](docs/en/MOD_TOOLKIT.md).

### Who you race against

- **The AI grid lives in one XML, not in the series' car list.** Editing the
  list of cars a series offers does not change who you race. The grid comes
  from an *AI roster document*, and that is the file this project edits.
- **Two kinds of grid.** A **pool** keeps the AI close to your car: its PI sits
  about 10–50 below yours, so the difficulty follows what you drive. A **fixed
  list** pins the field whatever you bring: a real multi-class grid from D to R,
  good for trackday, endurance and showcase events.
- **A pool larger than the grid gives a different field every race**, and a wide
  PI band is accepted, so one series can mix four to seven classes without
  repeating itself.
- **Spec races work.** Writing a roster of 23 cars of a single model gave a
  lobby of exactly that: a Subaru BRZ '22 in one series, a Porsche 911 GT3 RS
  '23 in another. Pointing an event at a different roster document changes its
  lobby. Limits: each roster needs an existing, unused document to overwrite
  (a brand-new file made the game go offline), and a car needs AI tune files to
  be eligible.
- **How far the AI sits from you is set by the roster's own PI band table**, not
  by the event's performance cap. An event capped at 300 still met AI at
  400–412. To keep the field in your class, choose the window floor and a
  narrow band.
- **The lobby badge is the car's real class; the number is the target PI.** A
  roster whose cars have a high lowest tune will show, say, B-class cars listed
  at 400–412 running at their B tune. Pick cars whose lowest tune is at or below
  the window floor.
- **A spec race is fairest with the event cap equal to the top of the window,
  and you at the cap.** With a ±10 band and the player below the ceiling, two
  cars ran away and the rest bunched in two packs; with the player at PI 800
  and the window maximum at 800, the whole field finished between 792 and 800.
  The spread came from the PI band, not from driver skill.
- **The AI is not flattened.** The vanilla catch-up and slow-down flags are on,
  yet faster cars still pull away from slower ones, so class gaps are real.
- **Expect one warm-up race.** The first race after an install change tends to
  reuse the previous grid's cars while the PI is recomputed.

### How an event starts and ends

- **There is no real qualifying in the career.** The client has a qualifying
  activity, but no career data field turns it on; four separate one-field tests
  changed nothing.
- **Practice orders the AI.** The race grid lines the **AI** up in practice order.
- **Where you start is decided by the session generator's grid shape**, not by the series. With an estimated-lap-time order and no start
  index, the slot you pick on the *Challenge the Grid* wager screen is obeyed. With rank order, an index of 0 to 5 puts you first and an
  index of 6 or more puts you **last** (24th of 24, 8th of 8), with no middle slot and whatever your lap. A qualifying order gives a
  mid-grid value that moves with the field, the AI roster and your car. The project uses the first two
  ([ADR-006](docs/project/decisions/ADR-006_grid_start_shapes.md)).
- **Practice length is the event's `NumberOfRequiredLaps`**, kept apart from the race laps: 1 and 5 practice laps ran with a 2-lap race,
  and the series' own lap limits do nothing. Setting the practice budget to zero removed the practice only in the Trackday.
- **Weather and time of day apply to the race only.** Heavy rain and a night start ran; the practice keeps its own settings.
- **A mandatory pit stop is a per-event switch** (`Pits`): on, it is demanded; off, the race ends without one.
- **Small fields run.** Races with 8, 12 and 16 cars started and finished.
- **Standing or rolling start** is decided by the session generator, not by the
  series' slot-car-start flag.
- **Race length comes from the event override**, and the **cap you see comes
  from the event's `TargetPI`**: one number opens or closes a series to higher
  classes (a cap of 700 held a series at A until it was raised).

### How the career pays

- **The payout is a base per track and car class, multiplied by global scalars** (AI difficulty, damage, rewinds, finish position).
  Only the base has a career-only table. There is no payout field for a single series.
- **Prizes come from each vanilla series' own challenges**; a brand-new series has none, so a prize car cannot be attached to a new series.
- **The wager bonus table lives on the cup**, so it applies to every series of that cup.
- Details and the cheapest tests: [ECONOMY_MAP](docs/reference/ECONOMY_MAP.md).

### Who can enter, and the career's shape

- **209 of the 711 cars appear in no event's accept list**, and the entry
  classes are the worst served (E: 31 of 50 cars used, D: 50 of 106). That is
  the gap a denser entry path fills.
- **New series are safe if they use fresh ids** and their own car block; the
  poster, banner and intro come from the series you copy.
- **Rename, reorder and unlock** change only the career tree; championship 1
  (multiplayer) is untouched.

### What this does not do

- It does not touch online play, physics or the account economy.
- Steam's *verify files* or a new server snapshot can undo install edits; run
  the tools again (the kits are reproducible).
- A new CMS file with an invented id is rejected by the game. Custom content
  needs an existing slot.
- A regulation of the online series put on a career generator showed no visible effect.
- Findings marked *observed* rest on one or two runs. If your result differs,
  open an issue with the numbers: see [CONTRIBUTING](CONTRIBUTING.md).

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
| [`docs/guides/`](docs/guides/CAREER_MOD.md) | **By goal**: the career mod, career basics, AI grids, custom multi-class races, a worked trackday series, troubleshooting |
| [`docs/reference/`](docs/reference/MODDING_SURFACE.md) | **The format**: what can be modded, career model, race system, cars and PI, field-by-field schema, data reference, series checklist, glossary |
| [`docs/data/`](docs/data/ENUMS.md) | **Tables** generated from your game: cars, tracks, classes and enum values |
| [`docs/project/`](docs/project/PROJECT_STATUS.md) | **The project**: status and roadmap, discoveries, open questions, career audit, decision records, third-party material |

The full map, by task: [docs/INDICE.md](docs/INDICE.md). The role of each
script: [_tools/TOOLS.md](_tools/TOOLS.md).

**For AI agents:** start at [okf/index.md](okf/index.md), an
[Open Knowledge Format](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf)
bundle of the rules, tools, specs and docs, with one index per folder so you can
descend one level at a time instead of loading everything. It is generated; do
not edit it by hand.

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
