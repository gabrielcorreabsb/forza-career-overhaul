# Career audit

The findings of a read-only audit of the career data: how much of it is vanilla
versus custom, how much of the car catalogue the career can actually reach, how
the performance ceilings are spread, how long the content is, and the defects
worth fixing.

Everything is career (championship 500) unless stated. The audit never writes to
the game: it reads the installed data and regenerates tables.

Three numbers frame the whole project. **209 of 711 cars** appear in no
acceptlist, and the two entry classes are the worst served (**E 31/50**,
**D 50/106**) — while the events themselves sit mostly at the top of the scale
(`TargetPI` 900 and 800 together are 245 of 627 events). A career shaped like
Forza Motorsport 4 is the opposite: dense at the entry end, with the right car
for each event. That distance is what this audit measures.

```powershell
python _tools\audit_career.py          # rebuild the audit tables
python _tools\audit_career.py --check  # non-zero if anything is stale
python _tools\inventory.py             # base inventory
```

## 6.1 Vanilla versus custom

| level | vanilla | custom | total |
|---|---|---|---|
| cup | 6 | 1 (103) | 7 |
| ladder | 34 | 1 | 35 |
| series | 176 | 2 (20003, 20004) | 178 |
| event | 623 | 4 | 627 |

- **verified** — Split as above. *How to reproduce:*
  `python _tools\audit_career.py`.
- **observed** — The custom cup is the last cup in the tree, and the custom
  series live in that cup only; no vanilla cup was given a custom series.
  *How to reproduce:* read each series' parent cup id in the career data — the
  two custom series both sit under cup 103.

## 6.2 Never-listed cars

A car is **never listed** when no vanilla acceptlist contains it. It can still be
driven in the 15 open-class series when its class and PI fit, so this index
measures listing coverage — how often a car is guaranteed a slot — not whether
the car is drivable at all (`CARS_AND_PI.md` §3.8).

- **verified** — **209 of 711** cars (29.4%) are never listed. The worst classes
  are the two entry classes:

| class | never listed / total |
|---|---|
| E | 31 / 50 |
| D | 50 / 106 |

*How to reproduce:* `python _tools\audit_career.py` — intersect every acceptlist
with the catalogue.

- **observed** — E and D being the worst hit is backwards from a player's point
  of view: those are the classes a career starts in, so the cars a player is
  most likely to own are the ones least likely to be listed in a series.
  *How to reproduce:* the same table, read against the class of the series a
  fresh profile can enter.

## 6.3 Where the performance ceilings sit

Events per `TargetPI` value (the effective cap, `RACE_SYSTEM.md` §2.11):

| `TargetPI` | events |
|---|---|
| 900 | 125 |
| 800 | 120 |
| 700 | 72 |
| 998 | 67 |
| 600 | 56 |
| 500 | 43 |
| 400 | 36 |
| 999 | 27 |
| 750 | 27 |
| 300 | 12 |
| other (one-offs) | 42 |

- **verified** — Counts as above; the ten listed values cover 585 events and 42
  events use a value outside the list. *How to reproduce:*
  `python _tools\audit_career.py`, PI histogram.

- **observed** — The distribution is top-heavy: 900 and 800 together are 245
  events, while 300 (the entry class) is 12. A career therefore spends most of
  its events in high-class content, and 750 and 999 appear as odd thresholds
  that do not coincide with a class band edge (750 sits inside S, 999 is X).
  *How to reproduce:* the same histogram compared with the class table in
  `CARS_AND_PI.md` §3.1.

### Class × track coverage

- **verified** — Every class appears on more than one layout, and no layout is
  unused (`DATA_REFERENCE.md` §5.3). *How to reproduce:*
  `python _tools\audit_career.py`; cross its class and track columns and the
  matrix has no empty row and no empty column.

- **observed** — Coverage is uneven by class: the high classes are spread over
  most layouts, the entry classes are concentrated on a handful. A player who
  stays in E sees a small slice of the 71 layouts.
  *How to reproduce:* the same matrix, read per class row.

## 6.4 Series shape

- **verified** — **37** series have a single event, and **28** of those are
  `RewardShowcase` (type 28). *How to reproduce:* `python _tools\audit_career.py`
  (events-per-series histogram crossed with `SeriesType`).

- **observed** — The overlap is not complete: 37 single-event series versus 28
  showcase series means 9 single-event series are ordinary series.
  *How to reproduce:* the same cross-tab.

## 6.5 Duration

- **verified** — Duration is expressible only in laps: **mean 7.0 laps per
  series, maximum 24**, no lap times stored. *How to reproduce:*
  `python _tools\audit_career.py`.

Per-cup lap totals in this copy:

| cup | required laps |
|---|---|
| 99 | 787 |
| 2 | 283 |
| 101 | 127 |
| 104 | 29 |
| 100 | 9 |
| 102 | 5 |
| 103 | 1 |

- **verified** — Totals as above; they are **laps, not minutes**, and cannot be
  converted without a lap-time table the data does not have.
  *How to reproduce:* the same command.

- **observed** — Cup 99 alone is 787 of 1241 laps (63%) over its 20 ladders,
  while the custom cup 103 is a single lap. Only one of those ladders is expired
  (§6.6 finding 1), worth **19 laps (1.5%)**; the rest of cup 99 is reachable.
  *How to reproduce:* the same command; sum the laps of the ladder-763 rows.

## 6.6 Findings

| # | finding | status | why it matters |
|---|---|---|---|
| 1 | Ladder **763** and its **7 series** in cup 99 ("Open Class Tour") are expired at **2025-06-25** | **verified** (data) | 19 laps (1.5%) unreachable; it is an older copy of ladder 764 ("Open Class Tour", live in cup 2), so the content itself is not lost. Cup 99 stays on the cup screen |
| 2 | Two events carry `ClassRestriction` 5 (ceiling 800 / S) with `TargetPI` 900 | **verified** (data) | the two gates disagree; which one wins is untested (`OPEN_QUESTIONS.md`) |
| 3 | `FeatureRace.Laps` disagrees with the event's `NumberOfRequiredLaps` on 600 of 627 events, while `TargetPI` agrees 627/627 | **observed**, unresolved | the race length may come from either copy; an experiment is proposed |
| 4 | The **career** series record has no `SeriesRules` field (the Featured record does) | **verified** | rules shown by the UI for some series have no storage in the career schema |
| 5 | The career-side AI selectable-cars list is empty on 82 series and populated on 96, yet changing it does not move the grid | **verified** (data) / **observed** (A/B) | it is not the field that pins a field; the AI field document is (`AI_GRIDS.md`) |
| 6 | 32 deny rules cover 45 always-denied ids, of which 32 are still listed in vanilla acceptlists | **verified** | a listed car can still be vetoed; the list alone is not the eligibility answer |
| 7 | `PointSpread` is one constant 24-value table on every event | **observed** | a template artefact: no event varies its points shape |

- **verified** — Each row above is reproduced by
  `python _tools\audit_career.py` (expiry, class, laps, schema, roster, deny and
  points are all in the rows and tables it regenerates).
  *How to reproduce:* run it and read the table named in the row.

- **observed** — Findings 1 and 5 are the only two that change what a player
  sees; 2, 3, 6 and 7 are data defects that may or may not surface in play.
  *How to reproduce:* apply a fix for each in a copy of the data and compare the
  in-game screen.

## 6.7 What the audit does not claim

- It does not state what vanilla gate values were: the current copy has every
  requirement list zeroed, and the originals were not captured
  (`CAREER_MODEL.md` §1.8).
- It does not convert laps to minutes and does not rank cars by pace: no lap
  times are stored (`OPEN_QUESTIONS.md`).
- It does not audit championship 1 series by series: the Featured/Multiplayer
  side is described structurally in `CAREER_MODEL.md` part 2 and
  `SCHEMA_REFERENCE.md` part 2, and it is never modified.

## See also

`CAREER_MODEL.md` · `RACE_SYSTEM.md` · `CARS_AND_PI.md` · `AI_GRIDS.md` ·
`DATA_REFERENCE.md` · `GLOSSARY.md`
