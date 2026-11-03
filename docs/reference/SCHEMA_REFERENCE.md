# Schema reference

Field-by-field catalogue of the career and Featured/Multiplayer records: what
each field is for and what a fresh record carries by default. No JSON, no asset
dumps — only names, purpose and defaults.

**Scope.** Two data sets, documented in separate sections:

1. **Championship 500 — the career.** Cups → ladders → series → events, all in
   one schedule document. 7 cups, 35 ladders, 178 series, 627 events.
2. **Championship 1 — Featured / Multiplayer.** A different document with its
   own shape: no cups and no ladders, series grouped into rotating collections.
   62 series, 4348 events. Never modified by this project.
3. **Client feature flags** — the switches the client reads before it uses
   either data set (Part 3).

A third championship, **22**, holds the one-session intro (FTUE) content and is
mentioned only where it explains a difference.

Evidence labels are defined in `CAREER_MODEL.md`. The commands behind the
reproduction lines:

```powershell
python _tools\inventory.py      # inventory of the installed content (read-only)
python _tools\audit_career.py   # career audit tables; --check fails if stale
```

The audit covers the career only. Featured numbers below come from reading the
racers-cup metadata document with the same CMS reader (procedure in each entry).

## 1. How to read the tables

- **Field** — the name exactly as it appears in the record.
- **Purpose** — what the field is consulted for. Where the purpose is inferred
  from behaviour rather than from a name, the row says so.
- **Default** — the value a newly cloned record of that type carries, expressed
  as the dominant value in the data. "empty" means `[]` or `""`; "never" is the
  far-future sentinel date.
- Anything a row cannot support is marked **hypothesis** and listed in
  `OPEN_QUESTIONS.md`.

---

# Part 1 — Championship 500 (career)

## 1.1 Where it lives

- **verified** — The whole career is one document, and it holds a single
  championship object: id **500** with **7** cups. There is no second
  championship in that document. *How to reproduce:*
  `python _tools\audit_career.py` (championship ids and cup count).

- **verified** — The championship object has **9 fields**:
  `ChampionshipId`, `Name`, `Title`, `Description`, `ImagePath`, `OpenTime`,
  `CloseTime`, `OnboardingSeries`, `ChampionshipCupData`.
  *How to reproduce:* `python _tools\audit_career.py` reads this object; the
  field names are visible in the loader it uses.

- **verified** — `OnboardingSeries` names the series offered to a brand-new
  profile; it is a single series id, not a list.
  *How to reproduce:* the championship object itself (one id) — the career
  starts on that series.

## 1.2 Cup — 15 fields

| field | purpose | default |
|---|---|---|
| `ChampionshipCupId` | cup identity (opaque) | unique per cup |
| `ChampionshipId` | owning championship | 500 |
| `Name` | display name, as an `IDS_` key | unique key per cup |
| `Description` | one-line description, as an `IDS_` key | empty |
| `ImagePath` | cup art | empty |
| `IntroVideoPath` | intro movie played on entry | `LogoParade.bk2` |
| `OpenTime` / `CloseTime` | availability window | `1-1-1 0:0:0.0` / never |
| `StartEndDate` | `From` / `To` bounds of the same window | sentinel pair |
| `OpenPracticeLimitationTime` | practice minutes at cup level | 10 |
| `EntryCriteria` | gate block (name, min level, required ladders/series/events + counts) | all empty |
| `ChallengeTheGridData` | challenge-the-grid setup (race wagers); the screen itself is gated by a client flag (Part 3) | one fixed block |
| `RewardVirtualTrophy` | trophy awarded for completing the cup | one fixed block |
| `ChampionshipLadder` | the cup's ladder objects | 1 per cup |
| `LadderOrderData` | ids of those ladders, in display order | mirrors the array |

- **verified** — The cup carries its own `EntryCriteria` and its own practice
  minutes, separate from the series defaults (a cup-level practice value is what
  the cup screen shows before any series is opened).
  *How to reproduce:* read a cup record — those two groups sit on the cup, not on
  its ladders or series.

## 1.3 Ladder — 14 fields

| field | purpose | default |
|---|---|---|
| `ChampionshipLadderId` | ladder identity | unique per ladder |
| `ChampionshipId` | owning championship | 500 |
| `Name` | display name, as an `IDS_` key | unique per ladder |
| `Description` | description key | empty |
| `ChampionshipLadderFlag` | free-form flag | empty |
| `ImagePath` | ladder art | one shared GAME: path on 34 ladders |
| `IntroVideoPath` | intro movie | `LogoParade.bk2` |
| `OpenTime` / `CloseTime` | availability window | fixed / never |
| `StartEndDate` | `From` / `To` of the same window | sentinel pair |
| `EntryCriteria` | gate block (same 8 sub-fields as the cup) | all empty |
| `LadderCompletionRequirements` | what must be finished to clear the ladder | `["AllSeries"]` |
| `ChampionshipSeriesData` | the ladder's series objects | 1+ per ladder |
| `OrderData` | ids of those series, in display order | mirrors the array |

- **verified** — `LadderCompletionRequirements` is the only completion rule in
  the career schema; it takes a list of requirement names, and
  `["AllSeries"]` (every ladder in the data) means "finish every series".
  *How to reproduce:* read the ladder records — one distinct value across them.

## 1.4 Series — 28 fields

| field | purpose | default |
|---|---|---|
| `ChampionshipSeriesId` | series identity (opaque; ≥ 20000 for customs) | unique |
| `ChampionshipId` | owning championship | 500 |
| `Name` | display name, as an `IDS_` key | unique key |
| `Description` | description key | empty on 153 of 178 |
| `ImagePath` / `BannerImagePath` / `ButtonImagePath` | series art | one shared GAME: path; button art empty on 155 |
| `ChampionshipEventData` | the series' event objects | 1–8 per series |
| `OrderedEventIds` | event ids in display order | mirrors the array |
| `OpenTime` / `CloseTime` | availability window | various / 122 series close never |
| `StartEndDate` | `From` / `To` of the window | sentinel pair |
| `DefaultEventOverrides` | 15-field defaults block (see §1.6) | one block per series |
| `IntroVideoPath` | intro movie | empty on 101 |
| `PlayIntroVideoFullScreen` | play it full screen | false |
| `CarSelectVideoPath` | clip played on the car-select screen | empty |
| `IntroCarColors` | paint overrides for the intro car | empty |
| `FirstCarSelectEnabled` / `FirstCarSelectCars` | pre-seed the first car choice | false / empty |
| `CarSelectAcceptlist` | **legacy** acceptlist slot | empty on all 178 |
| `SelectableCars` | the real car filter: 38 fields (see §1.5) | one open filter |
| `AISelectableCars` | `Acceptlist` of AI cars for the series | empty on 82, populated on 96 |
| `AIRaceBehaviors` | 2 behaviour blocks of 6 flags (see §1.7) | one block pair |
| `SeriesOpponentDrivatars` | `AIDrivatars` list | empty |
| `SeriesOrderData` | **legacy** ordering slot | empty on all 178 |
| `SeriesType` | `Default` (150) or `RewardShowcase` (28) | `Default` |
| `SkipBuildPhase` | skip the build/upgrade phase | false (true on 42) |
| `EntryCriteria` | gate block (same 8 sub-fields) | all empty |

- **verified** — `CarSelectAcceptlist` and `SeriesOrderData` are dead slots:
  both are empty in every one of the 178 series. Ordering comes from
  `OrderedEventIds`, and car gating from `SelectableCars`.
  *How to reproduce:* read the series records — one distinct value on each of
  those two columns.

- **verified** — `AISelectableCars` is **not** dead but is also not what pins a
  grid: it is empty on 82 series and populated on 96, and filling it on a series
  that had it empty changed nothing in game (`AI_GRIDS.md`).
  *How to reproduce:* the roster column of the audit; then the A/B test.

## 1.5 `SelectableCars` — 38 fields

The car filter is a single nested object with 38 fields. It is a *generic*
filter: it can match on 30+ car attributes and optionally carry an explicit
car list.

| group | fields | default |
|---|---|---|
| the list itself | `BlockOrAcceptlist`, `BlockOrAcceptlistType` | 163 series carry an **Acceptlist** (1–23 cars, mean 5.1); 15 carry an empty **Blocklist** |
| label | `Name` | empty |
| class / division | `CarClassId`, `CarDivisionId` | `Any` / `Open` |
| performance | `PIMin`, `PIMax` | 0 / 0 (inert) |
| power / weight | `PowerMin`, `PowerMax`, `WeightMin`, `WeightMax` | 0 / 0 (inert) |
| cost / level / year | `BaseCostMin`, `BaseCostMax`, `CarLevelMin`, `CarLevelMax`, `YearMin`, `YearMax` | 0 / 0, level 255 / 255, year 0 / 0 |
| identity | `ModelFamilyId`, `BodyFamilyId`, `FamilySpecialId`, `CarTypeId`, `CountryId`, `RegionId`, `MiniCareerId` | `Any` / 0 |
| drivetrain / engine | `DriveTypeId`, `AspirationId`, `CylinderId`, `EngineConfigId`, `EnginePlacementId` | `Any` |
| build / tuning | `BrakeLevelId`, `SuspensionLevelId`, `TireCompound`, `TireCompoundLevelId`, `Tuning`, `Upgrades`, `SeverityType`, `RearTireWidth` | `Any` / `Stock` / `None` / 0 |
| ownership | `Ownership` | `None` |

- **verified** — `BlockOrAcceptlistType` takes exactly two values:
  `Acceptlist` on 163 series and `Blocklist` on 15; the 15 with a blocklist have
  no entries and pin a fixed `CarClassId` instead, so the two modes never
  overlap. *How to reproduce:* `python _tools\audit_career.py` (filter type
  per series).

- **verified** — Acceptlist entries are car identity strings ending in a
  12-digit car id; 907 entries across the 163 series, all of that shape.
  *How to reproduce:* the audit's acceptlist check parses every entry.

- **verified** — The PI, power, weight, cost and year bounds are zero in every
  series: they are inert, and the effective cap is the event's `TargetPI`
  (`RACE_SYSTEM.md` §2.11). *How to reproduce:* the same table — one distinct
  value (0) in each of those columns.

## 1.6 `DefaultEventOverrides` — 15 fields

Series-level defaults applied to every event of the series.

| field | purpose | default |
|---|---|---|
| `AIDifficulty` | AI skill label | `NewRacer` (138), `Expert` (38), `Average` (2) |
| `DamageDifficulty` | damage model | `Cosmetic` (138) / `FuelTire` (40) |
| `DynamicTrackEnabled` | evolving track state | true (178) |
| `DraftingEnabled` | slipstream | true |
| `TireFrictionWearScalar` | tyre wear rate | 1.0 (108), 4.0 (56), 3.0 (10), 6.0 (4) |
| `TimeOfDayTimeScale` | time-of-day speed | 5.0 (133) |
| `OpenPracticeInMinutes` | practice length | 30 (137), 10 (40), 600 (1) |
| `MinutesUntilNextEventStart` | delay between events | 0 |
| `MaxAIPlayers` | AI slots | 23 (all) |
| `MaxPlayers` | session size | `TwentyFour` (112) / `One` (66) |
| `NumPlayerBuckets` | player grouping | 1 |
| `Buckets` | bucket definitions | empty |
| `PracticeSkipLapEnabled` | skip the practice out-lap | false |
| `QualifyingSkipLapEnabled` | skip the qualifying out-lap | false |
| `QualificationOptions` | limit type, lap limit, one-shot flag | `Unlimited`, 0, false |

- **verified** — `MaxPlayers` is either a full session or a solo series, and
  `MaxAIPlayers` is always 23. *How to reproduce:*
  `python _tools\audit_career.py` (series-defaults columns).

## 1.7 `AIRaceBehaviors` — 2 blocks × 6 flags

Two blocks, `FeaturedRace` and `PracticeAndQualification`, each with
`SessionType`, `EnableDifficultySlowDown`, `EnableDifficultyCatchUp`,
`EnableSlotCarRaceStart`, `EnablePosDifficultySpread`,
`EnableDifficultyProximity`.

- **verified** — Catch-up and slow-down are true on the race block of all 178
  series; `EnableSlotCarRaceStart` is true on only 2 of them, and that flag is
  the only start-related switch in the career schema (there is no start-type
  field — `RACE_SYSTEM.md` §2.8). Only **2** series (11594, 11556) have it on;
  the other 176 share one identical behaviour block.
  *How to reproduce:* read the behaviour block of each series and compare.

## 1.8 Event — 18 fields

| field | purpose | default |
|---|---|---|
| `EventDataId` | event identity (65897900–65899999 for customs) | unique |
| `ChampionshipId` | owning championship | 500 |
| `ChampionshipSeriesId` | owning series | set by the series |
| `Name` | display name, **literal** (not an `IDS_` key) | track name |
| `Description` | description, as an `IDS_` key | one shared key (522) |
| `TrackId` | track identity, GUID form | derived from `SerialTrackId` |
| `SerialTrackId` | track identity, integer form | must match `TrackId` |
| `NumberOfRequiredLaps` | race length in laps | 1 (298), 3 (281), 2 (46), 4 (2) |
| `OpenPracticeLimitationTimeInSeconds` | practice budget; 0 removes practice | 600 (316) |
| `TargetPI` | performance cap for the field | 900 (125), 800 (120), 700 (72) |
| `PointSpread` | points-per-position table | one constant 24-value table |
| `TargetLapTimeInSeconds` | reference lap time | 0 |
| `TargetLapTimeAdjustmentInSeconds` | offset on the reference | 0.0 |
| `ImagePath` | event poster | empty on all 627 |
| `TrackMapImagePath` | map art | one shared GAME: path |
| `TrackRibbonImagePath` | ribbon art | one shared GAME: path |
| `TrackEnvironmentImagePath` | environment art | 29 distinct paths |
| `TrackLoadingScreenImagePath` | loading art | 8 distinct paths |

- **verified** — The career event has no start-type field, no weather field and
  no pit field: laps, practice and PI are the only race-shape controls here.
  Weather and pits live in the override (§1.9).
  *How to reproduce:* the field list above — 18 names, none of them those.

## 1.9 Event override — 10 keys

One or more override records per event, matched by `ID` == `EventDataId`.

| key | purpose | default |
|---|---|---|
| `ID` | matches the event id | — |
| `Enabled` | apply this override | true (all 1086) |
| `Track` | track for this slot; must equal the event's `SerialTrackId` | event track |
| `PracticeAndQualifying` | 5-key session block (weather, time of day, time-scale override) | one block |
| `FeatureRace` | 8-key race block (laps, pits, weather, time of day, class/PI hints) | one block |
| `ParentGeneratorId` | generator template the slot was cloned from | donor's template |
| `ClassRestriction` | maximum class (0–8, ceiling 300…999) | 5 (164), 6 (157), 3 (76) |
| `TargetPI` | per-slot performance cap | 900 (137), 800 (132), 700 (72) |
| `AIFileName` | AI field document to load | `AIField_<id>_Gen.xml` |
| `Type` | race type discriminator | `BCSharedEventData` (all) |

Nested keys: `FeatureRace` = `WeatherForecast`, `Laps`, `Pits`,
`TimeOfDayHour`, `TimeOfDayMinute`, `_321Type` (373 of 1086: `Rolling` 219, `Full` 154),
`TimeOfDayTimeScale`, `TimeOfDayTimeScaleOverride`; `PracticeAndQualifying` =
`WeatherForecast`, `TimeOfDayHour`, `TimeOfDayMinute`, plus the two time-scale
keys (32 of 1086).

- **verified** — The override file holds **1086** records: **687** match a
  career event and **399** (336 distinct ids) match no career event at all.
  612 career events have exactly one override and 15 have five.
  *How to reproduce:* `python _tools\audit_career.py` (override coverage); the
  unmatched records are the Featured/multiplayer side (§2.5).

- **observed** — The five-record events are shared event slots: the same `ID`
  appears once per track variant, so an event is not guaranteed a single
  override block. Editing "the" override of such an event means editing five.
  *How to reproduce:* group the override rows by `ID` and count.

- **verified** — `ClassRestriction` never takes `-1` in the career (values 0–8
  only); `-1` does appear outside the career (207 records), so a validator must
  not assume the value is career-shaped.
  *How to reproduce:* the class column split by career / non-career rows.

- **verified** — The override's `Laps` differs from the event's
  `NumberOfRequiredLaps` on 600 of 627 events; `TargetPI` agrees on 627 of 627.
  *How to reproduce:* `python _tools\audit_career.py` compares the two copies
  field by field.

---

# Part 2 — Championship 1 (Featured / Multiplayer)

## 2.1 A different shape

- **verified** — Championship 1 is **not** in the career schedule: it lives in
  its own metadata document, whose championship object has **8 fields**:
  `ChampionshipId`, `Name`, `Title`, `Description`, `ImagePath`, `FTUESeries`,
  `SeriesTypeData`, `ChampionshipSeriesData` (empty). There are no cups and no
  ladders.
  *How to reproduce:* read the racers-cup metadata document with the project's
  CMS reader and inspect the championship object; `python _tools\audit_career.py`
  shows the career side has no id 1.

| championship | document | nesting | series | events |
|---|---|---|---|---|
| 500 career | career schedule | championship → cup → ladder → series → event | 178 | 627 |
| 1 Featured/MP | racers-cup metadata | championship → series type → collection → series → event | 62 | 4348 |
| 22 intro (FTUE) | FTUE schedule | championship → series → event | 1 | 2 |

## 2.2 Series types and collections

- **verified** — Championship 1 has **5** series types, each carrying a
  `SeriesTypeName` (`IDS_` key) and a list of `SeriesCollections`.
  *How to reproduce:* count `SeriesTypeData` entries in the metadata document.

- **verified** — A collection has **8 fields**:
  `SeriesCollectionName`, `Enabled`, `StartDate`, `SeriesCycleLength`,
  `PlaylistCycleLength`, `EnableRecurrence`, `ScheduledSeriesData`,
  `CycledSeriesData`. *How to reproduce:* the collection objects in that
  document.

| collection field | purpose | default |
|---|---|---|
| `SeriesCollectionName` | label key | one per collection |
| `Enabled` | collection active | true |
| `StartDate` | rotation anchor | `2025-01-02T00:00:00Z` |
| `SeriesCycleLength` | how long one series stays | `7.00:00:00` on the rotating collections; `00:00:00` on the evergreen one |
| `PlaylistCycleLength` | how long the playlist stays | `7.00:00:00` |
| `EnableRecurrence` | repeat forever | true |
| `ScheduledSeriesData` | series pinned to a window | 17 across all collections |
| `CycledSeriesData` | series that rotate through the cycle | 44 across all collections |

- **verified** — 61 series are distributed over the collections as 17
  scheduled + 44 cycled; the championship's `FTUESeries` holds one more, giving
  62 series and 4348 embedded events.
  *How to reproduce:* count both lists across every collection, then add
  `FTUESeries`.

## 2.3 Series — 16 fields

| field | purpose | default | portable to single-player? |
|---|---|---|---|
| `ChampionshipSeriesId` | series identity | unique | **viable** — the career uses the same id space (career ids and 1's ids overlap in range, but a moved series must be given an unused id ≥ 20000) |
| `ChampionshipId` | owning championship | 1 | **viable** — a career copy sets 500 |
| `Name` / `Description` | label keys | unique `IDS_` keys | **viable** — same key convention |
| `ImagePath` / `BannerImagePath` / `ButtonImagePath` | art | GAME: paths | **viable** — the career series has the same three fields |
| `ChampionshipEventData` | the series' events | 2–1187 per series | **partial** — the event record differs (§2.4): 7 career-only fields are missing, so the events must be rebuilt, not copied |
| `StartEndDate` | availability window | sentinel pair | **viable** — same sentinel dates |
| `Challenges` | challenge definitions | empty on all 62 | **not viable** — the career series has no such field, so the content would be dropped silently |
| `DefaultEventOverrides` | 15-field defaults block | one block | **viable** — the block has the same 15 fields as the career's |
| `SeriesEnableCarSelectBetweenEvents` | allow car changes mid-series | true | **viable** — career series allow it implicitly |
| `SeriesRules` | **numeric rule enum** (4 on 55, 23 on 6, 22 on 1) | 4 | **not viable** — the career series record has no `SeriesRules` field at all (§1.4) |
| `EntryCriteria` | gate block | all empty | **viable** — same 8 sub-fields |
| `PlaylistCycleLengthCopyTicks` | playlist timing copy | mirror of the collection | **not viable** — there is no playlist cycle in the career |
| `IsEvergreen` | always available | true (58), false (4) | **partial** — the career has no equivalent flag; a copy has to express it with the sentinel dates |

- **verified** — `SeriesRules` exists as a numeric enum on the Featured series
  and does **not** exist on the career series. This is the field the career
  schema is missing, which is why career series cannot display per-series rules.
  *How to reproduce:* compare the field lists of the two series records.

- **verified** — Featured series have **no** `SelectableCars` and no
  `AISelectableCars`: car and AI gating is not expressed on the series there.
  *How to reproduce:* the field list above — 16 names, neither present.

## 2.4 Event — 14 fields (a trimmed record)

| field | purpose | default | portable to single-player? |
|---|---|---|---|
| `EventDataId` | event identity | unique | **viable** — same id space, but a career copy must use the custom range |
| `ChampionshipId` / `ChampionshipSeriesId` | owners | 1 / series | **viable** |
| `Name` / `Description` | label | literal name, key description | **viable** |
| `TrackId` | track identity (GUID only) | per event | **partial** — the career event also needs `SerialTrackId`, and the two must agree |
| `ImagePath`, `TrackMapImagePath`, `TrackRibbonImagePath`, `TrackEnvironmentImagePath`, `TrackLoadingScreenImagePath` | art | GAME: paths | **viable** |
| `CarRestrictionNames` | car restriction expressed as **names** | per event | **not viable** — the career gates cars by `SelectableCars` + `TargetPI`, and has no name-based restriction |
| `LocPlaylistFormat` | playlist label format | per event | **not viable** — no playlist surface in the career |
| `Type` | race type discriminator | per event | **partial** — the career event has no `Type` field; the override carries one |

- **verified** — The Featured event record is missing 7 fields the career event
  has: `NumberOfRequiredLaps`, `OpenPracticeLimitationTimeInSeconds`,
  `TargetPI`, `TargetLapTimeInSeconds`, `TargetLapTimeAdjustmentInSeconds`,
  `PointSpread` and `SerialTrackId`. It adds 3 the career does not have:
  `CarRestrictionNames`, `LocPlaylistFormat`, `Type`.
  *How to reproduce:* intersect the two field lists — 14 = 18 − 7 + 3.

- **observed** — Because the Featured event has no lap count and no PI cap,
  those must come from somewhere else in that content pipeline. That "somewhere"
  is not in the career schedule and was not found in this audit; it is listed in
  `OPEN_QUESTIONS.md`.

## 2.5 Overrides for Featured content

- **verified** — 399 override records (336 distinct ids) in the override file
  match no career event. They do **not** match any Featured event either (0 of
  4348), so they belong to a third content set that this audit does not name.
  *How to reproduce:* intersect the override ids with the career and Featured
  event ids.

- **verified** — All 1086 override records share the identical 10-key schema,
  whatever content they belong to. *How to reproduce:* the key union over the
  whole file is the 10 keys of §1.9.

- **hypothesis** — The 336 unmatched overrides are the multiplayer/Featured
  race slots, and their events live in a schedule this audit does not read.
  *How to reproduce:* not yet possible — tracked in `OPEN_QUESTIONS.md`.

## 2.6 What this means for porting

- **verified** — Everything at the *override* level transfers without changes
  of shape: class ceiling, per-slot PI, AI field document, generator template
  and race block are the same 10 keys on both sides.
- **verified** — Everything at the *event* level does not: a Featured event has
  no lap count and no PI cap, so a career event cannot be produced from it by
  copying.
- **verified** — Everything at the *series* level transfers except the four
  Featured-only fields (`Challenges`, `SeriesRules`,
  `PlaylistCycleLengthCopyTicks` and the `IsEvergreen` shortcut), which the
  career schema has no slot for.

---

# Part 3 — Client feature flags

## 3.1 Where they live

The client reads a flag document, `ClientFeatureFlagConfiguration.json`, from
the CMS cache (not from the install; the install keeps only an opaque copy). It
holds about 400 named settings in some 55 blocks named
`FeatureFlagConfig.<System>Config` (for example `AIConfig`,
`ChampionshipObjectivesConfig`, `FuelAndTireWearEstimateConfig`,
`NewFeaturesConfig`): booleans named `Enable<Feature>`, tuning numbers, and a
few per-game-mode lists keyed by `GameMode` (`BuildersCup` is the career). Like every CMS payload it is
encrypted and re-applied with the same size/checksum model as the schedule.

## 3.2 What is proven

- **verified** — Turning `EnableBuildersCupChallengeTheGrid` off removes the
  challenge-the-grid (wager) screen from the career. Removing the wagers or the
  whole `ChallengeTheGridData` block from a cup did **not** remove it: the
  screen is gated by the flag, the cup block only feeds it.
- **verified** — The server does not overwrite the cached flag document within
  a session: the change held in game.
- **verified** — `EnableBuildersCupChallengeTheGrid` is **one boolean for the
  whole client** (`NewFeaturesConfig`), with no per-series scope. Despite the
  name it is read by every career series, vanilla ones included, while it is off.
  Whether it also reaches Featured/Multiplayer events is **not verified**: it
  needs one online event opened with the flag off.
- **observed** — The wager screen, when on, is what lets the player pick the
  starting slot; with it off the slot comes from the session generator
  (a fixed value, or the AI-rank cut described in the race-system reference).
- **hypothesis** — Other flags behave the same way (one flag tested so far).
  A read-only survey has classified every flag (summary table below); each
  career or layout-touching flag carries one proposed single-value test.

**Survey summary.** A read-only walk of the flag document counted **417**
settings in **53** `FeatureFlagConfig.*` blocks (8 blocks empty), classified by
name and structure:

| class | count | meaning |
|---|---|---|
| career | 12 | named for the career (`BuildersCup`, `Career`, championship objectives) or the `BuildersCup` entry of a per-game-mode list |
| shared | 115 | one switch or table that also reaches Featured/Multiplayer — includes every `AIConfig.*` setting, even the ones with `Career` in the name |
| closed | 119 | account, server, matchmaking, economy, progression or Featured-only screens — never touched for the career |
| unknown | 171 | menu, HUD or cosmetic switches with no career link in name or structure |

What the map says:

- No flag takes a series or event id: every flag is one value for the whole
  client, so a test is always one change plus a control check that a
  Featured/Multiplayer event is unchanged.
- The only per-mode separator found is the `BuildersCup` entry of the fuel
  scale list; the tire-type per-mode list carries no career entry, so the
  career is unreachable through it today.
- First candidates are the career-named toggles (championship objectives,
  career practice skip), the qualifying wait, the `BuildersCup` fuel entry
  and the pit-stop minimum — each with one value to flip, one career screen
  to watch and one online event as control.

## 3.3 Scope rule

A flag is a *global* switch. Prefer flags whose name scopes them to the career
(`BuildersCup`, championship objectives, career-only screens) or entries of a
per-game-mode list whose `GameMode` is `BuildersCup`. Flags shared with
Featured/Multiplayer (every `AIConfig.*` setting, even the ones with `Career`
in the name, and generic tire/fuel or AI switches) change online play too and are out of scope for this project unless a test proves they
are career-only.

## 4. Traps worth knowing

| trap | why it bites |
|---|---|
| `CarSelectAcceptlist` looks like the acceptlist | it is empty on all 178 series; the live list is `SelectableCars.BlockOrAcceptlist` |
| `SeriesOrderData` looks like the ordering | it is empty on all 178 series; order is `OrderedEventIds` |
| one event, one override | 15 career events have five override records |
| `ClassRestriction` is never `-1` | true in the career, false outside it (207 records) |
| the career event is the whole event schema | the Featured event has 14 fields, a different set |
| `SeriesRules` is missing from the schema | it is missing from the *career* series only; Featured has it |
| deleting `ChallengeTheGridData` hides the wager screen | it does not; the client flag `EnableBuildersCupChallengeTheGrid` does (§3.2) |

## See also

`CAREER_MODEL.md` · `RACE_SYSTEM.md` · `CARS_AND_PI.md` · `AI_GRIDS.md` ·
`DATA_REFERENCE.md` · `CAREER_AUDIT.md` · `GLOSSARY.md` · `OPEN_QUESTIONS.md`
