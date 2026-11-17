# Series and event field values (what vanilla uses)

Every value the game's own career series use, read from the live CmsCache on 14/11/2026:
**176 vanilla series** (ids below 20000) and **1080 vanilla event overrides**. "Used" means
seen in vanilla; it is **not** the game's allowed range. A value we tested is marked with its
decision (D72, D73 in [DISCOVERIES](../project/DISCOVERIES.md)); the rest are untested.

Where a field lives (three levels, plus the generator):

| level | file | holds |
|---|---|---|
| series, **DEO** (`DefaultEventOverrides`) | `BuildersCupScheduleDataV4.json`, inside each series | defaults for the series' events: AI difficulty, damage, wear, practice, qualifying |
| series, other fields | same file, same series | AI behaviour block, selectable cars, entry criteria, open and close times |
| event data | same file, `ChampionshipEventData` | practice laps, practice time, target PI |
| event **override** | `BCEventOverrides.json`, one row per event id | race and practice blocks (weather, hour, laps, pits, clock), start type, grid, generator |

## 1. DEO (series defaults)

| field | values used (series) | note |
|---|---|---|
| `TireFrictionWearScalar` | 1.0 (107), 4.0 (56), 3.0 (9), 6.0 (4) | **tested**: 6 against 1 at 10 laps lost grip (D72); above 6 unproven |
| `TimeOfDayTimeScale` | 5.0 (132), 4.0 (9), 8.0 (9), 6.0 (8), 2.0 (5), 12.0 (3), 24.0 (3), 14.0 (2), 7.0 (2), 0.0, 13.0, 7.5 (1 each) | **alone it does not move the race clock** (D73); the pair in the event override does |
| `DamageDifficulty` | `Cosmetic` (137), `FuelTire` (39); `Simulation` appears once elsewhere in the dump | the player's own difficulty choice probably decides whether wear exists (D72) |
| `AIDifficulty` | `NewRacer` (137), `Expert` (37), `Average` (2) | **tested** (16/11): NewRacer, Average and Expert gave the same grid and pace; no effect |
| `OpenPracticeInMinutes` | 30 (137), 10 (39) | **tested** (16/11): 30 did not make a 30-minute practice; the practice stayed limited by laps; no effect |
| `PracticeSkipLapEnabled` | `false` (176) | our bench base (20059) has `true`; **tested** (16/11): `false` did not remove the skip button in practice |
| `QualifyingSkipLapEnabled` | `false` (176) | bench base `true`; **not testable**: the career has no qualifying session |
| `QualificationOptions.QualificationLimitType` | `Unlimited` (176); `LimitedLaps` exists in other files | bench base `LimitedLaps` with 2 laps; **not testable**: the career has no qualifying session |
| `QualificationOptions.NumLimitedLaps`, `IsOneShot` | 0 and `false` (176) | |
| `MaxPlayers` | `TwentyFour` (111), 1 (65); `Twelve` appears once elsewhere | **tested** (16/11): 1 opened and still showed a 24-car grid; no effect |
| `MaxAIPlayers` | 23 (176) | **tested** (16/11): 1 still showed 24 drivers; the AI document decides |
| `DraftingEnabled`, `DynamicTrackEnabled` | `true` (176) | |
| `MinutesUntilNextEventStart`, `NumPlayerBuckets`, `Buckets` | 0, 1, empty (176) | |

## 2. Series level (outside the DEO)

| field | values used | note |
|---|---|---|
| `AIRaceBehaviors.FeaturedRace.EnableDifficultySlowDown`, `...CatchUp`, `...Proximity` | `true` (176) | the rubber-band switches; **our bench base has all three `false`** |
| `...FeaturedRace.EnablePosDifficultySpread` | `true` (174), `false` (2) | bench base `false` |
| `...FeaturedRace.EnableSlotCarRaceStart` | `false` (174), `true` (2: the two Modern NASCAR series, 11556 and 11594) | not the start-type switch (start comes from the generator or the override); bench base `true` |
| `...PracticeAndQualification.*` | CatchUp `false`, SlowDown `false`, Proximity `true`, PosSpread `true`, SlotCar `false` (176) | **tested, inconclusive** (17/11): flipped at once, race unchanged; keep vanilla (D90) |
| `SessionType` (both blocks) | `None` (176) | |
| `SeriesType` | `Default` (149), `RewardShowcase` (27) | `RewardShowcase` locks the car; **tested** (16/11) on a clone: the series completed and paid nothing (the clone defines no prize; the server decides prizes) |
| `SkipBuildPhase` | `false` (134), `true` (42) | **tested** (16/11): `true` skips the build phase |
| `FirstCarSelectEnabled`, `PlayIntroVideoFullScreen` | `false` (175), `true` (1) | |
| `EntryCriteria.RequiredSeriesCount` | 1 (148), 4 (17), 0 (8), 8 (2), 7 (1) | `RequiredSeries` gates a series on others (tested in the group-gate rounds); **tested** (16/11): 8 with an empty list kept the series locked, the hub did not break |
| `EntryCriteria.RequiredLaddersCount` | 0 (172), 1 (4) | |
| `EntryCriteria.MinDriverLevel`, `RequiredEventsCount` | 0 (176) | |
| `OpenTime`, `StartEndDate.From` | 28 distinct dates; `1-1-1` (47) is "always" | |
| `CloseTime`, `StartEndDate.To` | `3000-5-22` (121), `9999-12-31` (47), four 2025 dates | |
| `SelectableCars.BlockOrAcceptlistType` | `Acceptlist` (161), `Blocklist` (15) | |
| `SelectableCars.CarClassId` | `Any` (161), and one series each of D, C, B, A, S, R, E, P, X | |
| `SelectableCars.SeverityType`, `MiniCareerId` | `None` and 0 (161); `Strict` and -1 (15) | |
| `SelectableCars` other filters | all open (`Any`, 0, 255 for car level) in every series | the car list is the acceptlist |

## 3. Event data (`ChampionshipEventData`)

| field | values used (623 events) | note |
|---|---|---|
| `NumberOfRequiredLaps` | 1 (297), 3 (278), 2 (46), 4 (2) | the **practice** laps; the race laps live in the override |
| `OpenPracticeLimitationTimeInSeconds` | 600 (313), 1200 (265), 900 (38), 300 (3), 1800 (3), 2100 (1) | |
| `TargetPI` | 20 distinct values from 300 to 999 (500, 600, 700, 800 and 900 are the common ones) | |
| `TargetLapTimeInSeconds`, `TargetLapTimeAdjustmentInSeconds` | 0 (all) | **tested** (17/11): 60 and 150 s showed no effect (D89); keep 0 |

## 4. Event override (`BCEventOverrides.json`, 1080 vanilla rows)

| field | values used | note |
|---|---|---|
| `FeatureRace.Laps` | 1 to 67 (36 distinct); 2 (223), 4 (215), 5 (185), 6 (164) are the common ones | beats the event's laps (verified); **tested** (16/11): 1 and 67 both held |
| `FeatureRace.Pits` | 0 (1052), 1 (20), 2 (8) | `Pits` 1 demands a stop; **tested** (17/11, D90) |
| `FeatureRace.WeatherForecast` | 107 distinct ids; 11932 (401), 10 (103), 12 (102), 26 (70) | existing ids work (**tested** 16/11: 13 overcast, 10 clear, 26 storm); the body is editable (D74). 11932 is one 480 s phase with five skies at 20% each, and four races all started clear: a single phase seems to take its first condition (observed, not proved) |
| `FeatureRace.TimeOfDayHour` | 0 to 23, commonest 15 (134), 14 (126), 16 (106), 10 (107), 17 (101), 19 (99), 9 (89), 0 (72) | **tested** (16/11): 0, 15 and 23 held |
| `FeatureRace.TimeOfDayMinute` | 0 (614), 40 (341), 30 (39), 50 (34), 45 (19), 52 (18), 20 (7) and five more | **tested** (16/11): 30 and 45 set the start clock to 15:30 and 15:45 |
| `FeatureRace.TimeOfDayTimeScale` + `...Override` (pair, 13 rows) | 16.0 (6), 12.0 (4), 32.0 (2), 0.0 (1) | **tested**: 60 and 144 move the race clock, 144 faster than 60 (D73); 16 and 32 also moved it (16/11) |
| `FeatureRace._321Type` | `Rolling` (218), `Full` (154); absent in 708 | start type; beats the generator (verified n=1); **tested** (16/11): `Rolling` gave a rolling start and `Full` a standing start; a generator with `Rolling` also gave a rolling start |
| `PracticeAndQualifying.WeatherForecast` | 53 distinct ids | **tested** (16/11): 12 gave a partly cloudy practice |
| `PracticeAndQualifying.TimeOfDayHour` | 0 to 22, commonest 10 (211), 14 (146), 6 (114), 8 (105), 16 (93), 0 (82), 12 (79) | **tested** (16/11): 22 and 5 each set the practice hour, the race hour stayed 18 (D87) |
| `PracticeAndQualifying.TimeOfDayMinute` | 0 (1008), 30 (28), 15 (14), 45 (12), 20 (8) and four more | **tested** (17/11): 30 and 15 set the practice clock minute (D90) |
| `PracticeAndQualifying.TimeOfDayTimeScale` + `...Override` (pair, 31 rows) | 1.0 (22), 0.0 (9) | untested: the practice is too short to see the clock move |
| `ClassRestriction` | -1 (207), 5 (210), 6 (188), 4 (121), 3 (97), 2 (83), 1 (68), 7 (67), 8 (27), 0 (12) | -1 with `TargetPI` 0 is the open-class pattern; **tested** (16/11): -1 alone, with `TargetPI` 0, or with PI 800 left the grid and the UI limit unchanged; the AI document decides the grid |
| `TargetPI` | 0 (207), 800 (178), 900 (167), 700 (114), 600 (89), 500 (76), 400 (68), 998 (67), 999 (27) and 14 more | **tested** (16/11): 300 in the override blocked an S 800 car (the UI limit still showed S 800); 999 let it in and did not open the grid |
| `ParentGeneratorId` | 284 distinct generators | **tested** (16/11): 123 (a generator with local `GameOptions`) changed the start to rolling; the grid stayed the override's document; 4676 and 58936 (no `GameOptions` in the manifest) failed the connection; 56 crashed (cause open); use only generators with a local definition |
| `AIFileName` | one AIField document per slot | pins the grid (verified; again on 16/11 with a generator that names another document); the empty document `AIField_70560000` crashes the race (D45), do not use |

## 5. What the audit found missing from our bench base

Our bench series are clones of 20059. Against the vanilla values above they differ in:
the AI behaviour block (rubber band off, slot-car start on), the DEO (`AIDifficulty` `Expert`, 10-minute
practice, skip-lap on, two-lap qualifying) and the generator (4684). In the event override only
`_321Type` and the two clock pairs were missing. Results from the bench therefore describe a bench AI,
not the vanilla one.
