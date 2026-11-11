# Modding surface — what can be changed in Forza Motorsport (2023)

The map of what this project can change in the game. For each area it answers:
**where does the game read it, in what format, how do we write it, what does a
change reach, and how sure are we?** It holds no game values and no game text,
only names, places, tools and status. It comes from a read-only survey of the
cache, the install and the game database, done in the maintainer's lab.
Field-level detail: [SCHEMA_REFERENCE](SCHEMA_REFERENCE.md); enum and id tables:
[data/ENUMS](../data/ENUMS.md), [data/CARS](../data/CARS.md),
[data/TRACKS](../data/TRACKS.md).

## 1. Status labels

| label | meaning |
|---|---|
| **verified** | changed by a kit and the effect was seen in game |
| **observed** | seen in game or in data, but the cause is not isolated (or n=1) |
| **hypothesis** | a readable, writable field whose effect is not tested yet |
| **closed** | cannot be written today (no codec, no tool), or off-limits by project rule |

**Scope** says what a change reaches. **career** means championship 500 only.
**Featured** means championship 1, which is online. **global** means every
mode, multiplayer included. The project rule is that nothing global that
touches multiplayer ships without a discussion first.

## 2. Where the game reads things (the layers)

| layer | what it is | how we write it | notes |
|---|---|---|---|
| **CmsCache (live)** | `%LOCALAPPDATA%\Microsoft.ForzaMotorsport\CmsCache\`: encrypted payloads in content-addressed blobs, listed by the `prod\<snapshot>` manifest | `_tools/cache_edit.py` (plan → `--dry-run` → apply `--verify`), Strategy S | the runtime source for every CMS file that has a local blob. Only a minority of manifest entries have a local blob; the rest are fetched on demand, and editing those has no effect |
| **install-cms** | the CMS zips under the install's `media\pcfamily\cms\`, for content groups with no cache blob (e.g. AI grids) | `_tools/install_edit.py` (rewrites the zip and the install and cache manifest chain, with backup and restore) | the seed copies of groups that *do* have a cache blob are ignored at runtime (`docs/project/decisions/ADR-004_install_vs_runtime.md`) |
| **install, loose or readable zip** | plain XML/JSON/INI under `media\` (render presets, per-track settings, string tables, tunables) | no tool yet: needs a file-swap tool with backup and restore | Steam "verify files" undoes it; integrity coverage is unknown (section 12) |
| **install, encrypted container** | asset container with its own key (physics, prizes, unlocks, part of the tunables, install copies of the client flags and weather) | **closed**: this project does not write it | not needed for the career; nothing from it is in this repository |
| **gamedb** | the game database under `media\base\db\` | **closed** for writing | read-only reference (car attributes, upgrade tables, AI tuning tables); `inventory.py` reads it |
| **executable** | client defaults for optional config blocks | not modded | its string tokens show config keys that the data never sets |

Payload codec, Size/Checksum model and the Strategy S rule:
`docs/en/CONCEPTS.md` and `docs/en/PIPELINE.md`.

## 3. Career (championship 500)

| what | where the game reads it | format | how to write | scope | status |
|---|---|---|---|---|---|
| cup → ladder → series → event tree, order, names, art | `BuildersCupScheduleDataV4.json` (cache) | JSON | `_tools/build_series.py` (spec) or a `cache_edit` plan | career | **verified** (new series, reorder, renames) |
| per-event overrides (track, laps, AI grid file, generator) | `BCEventOverrides.json` (cache) | JSON list keyed by event id | `build_series.py` / `cache_edit` | career | **verified** |
| car eligibility per series | `BCSeriesSelectableCars.xml` (cache) + `SelectableCars` in the schedule | XML + JSON | `build_series.py` | career | **verified** (acceptlists); numeric limits in `SelectableCars` (PI, year, power, weight, cost) are a **hypothesis** |
| series defaults: qualifying options, skip-lap flags | `DefaultEventOverrides` in the schedule | JSON | `cache_edit` | career | **observed**: limited practice laps order the **AI's** grid; there is no separate qualifying session; the human's slot comes from the start-position wager when its screen is on, and is a per-event constant otherwise ([OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md) 16) |
| series defaults: damage, wear, time-of-day scale, drafting, dynamic track | same | JSON | `cache_edit` | career | **hypothesis** (bench kit built, no result yet) |
| entry gates (driver level, required ladders/series/events) | `EntryCriteria` at cup, ladder and series level | JSON | count fields: `cache_edit`; required lists: new schema | career | **hypothesis** |
| build phase, intro video, first-car select, series type | series fields in the schedule | JSON | `cache_edit` | career | **hypothesis** (bench kits built, results pending) |
| per-event generator (session options) | `GameOptions_<gen>_{FeaturedRace,PracticeAndQualification}.xml` via the override's `ParentGeneratorId` | XML | `cache_edit` (if the generator has a cache blob) or `install_edit` | career: the career generators share no id with the Featured overrides | **observed**: it decides the human's grid slot, the car-class filter and the start; every generator used by a career event has a local copy (most in the cache, a few only in install-cms). Option list: [RACE_SYSTEM](RACE_SYSTEM.md) 2.17 |
| human's grid slot | generator `GridOrderingType` + `ClusterHumansAtIndex` | XML | `cache_edit` on a generator no other mode uses | career | **observed** (n=1 per series): with `AIDriverRank` the index acts as a cut (0, 2, 5 → first; 6, 7, 8, 11, 23 → last, with no middle slot); with `Qualifying` a mid-grid value that varies with the field, the AI document and the car (7th of 24, 3rd of 8, 5th of 12 and of 16); the project uses index 23 and does not use `Qualifying` (ADR-006). The series' own fields cannot move it |
| car-class filter of an event | generator `Buckets/Bucket/CarRestrictions` | XML | pick a generator with the class you want (`ParentGeneratorId`) | career | **observed** (n=1 pair): a strict class-R generator refused a class C car the series allowed |
| penalty rules (ghost, off-track, collision, wrong way) | generator `RaceRegulationsId` → regulations table | XML + JSON | generator choice | career | **observed**: regulation 103 on a career generator showed no visible effect (collisions were already punished with 0) |
| mandatory pit stop | event override `FeatureRace.Pits` **and** the generator's `NumQuickStops` | JSON + XML | `build_series.py` (`pits`); `cache_edit` on a generator no other mode uses | career | **observed**: the AI is required to stop; `Pits` 0 removes the stop only when the generator's `NumQuickStops` is 0 (a generator with 1 still forced a stop, D54) |
| race weather and hour | event override `FeatureRace.WeatherForecast`, `TimeOfDayHour` | JSON | cache_edit after `build_series.py` | career | **observed** (n=1): they change the race only; the practice keeps the `PracticeAndQualifying` block |
| practice laps | the event's `NumberOfRequiredLaps` (the race laps stay in `FeatureRace.Laps`) | JSON | `cache_edit` (`build_series.py` writes both with one number today) | career | **observed**: events with 2, 3 and 4 required laps showed 2, 3 and 4 practice laps; the series' and the generator's lap limits did not act |
| AI document with no drivers | `AIField_<id>_Gen.xml` with an empty driver list | XML | `install_edit` | career | **closed** as a way to run solo: practice runs, the race crashes |
| series objectives | `ChampionshipSeriesObjectivesData_<SeriesId>.json` | JSON | **no tool**: career series have no document, and `cache_edit` cannot add a new logical entry | career + Featured (the enabling flag is shared) | **closed**: a switch-on test on a fresh series showed and paid nothing ([ECONOMY_MAP](ECONOMY_MAP.md) §5) |
| Challenge the Grid wagers | `ChallengeTheGridData` at cup level + a client flag | JSON | `cache_edit` | career | **verified**: the screen is driven by the client flag (section 11); the cup data only changes multipliers. **observed**: setting the table to 10.0 on every slot did **not** change the credits paid ([DISCOVERIES](../project/DISCOVERIES.md) D57) |

## 4. AI

| what | where the game reads it | format | how to write | scope | status |
|---|---|---|---|---|---|
| grid / roster (cars, PI band, slots) | `AIField_<id>_Gen.xml`, named by the override's `AIFileName` | XML | `_tools/build_aifield.py` + `install_edit.py` (the group usually has no cache blob) | career (Featured has no AI grid field) | **verified** (`AI_GRIDS.md`) |
| catch-up / slow-down / proximity per series | `AIRaceBehaviors` (two blocks: race, practice/qualifying) in the schedule | JSON | `cache_edit` | career | **observed** for catch-up and slow-down off in the race: the AI got better (user report, [DISCOVERIES](../project/DISCOVERIES.md) D59); the rest is a **hypothesis** |
| catch-up flags per grid file | `RaceBehaviorSettings` inside the AIField XML | XML | `install_edit` | career: no Featured, Rivals or Meetup generator cites a career grid; a few grids are shared by several career series | **hypothesis**; which layer wins is open |
| rubber banding / drivatar training per generator | `GameOptions_<gen>` attributes | XML | `cache_edit` | career | **observed** as already off in the career generators, so it is not the source of the elastic feel |
| global AI config (career spread, dynamic difficulty, catch-up) | `AIConfig.*` in the client flags | JSON | `cache_edit` | **global** | **hypothesis**, discuss first |
| per-track AI tuning | `TrackBalanceValues.TrackAITuningOverrides` (cache, empty) | JSON list | new schema; candidate fields are the gamedb `TrackAITuning` columns, which also appear as exe tokens | **global** | **hypothesis**: the key names have strong evidence; the item shape and effect are unproven |
| AI driving/line data | `media\base\ai\` (zips) | binary/XML | — | global | not surveyed for writing |

## 5. Credits, economy and progression

**Status so far: the cache's payout tables only change what the interface shows; the one concrete change to the credits paid is the session generator's mandatory stop (D58).** See [ECONOMY_MAP](ECONOMY_MAP.md).

| what | where the game reads it | format | how to write | scope | status |
|---|---|---|---|---|---|
| credit scalars, per-track car credit scaling, rewards, driver/car level config | `CreditScalars.json`, `CarCreditScalingTable.json`, `Rewards.json`, `LevelConfigurationV3.json`, `DriverLevelConfig.json` (cache) | JSON | `cache_edit` | **global** (account progression) | **hypothesis**, discuss first Per-track car credit scaling (the career base cell): doubling it changed the pre-race screen but **not** the credits paid (D56). |
| part discount by car level | `AffinityDiscountSettings` (client flags) | JSON | `cache_edit` | global | **hypothesis**; it is not manufacturer affinity |
| prize packs, unlock rules, level rewards, bonuses, forzathon | `media\base\prizes\`, `media\base\unlocks\`, tunables | encrypted container | **closed** | account / server-side | **closed** |
| affinity level rewards, legacy level config | `media\base\gametunablesettings\` (readable) | XML/JSON | file swap (no tool) | account | **hypothesis**; prefer the cache copy where one exists |
| upgrade tables, PI wizard tables | gamedb | SQLite (read-only) | **closed** | global | read-only reference |

Surveyed (`reference/ECONOMY_MAP.md`): race payout is **global with one
exception** - every scalar table (`CreditScalars.json`, rule-preset
`CreditScalar`) applies to all modes, and the only career-scoped piece
is the `BuildersCup` entry of the track-x-class base table
(`CarCreditScalingTable.json`). Prizes are challenges pointing at
`Rewards.json` ids (all references resolve); custom series have no
challenge file, so a new series inherits payout but gets no prize of its
own. **Closed (November 2026):** editing challenge conditions, prizes or
per-series objectives makes the client mark the row completed, but credits
and cars are granted by the server against its own challenges
([ECONOMY_MAP](ECONOMY_MAP.md) §5). Car/driver progression is account-global,
out of series-kit reach.

## 6. UI and text

| what | where the game reads it | format | how to write | scope | status |
|---|---|---|---|---|---|
| names and descriptions (`IDS_` keys) | LocStrings `.str` tables in the cache | `.str` (hashed keys) | `_tools/str_edit.py` + a `bytes` plan | per key | **verified**: new keys of any length work |
| install string tables | `media\base\stringtables\<lang>.zip` | `.str` | not needed (the cache copy wins) | — | **verified** that the cache is the runtime source |
| screens behind client flags | client flags (section 11) | JSON | `cache_edit` | depends on the flag | **verified** for one screen (n=1) |
| art (posters, banners, buttons) | image paths in the schedule | path strings | `build_series.py` (reuse existing paths) | career | **verified** (reuse only); own art: format read, no write tested ([SWATCHBIN](SWATCHBIN.md)) |

## 7. Tracks

| what | where the game reads it | format | how to write | scope | status |
|---|---|---|---|---|---|
| track per event, laps | override + event in the career schedule | JSON | `build_series.py` | career | **verified**: the race runs the override's lap count |
| track temperature, track lists | `TrackTemperature`, track tables (cache / gamedb) | JSON / SQLite | `cache_edit` (cache only) | global | **hypothesis** |
| per-track visual settings (sky, cubemaps, color grading, shadows) | `media\pcfamily\tracks\<track>\tracksettings*.xml` | loose XML | file swap (no tool) | client, visual | **hypothesis**; this is the first install pilot, once the tool exists |
| per-track surface contact params (friction, elasticity) | same files | loose XML | — | **global** (physics) | **closed** by project rule |
| track geometry, ribbons, assets | track zips (some compressed with a method that needs a native runtime) | binary | — | global | **closed** |

## 8. Graphics

| what | where the game reads it | format | how to write | scope | status |
|---|---|---|---|---|---|
| quality presets (resolution of shadows, liveries, reflections, LOD distances) | `media\pcfamily\renderscenarios\<preset>\*.xml` | loose XML | file swap (no tool) | client, visual | **hypothesis**: going "above ultra" is possible in data but untested |
| lens flares, photo-mode presets | `media\base\lensflare\`, photo-mode preset files | XML | file swap | client, visual | **hypothesis** |
| hardware profile | `media\base\targethardwareprofiler.xml` | XML | file swap | client | **hypothesis** |

## 9. Physics

| what | where the game reads it | format | how to write | scope | status |
|---|---|---|---|---|---|
| surfaces, collision objects, PI model, aero, suspension, physics settings | `media\base\physics\` | encrypted container | **closed** (no encoder) | **global**, online advantage | **closed** by project rule |
| car data (drivetrain, engine, tires, curves) | gamedb | SQLite (read-only) | **closed** | global | read-only; it feeds the career car filters |
| spec-series balance scalars (per car and spec division) | `SeriesSpecCarBalanceScalers.json` (cache, populated, known schema) | JSON | `cache_edit` | probably global | **hypothesis**, discuss first |
| spec-series physics scalars | `SeriesSpecCarPhysicsScalars.json` (cache, empty) | JSON | no known schema | probably global | **closed** (no schema source) |
| per-bucket traits (friction/torque scale) | `Buckets[].Traits` in Featured records | JSON | — | Featured | **closed** (Featured is not modded) |

## 10. Weather and time of day

| what | where the game reads it | format | how to write | scope | status |
|---|---|---|---|---|---|
| forecast per event | `WeatherForecastsV2.json` (cache), referenced by the generator and by override forecast ids | JSON | `cache_edit` / `build_series.py` | career (through career generators and overrides) | **hypothesis**; every career event links to a valid forecast |
| start/mid/end weather and probabilities, time-of-day start and scale | `GameOptions_<gen>` attributes + series `TimeOfDayTimeScale` | XML / JSON | `cache_edit` | career | **hypothesis** |
| localized weather tables, install forecast copy | `media\base\gametunablesettings\weather-*` | encrypted container | **closed** | global | not needed (the cache path covers the career) |

## 11. Client feature flags

| what | where the game reads it | format | how to write | scope | status |
|---|---|---|---|---|---|
| feature switches and per-mode lists (tire type, fuel scale, objectives, practice skip, race engineer, Challenge the Grid) | `ClientFeatureFlagConfiguration.json` (cache) | JSON | `cache_edit` (one value per kit) | per flag: per-`GameMode` lists are career-only when the item is `BuildersCup`; `AIConfig.*` and most switches are **global** | **verified** that the client reads the flags from the cache and the server does not override them (n=1); the others are **hypothesis** |
| install copy of the flags | `media\base\gametunablesettings\clientfeatureflagconfiguration.json` | encrypted container | **closed** | — | the cache copy is the live one |
| config blocks for qualifying limits, series points, pit repair times | short-named `*Config` blocks already present in the flags file (the long exe names are C++ types) | JSON | `cache_edit` | likely global | **hypothesis** |

## 12. Integrity

| what | where | status |
|---|---|---|
| cache chain (blob → `prod\<snapshot>` → `cache-manifest.json`) | CmsCache | **verified**: Strategy S plus manifest Size/Checksum updates are accepted; `_tools/cache_verify.py` checks it, `_tools/rollback_cache.py` restores it |
| install CMS chain (zip → install manifest → snapshot → cache manifest) | install + CmsCache | **verified** through `install_edit.py` (AI grid kits) |
| `hash.manifest` (base and pcfamily) | install | **observed** as a plain table of fixed-size records (id + number), chained between the two files. The id is an opaque asset id: path and content hashes of every loose file under `media\` match none. Whether loose-file edits are checked is **indeterminate** |
| `zipmanifest.xml` | install (encrypted container) | **observed**: it lists zips only (path, mount, priority, directory info), with no hashes and no loose files |
| Steam "verify files" | install | restores any install edit; cache edits are not affected |
| server snapshot change | CmsCache | a new snapshot drops cache kits; kits are snapshot-bound and must be regenerated |

## 13. Tools at a glance

- `_tools/cache_edit.py`: any cache JSON/XML/bytes change on an existing logical
  entry. It cannot add entries.
- `_tools/build_series.py`: new career series from a spec.
- `_tools/build_aifield.py`: AI grid definitions.
- `_tools/install_edit.py`: one CMS entry inside an install zip.
- `_tools/str_edit.py`: `.str` text keys.
- `_tools/inventory.py`, `_tools/audit_career.py` and
  `_tools/aifield_survey.py`: read-only inventories of your own game.
- Missing today:
  - an "add logical entry" operation for the cache;
  - an install file-swap tool with backup and restore;
  - writing the encrypted containers (not planned: physics and economy are
    global and out of scope).
