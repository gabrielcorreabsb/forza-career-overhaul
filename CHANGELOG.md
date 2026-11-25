<!-- docs_check: historical -->
# Changelog

User-facing history of the tools and docs in this repository. Mod payloads are
not published here: you generate your own kits from your copy of the game.

## Unreleased

- **The game database and own tracks that pay** (findings D128–D149 in [DISCOVERIES](docs/project/DISCOVERIES.md)): an edited row of the installed gamedb takes effect (a car's hood camera, a track's pit-lane limit and rolling-start speed); part prices in car points can be zeroed from the cache; the gamedb's AI tables, car prices, the affinity discount and the driver-level milestone credit do not act or are checked by the server. For tracks: a new track id earns nothing, the event's track field picks the track that loads and the pay, and the server pays only the ids of the game's credit/XP tables, so a track of our own earns behind one of those ids. PROGRESS (both languages) has Phases 0.12 and 0.13. Documentation only.

- **AI statics documented** ([AI_STATICS](docs/reference/AI_STATICS.md)): the six keys of the install's AI tuning file we changed, with direction and evidence (D76, D77); the file and its editing tool are not distributed.
- **README reorganised**: what the repository is, an at-a-glance table and the three-step quick start now come first; "Proven in game" is condensed (the detail stays in PROGRESS and DISCOVERIES); the visual-mods section has its own picture and a short table by area.
- **Install-only visual modifications** ([INSTALL_VISUAL_MODS](docs/reference/INSTALL_VISUAL_MODS.md), [MEDIA_MAP](docs/reference/MEDIA_MAP.md)): the file map of the install's `media\`, a list of what we changed (render, LOD, track look, camera, photo-mode watermark), one tool for the loose-XML changes (`graphics/apply_kit.py`: dry-run, backup, restore; the zip edits are documented, their tool is not published), and the rule that a rewritten zip keeps every entry at its offset ([D120](docs/project/DISCOVERIES.md)). Camera settings credited to GmSV2's Better Photo mode ([NOTICE](NOTICE.md)).
- **Own intro videos and the install's file index** (findings D105–D113 in [DISCOVERIES](docs/project/DISCOVERIES.md)): a
  series intro is a 3D scene picked by the video's name, or, with `PlayIntroVideoFullScreen`, the video file itself; the
  game reads only the install files listed in `hash.manifest`, whose path hash is now known and rebuilt for every record;
  a new video under its own name plays once indexed, and a clip we encoded to Bink 2 (`KB2j`) ran in game, with sound from one side only (D114, D118); `encode_intro.py` goes from an MP4 to an installed, indexed video in one command, with a standard preset (quantiser 8, audio quality 10), and only creates new files; `hash_manifest_edit.py --remove` drops records it added. New tools `bk2_install.py` and `hash_manifest_edit.py`; new references
  [INTRO_VIDEO](docs/reference/INTRO_VIDEO.md) and [INSTALL_INDEX](docs/reference/INSTALL_INDEX.md); GETTING_STARTED step 8,
  PROGRESS, MOD_TOOLKIT, README and a diagram (`assets/intro_video_pipeline.svg`). The first-car screen fails on our series:
  keep it off. `build_series --round` gains the `set_cup` and `set_series` ops.

- **Cups, ladders, texts and locks, tried in game** (findings D86–D97 in [DISCOVERIES](docs/project/DISCOVERIES.md)): year and PI ranges cut the list of cars a series offers (with an empty blocklist and class Any), a blocklist and a class filter act and intersect with an accept list; 0 practice laps give a timed free practice of 10 minutes; the AI's catch-up, slow-down and proximity switches each change the field when turned off (position spread does not); the points table of an event decides the series points by finishing position; the practice clock opens at any hour and minute and a stop can be demanded per event; a series locked by another series, a ladder or an event shows **our own text** on its card (up to 249 characters; an empty value shows the game's missing-text marker), while a lock by driver level always shows the game's message. What does **not** work: the description of a series, a ladder and a cup is not drawn by any career screen, a cup's practice limit and a ladder's label show nothing, and emptying a ladder's completion list showed nothing. The round builder gained `description` and `lock_text` for series, a group description and a cup description (documented in `specs/README.md`). PROGRESS and MOD_TOOLKIT (both languages), SCHEMA_REFERENCE, the README and the progress panel updated. Localization of the new texts into the other 20 languages is decided for the mod's release. Documentation and tools only.

- **Covering the values** (findings D81–D85 in [DISCOVERIES](docs/project/DISCOVERIES.md)): every field a series, an event and its override can set was tried in game in a bench of one-field series. Laps, start time, the clock-speed pair, the start type, the performance cap in the override, weather by forecast id, the build-phase skip and the event and series gates work; the open class, the slot counts, a 30-minute practice and the skip-lap flag do nothing; the career has no qualifying; some generators drop the connection and an empty roster document crashes the race. PROGRESS and MOD_TOOLKIT (both languages) and the value map updated. Documentation only.

- **The AI standard** (findings D76–D80 in [DISCOVERIES](docs/project/DISCOVERIES.md)): narrowing the AI's per-driver speed band
  (two global keys of the AI statics file) cut the AI's off-track errors on Brands Hatch GP and held on Lime Rock, an oval and
  class A; a higher off-track speed limit makes the AI recover faster; a levelled field at the class ceiling puts all 23 AI cars at
  one PI in class S and class A, with the model still setting the pace; the series' AI difficulty label and slot count do not act;
  a new per-track file in the AI statics zip is read by the game. PROGRESS and MOD_TOOLKIT (both languages) updated. Documentation only.
- **Limits written down** (finding D75 in [DISCOVERIES](docs/project/DISCOVERIES.md)): car level, car points and their price belong to the online service, and a career on a server of our own is not possible and not supported (the game checks a signature on every answer); anyone who tries it does so at their own risk. README, MOD_TOOLKIT (both languages) and ECONOMY_MAP updated. Documentation only.

- **README rewritten around what is proven in game**: a "Proven in game" opening, status badges, a progress panel and a diagram of the
  first own season (both drawn by us, in `assets/`; no game material), the try-it commands moved up. Documentation only.

- **A second season, built on the game's challenges** (findings D68–D71 in [DISCOVERIES](docs/project/DISCOVERIES.md)): own AI
  pools work at every size tried (4 to 37 models, one theme each); a series of ours counts toward the game's live challenges one
  for one, the progress lives on the server and finishing one pays the real prize (a Mustang, a Nissan earned at Suzuka, a
  Ferrari 488 GTB at Daytona); a track-only challenge (a segment score at Daytona) counts by the track alone and paid a Porsche;
  a 46-slot roster document still showed 24 drivers. A cup of five groups, one per live challenge, is in game, two groups played. README, PROGRESS,
  MOD_TOOLKIT, CAREER_MOD and the two diagrams updated. Documentation only.
- **Phase 0.3 — an own season** (findings D60–D67 in [DISCOVERIES](docs/project/DISCOVERIES.md)): the game reads the AI roster
  from the **cache**, so AI grids are written with `cache_edit.py` (`build_aifield.py --cache-plan`); a series with **several events**
  runs in sequence and accumulates points; one roster per class keeps the AI in the player's class; a closed pool of chosen models gives
  a grid of only those models, while a series' own car list does not filter the roster; a vanilla roster document with an identical copy
  can be **freed** and reused as a pool of ours. A first season of our own (a cup, three groups that unlock in order) is in game.
  The game's PI scale (C 500 … R 900) is not the catalogue's PI column.
- **Phase 0.2 — rewards**: prizes belong to the server. Edited challenge conditions mark the row completed but nothing is paid, and
  payout rates and bonuses in the install's tunable files changed nothing; live vanilla challenges do count races run in our series.
  [ECONOMY_MAP](docs/reference/ECONOMY_MAP.md) §5.
- **Docs consolidated**: `PROJECT_STATUS` is now part of [PROGRESS](docs/en/PROGRESS.md) (the next steps and how to help are there),
  `CUSTOM_RACE` is part of [AI_GRIDS](docs/guides/AI_GRIDS.md) (§8, choosing and a test protocol) and `CIRCUIT_EXPERIENCE` is part of
  [CAREER_MOD](docs/guides/CAREER_MOD.md) (the trackday example). The answered open questions (lap count, the start slot, where the
  credits come from) are now short answers.
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
