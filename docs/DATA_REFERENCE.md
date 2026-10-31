# Data reference

A compact reference to the career data: the tree, record sizes, counts,
identity rules, id ranges, text and art conventions, and the derived tables that
ship next to this page.

Everything here is **career** (championship 500) unless a line says otherwise.
Championship 1 lives in its own document with a different shape (no cups, no
ladders) and is never modified (`CAREER_MODEL.md`, part 2). Reproductions use:

```powershell
python _tools\inventory.py
python _tools\audit_career.py          # rebuild the derived tables
python _tools\audit_career.py --check  # non-zero if they are stale
```

## 5.1 Tree

```
Championship 500
└── cup            (7)   sequenced by cup.LadderOrderData
    └── ladder     (35)  sequenced by ladder.OrderData
        └── series (178) sequenced by series.OrderedEventIds
            └── event (627)
```

- **verified** — The four levels and the three order lists above are the whole
  shape; there is no fifth level and no cross-link between two cups.
  *How to reproduce:* `python _tools\audit_career.py`.

- **verified** — The three order lists contain ids only; the objects live in the
  parent's array. *How to reproduce:* the same command — list length equals child
  count at every level.

## 5.2 Record sizes

| record | fields |
|---|---|
| championship (career) | 9 |
| cup | 15 |
| ladder | 14 |
| series | 28 |
| event | 18 |
| event override | 10 |
| series defaults block | 15 |
| AI behaviour block | 2 blocks × 6 flags |
| car filter (`SelectableCars`) | 38 |
| series AI selectable-cars block | 1 (`Acceptlist`) |

Outside the career tree the records are different: the Featured series has **16**
fields and the Featured event **14** (`SCHEMA_REFERENCE.md` part 2).

- **verified** — These are the record sizes of the career schema.
  *How to reproduce:* count the field names of one record of each type in the
  career data — the audit loader (`_tools\audit_career.py`, `model_from_bcs`)
  reads every one of them.

- **verified** — The **career** series record has no `SeriesRules` field (the
  Featured record does) and its `SeriesOrderData` list is always empty; the PI,
  cost, power and weight fields are always zero; the division field is always
  open. *How to reproduce:* the same loader, plus one record per series — no rule
  field exists to read, and those five groups carry the same value in every
  record.

## 5.3 Counts

### Career totals

| level | vanilla | custom | total |
|---|---|---|---|
| cup | 6 | 1 (103) | 7 |
| ladder | 34 | 1 | 35 |
| series | 176 | 2 (20003, 20004) | 178 |
| event | 623 | 4 | 627 |

- **verified** — Totals per level. *How to reproduce:*
  `python _tools\audit_career.py`.

- **observed** — The live copy mixes the vanilla content with the custom
  additions, so a vanilla count taken on this copy has to be split as above to
  be comparable with a clean install.

- **observed** — Per-cup ladder counts are **not** vanilla: cups were
  reorganised (a ladder moved between cups), so only the totals above are
  publishable. Publishing a per-cup layout would misrepresent a clean install.
  *How to reproduce:* compare the cup of a ladder in this copy with a clean
  install — the totals agree, the per-cup distribution does not.

### Events per series

| events in series | series |
|---|---|
| 4 | 69 |
| 1 | 37 |
| 3 | 31 |
| 5 | 28 |
| 6 | 8 |
| 8 | 3 |
| 7 | 1 |
| 2 | 1 |

- **verified** — 178 series, 627 events.
  *How to reproduce:* `python _tools\audit_career.py`.

### Track layouts

- **verified** — 71 layouts are used by the 627 events; the most used layout
  carries 28 events, the least used carries 1, so no layout is unused.
  *How to reproduce:* `python _tools\audit_career.py`; the
  per-layout event count is also published in `docs/data/TRACKS.md`.

## 5.4 Identity

- **verified** — A track has two identities that must always change together:
  `SerialTrackId` (integer) and `TrackId` (GUID form whose last twelve digits
  are that same serial). Changing one without the other yields an event that
  loads the wrong layout or fails. *How to reproduce:*
  `python _tools\audit_career.py` — every event's two ids agree in all 627 rows;
  desynchronise one in a copy and the event breaks.

- **verified** — Cup, ladder, series and event ids are opaque and must never be
  recomputed. Only the documented custom ranges constrain a new id.
  *How to reproduce:* the same command; ids bear no relation to the
  names they belong to.

| kind | reserved range |
|---|---|
| custom series | ≥ 20000 |
| custom events | 65897900–65899999 |

- **verified** — Reusing an id is worse than a duplicate row: a profile that
  completed the old object shows the new one as completed.
  *How to reproduce:* the per-series and per-event id columns of the audit —
  a reused id appears twice; in game, a recycled id shows the series
  pre-completed for a profile that played the old one.

## 5.5 Text

- **verified** — Cup, ladder and series `Name` fields hold an `IDS_` key; the
  event `Name` and `Description` are literal strings. *How to reproduce:*
  `python _tools\audit_career.py` — it reports missing string keys, and none is
  reported for a series/cup/ladder name, while event names resolve to nothing.

- **verified** — `IDS_` keys may be any length (resolution is by name hash), and
  only the player's locale need carry the new key; other locales fall back to
  the base string. *How to reproduce:* add a key of a different length to one
  locale, apply, switch languages.

## 5.6 Art

- **verified** — Event art fields hold `GAME:`-prefixed asset paths. They are
  **not** localised and must be copied verbatim from a donor event; inventing a
  path leaves the event without art, and the poster is the field most likely to
  be forgotten. *How to reproduce:* `python _tools\audit_career.py` — every
  populated path starts with the same prefix, and any event whose art was
  invented shows a blank tile in game.

- **observed** — Art is shared between events: several events point at the same
  poster, so a duplicated art path is normal rather than a bug.
  *How to reproduce:* the same command (path reuse counts).

## 5.7 Derived tables

Two generated tables accompany this page. They are rebuilt by the audit command
and are the only place where per-car and per-track rows are listed:

| table | columns |
|---|---|
| `docs/data/CARS.md` | `CarId`, name, year, class, PI, price, status + reason |
| `docs/data/TRACKS.md` | `SerialTrackId`, track/layout, event count |

- **verified** — `python _tools\audit_career.py --check` exits non-zero when
  either table is out of date with the data. *How to reproduce:* the command
  itself.

Underlying totals used by those tables:

| set | count |
|---|---|
| catalogue cars | 711 |
| showroom cars | 682 |
| AI cars (`AI_` prefixed) | 541 |
| usable AI cars | 508 |
| divisions | 52 |
| posters | 168 |
| deny rules / always-denied ids | 32 / 45 |

- **verified** — Counts as above. *How to reproduce:* `python _tools\inventory.py`
  and `python _tools\audit_career.py`.

- **observed** — 32 of the 45 always-denied ids are still listed in vanilla
  acceptlists, which is why the deny layer has to be applied on top of the list
  rather than instead of it (`CARS_AND_PI.md` §3.4).

## 5.8 Snapshots — always say which one

- **verified** — The installed data holds **two** snapshots of the career
  content, and they do not carry the same series count: one has 126–127 series,
  the other 177–178. Any count quoted in this doc set refers to the **live**
  snapshot, the one with 178 series (176 vanilla + 2 custom) and 627 events.
  *How to reproduce:* `python _tools\inventory.py` prints both snapshot ids and
  their per-group file counts; the audit prints the live one it used.

- **verified** — Reading the wrong snapshot produces plausible but wrong
  numbers, because both snapshots contain same-shaped records.
  *How to reproduce:* point the inventory at the older snapshot and compare the
  series total with this page.

## See also

`CAREER_MODEL.md` · `RACE_SYSTEM.md` · `CARS_AND_PI.md` · `AI_AND_GRIDS.md` ·
`CAREER_AUDIT.md` · `GLOSSARY.md`
