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

- **verified** — **Practice can set the grid.** A bench series with the
  series' `QualificationOptions` set to a limited number of laps (the shape the
  Featured series use) plus `QualifyingSkipLapEnabled` and
  `PracticeSkipLapEnabled` showed a practice limited to those laps, and the
  starting grid followed the practice lap times. There is no separate
  "Qualifying" session; the practice is the qualifying. Decline the Challenge the
  Grid wager when testing — choosing a start position overrides the result (the
  wager screen can be switched off by a client flag, see
  [MODDING_SURFACE](MODDING_SURFACE.md)).

- **hypothesis** — `IsOneShot` turns it into a single timed lap; not tested.

## 2.6 Pit stops

- **verified** — Mandatory pit stops: **0** on 1058 slots, **1** on 20, **2** on
  8. The counts are per override slot rather than per event, which is why they
  do not add up to 627. *How to reproduce:* `python _tools\audit_career.py`.

## 2.7 Weather

- **verified** — A single value, **11932**, dominates the weather field; it is a
  sentinel rather than a weather preset index. *How to reproduce:*
  `python _tools\audit_career.py` — one value on almost every
  event.

- **hypothesis** — 11932 means "inherit the track's default weather", because
  events carrying it show whatever the track does and no event sets it
  explicitly. No controlled test has been run.

## 2.8 Start type

- **verified** — Neither the event record nor the override has a start-type
  field (§2.1), and only **2 series** carry any slot-car-start flag.
  *How to reproduce:* `python _tools\audit_career.py`.

- **observed** — A custom event built from a Nordschleife donor started
  **rolling** in game, although the event data says nothing about a start type.
  *How to reproduce:* run that event and watch the start.

- **hypothesis** — The start type is inherited from the donor/generator
  (`ParentGeneratorId`) or from the track, not from the copied event fields.
  This is why a cloned event can behave unlike its new neighbours.

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

## See also

`CAREER_MODEL.md` · `CARS_AND_PI.md` · `AI_GRIDS.md` ·
`DATA_REFERENCE.md` · `CAREER_AUDIT.md` · `GLOSSARY.md`
