# GT Mode — the common career (the basics)

> **Area: carreira comum.** What every ordinary series shares: how the career
> is modelled, what each layer controls, how the AI is wired in vanilla, and
> which tool changes what. The multi-class grids are in
> [CUSTOM_RACE](CUSTOM_RACE.md); the 20004 package is in
> [CIRCUIT_EXPERIENCE](CIRCUIT_EXPERIENCE.md); the discovery log is in
> [GT_CAFE](GT_CAFE.md).

Named after Gran Turismo's career mode, the project's inspiration: a ladder of
leagues you climb. Deeper background: [CONCEPTS](../en/CONCEPTS.md).

## 1. The model

`BuildersCupScheduleDataV4.json` (BCS), championship **500** = the career:

```
championship 500
  └─ cup           (order = LadderOrderData)
      └─ ladder    (order = OrderData)
          └─ series  (SeriesId; Name = IDS_ key in the .str)
              └─ event (EventDataId)  ── ID ──> BCEventOverrides.json
series ── SeriesId ──> BCSeriesSelectableCars.xml (required; without it the click crashes)
```

Championship 1 is multiplayer and is never touched.

## 2. What each file controls

| file (CmsCache) | controls |
|---|---|
| `BuildersCupScheduleDataV4.json` | structure and order, series `AISelectableCars`, per-event `TargetPI`, dates, unlock state |
| `BCEventOverrides.json` | race rules per event: laps, weather, `ClassRestriction`, `TargetPI`, `AIFileName`, `ParentGeneratorId` |
| `BCSeriesSelectableCars.xml` | which cars the player may bring (acceptlist) |
| `LocStrings_pt-BR.str` | every displayed name (`IDS_<hash>` keys; new keys of any length work) |
| `AIField_<n>_Gen.xml` (**install zip only**) | who the AI drivers are and their PI — see [CUSTOM_RACE](CUSTOM_RACE.md) |

Two things that hide real caps (both bit this project):

- The **event's** `TargetPI` and `ClassRestriction` decide what the player may
  enter; the `BCEventOverrides` value was ignored while the BCS value stood.
  The "A700" cap of series 20004 was `TargetPI = 700` inherited from the donor
  event (fixed by kit mc59 → 999).
- `AISelectableCars` alone does **not** change the AI grid; the AIField XML does.

## 3. Rules the game enforces (verified)

- Acceptlist: at most **23** cars per series (a 682-car list left no eligible car).
- The car the game suggests when you own none of the list = the **lowest CarId**
  of the acceptlist; an empty or invalid list falls back to the MP4/4.
- New ids: `ChampionshipSeriesId` ≥ 20000, `EventDataId` 65897900–65899999,
  **never reused** (a reused event id shows as "already completed").
- A new series needs its `BCSeriesSelectableCars.xml` block (`ArrayLength` + 1).
- Poster, banner and intro are inherited from the donor series — replace them.

## 4. How the vanilla AI is wired

Survey of the 176 vanilla series that have AI (`python _tools\aifield_survey.py`
and the BCS + overrides, excluding series 20004):

- **522 events** use a *template* AIField, **85 events** (23 series, mostly
  endurance/showcase series) use a *list*, 18 have none. So the pool with a
  dynamic PI is the career's default and the fixed list is the exception.
- A template field draws 23 AI cars from a pool of **1–22** cars (most often
  8–9) with a PI window per class tier (`700–800`, `800–900`, `600–700`…).
- The AI target PI follows the **player's** PI, 10–50 below it: the common
  frame set is `−40…+10 / −40…0 / −50…−10` (146 files), and the last frame
  gave exactly that in three runs on our series. Details and evidence:
  [AIFIELD_GRIDS](../AIFIELD_GRIDS.md).

Consequence for an ordinary series: you pick the *kind* of field (pool or list)
and the cars; the difficulty comes from the player's own car.

## 5. What to touch, and with what

| goal | how | doc |
|---|---|---|
| rename a series/cup/ladder | `str_edit.py` + `bytes` kit | [tutorial 01](../tutorials/01_rename.md) |
| reorder or unlock | permute `LadderOrderData`/`OrderData`; flip unlock flags | [tutorial 02](../tutorials/02_reorder.md) |
| new series | spec + `build_series.py` | [tutorial 03](../tutorials/03_new_series.md), [F3_TEMPLATE](../F3_TEMPLATE.md) |
| lift an event's PI/class cap | kit on the event's `TargetPI` (mc59 is the model) | [AIFIELD_GRIDS](../AIFIELD_GRIDS.md) |
| change who the AI is | `AIField` via `fmlib.aifield` + `install_edit.py` | [CUSTOM_RACE](CUSTOM_RACE.md) |
| apply or undo anything | `cache_edit.py` (CmsCache) / `install_edit.py` (install) | [PIPELINE](../en/PIPELINE.md) |

## 6. Before touching a series

1. Which copy does the game read? CmsCache for everything that lives there;
   the install only for groups the cache never holds ([ADR-004](../decisions/ADR-004_install_vs_runtime.md)).
2. Is the target's content group in the cache? If not, `cache_edit.py` skips it.
3. Kits are **snapshot-bound**: a new server snapshot means regenerating.
4. Game **closed** before any write; `--dry-run` first, `--verify` after.
5. Check the **event** (`TargetPI`, `ClassRestriction`, `AIFileName`) before
   blaming the series or the XML.
