# Cars and PI

The car side of the career: the class/PI scale, how many cars exist, how a
series limits them (acceptlistlist, suggested car), how a player actually
gets a car, and how much of the catalogue the career copy can reach.

Scope is championship 500 (career) unless stated. Evidence labels are defined in
`CAREER_MODEL.md`; reproductions use:

```powershell
python _tools\inventory.py
python _tools\audit_career.py
```

## 3.1 Class scale

- **verified** — The performance scale is a letter class over a PI range:

| class | PI range |
|---|---|
| E | 0–300 |
| D | 301–400 |
| C | 401–500 |
| B | 501–600 |
| A | 601–700 |
| S | 701–800 |
| R | 801–900 |
| P | 901–998 |
| X | 999 |

*How to reproduce:* `python _tools\inventory.py` (per-car class and PI) and
`python _tools\audit_career.py` — every car's PI falls inside its
declared class band, with X a single value at the top.

- **verified** — X is not a band but the value 999: there is no room above it.
  *How to reproduce:* the same command.

- **verified** (10/11/2026) — The table above is the **game's** PI scale: an event's
  `TargetPI`, an AI roster window and the PI shown in a lobby use it, so the caps of a
  series are the class ceilings (C 500, B 600, A 700, S 800, R 900). The `PI` column of
  the catalogue inventory is **not** on this scale (a class-C car lists 549 there while
  its lowest AI tune is 459); use the class and, for a per-car number, the lowest AI tune.
  *How to reproduce:* `python _tools\inventory.py` (catalogue PI) against
  `python _tools\aifield_survey.py --car <id>` (tune ladder).

## 3.2 Catalogue

- **verified** — The catalogue holds **711 cars**:

| class | cars |
|---|---|
| E | 50 |
| D | 106 |
| C | 64 |
| B | 92 |
| A | 95 |
| S | 125 |
| R | 111 |
| P | 62 |
| X | 6 |

*How to reproduce:* `python _tools\inventory.py`, car totals by class.

- **verified** — The car record's stored `PerformanceIndex` field is **not** on
  the game scale; it is an internal value of a different magnitude. Use the
  class id and the tuned PI range instead of that field.
  *How to reproduce:* `python _tools\audit_career.py` — compare the
  stored field with the class band for the same car.

## 3.3 How a series limits cars

A series can limit its field two ways, and in this data the two are mutually
exclusive per series. Both live in the 38-field `SelectableCars` object, in the
pair `BlockOrAcceptlist` + `BlockOrAcceptlistType`:

| mode | series | what it means |
|---|---|---|
| `Acceptlist` | 163 | a hand-written list of 1–23 cars; `CarClassId` is `Any`, so the field is defined by the list, not by the class |
| `Blocklist` | 15 | no entries at all: any car of the series' fixed class is eligible unless denied |

- **verified** — 163 series carry an explicit `Acceptlist` with an open class
  requirement, and 15 carry an empty `Blocklist` with a fixed class — 178 in
  total, so no series uses both modes.
  *How to reproduce:* `python _tools\audit_career.py` (filter type per series).

- **verified** — The series field `CarSelectAcceptlist` is a dead slot: empty on
  all 178 series. Reading it as "the acceptlist" yields an empty career.
  *How to reproduce:* the same table — one distinct value (empty) on that
  column, against 163 non-empty `SelectableCars` lists.

- **verified** — Entries in the acceptlist are car identity strings whose last
  twelve digits are the `CarId`; the prefix is a fixed GUID form. Matching must
  therefore be done on the 12-digit tail. 907 entries carry that shape.
  *How to reproduce:* the audit rows carry the parsed `CarId` for every
  acceptlist entry of every series.

- **verified** — Acceptlists hold at most **23** cars (907 entries over 163
  series, mean 5.6 there / 5.1 over all 178, minimum 1): the list can never
  exceed the 23 AI slots it feeds.
  *How to reproduce:* `python _tools\audit_career.py`; the per-series rows carry
  the acceptlist size, which is what the statistics are taken from.

- **verified** — A 682-car acceptlist broke eligibility: the series stopped
  offering its cars. 23 is the largest size observed to work.
  *How to reproduce:* build a series whose acceptlist is the whole catalogue,
  apply, open the series — no car can be selected. The exact engine limit
  between 23 and 682 is not known. **hypothesis** — a fixed buffer sized to the
  23 field slots; see `OPEN_QUESTIONS.md`.

- **verified** — The car selectability XML mirrors these two lists (whitelist
  for the acceptlistlist). Editing one side without the
  other leaves the series listing cars it will not accept.
  *How to reproduce:* compare a series' selectable-cars XML against its data
  lists, edit only the data list, apply, open the series — the car appears but
  cannot be selected.

### Suggested car

- **verified** — The car the series screen pre-selects is the entry with the
  lowest `CarId` in the acceptlist; with an empty list it falls back to a
  hard-coded default (the MP4/4, `CarId` 1670).
  *How to reproduce:* `python _tools\audit_career.py` —
  it prints the picked entry per series and the fallback when the list is empty.

- **observed** — No purchase popup is offered from the career screen: a car the
  player does not own cannot be acquired from there, and buying is a manual trip
  to the dealership. *How to reproduce:* open a series listing a car you do not
  own; the screen offers it but does not sell it.

## 3.4 Deny lists

- **verified** — A deny layer sits above the acceptlists: **32 rules** covering
  **45 car ids that are always denied**, of which **32 ids still appear in
  vanilla acceptlists**. So a listed car can still be vetoed.
  *How to reproduce:* `python _tools\audit_career.py` — it
  intersects the deny ids with every acceptlist.

- **verified** — The player must satisfy the acceptlist **and** the class
  ceiling **and** the deny layer **and** ownership at once; any one of them
  excludes the car. *How to reproduce:* the same intersection, then try one such
  car in game: the series lists it but refuses the selection.

## 3.5 The real PI gate

- **verified** — The PI filter fields on the series are inert in this data: PI
  min/max are zeroed and the class field reads open, while the class gate is
  carried by the events.
  *How to reproduce:* `python _tools\audit_career.py` — all
  distinct values are the zero/open ones.

- **verified** — 137 of 178 series use a **single** `TargetPI` across all their
  events; the other 41 vary it per event. The event `TargetPI` is the effective
  cap (`RACE_SYSTEM.md` §2.11).
  *How to reproduce:* the per-series audit rows carry the distinct `TargetPI`
  values of their events; the filter fields are read straight off the series
  record.

## 3.6 Multiclass

- **verified** — Multiclass is expressed purely by giving selected events of the
  same series **different** class ceilings and `TargetPI` values; there is no
  separate multiclass flag in the data.
  *How to reproduce:* compare the per-event ceilings inside a mixed series
  (`python _tools\audit_career.py`).

- **verified** (data) / **observed** (playable) — The player must satisfy the
  acceptlist, the class ceiling, the deny layer and ownership for the slot they
  enter; in a mixed series that means a different car requirement per slot.
  *How to reproduce:* enter each slot of a mixed series with a car from only one
  of its classes — the slots outside that class refuse the car.

## 3.7 Divisions

- **verified** — There are **52** division ids, numbered 0–53 minus three
  unused numbers. In this data every series sits in the open division, so
  divisions do not restrict anything today; restriction happens by class.
  *How to reproduce:* `python _tools\audit_career.py` — one
  distinct series value (open) against 52 defined divisions.

## 3.8 Listing coverage

- **verified** — The showroom offers **682** of the 711 catalogue cars; the
  remaining 29 are engine swaps with no showroom listing.
  *How to reproduce:* `python _tools\inventory.py` (showroom count) and the
  `swap` rows of `docs/data/CARS.md`.

- **verified** — **502 of 711** cars (70.6%) appear in at least one vanilla
  acceptlist; **209** (29.4%) are never listed:

| class | listed / total |
|---|---|
| E | 19 / 50 |
| D | 56 / 106 |
| C | 43 / 64 |
| B | 62 / 92 |
| A | 75 / 95 |
| S | 102 / 125 |
| R | 90 / 111 |
| P | 50 / 62 |
| X | 5 / 6 |

*How to reproduce:* `python _tools\audit_career.py` — intersect the acceptlists
of all series with the catalogue.

- **observed** — Being unlisted is not the same as being undriveable: the 15
  open-class series accept any car of their class and PI without a list
  (§3.3). The 209 figure therefore measures *listing* coverage — how often a car
  is guaranteed a slot — while `docs/data/CARS.md` reports a wider
  career-eligible set (637 cars, status `usable`), because the career car filter
  resolves to the open division. Both numbers are right about different
  questions. *How to reproduce:* read the two tables side by side.

- **verified** — Cars are reused heavily: a car appears in up to **6** vanilla
  series, median **2**. *How to reproduce:* `python _tools\audit_career.py`
  (per-car series count).

## 3.9 Status vocabulary

The generated car table gives every car exactly one status:

| status | count | reason |
|---|---|---|
| usable | 637 | career-eligible through the open division (and not denied) |
| denied | 45 | matched by the deny layer, so no series will accept it |
| swap | 29 | an engine swap, with no showroom listing |

*How to reproduce:* `docs/data/CARS.md`, regenerated by
`python _tools\audit_career.py`; the counts are the row totals per status.

See `DATA_REFERENCE.md` for the derived table's columns.

## See also

`CAREER_MODEL.md` · `RACE_SYSTEM.md` · `AI_GRIDS.md` ·
`DATA_REFERENCE.md` · `CAREER_AUDIT.md` · `GLOSSARY.md`
