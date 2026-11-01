# Series checklist — what a new career series needs, and why

The reference behind `build_series.py`: every step a new series needs, in
execution order, with the reason it exists. The default path is a spec
([specs/README.md](../../specs/README.md), `specs/_TEMPLATE.json`) and
`python _tools\build_series.py --spec …`, which implements steps 1–9 with
checks; the step-by-step walk-through is [tutorial 03](../tutorials/03_new_series.md).
Read this page when a generated series misbehaves or when you need to know
why a field is set the way it is.

Validated in game: a series built this way shows up, lists its events, lets you
take the track with an eligible car, finishes and records the result.

## 1. Checklist (execution order)

1. **Ids**: a new `ChampionshipSeriesId` (≥ 20000) and new `EventDataId`s
   (65897900–65899999). **Never reuse an event id**: the save marks completion
   by `EventDataId`, so a series with a reused id shows up as already done.
   `plan_lint.py` rejects retired ids.
2. **Series**: clone the shell of a working series, changing only
   `ChampionshipSeriesId`, `Name` (a new text key), the events and
   `OrderedEventIds` (invariant: the event array and `OrderedEventIds` hold the
   same ids in the same order). Set `StartEndDate.To` and `CloseTime` to
   `9999-12-31 23:59:59.999`; zero `EntryCriteria`.
3. **Ladder**: append the series object to the end of `ChampionshipSeriesData`
   **and** its id to the end of `OrderData` (invariant: array == `OrderData`).
4. **Events**: clone events from existing tracks; only `EventDataId` and
   `ChampionshipSeriesId` are new. Pick a donor event on the same track that
   has a valid AI grid (`python _tools\inventory.py` lists them).
5. **Overrides**: one entry per event (`ID == EventDataId`), cloning `Track`,
   `AIFileName` and `ParentGeneratorId` from the donor. `AIFileName` must exist
   in the manifest: a missing AI grid crashes the game when you enter the series.
6. **Car registry (the root cause of crashes)**: a
   `CarSelectCarRestrictions SeriesId="<id>"` entry in
   `BCSeriesSelectableCars.xml`, plus `ArrayLength` + 1, mirroring the
   acceptlist. Without it the game throws a C++ exception (`0xe06d7363`) when you
   click the series.
7. **Eligibility**: `SelectableCars` plus the registry entry with an explicit
   `Acceptlist` that holds **at least one cheap car**. With no eligible car the
   game suggests buying the car with the **lowest CarId in the list**; an
   invalid list makes it suggest a fixed fallback car. There is no purchase
   pop-up in the flow — buying is manual in the shop. Keep denied cars out of
   the list ([data/CARS](../data/CARS.md) marks them).
8. **Name**: a new `IDS_` key in the pt-BR `.str` table (pt-BR alone is enough;
   other locales show the key). Never change vanilla strings. `str_edit.py`
   writes keys of any length.
9. **Art**: reuse an existing poster and banner path; new image assets are not
   supported.
10. **Apply**: the generator reads the current cache (blobs matched by
    Checksum, indices resolved per snapshot), encrypts with the oracle using the
    current payload as template, and writes a kit. Then `--dry-run`, game
    **closed**, apply with `--verify`, `cache_verify.py` with 0 errors
    ([PIPELINE](../en/PIPELINE.md)). Kits are snapshot-bound.
11. **In-game test**: the series appears → opens → you enter with an eligible
    car → you finish → the result is recorded.

**Not needed:** championship objectives documents (no career series has one),
new `GameOptions_*` generators (reuse the donor's), `.str` keys in other
languages, `SeriesSpecDivisionId` (zero everywhere).

## 2. Series object — what to change

Clone and change only the fields marked ★. `ChampionshipId` = 500 (the career).
`ButtonImagePath` = `""`; `SeriesOrderData` is always `[]`; events carry
`Type: "ChampionshipEventDataV3_MetaData"`.

| field | origin |
|---|---|
| `ChampionshipSeriesId` ★ | new, unique |
| `Name` ★ | a new `IDS_` key (a literal does **not** work here) |
| `Description` | `""` or an `IDS_` key |
| `ImagePath` / `BannerImagePath` ★ | reuse an existing `GAME:\…` path |
| `ChampionshipEventData[]` ★ | the new events, in the order of `OrderedEventIds` |
| `OrderedEventIds` ★ | the new ids, same order |
| `StartEndDate.To`, `CloseTime` ★ | `9999-12-31 23:59:59.999` |
| `OpenTime`, `StartEndDate.From` | copy from the donor |
| `EntryCriteria` ★ | zeroed (empty lists, counts 0) |
| `DefaultEventOverrides` | copy (difficulty, damage, number of players…) |
| `SelectableCars` ★ | an explicit `Acceptlist` with a cheap car (§4); `CarDivisionId: "Open"` |
| `AISelectableCars`, `SeriesOpponentDrivatars`, `AIRaceBehaviors`, `IntroCarColors`, `FirstCarSelect*`, `CarSelectAcceptlist`, the rest | copy from the donor |

Field-by-field meaning: [SCHEMA_REFERENCE](SCHEMA_REFERENCE.md).

## 3. Event object and override

**Event**: a new `EventDataId` ★ and `ChampionshipSeriesId` ★; `Name` is an
editable literal; `TrackId` and `SerialTrackId` always change together; track
images are copied; `TargetPI` and `PointSpread` are copied and tuned later.

**Override**: `{ID ★, Enabled: true, Track = SerialTrackId,
PracticeAndQualifying {…}, FeatureRace {Weather, Laps, Pits, …},
ParentGeneratorId, ClassRestriction, TargetPI, AIFileName,
Type: "BCSharedEventData"}`, cloned from the donor.

Two rules verified in game decide which copy of a value counts:

- **Race length comes from the override** (`FeatureRace.Laps`), in both
  directions; the event's `NumberOfRequiredLaps` is not what the race runs.
- **The cap a player sees comes from the event's `TargetPI`**; the override's
  `ClassRestriction` did not apply. To open or close a series to a class,
  change the event's `TargetPI`.

## 4. Eligibility and the suggested car

- A series requires an eligible car you **own**. Without one, the game names
  the car with the **lowest CarId in the acceptlist** (not the cheapest).
- An empty or invalid list makes it suggest a fixed fallback car.
- Keep denied cars out of the list and always keep one cheap car in it.

## See also

[CAREER_MODEL](CAREER_MODEL.md) · [RACE_SYSTEM](RACE_SYSTEM.md) ·
[CARS_AND_PI](CARS_AND_PI.md) · [TROUBLESHOOTING](../guides/TROUBLESHOOTING.md)
