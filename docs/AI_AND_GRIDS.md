# AI and grids

How the career fills a grid: the two places an AI roster can live, which one
actually decides the field, how a roster document describes a template (PI
window pool) or a list (fixed cars), and how the PI of the field relates to the
player's car.

Scope is championship 500 (career). Reproductions use:

```powershell
python _tools\audit_career.py     # career-side roster fields
python _tools\aifield_survey.py   # survey of all AI field documents
```

## 4.1 Two roster targets, only one of them matters

1. **The series' AI selectable-cars list** (`AISelectableCars`), inside the
   career data. It is what the apply pipeline can reach.
2. **The AI field document** named by the override's `AIFileName`. It is a
   separate asset document and it is what actually pins the grid.

- **verified** — The career-side AI list is **not** uniform: it is empty on 82
  series and populated on 96 (2 to 23 entries). Writing it on a series that had
  it empty changed nothing in game, and the field still followed the AI field
  document. *How to reproduce:* `python _tools\audit_career.py` (the list per
  series); then fill it on an empty one, apply, run the event — the field is
  unchanged.

- **verified** (A/B) — Writing the AI field document named by `AIFileName`
  changes the grid; the career-side list alone does not. The A/B pair is: same
  event, same career data, only the field document differs — the grid follows
  the document. *How to reproduce:* two apply passes over one event, one with
  each target, and compare the fields in game — the override's `AIFileName` is
  the document that differs.

- **verified** — The field document lives outside the group the career data
  belongs to, so the ordinary career applier does not carry it; it needs an
  install-level writer. Steam's "verify files" or a new server snapshot reverts
  it, and the write has to be repeated. *How to reproduce:* write the document
  with the install-level writer, run the event (grid changes), verify files,
  run it again (grid reverts).

## 4.2 Survey of the field documents — 645 documents

| document type | count | how the field is built |
|---|---|---|
| `AIDrivatarTemplate` | 553 | a PI window plus an eligible-car pool fills `NumberOfDrivatars` slots |
| `AIDrivatarList` | 92 | an explicit car per slot |

- **verified** — Slots per document:

| slots | documents |
|---|---|
| 23 | 552 |
| 46 | 83 |
| 24 | 5 |
| 7 | 1 |
| 20 | 1 |
| 0 | 3 |

*How to reproduce:* `python _tools\aifield_survey.py` — it prints the type and
slot histogram; 46 appears where a 23-slot list is written twice in one file.

- **verified** — `NumberOfDrivatars` is 23 in the productive documents, matching
  the 23 AI + 1 player ceiling (`RACE_SYSTEM.md` §2.14).
  *How to reproduce:* the same survey.

### Template documents (the pool)

- **verified** — The most common PI windows are 700–800 step 10 (80 documents),
  800–900 step 10 (76) and 600–700 step 10 (39): the pool is usually a single
  class band, and the career's default difficulty setting does the rest.
  *How to reproduce:* the survey's window histogram.

- **verified** — A template's pool holds between 1 and 22 cars, most often 8–9,
  i.e. **fewer cars than slots**, so a template grid repeats cars.
  *How to reproduce:* the survey's pool-size histogram, compared with the slot
  count of the same document.

### List documents (the fixed grid)

- **verified** — In a list document each slot names an explicit car and carries
  `TargetPI = -1`. Repeating the same car in several slots weights it — the
  more slots a car occupies, the more likely it appears.
  *How to reproduce:* open one list document (`python _tools\aifield_survey.py
  --car <carid>` names them per car) — one car entry per slot, `TargetPI = -1`;
  duplicating a slot in a copy and running the event shows the car more often.

- **hypothesis** — The `EligibleCars` set in a list document acts as a filter
  over which of the named cars may actually be used; no test has isolated it.
  Listed in `OPEN_QUESTIONS.md`.

## 4.3 AI-class cars

- **verified** — The catalogue contains a parallel set of AI-only cars (names
  prefixed `AI_`) carrying a PI in their name, e.g. `AI_<car>_<pi>`: 541 such
  cars, of which **508** are usable in a field. *How to reproduce:*
  `python _tools\aifield_survey.py`, AI car inventory.

| class | usable AI cars |
|---|---|
| E | 22 |
| D | 69 |
| C | 45 |
| B | 59 |
| A | 75 |
| S | 93 |
| R | 87 |
| P | 52 |
| X | 6 |

## 4.4 Choosing the document for a `TargetPI`

- **verified** — `TargetPI = -1` selects the **lowest** PI document available
  for the requested class; a positive `TargetPI` selects the **highest**
  document whose PI is ≤ the requested value, clamped to the lowest when none
  is low enough. Verified byte-exactly against 96 (requested, chosen) pairs.
  *How to reproduce:* `python _tools\aifield_survey.py --car <carid>` prints
  that car's ladder of field documents; for each of the 96 pairs the document
  loaded by the writer was compared with the one this rule predicts.

- **verified** — The lowest document per class approximates the stock PI bands:

| class | lowest document PI range |
|---|---|
| E | 214–293 |
| D | 288–383 |
| C | 359–471 |
| B | 441–571 |
| A | 531–670 |
| S | 638–785 |
| R | 742–863 |
| P | 828–962 |
| X | 966–999 |

*How to reproduce:* the survey's per-class minimum.

## 4.5 How the pool is drawn

A template document can carry a progression frame that offsets the pool from the
player's car: three frames named `AIProgressionFrame` with a
`PlayerPIRelativeToClass` window.

- **verified** — The pool draws inside `[player PI + lower, player PI + upper]`
  of the *active* frame. The three vanilla windows are 40 / 80 / 100 with bands
  **−40..+10**, **−40..0** and **−50..−10**: the field is always at or slightly
  below the player. The last frame matched a −49..−12 window over three runs.
  *How to reproduce:* run the same event three times with the same player car;
  record the grid PI spread; the three windows themselves are in each
  document's `DrivatarProgressionFrames` block, one `AIProgressionFrame` per
  `PlayerPIRelativeToClass` value.

- **hypothesis** — The numeric key names the frame (40/80/100 is the class index
  the window belongs to) rather than being arbitrary. Unproven; no test
  distinguishes a renamed key from a renumbered one.

### Wide band test

- **verified** (3 runs each) — With the window widened to −350..+250 the field
  spreads far beyond the player and still fills 23 distinct cars, with no pile-up
  at the PI floor:

| player car | resulting grid PI | composition |
|---|---|---|
| C 404 | 310–637 | 4 D, 8 C, 6 B, 5 A |
| S 701 | 368–931 | — |
| A 678 | 345–908 | — |

*How to reproduce:* widen `PlayerPIRelativeToClass` in a copy of the document,
apply with the install-level writer, run the event three times and record the
grid PIs.

- **verified** — When the pool has more cars than slots the grid varies per run:
  40 pool cars produced a different set of 23 on every run; 56 pool cars still
  produced 23 cars, drawn across 4–7 classes.
  *How to reproduce:* enlarge the pool, run the event repeatedly, diff the
  grids.

## 4.6 Fixed lists

- **verified** (one run) — With a list document the field PI comes out as the
  lowest document PI **+20..77**, a constant offset per class, and the lineup is
  a weighted random draw from the named slots, not the literal slot order.
  *How to reproduce:* apply a 23-slot list with known cars, run the event, map
  the grid back to the list.

- **observed** — The PI printed in a list entry is a **target, not the loaded
  tune**: a car listed from the 775 document at D310 behaved in game as a real
  D-class car (its pace matched D, not S). No lap-time table exists to quantify
  the gap.
  *How to reproduce:* run an event whose list mixes listed PI apart from the
  loaded class, then compare its lap times with a same-class reference car.

## 4.7 Warm-up run

- **hypothesis** — The first run after a grid change reuses the previous cars
  with recomputed PI, so the new roster only appears from the second run on.
  Seen in 2–3 cases; it is listed in `OPEN_QUESTIONS.md` because no run was
  logged specifically to prove it.

## 4.8 Composition rules that hold

- **verified** — Every validated grid satisfied all of: cars from the catalogue,
  no denied car, an AI car for every slot, one car per make per class, a mix of
  eras, and 23 slots. *How to reproduce:* apply a roster built to those rules
  and audit the resulting grid in game against the list.

- **untested** — Nothing in the data or in this project has produced a field
  above 24 cars in total; there is no precedent for a larger grid. See
  `OPEN_QUESTIONS.md`.

## See also

`CAREER_MODEL.md` · `RACE_SYSTEM.md` · `CARS_AND_PI.md` ·
`DATA_REFERENCE.md` · `CAREER_AUDIT.md` · `GLOSSARY.md`
