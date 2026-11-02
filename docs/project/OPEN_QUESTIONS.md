# Open questions

These are the questions that controlled in-game tests will settle. Each one has
what is already known, why the answer matters and a **concrete experiment** that
decides it. Every claim in this doc set marked **hypothesis** has an entry
below; nothing here is a fact about the game — treat the whole page as work to
do.

Scope is the career (championship 500) unless stated. Reproduction and survey
commands are the ones named in the pages that raise each item.

---

## 1. Where is the start type stored?

**Question.** Rolling and standing starts are visible in game; where does the game
read the start type from? — **answered** (one pair; repeat on another track)

**What we know.** **observed** — the session generator's race template carries a
start-type attribute (`Full` = standing, `Rolling`), and about a third of the
career overrides carry the same attribute in their race block. A bench series on
a `Rolling` generator started with a rolling lap; a second bench series on a
`Full` generator started standing **although its series flag for a slot-car start
was on** — so that flag is not the lever (one run each, user reports). A custom
event cloned from a Nordschleife donor started rolling, consistent with an
inherited generator.
**verified** (n=1) — the override's value wins over the generator's (they
disagree in about 30 overrides). A twin pair on the same `Full` generator,
identical but for `FeatureRace._321Type = "Rolling"` in one override: the one with
the key started rolling, the other standing.

**Why it matters.** A new event picks its start type by one override field; the
shared generator never needs touching.

**What is left.** One pair, one run each: repeat it on a second track, and try
`Full` on an event whose generator says `Rolling`. Details and the other
override keys: [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.8 and §2.16.

## 2. Which lap count wins — the event's or the override's? — **answered**

**Question.** `NumberOfRequiredLaps` and `FeatureRace.Laps` disagree on 600 of
627 events. Which one does the race run?

**Answer.** **verified** — **the override wins, in both directions.** A bench
series ran the same track twice: event 2 laps / override 8 laps raced 8 laps on
the HUD, and event 8 / override 2 raced 2. Write race length into the override
(`build_series.py` does).

**Why it mattered.** Every new event or rebalanced lap count has to be written
into the field that matters; edits to the event's lap count alone are inert.

## 3. How are series rules wired in the career?

**Question.** The **career** series record has no `SeriesRules` field, yet the
Featured series record does (a numeric enum: 4 on 55 series, 23 on 6, 22 on 1).
How does the career UI decide to show rules at all?

**What we know.** **verified** — 28 fields per career series, none of them
`SeriesRules`, and `SeriesOrderData` is always empty. **verified** — the Featured
series carries the field and the values are enum ids, not text. **hypothesis** —
the career derives any rule text from `SeriesType` (28 = `RewardShowcase`), the
acceptlist shape, or a build-side table.

**Why it matters.** A new career series that should show rules shows nothing, and
there is no obvious field to fill; conversely, the enum has no career slot to be
ported into.

**Test.** Clone two series that differ only in the rule text, diff their full
records, and see whether anything outside the 28 known fields changes. If
nothing does, the text is build-side; if the enum's values can be matched to
displayed rules in Featured, the enum is at least partially decoded.

## 4. What exactly does `PlayerPIRelativeToClass` mean?

**Question.** The three progression frames match the player at −40..+10,
−40..0 and −50..−10. Is the numeric key a class index, a band name, or arbitrary?

**What we know.** **verified** — the pool is drawn inside the active frame's
window relative to the player's PI, and the last frame matched −49..−12 over
three runs. **hypothesis** — the key names the class the frame belongs to.

**Why it matters.** Reusing a frame for a different class might silently apply
the wrong window; a band chosen to look right could be a copy of another class.

**Test.** Rename a frame's key without changing its window, then run the event
with two different player cars: if the field still matches the window, the key
is cosmetic; if it changes, the key selects the window.

## 5. What is `EligibleCars` for in a list document?

**Question.** A list document names an explicit car per slot and also carries an
`EligibleCars` set. Is the set a filter, a fallback pool, or dead weight?

**What we know.** **verified** — list documents carry both, the slots carry
`TargetPI = -1`, and repeating a car across slots weights it.
**hypothesis** — `EligibleCars` restricts which of the named cars may actually
be used.

**Why it matters.** If it filters, a list can be made much more varied by
widening it; if it is dead, every list is a fixed 23 entries and nothing else.

**Test.** Take a list with known variants, empty its `EligibleCars`, apply, run
the event three times. Then set `EligibleCars` to a single car and repeat.

## 6. Does a fixed list's PI depend on the player's car?

**Question.** A list's field PI comes out as the lowest document PI +20..77.
Does that offset move with the player's car, or is it independent?

**What we know.** **verified** (one run) — the offset is constant per class and
the lineup is a weighted draw, not the literal slot order. **hypothesis** — the
offset is fixed and does not follow the player.

**Why it matters.** If it follows the player, a fixed list is not really fixed
and cannot be used to pin a grid to a class.

**Test.** Run the same list event three times with three player cars of widely
different PI and record the grid PIs. A constant field means the offset is
independent.

## 7. What does the warm-up run actually do?

**Question.** The first run after a grid change seems to reuse the previous cars
with recomputed PI. Is that real, and does it happen per event or per session?

**What we know.** **hypothesis**, from 2–3 cases, not a logged test: the second
run shows the new roster, the first does not.

**Why it matters.** A one-run test can legitimately show the old grid and be
reported as "the change did nothing".

**Test.** Change a roster to 23 cars none of which appeared before, run the event
once (record the grid), quit to the cup, run it again (record). Repeat on a
fresh session. If run 1 is stable across sessions, it is a cache, not a race
warm-up.

## 8. Can a field exceed 24 cars?

**Question.** The ceiling observed everywhere is 23 AI + 1 player. Is it a hard
limit or just the largest document anyone built?

**What we know.** **verified** — 23 slots in 552 documents, `NumberOfDrivatars`
23, `MaxAI` 23 on all 178 series. No document or event asks for more.

**Why it matters.** Any grid ambition beyond 24 cars is currently speculation.

**Test.** Write a document with 30 slots and an event that accepts it, apply, and
run. Expect a truncated field or a failure; either outcome is the answer.

## 9. How fast is each class, really?

**Question.** No lap times are stored, so nothing in the data says how long an
event takes or how a class compares on pace. The listed PI of a fixed-list car
also does not match its loaded class (a 775-file car listed D310 drove like a D
car).

**What we know.** **observed** — the mismatch between listed PI and loaded
behaviour, in one case; **observed** — duration exists only in laps (mean 7.0 per
series, max 24).

**Why it matters.** Balance work and duration estimates both need pace, and the
audit can only report laps.

**Test.** Record lap times for one car per class on one layout, three laps each,
and build the table the data lacks. Until then, no pace claim belongs in these
docs.

## 10. What is the real acceptlist size limit?

**Question.** Vanilla acceptlists top out at 23 (mean 5.1), and a 682-car list
broke eligibility. Where between 23 and 682 does it break?

**What we know.** **verified** — 23 works, 682 fails. **hypothesis** — a buffer
sized to the 23 field slots, so the limit is close to 23.

**Why it matters.** A large acceptlist is the obvious way to make a class-wide
series; if the limit is tight, that approach needs a different mechanism.

**Test.** Binary search with one series: 24, 32, 48, 64 cars, apply each, open
the series and check that cars can still be selected.

## 11. What does the weather value 11932 mean?

**Question.** One value dominates the weather field. Is it a sentinel for "track
default", a preset index, or a placeholder?

**What we know.** **verified** (data) — 11932 is dominant across events.
**hypothesis** — it means "inherit the track's weather".

**Why it matters.** Setting weather per event is a natural mod request, and
writing a plausible-looking index could produce a broken session.

**Test.** Set one event to 11932 and a neighbouring one to a different value on
the same track, apply, and compare the sessions. If 11932 matches the track and
the other value does not, it is a real index or a sentinel — the direction of the
difference tells which.

## 12. Why are cups 100 and 2 pinned first?

**Question.** Cups 100 and 2 always come first on the cup screen, while the
other cups follow the cup array. What pins those two?

**What we know.** **verified** — reordering the cup array does not move them,
but it does reorder every cup after them (`CAREER_MODEL.md` §1.3). **hypothesis** — they are the "intro" cups by id, or
they are pinned by the build to guarantee a starting point.

**Why it matters.** A custom cup can never be promoted to the first slot, which
constrains what a "new starting cup" mod can do.

**Test.** Clone cup 100's content under a different id, remove the original, and
see whether the first slot stays empty or is taken by the next cup in build
order. A second run with a cup id of 1 would show whether the id itself is the
key.

## 13. Are the deny rules time-scoped or global?

**Question.** The deny layer covers 45 ids through 32 rules, and 32 of those ids
are still listed in vanilla acceptlists. Are the rules permanent, or scoped to a
window like the series expiry dates?

**What we know.** **verified** — the rules and the ids exist and overlap the
acceptlists; the deny layer wins over the list. **hypothesis** — the rules are
global, with no date window.

**Why it matters.** A denied car that is listed looks like a data bug; if the
rules are date-scoped, expired rules can be ignored instead of worked around.

**Test.** Take one denied id that is listed, and check whether its rule carries
any date field. If it does, change only the date and see whether the car becomes
selectable.

## 14. Where do Featured laps, PI and car restrictions come from?

**Question.** The Featured event record has 14 fields and carries **no**
`NumberOfRequiredLaps`, `TargetPI` or `SerialTrackId`; car restrictions are
expressed as names (`CarRestrictionNames`). Which record supplies the lap count
and the performance cap for a Featured race?

**What we know.** **verified** — the Featured event lacks those fields, and none
of the 4348 Featured events matches an override id, while 399 override records
(336 ids) match no career event. **hypothesis** — a third schedule, not read by
this audit, holds the Featured race slots and supplies laps/PI.

**Why it matters.** Until that record is found, Featured content can be inspected
but not reproduced; and any claim that a career event could be generated from a
Featured event is unsupported (the portability table in `CAREER_MODEL.md` part 2
marks it partial for that reason).

**Test.** Take one Featured series, follow its `ChampionshipEventData` entry back
through the content set, and look for a document that pairs its `EventDataId`
with a lap count or a PI. Any hit names the missing schedule; no hit means the
values are build-side constants.

---

## 15. Which client flags are career-only, and which are read at all?

**Question.** The client flag document (`SCHEMA_REFERENCE.md` Part 3) has about
400 switches. Which of them does the client actually read from the cache, and
which affect only the career rather than Featured/Multiplayer too?

**What we know.** **verified** — one flag, `EnableBuildersCupChallengeTheGrid`,
is read from the cache and removes the wager screen when turned off.
**observed** (data) — per-mode lists inside the flags (tire type, fuel scale)
are keyed by `GameMode`, so an item for `BuildersCup` reaches only the career;
the championship-objectives switch is shared with Featured, so it is not
career-only. The full map of what is career-only, global or closed is in
[MODDING_SURFACE](../reference/MODDING_SURFACE.md).
**hypothesis** — flags named for career systems (championship objectives,
Builders Cup tire overrides, affinity) are equally live and career-scoped; the
qualifying, affinity and tire-compound pillars judged out of reach may reopen
through them.

**Why it matters.** A proven flag is the cheapest change the project can make:
one value, no new ids, trivial rollback. A flag that also changes online play
must not be touched.

**Test.** One flag per change, career-scoped names first: flip it, check the
career screen it names, then open one Featured/Multiplayer event to confirm
nothing changed there. A flag with no visible effect after a restart is recorded
as not read.

---

## 16. Where does the human's fixed starting slot come from?

**Question.** The starting grid splits in two rules: the practice session orders
the **AI**, and the **human** gets a start position that is a constant per event
when the start-position wager screen is off — his own practice time does not move
it. Which data computes that slot, and why does it not change with the session?

**What we know.** **observed** — the AI half is the practice session: the AI's
practice classification came back as the race grid order, one entry after
another (a single swap, from a tied time), in a run on the plain baseline, and
again with the wager screen switched back on. **observed** — the human half is
not the practice: the same slot with the best practice time of the session and
with no timed lap at all, and a different slot in another layout while the
start-position wager was active, for different cars. **verified** — with the
wager screen switched back on (one client flag), the screen **suggests a start
position of its own** and the slot the player picks on it is the slot he starts
from: a pick away from the suggestion was honoured in full, with the AI still on
the practice order (n=1). So the wager is a real control of the player's slot,
and the constant slot is the state of the screen-off path.
**verified** (data) — neither the event record nor the override of that event
carries a start-position or seed field, the AI field document only holds the
drivatar template (a PI window and a count, no position or seed), and the
session generator's grid-ordering shape changes neither the player's slot nor the
order the AI comes out in (a qualifying-order generator with a real human
cluster slot was run against the estimated-order one).

**Refuted.** ~~The slot he gets with the screen off is the wager's suggested slot
applied without the UI.~~ With the screen on, the suggestion was not the slot of
the screen-off state, so the constant slot has another source. The wager block
(a projected race-time delta, an overtake time and a following-car time, i.e. the
inputs of a projected start position) was the likely input of the
**suggestion**; the tests below point the other way.

**Answered (second round of tests).** (ii) The suggestion does **not** follow the
player's practice time: with the best lap of the session by about six seconds it
was the same slot as with no timed lap, and the same with cars of two classes, so
it follows neither the lap nor the car. The projected race-time delta ×10 and a
payout table cut to one row did not move it either. On a 24-car grid it is the
**middle slot (12th)**; the screen-off state is another constant (7th on the
test oval). Four further one-field tests meant to reach a real Qualifying
(generator grid shape, practice limit type `Disabled`, a series-level rules
reference, series field size) had no effect in the career, so no data lever for
the slot or for a Qualifying session is known (DISCOVERIES D33). Small samples.

**Still open.** (i) Where the fixed slot of the screen-off state comes from
(a client constant is the likeliest reading). (iii) Whether the wager's other two
terms (overtake time, following-car time) move the suggestion — judged unlikely
after the delta did not, not tested. (iv) Whether the suggestion scales with the
field size — the field-size field of the series is ignored, so the question could
not be asked that way.

**New (third round, observed, n=3 on one event).** A *different* generator
value moved the slot. With the event pointed at a generator whose grid options
were `GridOrderingType = AIDriverRank` and `ClusterHumansAtIndex = 2` (the
earlier shape tests only compared `Qualifying` and the estimated order), with
the wager screen on: the player picked the **12th** slot and started **1st**;
on a second run he picked the **24th** and was pulled to **1st** again, and after restarting the series he started **1st** a third time. His
practice lap (1:08.661) was one of the two slowest of the 24, and the AI came out
in an order that does **not** follow lap time (the best lap of the list sat at
18th) — consistent with an AI order by driver rank. So the generator's grid
options **can** set the human's slot and **override the wager's pick**. Not
explained: index 2 was expected to give 3rd, not 1st. Next: repeat with a fast
lap and with a slow lap, then other index values (0, 5, 11, 23).

**Grid bench (fourth round, observed, n=1 per series).** Six generators, one field each, same event design. With `AIDriverRank`: index **0, 2, 5 → 1st**; index **11, 23 → 24th**, and the 24th held with a fast practice lap. With `Qualifying` and index 2 the slot was **already fixed from the start of practice (7th)**, so the qualifying shapes give the old constant slot and only `AIDriverRank` moves the human. So the index is not a position: it behaves as a cut, with the turn between 5 and 11. One reading is that the index is compared with the AI's driver rank (all 23 ranks lying between 6 and 11); then indices 6–10 should give intermediate slots. Next: indices 7, 8 and 9. The `Qualifying` slot is the same **7th** with the best lap, with a slow lap or none, with index 2 and with index 10 (Racers Cup generator, class R car, another track), and it matched the old oval constant: a fixed value of that path, not computed from the lap, the index, the class or the track. The ordering by estimated lap time gave **13th** in another series, so the constant depends on the ordering shape. Hypothesis to test: the 7th and 13th are fractions of the 24-car field (about a quarter and a half); a roster of 8 cars (the one document with 7 drivatars) would then start 3rd and 5th rather than 7th.

**Why it matters.** A mod that reorders a field or builds a race weekend has to
know whether the human's slot is data it can set or a constant it has to accept.
Today it is a constant it can only **override by the player's own pick** on the
wager screen: the practical route to a qualifying is to switch the screen on and
choose the slot the lap deserves, or to accept the fixed slot with the screen
off.

---

## 17. Why does the AI leave the track at the same corners?

**Question.** On the bench series the AI cars repeatedly run off the track at the
same corners. Is it the grid's car (PI window against the tune), the track donor's AI
document, the difficulty, or a track-level AI tuning table? — **open**

**What we know.** **observed** (user report, 02/11) — it repeats at the same corners
across runs. Which series, car and corner is not recorded yet.

**Test.** After the current bench is closed: note series, track, corner and the AI
document for two or three corners; compare the same corner on a vanilla series and on
one with a different AI document.

---

## Tracked hypotheses without a numbered item

These are raised in the pages but are smaller than the numbered items above; each
is a belief, not a finding.

| hypothesis | page | what would settle it |
|---|---|---|
| A reorder must permute the object array *and* the order list; contradicting them is unsafe | `CAREER_MODEL.md` §1.2 | permute only the list, apply, and check which screens follow which order |
| The zeroed PI/cost/power/weight series fields are dead, and gating is done by `TargetPI` + acceptlist | `CAREER_MODEL.md` §1.11 | set one of them to a non-zero value and see whether anything changes |
| ~~In the two events where `ClassRestriction` (800/S) and `TargetPI` (900) disagree, `TargetPI` wins~~ — **settled**: the event's `TargetPI` governs the cap shown and the cars accepted (a bench event showed the event's value, and an S car entered once the event's `TargetPI` was raised); the override's class restriction did not apply | `RACE_SYSTEM.md` §2.10 | — |
| Featured/Multiplayer content can be ported into the career tree for schema-level mechanisms only (the reward/progression surface does not come along) | `CAREER_MODEL.md` part 2 | port one Featured series into a career ladder and compare what the series screen offers |
| The `PlayerPIRelativeToClass` numeric key is a class index | `AI_GRIDS.md` §5 | same test as item 4 |
