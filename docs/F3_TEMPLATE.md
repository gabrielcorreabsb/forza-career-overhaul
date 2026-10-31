# F3 — Final pipeline for a new series (validated in-game 2026-10-30)

A working new series = **20003 "ModCarrera Teste 1 [20003]"** (cup 2/ladder 22):
it shows up, lists events, takes the track with an eligible car, finishes and
records the result. Sources: the maintainers' lab diary and the generated inventories.

> **Default path (since 2026-10-30):** write a spec (`specs/README.md`,
> `specs/_TEMPLATE.json`) and run `python _tools\build_series.py --spec …`.
> It implements steps 1–9 below with checks. The generator is
> regression-tested against a private reference kit. This
> checklist remains the reference for the *why* behind each step.

## 1. Checklist (execution order)

1. **Ids**: a new `ChampionshipSeriesId` (range ≥20000) plus new `EventDataId`s
   (range ≥65897900). **Never reuse an event id** — the save marks completion
   by `EventDataId` (a series with a reused id shows up as "already done", mc50).
2. **Series**: clone the shell of a working series (recommended: 601), changing
   only `ChampionshipSeriesId`, `Name` (new key), events and `OrderedEventIds`
   (invariant: array == `OrderedEventIds`, 176/176). Dates `To`/`CloseTime` =
   `9999-12-31 23:59:59.999`; `EntryCriteria` zeroed.
3. **Ladder**: append the object to the end of `ChampionshipSeriesData` **and**
   the id to the end of `OrderData` (invariant array == OrderData).
4. **Events**: clone events from existing tracks (`tracks.json`, 71
   layouts; donors with valid AI per track in `track_events.json` — only
   tracks 70 and 513 have no donor), only `EventDataId` +
   `ChampionshipSeriesId` new.
5. **Overrides**: one sibling entry per event (`ID == EventDataId`; vanilla
   coverage 100%), cloning `Track + AIFileName + ParentGeneratorId` from the
   track. `AIFileName` must exist in the manifest (ladder 736 crashed because
   the AI was missing).
6. **Car registry (root cause of the crashes!)**: a
   `CarSelectCarRestrictions SeriesId="<id>"` entry in `BCSeriesSelectableCars.xml`
   plus `ArrayLength`+1, cloned from a working series and mirroring the
   acceptlist. Without it the game throws a C++ exception (`0xe06d7363`) when
   you click the series. Vanilla 11520 also lacked it.
7. **Eligibility**: `SelectableCars` + registry entry with an explicit
   `Acceptlist` containing **at least one cheap car** (e.g. Veloster 54k). An
   empty `Blocklist` only exists in the "Open Class" tours and falls back to the
   reserve car. With no eligible car the game suggests buying the one with the
   **lowest CarId in the list** (rule proven 3×: Astra 1490, Camaro 2523,
   Ghibli 2051); an invalid list → suggests the **MP4/4 (1670)**. There is no
   purchase popup in the flow (`Ownership=None` everywhere) — buying is manual
   in the shop. Check that no car in the list is in `denylist.json`
   (32 global vetoes; the Luka Camaro 3972 included).
8. **Name**: key `IDS_<md5("MC44|<label>")>` in `LocStrings_pt-BR.str`
   (pt-BR alone is enough); it may include `[id]` for debugging. Never change
   vanilla values.
9. **Art**: reuse an existing poster/banner (`posters.json`, 168).
10. **Pipeline**: the generator starts from the current cache (blob by Checksum
    **and indices resolved per snapshot** — the old snapshot has 126–127 series
    vs 177–178 on the live one) → encrypt with the oracle (template = current
    payload, Strategy S) → `--dry-run` → game **closed** → `--verify` →
    `cache_verify.py` 0 errors → kit `patches/mcNN/` (`plan.json` + `.enc` +
    the kit's notes file). Kits are snapshot-bound. Reference implementation:
    `_tools/build_series.py` and `fmlib` (bytes op + oracle, json op by path, XML).
11. **F3.7 test**: appears → opens → enters (eligible car!) → finishes → prize.

NOT needed: `ChampionshipSeriesObjectivesData_*` (0/176 have them),
`GameOptions_*` (low raceIds only), `.str` of other languages,
`SeriesSpecDivisionId` (0 everywhere).

## 2. Series object — field catalogue (28, live source)

Clone and change only ★. `ChampionshipId`=500 fixed. `ButtonImagePath`=`""`;
`SeriesOrderData` always `[]`; `Type:"ChampionshipEventDataV3_MetaData"` on the
events.

| field | origin |
|---|---|
| `ChampionshipSeriesId` ★ | new, unique |
| `Name` ★ | new `IDS_` key (displayed name; a literal does NOT work here) |
| `Description` | `""` or an `IDS_` key |
| `ImagePath` / `BannerImagePath` ★ | reuse an existing `GAME:\…` |
| `ChampionshipEventData[]` ★ | new events, order == `OrderedEventIds` |
| `OrderedEventIds` ★ | new ids, same order |
| `StartEndDate.To`, `CloseTime` ★ | `9999-12-31 23:59:59.999` |
| `OpenTime`, `StartEndDate.From` | copy (`1-1-1…` or the vanilla date) |
| `EntryCriteria` ★ | zeroed (empty lists, counts 0) |
| `DefaultEventOverrides` | copy (difficulty, number of players…) |
| `SelectableCars` ★ | explicit `Acceptlist` with a cheap car (see §4); `CarDivisionId:"Open"` |
| `AISelectableCars` / `SeriesOpponentDrivatars` / `AIRaceBehaviors` / `IntroCarColors` / `FirstCarSelect*` / `CarSelectAcceptlist` / rest | copy from the donor |

## 3. Event object + override

Event: new `EventDataId`★ + `ChampionshipSeriesId`★; `Name` is an editable
literal; `TrackId`+`SerialTrackId` always go together; track images copied;
copy `TargetPI`/`PointSpread`/`NumberOfRequiredLaps` (tune later).
Override: `{ID★, Enabled:true, Track=SerialTrackId, PracticeAndQualifying{…},
FeatureRace{Weather,Laps,Pits,Hora}, ParentGeneratorId, ClassRestriction,
TargetPI, AIFileName, Type:"BCSharedEventData"}` — clone it from the track.

`ClassRestriction`: -1 = any class, otherwise the **event's maximum class**
(classes 0–8 by `MaxPerformanceIndex` in the gamedb: 2≈≤557, 3≈≤619, 4≈≤686,
5≈≤771; inferred — a class-2 Astra was suggested for a CR3 event, so it is not
an exact class). Eligible = acceptlist ∩ class ≤ CR ∩ not vetoed.

## 4. Eligibility and the suggested car (proven rules)

- A series requires an eligible car you **own**; without one, the message
  `IDS_BuildersCup_MissingCarForRewardShowcase` names the car with the **lowest
  CarId in the acceptlist** (not the cheapest: Veloster 54k < Astra 61k, and it
  suggested the Astra).
- Empty/invalid list → suggests the **MP4/4 (1670)**.
- Check the vetoes (`denylist.json`) and always keep a cheap car in the list.

## 5. Data files (`_data`, live source + gamedb + showroom)

> Generated **only** by `python _tools\inventory.py` (never hand-edited);
> readable version in the inventory pages (CARROS, PISTAS, CARREIRA, POSTERS,
> ESTADO). Newer ones: `career.json` (tree with pt-BR names), `ids.json`,
> `kits_state.json`, `_meta.json`. Donors in `track_events.json` = **vanilla**
> overrides only.

| file | content |
|---|---|
| `tracks.json` | 71 tracks: SerialTrackId → TrackId GUID, name, posters |
| `track_events.json` | 73 tracks: override entries with valid AI (recommended donor) |
| `posters.json` | 168 posters and their usage |
| `ladders.json` | 34 ladders: cups, orders, series |
| `divisions.json` / `divisions_full.json` | 52 car divisions (ids 0–53, no 3; division ≠ class) |
| `cars.json` | **711 cars**: id, pt name, year, make, class, PI, price |
| `denylist.json` | 32 global vetoes |

## 6. F3 ids (do not reuse retired ones)

> Source of truth: `ids.json` (live custom ids + kit metadata) and
> `patches/ids_retired.json` (retired, hand-edited). `plan_lint` rejects a plan
> whose `series_id`/`event_id`/`cup_id`/`ladder_id` is retired. Custom
> `EventDataId` range: **65897900–65899999** (vanilla uses higher ids). The
> table below is historical.

| entity | range | in use | retired |
|---|---|---|---|
| `ChampionshipSeriesId` | 20000+ | 20003 (lad22), 11520 (vanilla, lad736) | 20001, 20002 |
| `EventDataId` | 65897900+ | 65897910-12 (20003) | 65897900/01 |
| `IDS_` (pt-BR) | `md5("MC44\|…")` | Teste 1 `[20003]`, Teste 2 `[20002]`, 11520 `[11520]` | `IDS_5c98…` (no id) |

## 7. Kits (applied, 0 errors; the kit's notes file in every one)

mc53 (final solution) · mc52 (lowest-CarId proof) · mc51 (rotation) ·
mc50 (unique events) · mc49 (acceptlist 23) · mc48 (common poster) ·
mc46 (intro events) · mc44 (ids in the title) · mc43/mc42 (open the cars) ·
mc41 (clean copy of 20003) · mc40 (the registry! root cause) · mc38 (swap) ·
mc36 (clone 601) · mc34/35 (Test A/B) · mc33 (carfix/diff/xref) ·
mc32 (video) · mc31 (AI) · mc30 (new series).
