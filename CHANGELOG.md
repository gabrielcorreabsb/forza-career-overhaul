<!-- docs_check: historical -->
# Changelog

User-facing history of the tools and docs in this repository. Mod payloads are
not published here: you generate your own kits from your copy of the game.

## Unreleased

- **Phase 0.3 — an own season** (findings D60–D67 in [DISCOVERIES](docs/project/DISCOVERIES.md)): the game reads the AI roster
  from the **cache**, so AI grids are written with `cache_edit.py` (`build_aifield.py --cache-plan`); a series with **several events**
  runs in sequence and accumulates points; one roster per class keeps the AI in the player's class; a closed pool of chosen models gives
  a grid of only those models, while a series' own car list does not filter the roster; a vanilla roster document with an identical copy
  can be **freed** and reused as a pool of ours. A first season of our own (a cup, three groups that unlock in order) is in game.
  The game's PI scale (C 500 … R 900) is not the catalogue's PI column.
- **Phase 0.2 — rewards**: prizes belong to the server. Edited challenge conditions mark the row completed but nothing is paid, and
  payout rates and bonuses in the install's tunable files changed nothing; live vanilla challenges do count races run in our series.
  [ECONOMY_MAP](docs/reference/ECONOMY_MAP.md) §5.
- **New [PROGRESS](docs/en/PROGRESS.md)** (English and Portuguese): the project's timeline by phase. The README is shorter and points
  to it. Documentation only: nothing new is distributed.

- **Economy tests (status so far: the cache's payout tables only changed the interface; the session generator's mandatory stop changed the credits paid)**: the credits come as parcels (practice, race finish, VIP, difficulty, rule set); the career base cell of a track and car class
  and the cup's wager table, edited one at a time, changed what the screens showed but **not** the credits paid, and the start slot did not
  either. A mandatory stop demanded by the session generator lowered the credits in a one-field check (550 against 800 for the race parcel, same
  series and finish). Updated
  [ECONOMY_MAP](docs/reference/ECONOMY_MAP.md), [DISCOVERIES](docs/project/DISCOVERIES.md) D55–D58, [MODDING_SURFACE](docs/reference/MODDING_SURFACE.md)
  and [MOD_TOOLKIT](docs/en/MOD_TOOLKIT.md).

- **Test batteries 3 and 4: where you start, how long you practise, weather, small fields.** New findings (evidence in
  [DISCOVERIES](docs/project/DISCOVERIES.md) D46–D53): the session generator's grid shape decides where you start (a free pick, first,
  or last; the project fixes a free start and a start at the back, [ADR-006](docs/project/decisions/ADR-006_grid_start_shapes.md));
  practice laps are the event's required laps, apart from the race laps; weather and time of day apply to the race only; races with 8,
  12 and 16 cars run; a mandatory stop is a per-event switch. Not found: a regulation of the online series on a career generator had
  no visible effect, and a zero practice budget removed the practice only in the Trackday.
- **New [ECONOMY_MAP](docs/reference/ECONOMY_MAP.md)**: how the career pays credits and prizes (base per track and class, global scalars,
  the wager bonus per cup, prizes tied to vanilla series), and which pieces a series kit can reach.
- **Client flags surveyed** (read-only): 417 settings in 53 blocks, 12 of them career-named; the wager-screen flag is one global switch,
  with no series or cup scope ([SCHEMA_REFERENCE](docs/reference/SCHEMA_REFERENCE.md) Part 3).
- **Updated [MOD_TOOLKIT](docs/en/MOD_TOOLKIT.md)** (English and Portuguese), [CAREER_MOD](docs/guides/CAREER_MOD.md), the README and
  the open questions with the above. Documentation only: nothing new is distributed.

- **New [CAREER_MOD](docs/guides/CAREER_MOD.md)** and a README reframed around
  it: the career mod we are building (Forza Motorsport 4 × Gran Turismo 4), its
  stages with their state, and the series that already run as worked examples.
  The toolkit becomes the second level ("build your own"). Documentation only:
  nothing new is distributed.

- **README now explains the findings in play terms**: who you race against
  (pool vs fixed list, custom single-car rosters, how far the AI sits from
  you), how an event starts (no real qualifying, practice and the wager, start
  type) and the limits. New rows in "At a glance". Evidence stays in
  [DISCOVERIES](docs/project/DISCOVERIES.md) D34–D41.

- **Docs restructured by purpose**: `docs/guides/` (by goal), `docs/reference/`
  (the format), `docs/project/` (status, discoveries, open questions,
  decisions) and `docs/data/` (generated tables). New README with the project
  logo and a map of the docs.
- **New [MODDING_SURFACE](docs/reference/MODDING_SURFACE.md)**: what can be
  changed in the game, area by area — where it is read, the format, the tool,
  whether it reaches only the career or the whole game, and how sure we are.
- **New [AI_GRIDS](docs/guides/AI_GRIDS.md)** (merges `AI_AND_GRIDS` and
  `AIFIELD_GRIDS`) and **[SERIES_CHECKLIST](docs/reference/SERIES_CHECKLIST.md)**
  (replaces `F3_TEMPLATE`).
- **New [data/ENUMS](docs/data/ENUMS.md)**: car classes and the enum values
  seen in your own game data, generated by `audit_career.py`.
- **Findings**: race length comes from the event override; the cap a player
  sees comes from the event's `TargetPI`; limited practice laps set the starting
  grid; the client reads its feature flags from the cache
  ([DISCOVERIES](docs/project/DISCOVERIES.md) D28–D32).
- **Fix**: `cache_verify.py` and `rollback_cache.py` no longer use a hardcoded
  folder; they resolve paths from their own location.
- **Docs reframed around the Forza Motorsport 4 career structure** (permanent
  event list, the right car for each event, denser entry classes, a more honest
  AI). New [PROJECT_STATUS](docs/project/PROJECT_STATUS.md): what works, what we learned,
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
