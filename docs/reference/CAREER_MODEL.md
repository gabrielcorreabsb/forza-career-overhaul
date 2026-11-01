# Career model

How the single-player career of Forza Motorsport (FM8) is assembled from data:
three championships in three documents, four nested levels, id rules, text
keys, gates and expiry.
Read this first; per-field detail is in `RACE_SYSTEM.md`, the car/PI layer in
`CARS_AND_PI.md`, the AI layer in `AI_GRIDS.md` and the numbers in
`DATA_REFERENCE.md`.

## Scope and evidence

Two scopes are kept apart in every page of this set:

1. **Single-player — championship 500** (the career). 6 vanilla cups + 1 custom
   cup (id 103) = **7 cups**; 34 vanilla ladders + 1 = **35**; 176 vanilla
   series + 2 custom (20003, 20004) = **178**; 623 vanilla events + 4 = **627**;
   **711 cars**; **71 track layouts**.
2. **Featured / Multiplayer — championship 1.** Same record schema, own
   progression and reward surface. It is **never modified** by this project and
   is documented only in [part 2](#part-2--featured--multiplayer-championship-1)
   of this page.

Counts above belong to scope 1 unless stated otherwise.

### Evidence labels

| label | meaning | requires |
|---|---|---|
| **verified** | reproduced from the data, or reproduced in game more than once | a "How to reproduce" command or procedure |
| **observed** | seen once, in game, or read off a single data pass | a "How to reproduce" command or procedure |
| **hypothesis** | plausible reading with no direct evidence | an entry in `OPEN_QUESTIONS.md` |

Two read-only commands back almost every reproduction line:

```powershell
python _tools\inventory.py      # read-only inventory of the installed game data
python _tools\audit_career.py   # career audit tables; --check fails if stale
```

---

# Part 1 — Career (championship 500)

## 1.1 Where the championships live

- **verified** — The career schedule holds exactly **one** championship, id
  **500**; there is no second championship in that document. The Featured /
  multiplayer set is a separate document entirely (part 2), and the intro
  content is a third one. *How to reproduce:* `python _tools\audit_career.py`
  (championship ids and cup count) and `SCHEMA_REFERENCE.md` §2.1.

- **verified** — The career tree is not a separate data file: cups, ladders,
  series and events are one hierarchy rooted at championship 500.
  *How to reproduce:* `python _tools\audit_career.py`.

## 1.2 Hierarchy and order lists

| level | count (vanilla + custom) | field holding the id | list that sequences the children |
|---|---|---|---|
| championship | 1 (id 500) | — | — |
| cup | 7 (6 + 1) | cup id | `cup.LadderOrderData` |
| ladder | 35 (34 + 1) | ladder id | `ladder.OrderData` |
| series | 178 (176 + 2) | `ChampionshipSeriesId` | `series.OrderedEventIds` |
| event | 627 (623 + 4) | `EventDataId` | position inside `OrderedEventIds` |

- **verified** — Each level sequences its children through the list named in the
  table (`LadderOrderData`, `OrderData`, `OrderedEventIds`); the lists hold ids,
  not copies of the objects. *How to reproduce:* `python _tools\audit_career.py`
  — every child id appears exactly once in its parent list.

- **verified** — A reorder is a permutation of **both** the array of objects and
  the matching order list. Permuting only one of them leaves the two out of
  step. *How to reproduce:* permute an order list in a copy of the data, apply
  it, reload the cup: the series order follows the list, while screens that
  iterate the array keep the old order.

- **hypothesis** — That dual permutation is required rather than merely
  safe: no test has been run with the array and the list deliberately
  contradicting each other. Tracked in `OPEN_QUESTIONS.md`.

## 1.3 Cup screen order

- **verified** — The cup screen shows cups **100** and **2** first (pinned
  code-side), then the remaining cups **in the order of the cup array**. So the
  rule is `[100, 2] + rest of the array`: the tail is permutable from the data,
  the first two are not. *How to reproduce:* permute the cup array after the
  first two entries, apply, and reload the cup screen; the tail follows the
  array, cups 100 and 2 stay first.

## 1.4 Visibility gating

- **verified** — A cup is visible only while it still has at least one visible
  ladder/series chain beneath it; the gate lives at ladder/series level, not at
  cup level. *How to reproduce:* `python _tools\audit_career.py`, then apply the
  same change and reload the cup screen.

- **verified** — Expiring every ladder/series chain of a cup makes the whole cup
  disappear from the screen, and un-expiring one ladder plus one of its series
  brings it back (seen with cup 102: its ladder and series were un-expired and
  the cup reappeared). *How to reproduce:* set `CloseTime` of a cup's only
  ladder and series to a sentinel date, apply, reload the cup screen.

## 1.5 Ids

- **verified** — Custom series use ids **≥ 20000**; custom events use
  **65897900–65899999**. The ranges are reserved for mods.
  *How to reproduce:* `python _tools\audit_career.py`, id ranges — vanilla ids
  never enter either range.

- **verified** — An id must never be reused. A profile that already completed a
  series keeps that completion, so a new series carrying an old id shows up as
  already finished. *How to reproduce:* `python _tools\audit_career.py --check`
  (duplicate-id test over the whole tree); in game, a recycled id shows the
  series pre-completed for a profile that played the old one.

- **verified** — Cup, ladder, event and series ids are opaque: they are not
  derived from names by any hash and must never be recomputed. Only the
  documented ranges constrain new ones. *How to reproduce:*
  `python _tools\audit_career.py`, id audit — ids are unrelated to the strings
  they belong to.

## 1.6 Text

- **verified** — Series, cup and ladder `Name` fields hold an `IDS_` key
  resolved from the string tables; the event `Name` field is a **literal**
  string. Mixing the two conventions produces a raw key or a duplicated label.
  *How to reproduce:* `python _tools\audit_career.py` — every
  series/cup/ladder name matches an existing string key, while event names do
  not.

- **verified** — New `IDS_` keys may be any length: the tables index by a name
  hash, so nothing forces the key to keep the length of the string it replaces.
  *How to reproduce:* add a key of a different length with the string editor,
  apply it, load the series — the label resolves.

- **verified** — Only the player's locale table needs the new key; the other
  locales fall back to the English entry. *How to reproduce:* add the key to
  one locale only, switch the game language: the untranslated locales show the
  base text rather than a raw key.

## 1.7 What a new series needs

- **verified** — A new series needs its `CarSelectCarRestrictions` block. With
  the block missing, clicking the series throws a native exception instead of
  opening the car-select screen. *How to reproduce:* `python _tools\audit_career.py`,
  then click such a series in game — native exception dialog, no screen.

- **verified** — The remaining minimum: one or more events, an entry in its
  ladder's `OrderData`, a `ChampionshipSeriesId` in the custom range, event ids
  in the custom range, and a string key for the name. *How to reproduce:* the
  same command lists exactly these references per series.

## 1.8 Gates

- **verified** — Prerequisites are expressed as
  `EntryCriteria.RequiredLadders` / `RequiredSeries` / `RequiredEvents`, plus
  the matching counters and `MinDriverLevel`. An **empty** requirement list
  means "no prerequisite". *How to reproduce:* `python _tools\audit_career.py`,
  then open a series with all three lists empty from a fresh profile.

- **observed** — In the current copy of the data every requirement list is
  zeroed, so no series is gated today. *How to reproduce:* the same command.

- This page deliberately does **not** state what the vanilla requirements were:
  the zeroing is the shipped state of this copy and the original values were not
  captured. Treat "vanilla has no gates" as unsupported.

## 1.9 Expiry

- **verified** — Availability is bounded by `OpenTime`, `CloseTime` and
  `StartEndDate.From` / `StartEndDate.To`. Two sentinel dates appear:
  **3000-05-22** and **9999-12-31**, both meaning "never expires".
  *How to reproduce:* `python _tools\audit_career.py` — every
  series carries either a sentinel or a real date.

- **verified** — The expiry date seen on the retired live-service content is
  **2025-06-25**; anything bounded by it is past its window.
  *How to reproduce:* the same command; the series in that bucket carry that date.

- **verified** (audit finding) — In the live copy, ladder **763** and its **7
  series** in cup **99** ("Open Class Tour") are still expired at 2025-06-25.
  It is an older copy of ladder 764 (same name, live in cup 2); cup 99 itself
  stays visible through its other ladders (§1.4).
  *How to reproduce:* `python _tools\audit_career.py --check` flags it.

## 1.10 Series type

- **verified** — `SeriesType` takes two values in this data: **28**
  (`RewardShowcase`) on 28 series and the default on the remaining 150. The
  showcase type is the single-event, fixed-reward shape.
  *How to reproduce:* `python _tools\audit_career.py`.

## 1.11 Shape of a series record

- **verified** — A series record has **28 fields**; `SeriesOrderData` is always
  empty; the PI, cost, power and weight fields are always zero; `CarDivisionId`
  is always the open division. *How to reproduce:* count the field names of one
  series record in the career data — the audit loader
  (`_tools\audit_career.py`, `model_from_bcs`) reads each one of them.

- **verified** — There is no `SeriesRules` field in the **career** series
  record, so rules that the UI can display for some series have no storage here.
  The Featured series record *does* carry it, as a numeric enum
  (`SCHEMA_REFERENCE.md` §2.3). *How to reproduce:* the same loader — it has no
  rule field to read, and every career record carries the same 28 names.

- **hypothesis** — Because the PI/cost/power/weight fields are dead, the real
  gating happens through the event `TargetPI` and the acceptlist; §1.8, the
  class ceiling in `RACE_SYSTEM.md` and `CARS_AND_PI.md` are consistent with
  that reading, but no test isolates the fields.

## 1.12 Championship 1 is never touched

- **verified** — The apply pipeline's static lint rejects any plan whose targets
  fall inside championship 1. Multiplayer content is out of bounds for this
  project by construction, not by convention. *How to reproduce:*
  `python _tools\plan_lint.py --plan <plan.json>` on a plan that names a
  championship-1 series — the lint fails.

---

# Part 2 — Featured / Multiplayer (championship 1)

Championship 1 does **not** share the career tree. It lives in its own metadata
document with a flatter shape — championship → series type → collection → series
→ event — and no cups or ladders; its series rotate through weekly collections.
It also uses a *trimmed*, 14-field event record and a 16-field series record
that carries a `SeriesRules` enum the career lacks. Full field catalogue:
`SCHEMA_REFERENCE.md` part 2.

Nothing in this project writes to it (§1.12). The table asks, per mechanism the
career copy already uses, whether it would survive being pointed at single-player
content — not the reverse.

| mechanism | portable to single-player? | reason |
|---|---|---|
| cup → ladder → series → event tree with the three order lists | viable | this is the career's own mechanism; a Featured series would have to be re-parented into a career ladder (verified, §1.2) |
| event `TargetPI` as the effective car cap | viable | the cap is an event-level field; the career copy uses it everywhere (verified) |
| series acceptlist / blocklist car gating (`SelectableCars`) | viable | the career uses both modes today (verified, `CARS_AND_PI.md`) |
| expiry through `OpenTime` / `CloseTime` / `StartEndDate` | viable | same fields, same sentinels (verified, §1.9) |
| custom ids ≥ 20000 / 65897900–65899999 | viable | ids must be fresh; a moved series has to be renumbered (verified, §1.5) |
| collection cycling (`SeriesCycleLength` / `PlaylistCycleLength`) | not viable | the career has no playlist cycle and no collection level at all (verified, `SCHEMA_REFERENCE.md` §2.2) |
| `SeriesRules` enum | not viable | the career series record has no such field (verified, §1.11) |
| `Challenges` block | not viable | the career series record has no such field (verified) |
| `CarRestrictionNames` on the event | not viable | the career gates cars by `SelectableCars` + `TargetPI`, never by name (verified) |
| AI field pinned by an `AIField` document | partial | the roster document lives outside the career data and is named per override, so it needs the same install-level writer (verified, `AI_GRIDS.md`) |
| Featured rewards and progression surface | not viable | the reward/progression surface belongs to the Featured build; moving a series into the career tree does not bring it along (hypothesis) |
| gates that reference Featured ladders | not viable | requirement ids would point into a tree the career does not contain (hypothesis, follows from §1.8) |

**Read the last column as a judgment, not a test result.** Rows marked viable
rest on schema-level facts that are verified in the career copy; rows marked
partial or not viable are hypotheses about the Featured build and are listed in
`OPEN_QUESTIONS.md` where they need a test.

## See also

- `RACE_SYSTEM.md` — event/override fields, laps, practice, classes, series defaults.
- `CARS_AND_PI.md` — class scale, acceptlists, coverage, disposal.
- `AI_GRIDS.md` — the two AI roster targets.
- `DATA_REFERENCE.md` — field counts, id ranges, derived tables.
- `CAREER_AUDIT.md` — the audit findings, including the expired-cup find.
- `GLOSSARY.md` — every term used above.
