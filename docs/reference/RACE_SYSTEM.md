# Race system

How a career event is described in the data: the event record, the override
record, laps, practice and qualifying, pit stops, weather, start type, the
series defaults block, and the two fields that actually decide who can drive
(`TargetPI` and `ClassRestriction`).

Scope is the **career** (championship 500) unless a line says otherwise.
Championship 1 uses a different document and a trimmed record shape, and is
never modified — see
`CAREER_MODEL.md`, part 2. Evidence labels are defined in `CAREER_MODEL.md`;
the two read-only reproduction commands are:

```powershell
python _tools\inventory.py
python _tools\audit_career.py
```

## 2.1 The event record — 18 fields

- **verified** — A `ChampionshipEventData` record has exactly **18 fields**:

| field | what it carries |
|---|---|
| `EventDataId` | the event id |
| `ChampionshipId` | owning championship (500 for the career) |
| `ChampionshipSeriesId` | owning series |
| `Name` | literal display string (not an `IDS_` key) |
| `Description` | literal display string |
| `TrackId` | track identity, GUID form |
| `SerialTrackId` | track identity, integer form |
| `NumberOfRequiredLaps` | lap count for the feature race |
| `OpenPracticeLimitationTimeInSeconds` | practice time budget |
| `TargetPI` | the effective performance cap for the field |
| `PointSpread` | points table id for scoring |
| `TargetLapTimeInSeconds` | reference lap time the game aims the field at |
| `TargetLapTimeAdjustmentInSeconds` | offset applied to the reference |
| `ImagePath` | poster art for the event |
| `TrackMapImagePath` | track map art |
| `TrackRibbonImagePath` | ribbon art |
| `TrackEnvironmentImagePath` | environment art |
| `TrackLoadingScreenImagePath` | loading art |

*How to reproduce:* read the field names of one event record in the career
data — the audit loader (`_tools\audit_career.py`, `model_from_bcs`) reads each
one of them.

- **verified** — There is no start-type field anywhere in this record, and no
  lap-count field other than `NumberOfRequiredLaps`.
  *How to reproduce:* the same field list.

## 2.2 The override record — 10 keys

Each event is matched by one or more override records in a sibling table (the
override file), with exactly ten keys. The record is **not** inside the series
object: the series holds the events, the override table holds the race slots.

| key | role |
|---|---|
| `ID` | override id |
| `Enabled` | whether the override applies |
| `Track` | track for this slot |
| `PracticeAndQualifying` | practice/qualifying block |
| `FeatureRace` | race block (laps, grid, class, PI) |
| `ParentGeneratorId` | generator template this slot was cloned from |
| `ClassRestriction` | maximum class allowed |
| `TargetPI` | performance cap for this slot |
| `AIFileName` | AI field document to load |
| `Type` | race type discriminator |

- **verified** — The override table holds 1086 records; 687 of them match a
  career event. 612 career events have exactly one override and 15 have five
  (the same `ID` repeated once per track variant), so "the override" is not
  always a single record. *How to reproduce:* `python _tools\audit_career.py`
  (override coverage), or group the override rows by `ID` and count.

- **verified** — The override's `TargetPI` and `ClassRestriction` are separate
  fields from the ones on the event record, and both copies exist for every
  event. *How to reproduce:* `python _tools\audit_career.py` (both copies are
  carried in its rows) or read one override record directly.

- **verified** — When the two copies of `TargetPI` were set differently, the
  game used the **event** record's value: raising the event `TargetPI` from 700
  to 999 made an A-class (700-cap) event list X-class cars and accept a car
  above 700, with the override untouched. *How to reproduce:* set only the event
  value, apply, open the event — the field and the eligibility follow the event
  copy; a 701-PI car was accepted in the recorded run.

- **hypothesis** — `ClassRestriction` in the override caps the class
  independently of `TargetPI`, so an event can list cars its ceiling forbids.
  The two events where the two values disagree (§2.10) are the case to settle
  this; see `OPEN_QUESTIONS.md`.

## 2.3 Laps

- **verified** — `NumberOfRequiredLaps` over all 627 events:

| laps | events |
|---|---|
| 1 | 298 |
| 3 | 281 |
| 2 | 46 |
| 4 | 2 |

*How to reproduce:* `python _tools\audit_career.py`, event histogram.

So a career event is 1–4 laps; there are no endurance lengths in the career
tree.

### Contradiction: two different lap counts per event

- **observed** — For **600 of 627** events, the override's `FeatureRace.Laps`
  does **not** equal the event's `NumberOfRequiredLaps`, while `TargetPI`
  agrees between the two copies for **627 of 627**. So the mismatch is specific
  to laps, not to overrides being stale in general.
  *How to reproduce:* `python _tools\audit_career.py` — it counts
  agreeing and disagreeing pairs for both fields.

- **verified** — **The override wins.** A bench series set one event to
  2 laps in the event record and 8 in the override, and another to the reverse;
  the HUD showed 8 and 2 laps. Write race length into `FeatureRace.Laps`
  (`build_series.py` does); the event's `NumberOfRequiredLaps` alone is inert.
  *How to reproduce:* the same two-event test (`OPEN_QUESTIONS.md` item 2).

## 2.4 Practice

- **verified** — `OpenPracticeLimitationTimeInSeconds` over all events:

| seconds | events | meaning |
|---|---|---|
| 600 | 316 | 10 min |
| 1200 | 265 | 20 min |
| 900 | 38 | 15 min |
| 300 | 3 | 5 min |
| 1800 | 3 | 30 min |
| 0 | 1 | no practice |

The six buckets cover 626 of 627 events; one event carries a value outside them.
*How to reproduce:* `python _tools\audit_career.py`.

- **verified** — A value of `0` removes the practice session for that event —
  it is a real switch, not "unlimited". *How to reproduce:* set the field to 0
  on an event that has practice, apply, open the event: the session is gone.

- **verified** — When the event leaves practice open, the session length also
  comes from the series defaults block, whose "practice minutes" field is
  30 min on 137 series, 10 min on 40 and 600 on 1. *How to reproduce:*
  `python _tools\audit_career.py`, series defaults histogram.

## 2.5 Qualifying

- **verified** — In the vanilla career, qualifying is uniform across all
  series: unlimited, no lap limit, not one-shot. *How to reproduce:*
  `python _tools\audit_career.py` — one distinct tuple for all series.

- **observed** — **Practice sets the AI's grid order, not the player's slot.** A
  bench series with the series' `QualificationOptions` set to a limited number of
  laps (the shape the Featured series use) plus `QualifyingSkipLapEnabled` and
  `PracticeSkipLapEnabled` gives a practice limited to those laps, and there is
  no separate "Qualifying" session — the practice is the only countdown. The race
  grid then reproduced the **practice classification of the AI**: the AI that set
  the quickest practice time lined up first and the rest followed in order (a
  single swap, from a tied time). Two runs on the live cache, one of them with
  the start-position wager screen switched back on, and the AI order was the
  practice order both times. The **player** did not follow it: with the wager
  screen off (one client flag, see [MODDING_SURFACE](MODDING_SURFACE.md)) he kept
  the same slot with the best practice time of the session and with no timed lap
  at all, so practice orders the AI and does not place the human.
  *How to reproduce:* run the same career event twice, once with a fast practice
  lap and once without completing a timed lap, and compare the practice
  classification with the race grid.

- **verified** — **The start-position wager sets the player's slot.** With the
  wager screen switched back on, the screen **suggests a start position of its
  own** — a computed slot, not the constant the screen-off state gives — and the
  slot the player picks on it is the slot he starts from: a control pick away
  from the suggestion was honoured in full, while the AI kept the practice order.
  So the player's slot is a real control (n=1). Whether the constant slot seen
  with the screen off is a fallback of this same path or another source is still
  open ([OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md) 16).
  *How to reproduce:* one client flag brings the screen back
  ([MODDING_SURFACE](MODDING_SURFACE.md)); on the same career event, note the
  suggested slot, then pick a different one and watch the start.

- **verified** — In vanilla, the grid ordering of the session generators splits
  in two shapes that always travel together: an estimated grid
  (`GridOrderingType=EstimatedLapTime` with `ClusterHumansAtIndex=-1`) or a
  qualifying grid (`GridOrderingType=Qualifying` with the human cluster index
  set to a real slot). No vanilla generator mixes the qualifying ordering with
  the "no cluster" value; the only exception is a handful of generators that
  randomise the grid. *How to reproduce:* read every `GameOptions_*` pair in the
  cache — those are the shapes that appear on the career generators. Both shapes
  were run in game on the same career event and neither moved the player's slot,
  and the qualifying-order run reproduced the same AI order as the estimated
  one, so this shape is not the lever.

- **observed** — **The suggested slot is a constant, not a computation on
  anything the data exposes.** On a 24-car grid the screen suggested the middle
  slot (12th) in every run: with the player's practice time the best of the
  session by about six seconds, with no timed lap at all, with cars of two
  different classes, with the payout table cut to one row, and with the block's
  projected race-time delta multiplied by ten. The screen-off state starts from
  another constant slot (7th on the oval used for the tests). Small samples
  (one to three runs each), but nothing moved either number.

- **observed** — **A real qualifying exists in the client, not in the career
  data.** The client has an event *activity* type named Qualification (separate
  from the eight session types, which have no such member), with its own track
  cinematic ("return to the pits"), a qualifying report and a provisional-grid
  screen, and a Qualify entry in the pre-race menu next to Practice. Which
  activity a career event runs as is not exposed by any field we could find.
  Tried and **found to have no effect on the career**: the grid-ordering shape of
  the session generator, the practice limit type (`Disabled` was ignored and the
  practice stayed limited), a series-level `SeriesRules` reference (the Featured
  series carry one, the career schema does not), the field size of the series and
  the AI roster document. The Featured championship's series data uses the same
  per-event override keys as the career, so the difference is not in them.

- **hypothesis** — `IsOneShot` turns it into a single timed lap; not tested.

## 2.6 Pit stops

- **verified** — Mandatory pit stops: **0** on 1058 slots, **1** on 20, **2** on
  8. The counts are per override slot rather than per event, which is why they
  do not add up to 627. *How to reproduce:* `python _tools\audit_career.py`.

- **observed** — **`Pits = 1` is enforced on the AI.** Two bench races, identical
  but for the length: on **2 laps** many AI cars were disqualified for not making
  the mandatory stop; on **4 laps** all 24 cars stopped (22 once, 2 twice) and the
  field finished normally. One run each, and no 4-lap control with `Pits 0`, so
  stops caused by tire wear are not ruled out. Practical rule: give a mandatory
  stop enough laps to fit it. *How to reproduce:* clone one event with `Pits 1`
  and 2 laps, another with `Pits 1` and 4 laps, run both and read the result
  table (the stops column and the disqualifications).

## 2.7 Weather

- **verified** — A single value, **11932**, dominates the weather field; it is a
  sentinel rather than a weather preset index. *How to reproduce:*
  `python _tools\audit_career.py` — one value on almost every
  event.

- **hypothesis** — 11932 means "inherit the track's default weather", because
  events carrying it show whatever the track does and no event sets it
  explicitly. No controlled test has been run.

## 2.8 Start type

- **verified** — The event record has no start-type field (§2.1) and only **2
  series** carry any slot-car-start flag; the override's race block carries an
  optional start-type attribute (see below).
  *How to reproduce:* `python _tools\audit_career.py`.

- **observed** — A custom event built from a Nordschleife donor started
  **rolling** in game, although the event data says nothing about a start type.
  *How to reproduce:* run that event and watch the start.

- **observed** — **The start type is a field of the session generator, not of
  the series flag.** The race-session generator template carries a start-type
  attribute (`_321Type`, values `Full`, `Rolling`, and `Restart` on the practice
  template), and about a third of the career overrides carry the same attribute
  inside the race block (`FeatureRace._321Type`), disagreeing with the generator
  in about 30 cases. In the audited table 373 of the 1086 records carry it (219
  `Rolling`, 154 `Full`). Which one wins is settled in the next bullet.
  Two bench series show the generator at work: the one whose generator says
  `Rolling` starts with a rolling lap; the one whose generator says `Full`
  starts standing **even with the series' slot-car-start flag switched on**. So
  that flag does not make the start rolling. *How to reproduce:* read
  `_321Type` in the race template of the event's generator, then run the event
  and watch the start.
- **verified** (n=1) — **`FeatureRace._321Type` in the override beats the
  shared generator.** Two bench series were built identical in everything (same
  track, laps, class cap, PI cap, AI field, same shared generator) except one
  key: the override of one carries `_321Type = "Rolling"`, the other has none.
  The one with the key started **rolling**; its twin, on the same generator,
  started **standing**. So the start type is a choice **per event**: add the key
  to one override and the shared generator never needs touching. One pair, one
  run each; repeat it on another track before treating it as a rule.
  *How to reproduce:* clone an event, insert `_321Type = "Rolling"` into the
  clone's `FeatureRace` block right after `WeatherForecast` (the spelling and
  position vanilla overrides use), leave the twin alone, and watch both starts.
  A cloned event that does **not** carry the key inherits the start from its
  generator, which is why it can behave unlike its new neighbours.

## 2.9 Series defaults — 15 fields

Every series carries a defaults block applied to its events. The block has
**15 fields**; the distributions below are over all 178 series.

| field | values (series count) |
|---|---|
| `AIDifficulty` | NewRacer 138, Expert 38, Average 2 |
| `Damage` | Cosmetic 138, FuelTire 40 |
| `DynamicTrack` | true 178 |
| `TimeScale` | 5.0 on 133 (remaining 45 differ) |
| `TireWear` | 1.0 108, 4.0 56, 3.0 10, 6.0 4 |
| `MaxPlayers` | 24 on 112, 1 on 66 |
| `MaxAI` | 23 on 178 |

*How to reproduce:* `python _tools\audit_career.py`; the 15 field names come
from one series record in the career data (same loader).

- **verified** — `MaxAI` is 23 on every series, and `MaxPlayers` is either a
  full session (24) or a solo series (1). *How to reproduce:* the same command.

- **observed** — `AIDifficulty` is NewRacer on 138 of 178 series: the career
  copy is overwhelmingly tuned to the lowest difficulty label regardless of the
  class or PI of its events. This is a tuning observation, not a bug claim.

## 2.10 `ClassRestriction` — a ceiling, never a "none"

- **verified** — `ClassRestriction` takes the values 0–8 in the career and
  **never** -1: it always names a maximum class. (Outside the career, -1 does
  appear, so a general validator must not assume the career shape.) 625 of 627
  events sit at or below their own ceiling; 2 do not.
  *How to reproduce:* `python _tools\audit_career.py`.

| value | max PI | max class | note |
|---|---|---|---|
| 0 | 300 | E | |
| 1 | 400 | D | |
| 2 | 500 | C | |
| 3 | 600 | B | |
| 4 | 700 | A | most common in the career |
| 5 | 800 | S | |
| 6 | 900 | R | |
| 7 | 998 | P | |
| 8 | 999 | X | open ceiling |

- **observed** — The two anomalies are events with `ClassRestriction` 5 (ceiling
  800 / class S) but `TargetPI` 900. Which of the two gates the player car is
  not proven; see `OPEN_QUESTIONS.md`.

- **verified** — The ceiling is a *maximum*: a lower-class car is always
  accepted by the class rule, and only the PI cap and the acceptlist can exclude
  it. *How to reproduce:* enter a low-class car in a high-ceiling event — the
  event accepts it.

## 2.11 `TargetPI` is the effective cap

- **verified** — The performance cap that actually bites is the event's
  `TargetPI`. Raising it from 700 to 999 opened a 700-cap event to X-class cars
  and to a player car above 700.
  *How to reproduce:* set the event `TargetPI` in a copy of the data, apply,
  open the event. See `CARS_AND_PI.md` for the PI scale and the per-class bands.

## 2.12 `PointSpread`

- **verified** — `PointSpread` is the same constant table on every event: one
  24-value points-to-position table reused everywhere, not a per-event choice.
  *How to reproduce:* `python _tools\audit_career.py` — one
  distinct table for all events.

- **observed** — Because the field never varies, it is a template artefact
  rather than a design decision per event: no event has a different points
  shape. *How to reproduce:* the same command.

## 2.13 `ParentGeneratorId`

- **verified** — Each override names a generator template
  (`ParentGeneratorId`) from which its slot was cloned. The template fixes
  track-dependent behaviour; pointing an event at a generator built for a
  different track breaks the cup (the event does not load correctly).
  *How to reproduce:* repoint one event's `ParentGeneratorId` to a template from
  another track in a copy, apply, open the cup — the cup fails to load; the
  audit lists each event's generator so a valid donor can be chosen.

## 2.14 Grid ceiling

- **verified** — A race holds at most **23 AI + 1 player = 24 cars**. No event
  in the data asks for more, and the AI field documents top out at 23 slots.
  *How to reproduce:* `python _tools\audit_career.py`, and the AI
  survey in `AI_GRIDS.md`.

## 2.15 Duration

- **observed** — Career duration can only be expressed in **laps**, and the
  data records no lap times, so no wall-clock duration can be derived from it:
  mean 7.0 laps per series, maximum 24. *How to reproduce:*
  `python _tools\audit_career.py`.
  Estimating minutes would need a lap-time table the data does not have — see
  `OPEN_QUESTIONS.md`.

## 2.16 Per-event levers — what each override key can change

The override (§2.2) is the one record you can edit to change a single event
without touching a generator that other events share. This table says, key by
key, how much we know. **verified** = seen in game or reproduced by a script;
**observed** = the data shows it, no controlled test; **hypothesis** = untested.

| key (inside the override) | what it controls | state | note |
|---|---|---|---|
| `FeatureRace.Laps` | race length | **verified** | beats the event's `NumberOfRequiredLaps` (§2.3) |
| `FeatureRace.Pits` | mandatory pit stops | observed (n=1) | enforced on the AI: 2 laps disqualified many, 4 laps all stopped (§2.6); player penalty and HUD not yet recorded |
| `FeatureRace.WeatherForecast` | weather forecast id | observed | 11932 on almost every slot; "inherit the track's weather" is a hypothesis (§2.7) |
| `FeatureRace.TimeOfDayHour`, `TimeOfDayMinute` | start time of day | hypothesis | values are in the data; no test moved them |
| `FeatureRace.TimeOfDayTimeScale`, `TimeOfDayTimeScaleOverride` | clock speed during the race | hypothesis | the series also has a `TimeScale` default (§2.9); which wins is untested |
| `FeatureRace._321Type` | standing (`Full`) or rolling (`Rolling`) start | **verified** (n=1) | beats the shared generator (§2.8); present on about a third of the overrides |
| `PracticeAndQualifying.*` | the same five weather/time keys for practice and qualifying | hypothesis | no key here adds a qualifying session (§2.5) |
| `AIFileName` | the AI field document that sets the grid | **verified** | pins the grid, not the series' car list ([AI_GRIDS](../guides/AI_GRIDS.md)); a document with an empty driver list ran the practice with no AI but **crashed the race** (observed, n=1) |
| `TargetPI` | performance cap | **verified** | when it differs from the event record's copy, the event's wins (§2.2, §2.11) |
| `ClassRestriction` | class ceiling | hypothesis | may cap the class on its own, independent of `TargetPI` (§2.2, §2.10) |
| `Track` | the track of the slot | observed | must equal the event's track; one id repeated per track variant (§2.2) |
| `ParentGeneratorId` | which generator template the slot was cloned from | **verified** (breaks) · hypothesis (gains) | pointing at another track's template breaks the cup (§2.13); that the template also carries the regulation, tuning and qualifying options is a hypothesis, tested by repointing one event |
| `Enabled` | whether the override applies | hypothesis | no test switched it off |

Order of the next bench tests, one key per test: pit stops (with laps), then
weather and time of day, then `ParentGeneratorId`.

## 2.17 Session generator options — what a generator brings with `ParentGeneratorId`

An override points at a **session generator** (§2.13): two XML files, one for the
race and one for practice and qualifying. Everything below comes with the generator
and is shared by every event that points at it, so a generator is edited only when
no other mode uses it. States as in §2.16.

| option (inside the generator) | what it is | state | note |
|---|---|---|---|
| `Buckets/Bucket` (`Name`, `MaxPlayers`) | the online mode's player group; the career has one | observed | the name is a label of the original online series |
| `Bucket/CarRestrictions` (same 38 fields as the series' `SelectableCars`) | the car filter of that group | **observed (n=1 pair)** | a strict class-R bucket refused a class C car the series allowed and accepted a class R one |
| `CarRestrictions@SeverityType` (`Strict`, `Warning`) | how hard the filter is | hypothesis | a `Warning` bucket (class A, PI 700) accepted a class C car |
| `CarRestrictions@BlackOrWhitelistType` | the list type (`Whitelist` on 176 series, `Blacklist` on 9) | open | how a class works under `Blacklist` is not known |
| `RaceRegulationsId` → regulations table | penalty rules: a ghost after leaving the leader's lap, off-track monitor, collision monitor, wrong way, disqualification | observed (parameters read); effect in game: hypothesis | the career uses 0 (none); the online series use 103 |
| `_321Type`, `StartingGridOptions@StartType` | the start | observed | the event override's `_321Type` beats it (§2.8) |
| `GridOrderingType`, `ClusterHumansAtIndex` | the AI order and the human's slot | **observed** | only rank order moves the human, and the index acts as a cut: first at 0, 2 and 5, last at 7, 8, 11 and 23, with no middle slot (D46); qualifying order gives a share of the field, 7th of 24 and 3rd of 8 (D47) |
| `GroupByBucket` | grid grouped by group | open | one group in the career |
| `MaxAIPlayers` | size of the AI field | **ignored** | the AI document decides (§2.16, D38) |
| `EndConditionOptions` (laps, time) | how an online race ends | open | the career uses the override's `Laps` |
| `TimeOfDay*`, `WeatherForecast*`, `TireFrictionWearScalar`, `DamageDifficulty` | conditions | observed | the override's keys (§2.16) take precedence where they exist; in the event override, `FeatureRace` weather and hour act on the race only and `PracticeAndQualifying` holds the practice's own (D48) |

**What comes with a generator for free:** the group, its car restriction, the
regulation, the grid ordering, the start type and the wear. **What does not:**
`MaxAIPlayers` (the AI document decides), the series-level group list and rules
reference (the career ignores them), and real matchmaking.

**To reproduce an online event in the career:** point the override at its generator,
give the series cars of the class its group asks for with a matching cap, and pick an
AI document of that class. An AI document with an empty driver list is not a way to
run it solo: the practice ran, the race crashed.

## See also

`CAREER_MODEL.md` · `CARS_AND_PI.md` · `AI_GRIDS.md` ·
`DATA_REFERENCE.md` · `CAREER_AUDIT.md` · `GLOSSARY.md`
