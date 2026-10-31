# Glossary

Terms used across this doc set, in alphabetical order. Definitions are pointers,
not evidence: the labelled claims, with their reproduction commands, live in the
page named at the end of each entry.

---

**Acceptlist** — A hand-written list of cars a series will field, held in
`SelectableCars.BlockOrAcceptlist` with `BlockOrAcceptlistType` = `Acceptlist`.
Entries are car identity strings; the last twelve digits are the `CarId`. An
acceptlist series typically sets its class requirement to any. Contrast
**blocklist**.
→ `CARS_AND_PI.md` §3.3

**AIField** — The asset document that actually pins an AI grid, named per event
override by `AIFileName`. Two kinds: `AIDrivatarTemplate` (a PI window plus a
pool, filled to the slot count) and `AIDrivatarList` (an explicit car per slot).
→ `AI_AND_GRIDS.md` §4.1–4.2

**`AIProgressionFrame`** — One frame inside a field document's
`DrivatarProgressionFrames` block, carrying a `PlayerPIRelativeToClass` value
and a lower/upper offset. The pool is drawn relative to the player's car in the
range of the active frame.
→ `AI_AND_GRIDS.md` §4.5

**`AI_<car>_<pi>`** — Naming pattern of the AI-only cars: a catalogue car with a
PI suffix, one file per class step. 541 exist, 508 are usable in a field.
→ `AI_AND_GRIDS.md` §4.3

**Blocklist** — A series' deny list of cars, used together with a fixed class
and no acceptlist. Mutually exclusive with the acceptlist mode in this data.
Both modes live in `SelectableCars`, in the `BlockOrAcceptlist` +
`BlockOrAcceptlistType` pair.
→ `CARS_AND_PI.md` §3.3

**`BlockOrAcceptlist`** — The list inside `SelectableCars`: 163 series fill it as
an `Acceptlist`, 15 leave it empty and set `BlockOrAcceptlistType` to
`Blocklist` instead.
→ `SCHEMA_REFERENCE.md` §1.5

**`CarClassId`** — The class requirement of a series. In this data it reads
"any" for acceptlist series and names a fixed class for blocklist series; the
effective per-event cap is `TargetPI` plus `ClassRestriction`.
→ `CARS_AND_PI.md` §3.3

**`CarDenyLists`** — The veto layer above the acceptlists. A **rule** is one
entry in that layer (32 exist); a **denied id** is a car covered by a rule (45
exist, 32 of them still listed in vanilla acceptlists). Rule and id are not the
same object: one rule can cover several ids.
→ `CARS_AND_PI.md` §3.4

**`CarSelectCarRestrictions`** — The per-series block that feeds the car-select
screen. Missing it makes the series throw a native exception when clicked.
→ `CAREER_MODEL.md` §1.7

**Championship** — A root record. Three exist, in three different documents:
**500** (career, cup → ladder → series → event), **1** (Featured/multiplayer,
series type → collection → series → event, no cups or ladders) and **22** (the
one-session intro). Only 500 is modified by this project.
→ `SCHEMA_REFERENCE.md` §1.1, §2.1

**`ChampionshipSeriesId`** — The id of a series, and the key an event uses to
name its owning series. Distinct from `EventDataId`; a series of 4 events has one
series id and four event ids.
→ `DATA_REFERENCE.md` §5.4

**`ClassRestriction`** — The maximum class an event admits, held on the override.
Values 0–8 map to ceilings 300/400/500/600/700/800/900/998/999; `-1` never
appears. It is a ceiling, not an allowed set.
→ `RACE_SYSTEM.md` §2.10

**`ContentManifest`** — The list inside a field document that maps the document's
car entries to their AI car files. Rows pointing at a file that no longer exists
break the field.
→ `AI_AND_GRIDS.md` §4.2

**Cup** — The level under the championship; it sequences its ladders through
`cup.LadderOrderData`. 7 in the career (6 vanilla + 1 custom).
→ `CAREER_MODEL.md` §1.2

**`DefaultEventOverrides`** — The series defaults block (15 fields) applied to a
series' events: AI difficulty, damage, dynamic track, time scale, tyre wear,
player/AI counts and the session defaults.
→ `RACE_SYSTEM.md` §2.9

**`EligibleCars`** — In a template document, the pool the PI window draws from.
In a list document its role is unproven.
→ `AI_AND_GRIDS.md` §4.2, `OPEN_QUESTIONS.md` 5

**`EventDataId`** — The event id. Custom events use 65897900–65899999; ids are
opaque and are never reused.
→ `DATA_REFERENCE.md` §5.4

**Event** — The leaf of the tree: one race slot with its own track, lap count, PI
cap and art. 627 in the career (623 vanilla + 4 custom).
→ `RACE_SYSTEM.md` §2.1

**`EventGeneratorMetaDataV2`** — The block that describes a generator template
and is referenced by `ParentGeneratorId`. Repointing an event at a template from
another track breaks the cup.
→ `RACE_SYSTEM.md` §2.13

**`IDS_` key** — The string-table key used by cup, ladder and series names (event
names are literals). Keys may be any length and are resolved by name hash, so
only the player's locale needs the new entry.
→ `DATA_REFERENCE.md` §5.5

**Install-only** — Content the career pipeline cannot carry, because it lives
outside the group the career data belongs to (the AI field document is the known
case). It needs an install-level writer, and a file verification or a new
snapshot reverts it.
→ `AI_AND_GRIDS.md` §4.1

**Kit** — A mod pack: the intended changes plus their packaged payloads and a
short note on scope and how to reapply. A kit is bound to the data snapshot it
was built against.
→ `DATA_REFERENCE.md` §5.8

**Ladder** — The level under a cup; it sequences its series through
`ladder.OrderData`. 35 in the career (34 vanilla + 1 custom).
→ `CAREER_MODEL.md` §1.2

**`LadderOrderData`** — The list on a cup holding the ids of its ladders, in
display order.
→ `CAREER_MODEL.md` §1.2

**`NumberOfDrivatars`** — The slot count a field document asks for. 23 in the
productive documents, matching the 23 AI + 1 player ceiling.
→ `AI_AND_GRIDS.md` §4.2

**`NumberOfRequiredLaps`** — The lap count on the event record. Career events
run 1–4 laps. It disagrees with the override's `FeatureRace.Laps` on 600 of 627
events.
→ `RACE_SYSTEM.md` §2.3

**`OpenPracticeLimitationTimeInSeconds`** — The practice time budget on the
event. `0` removes the session rather than making it unlimited.
→ `RACE_SYSTEM.md` §2.4

**`OrderData`** — The list on a ladder holding the ids of its series, in display
order.
→ `CAREER_MODEL.md` §1.2

**`OrderedEventIds`** — The list on a series holding the ids of its events, in
display order. Position in this list is the event's slot.
→ `CAREER_MODEL.md` §1.2

**`ParentGeneratorId`** — The generator template an override was cloned from. It
carries track-dependent behaviour (including the start type, by hypothesis).
→ `RACE_SYSTEM.md` §2.13

**PI (performance index)** — The numeric performance rating. The scale is
E 0–300, D 301–400, C 401–500, B 501–600, A 601–700, S 701–800, R 801–900,
P 901–998, X 999. The stored `PerformanceIndex` field in the car record is *not*
on this scale; use the class id.
→ `CARS_AND_PI.md` §3.1–3.2

**`PlayerPIRelativeToClass`** — The lower/upper offset pair in a progression
frame, applied to the player's car PI to define where the pool is drawn from.
→ `AI_AND_GRIDS.md` §4.5

**`PointSpread`** — The points-per-position table. One constant 24-value table
on every event in this data.
→ `RACE_SYSTEM.md` §2.12

**Series** — The level under a ladder; it sequences its events through
`OrderedEventIds` and owns the selectable-cars filter, defaults and gates. 178 in
the career (176 vanilla + 2 custom, ids ≥ 20000).
→ `CAREER_MODEL.md` §1.2, §1.11

**`SeriesCollection`** — The Featured/multiplayer level between a series type and
its series: 8 fields carrying the rotation anchor, the cycle lengths, recurrence
and the scheduled/cycled series lists. The career has no equivalent level.
→ `SCHEMA_REFERENCE.md` §2.2

**`SeriesRules`** — A numeric rule enum on the **Featured** series record (values
4, 22, 23 in this data). The career series record has no such field, which is why
career series cannot display per-series rules.
→ `SCHEMA_REFERENCE.md` §2.3

**`SelectableCars`** — The 38-field car filter on a career series: the real
acceptlist/blocklist plus ~30 optional attribute filters (class, PI, power,
weight, year, drivetrain, tuning…). Its PI/power/weight/cost bounds are zero
everywhere in this data. The series field `CarSelectAcceptlist` is a dead slot.
→ `SCHEMA_REFERENCE.md` §1.5

**`SeriesType`** — The series shape discriminator. `28` = `RewardShowcase` (28
series), the default on the remaining 150.
→ `CAREER_MODEL.md` §1.10

**`SerialTrackId` / `TrackId`** — The two identities of a track: an integer and a
GUID whose last twelve digits are that integer. They must always change together.
→ `DATA_REFERENCE.md` §5.4

**Snapshot** — One versioned copy of the game's content as delivered by the
server. The install carries two; counts differ between them (126–127 vs 177–178
series), so every number must state which snapshot it came from.
→ `DATA_REFERENCE.md` §5.8

**`TargetPI`** — The effective performance cap for an event, and the value used
to pick the AI field document. Raising it opens the event to higher-class cars
(subject to `ClassRestriction`). Also exists on the override, where the event
copy wins.
→ `RACE_SYSTEM.md` §2.11, `CARS_AND_PI.md` §3.5

**`Whitelist` / `Blacklist` mirror** — The car selectability XML mirrors the
series acceptlist (whitelist) and blocklist (blacklist). The two sides must agree:
editing one without the other leaves the series listing cars it will not accept.
→ `CARS_AND_PI.md` §3.3

**Warm-up run** — The first race after a grid change, which is suspected to
reuse the previous cars with recomputed PI, so the new roster only shows from
the second run on.
→ `AI_AND_GRIDS.md` §4.7, `OPEN_QUESTIONS.md` 7

## See also

`CAREER_MODEL.md` · `RACE_SYSTEM.md` · `CARS_AND_PI.md` · `AI_AND_GRIDS.md` ·
`DATA_REFERENCE.md` · `CAREER_AUDIT.md` · `OPEN_QUESTIONS.md`
