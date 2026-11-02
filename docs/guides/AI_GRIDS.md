# AI grids

How the career fills a grid and how to build your own: the two places an AI
roster can live, which one actually decides the field, the two kinds of roster
document (a PI-window pool or a fixed list), how the field's PI relates to the
player's car, and the recipe to write a grid with `build_aifield.py`.

Every claim carries a status: **verified** (seen in game or reproducible with the
command given), **observed** (seen, cause not isolated), **hypothesis** (not
tested yet). Scope is championship 500 (the career). Reproductions use:

```powershell
python _tools\audit_career.py     # career-side roster fields
python _tools\aifield_survey.py   # survey of all AI field documents
```

Step by step: [tutorial 04](../tutorials/04_ai_grid.md). Multi-class recipes and a
test protocol: [CUSTOM_RACE](CUSTOM_RACE.md).

## 1. Two roster targets, only one of them matters

1. **The series' AI selectable-cars list** (`AISelectableCars`), inside the
   career data in the CmsCache. `cache_edit.py` can reach it.
2. **The AI field document** named by the override's `AIFileName`
   (`AIField_<id>_Gen.xml`). It is a separate asset document, and it is what
   actually pins the grid.

- **verified** — The career-side AI list is **not** uniform: it is empty on 82
  series and populated on 96 (2 to 23 entries). Writing it on a series that had
  it empty changed nothing in game, and the field still followed the AI field
  document.
- **verified** (A/B) — Writing the AI field document changes the grid; the
  career-side list alone does not. Same event, same career data, only the field
  document differs — the grid follows the document.
- **verified** — The field documents belong to a content group that has no blob
  in the CmsCache, so the game reads them from the install's CMS zip.
  `cache_edit.py` skips them; `install_edit.py` writes them and keeps the
  install and cache manifests consistent. Steam's "verify files" or a new server
  snapshot reverts the write; repeat it.
- **verified** — No Featured, Rivals or Meetup generator cites a career AI
  field document, so editing a career grid changes only the career. A few
  documents are named by more than one career series: check which series use
  the same `AIFileName` before editing one.

## 2. The field documents — 645 in the install

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

46 appears where a 23-slot list is written twice in one file (once at the
document root, once inside `AIDrivatarConfiguration`). `NumberOfDrivatars` is 23
in the productive documents, matching the 23 AI + 1 player ceiling
([RACE_SYSTEM](../reference/RACE_SYSTEM.md)).

Other fields, identical in both modes: `AIDifficulty`, `AIRubberBandingEnabled`
and a `BehaviorSettings` block (catch-up, slow-down and proximity flags).

### Template documents (the pool)

- **verified** — The most common PI windows are 700–800 step 10 (80 documents),
  800–900 step 10 (76) and 600–700 step 10 (39): the pool is usually a single
  class band.
- **verified** — A template's pool holds between 1 and 22 cars, most often 8–9,
  i.e. **fewer cars than slots**, so a vanilla template grid repeats cars. A
  pool **larger** than the slots has no vanilla precedent, but it works (§4).

### List documents (the fixed grid)

- **verified** — Each slot names an explicit car with `TargetPI = -1`. Repeating
  a car in several slots weights it.
- **hypothesis** — The smaller `EligibleCars` subset of a list document acts as a
  filter over the named cars; no test has isolated it
  ([OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md)).

## 3. AI cars and the class scale

- **verified** — The catalogue holds a parallel set of AI tune files named
  `AI_<car>_<pi>`: 541 cars have them, **508** are usable in a field. Each car
  has a **ladder** of files, one per PI step.

| class | game PI band | usable AI cars | lowest AI file PI seen |
|---|---|---|---|
| E | 0–300 | 22 | 214–293 |
| D | 301–400 | 69 | 288–383 |
| C | 401–500 | 45 | 359–471 |
| B | 501–600 | 59 | 441–571 |
| A | 601–700 | 75 | 531–670 |
| S | 701–800 | 93 | 638–785 |
| R | 801–900 | 87 | 742–863 |
| P | 901–998 | 52 | 828–962 |
| X | 999 | 6 | 966–999 |

- **verified** — File choice: `TargetPI = -1` loads the **lowest** file of the
  car; a positive target loads the **highest** file whose PI is ≤ the target,
  clamped to the lowest. Checked byte-exactly against 96 (requested, chosen)
  pairs. `python _tools\aifield_survey.py --car <carid>` prints a car's ladder.
- **verified** — The `AI_` file numbers are on the game's class scale, so a
  car's lowest file approximates its stock PI. Take classes from this scale,
  not from other PI columns of the derived car tables
  ([CARS_AND_PI](../reference/CARS_AND_PI.md)).
- **observed** (reinforced) — On a roster with window 400–600 and a player at
  about 406, 5 of 13 AI cars showed a PI of 400–412 with a **B** class badge while
  the others showed C: the badge follows the car's real class, the number is the
  target. 17 of that roster's 21 cars have a lowest AI tune above 412 (most of
  them class B, up to the 570s), and with the window floor at 400 they load that
  lowest tune — so they are faster than their listed PI. A roster that fits a
  class needs cars whose lowest tune is at or below the window floor.
- **observed** — The PI shown on the grid is the **target**, not the tune
  loaded: a car whose ladder starts far above the listed PI can be listed low,
  and its pace seemed to follow the listed class. No lap-time table yet.

## 4. Pool or fixed list

| | template pool | fixed list |
|---|---|---|
| who is on the grid | up to `NumberOfDrivatars` cars drawn from `EligibleCars`; a pool larger than the slots gives a different grid per run | a **weighted random draw** from the listed cars, not the literal slot order |
| PI of each AI car | follows the **player's** PI through the progression band, clamped by the window and the car's ladder | constant per car: its lowest `AI_` file PI plus a small offset |
| classes in one grid | the band decides: narrow = the player's class, wide = several classes | the cars decide: a real multi-class grid regardless of the player |

- **verified** — Pool: 40 cars over 23 slots produced a different set of 23 on
  every run; 56 cars still produced 23 distinct cars.
- **verified** (one run) — List: a 23-slot list gave D, C, B, A, S and R cars in
  one grid against a C-class player; cars repeated beyond their listed weight.

## 5. How the pool follows the player (progression band)

A template carries three `AIProgressionFrame` entries keyed by
`PlayerPIRelativeToClass` (40 / 80 / 100), each a band `[lower, upper]` around
the player's PI.

- **verified** — Each AI driver draws its target PI inside
  `[player PI + lower, player PI + upper]` of the active frame; the window
  (`MinimumPI..MaximumPI`) and the car's ladder clamp it. The vanilla bands are
  **−40..+10**, **−40..0** and **−50..−10**: the field is always at or slightly
  below the player, in the player's class. Three runs matched the last frame.
- **observed** (3 runs, two roster documents) — **The frame is picked by the
  player's PI minus the document's `MinimumPI`**: the frame whose key is the
  highest one not above that difference. A player at 404 on a document with
  minimum 320 (difference 84, frame 80, band −50..−10) met a field of about
  354–394; a player at 406 on a document with minimum 400 (difference 6, frame 0,
  band −30..+10, clamped at the window floor) met a field of 400–412. The
  event's own `TargetPI` (300 in the second case) did **not** cap the AI. So the
  field's distance from the player is chosen by the document's band table, and
  to keep the AI in the player's class a document needs a window that starts at
  or below the player's PI and a frame with a narrow band around zero. Still
  worth setting all three frames equal in any experiment that isolates the band.
- **verified** (3 runs) — A wide band of **−350..+250** spreads the field over
  4–7 classes and still follows the player at both ends:

| player car | resulting grid PI |
|---|---|
| C 404 | 310–637 |
| A 678 | 345–908 |
| S 701 | 368–931 |

No pile-up at the PI floor: the draw is restricted to band ∩ window. The PI is
per driver, not per car (the same car appeared at several PIs).

- **hypothesis** — The first race after a grid change reuses the previous
  grid's cars with a recomputed PI ("warm-up run"); the new roster shows from
  the second race on. Seen in 2–3 cases, never logged on purpose.

## 6. Build a grid

1. **Describe it** in `specs/aifield/<name>.json`: the logical document to
   write, a vanilla template document as the layout, the mode (`pool` or
   `list`), the roster (car ids) and, for a pool, the window and band. Examples:
   `specs/aifield/trackday_pool56.json` (pool, wide band) and
   `specs/aifield/trackday_list23.json` (fixed list).
2. **Check it**: `python _tools\build_aifield.py --def specs\aifield\<name>.json --check`
   validates every car (catalogue, denied cars, `AI_` coverage) and writes
   nothing.
3. **Build it**: the same command without `--check` writes the encrypted
   payload into a kit folder. The cipher template is the current payload of
   that entry in the install zip.
4. **Apply it** with the game closed: `install_edit.py --dry-run`, then with
   `--verify` ([PIPELINE](../en/PIPELINE.md)). Install writes have no
   cache-copy rehearsal; the test is the game. Revert with
   `install_edit.py --restore <backup>`.
5. The library behind it is `_tools/fmlib/aifield.py`;
   `_tools/test_aifield.py` proves it rebuilds a vanilla document byte for byte.

## 6b. A one-model roster for a series (spec race)

Proven in game with two series: a grid of 23 Subaru BRZ '22 (class C) and a grid
of 23 Porsche 911 GT3 RS '23 (class S), each series on its own document. One
roster per document; any number of events can share a document.

1. **Pick the car** and check it has AI tune files:
   `python _tools\aifield_survey.py --car <id>`. A car with none cannot be an AI
   car (the Toyota GR86 '22 has none; its twin, the Subaru BRZ '22, has 22).
2. **Pick the destination document.** It must be an existing roster document
   that no reachable series uses: not cited by any override (`AIFileName`) and not
   cited by any session generator (`AIFieldFile`) in the live cache, and present in
   **both** cache snapshots (the install tool requires it). A **brand-new file name
   does not work**: the game went offline when an event pointed at one, because the
   entry is unknown to the server. Re-read the usage after every new server
   snapshot, since a revived event could start using the document.
3. **Describe it** (`specs/aifield/<name>.json`, mode `pool`, one car): a window
   whose floor is at or just below the car's lowest tune (so the label matches the
   tune), a narrow band around the player (−10…+10 gave a spread; try 0…0), and
   optionally the document's own flags through the spec keys `difficulty`,
   `rubber_banding` and `behavior` (per session type: slow-down, catch-up,
   proximity, position spread, slot-car start).
4. **Check, build and apply** as in §6.
5. **Point the event at the document**: the override's `AIFileName` (a one-field
   cache edit). Read the lobby: every car is the model, and the class badge
   matches the PI. Treat the first race after a change as a warm-up.

Caveats: Steam "verify files" reverts the document; a band wider than zero makes
the AI cars differ in pace even though they are the same model; whether the
document's flags or the series' flags win is untested.

## 7. Composition rules that held

- **verified** — Every validated grid used cars from the catalogue, no denied
  car, an `AI_` file for every car, at most one car per make per class, a mix
  of eras, and 23 slots.
- **untested** — Nothing has produced a field above 24 cars in total; there is
  no precedent for a larger grid ([OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md)).

## See also

[CAREER_MODEL](../reference/CAREER_MODEL.md) ·
[RACE_SYSTEM](../reference/RACE_SYSTEM.md) ·
[CARS_AND_PI](../reference/CARS_AND_PI.md) ·
[DATA_REFERENCE](../reference/DATA_REFERENCE.md) ·
[GLOSSARY](../reference/GLOSSARY.md)
