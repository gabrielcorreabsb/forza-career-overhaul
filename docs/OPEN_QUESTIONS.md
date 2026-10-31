# Open questions

Every claim in this doc set that is marked **hypothesis** has an entry below: the
question, what is known, why it matters and the experiment that would settle it.
Nothing here is a fact about the game; treat the whole page as work to do.

Scope is the career (championship 500) unless stated. Reproduction and survey
commands are the ones named in the pages that raise each item.

---

## 1. Where is the start type stored?

**Question.** Rolling and standing starts are visible in game, but no field in
the event record or the override carries a start type (`RACE_SYSTEM.md` §2.1).
Where does the game read it from?

**What we know.** **verified** — there is no start-type field in the event or
override schema, and only 2 series carry a slot-car-start flag. **observed** — a
custom event built from a Nordschleife donor starts rolling. **hypothesis** — the
start comes from the generator template (`ParentGeneratorId`), the track, or the
series flag, in that order of likelihood.

**Why it matters.** A new event cannot choose its start type, and a cloned event
silently inherits one from a donor it no longer resembles.

**Test.** Build three events from three donors with different start behaviour on
the same track, change nothing else, and record the start of each. That isolates
the generator from the track.

## 2. Which lap count wins — the event's or the override's?

**Question.** `NumberOfRequiredLaps` and `FeatureRace.Laps` disagree on 600 of
627 events. Which one does the race run?

**What we know.** **observed** — the disagreement is real and specific to laps;
`TargetPI` agrees on 627/627, so overrides are not simply stale. **observed** —
career races feel like the short 1–4 lap lengths of the event record.
**hypothesis** — the event record wins.

**Why it matters.** Every new event or rebalanced lap count has to be written
into the field that matters; if it is the override, half the lap edits done so
far are inert.

**Test.** Pick one event. Set `NumberOfRequiredLaps` to 2 and
`FeatureRace.Laps` to 8, apply, run it and count the laps. Then invert the two
values and run it again. One run settles it.

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

## Tracked hypotheses without a numbered item

These are raised in the pages but are smaller than the numbered items above; each
is a belief, not a finding.

| hypothesis | page | what would settle it |
|---|---|---|
| A reorder must permute the object array *and* the order list; contradicting them is unsafe | `CAREER_MODEL.md` §1.2 | permute only the list, apply, and check which screens follow which order |
| The zeroed PI/cost/power/weight series fields are dead, and gating is done by `TargetPI` + acceptlist | `CAREER_MODEL.md` §1.11 | set one of them to a non-zero value and see whether anything changes |
| In the two events where `ClassRestriction` (800/S) and `TargetPI` (900) disagree, `TargetPI` wins | `RACE_SYSTEM.md` §2.10 | enter a 850-PI car in one of them; acceptance means `TargetPI` wins |
| Featured/Multiplayer content can be ported into the career tree for schema-level mechanisms only (the reward/progression surface does not come along) | `CAREER_MODEL.md` part 2 | port one Featured series into a career ladder and compare what the series screen offers |
| The `PlayerPIRelativeToClass` numeric key is a class index | `AI_AND_GRIDS.md` §4.5 | same test as item 4 |
