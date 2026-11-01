# Tutorial 02 — Reorder cups, ladders and series

Goal: change the order the career shows, without creating or deleting any id.

Canonical references: `docs\en\PIPELINE.md` → *Editing the career*;
`docs\en\CONCEPTS.md` §3 (career model + invariants). Kits are still applied by
the normal pipeline (plan → `--dry-run` → `--verify`).

## Where the order lives

`BuildersCupScheduleDataV4.json`, championship **500** (career):

| level | order field | contents |
|---|---|---|
| cup | `ChampionshipCupData` | the cup array itself |
| cup → ladders | `LadderOrderData` | list of `ChampionshipLadderId`, free permutation |
| ladder → series | `OrderData` | list of `ChampionshipSeriesId` |

Championship **1** (Featured Multiplayer) lives in another file and is off
limits — `plan_lint` refuses any target in it (`_tools\plan_lint.py`).

## Recipe A — reorder ladders inside a cup (cheap, `json` targets)

`LadderOrderData` is a pure id list, so one `json` target per snapshot is
enough. Reordering keeps the same set of ids: no new ids, no save risk
(`docs\en\PIPELINE.md`).

Find the real ids and positions first — the `CARREIRA` inventory page (career
tree) and the generated `ladders.json` (cups, ladders, series) come from
`_tools\inventory.py`; never hand-edit them. In the snapshots this repository
ships, the second cup (`ChampionshipCupData[1]`, cup id 2) has the ladders
`[764, 25, 24, 23, 22]`; the plan below reverses its tail.

```json
{
  "note": "tutorial 02: ladders of cup 2, tail reversed",
  "targets": [
    {"logical": "BuildersCupScheduleDataV4.json",
     "group": "14571097C5A44CF4154937B60E5F6DDE",
     "op": "json",
     "path": "Championships[0].ChampionshipCupData[1].LadderOrderData",
     "value": [764, 22, 23, 24, 25],
     "snapshots": ["20260923t185113xwyk"]},
    {"logical": "BuildersCupScheduleDataV4.json",
     "group": "14571097C5A44CF4154937B60E5F6DDE",
     "op": "json",
     "path": "Championships[0].ChampionshipCupData[1].LadderOrderData",
     "value": [764, 22, 23, 24, 25],
     "snapshots": ["20251124t234605pkod"]}
  ]
}
```

Notes on the plan format:

- The path index (`ChampionshipCupData[1]`) is per snapshot — the old snapshot
  has different content (`SERIES_CHECKLIST.md` §1.10), so verify each snapshot
  separately instead of copying indexes blindly (check the `cup id=` the index
  lands on, not just the position).
- One target per snapshot: `plan_lint` rejects a duplicated
  `(logical, snapshot, path)` triple, and `cache_edit.py` re-encrypts each
  target with the *current* payload as template, so several `json` targets on
  the same file accumulate in order.
- A `json` target is **not** covered by `check_invariants` (it only runs in a
  `bytes` kit): nothing stops you from writing an id of a ladder that does not
  exist, or dropping one. Read the field back after the apply (step *Check in
  game*, below) and confirm the new list is a permutation of the old one.
- Reordering **cups** means rewriting the whole `ChampionshipCupData` array;
  that is a `bytes` kit, not a small `json` value (build it with
  `fmlib`).

## Recipe B — reorder series inside a ladder (`bytes` kit)

`ladder.OrderData` must match the order of the series array
(`ChampionshipSeriesData`), not just its set — that invariant is checked by
`fmlib.bcs.check_invariants` and asserted by the frozen generators that move
series. So a series reorder permutes **both** the array and `OrderData`, and the
array is too big to inline in a `json` target: build a `bytes` kit.

```python
# _work\reorder_series.py  - run from the repo root
import json, os, sys
sys.path.insert(0, os.path.join(os.getcwd(), "_tools"))
from fmlib import bcs
from fmlib.cache import Cache
from fmlib.crypto import decrypt
from fmlib.kit import Kit

CUP, LADDER = 2, 22            # from _data\ladders.json
ORDER = [20003, 570, 571, 572, 553, 601]   # new series order (same ids, permuted)

cache = Cache(r"_work\cachetest")
kit = Kit("mc99_order", cache, out_dir=r"_work\kit_order")
for snap in cache.snapshots:
    obj = json.loads(
        decrypt(cache.payload(snap, bcs.LOGICAL)).decode("utf-8"))
    _c, lad = bcs.find_ladder(obj, LADDER)
    by_id = {s["ChampionshipSeriesId"]: s for s in lad["ChampionshipSeriesData"]}
    if set(ORDER) != set(by_id):
        raise SystemExit("ORDER is not a permutation of ladder %d: missing %s, "
                         "extra %s" % (LADDER, sorted(set(by_id) - set(ORDER)),
                                       sorted(set(ORDER) - set(by_id))))
    lad["ChampionshipSeriesData"] = [by_id[i] for i in ORDER]
    lad["OrderData"] = list(ORDER)
    bcs.check_invariants(obj, snap)          # unique ids + both order invariants
    plain = json.dumps(obj, ensure_ascii=False,
                       separators=(",", ":")).encode("utf-8")
    kit.add(snap, bcs.LOGICAL, plain)
print(kit.write_plan("reordena as series da ladder %d" % LADDER))
```

`ORDER` must list **every** current series of the ladder, or the omitted one
disappears from the career; the `set(ORDER) != set(by_id)` guard turns that into
a loud error instead of a silent deletion. In the snapshots this repository
ships, ladder 22 holds `[601, 553, 572, 571, 570, 20003]` — the example above is
that list reversed.

`separators=(",", ":")` with `ensure_ascii=False` reproduces the original file
byte for byte apart from your change (`docs\en\PIPELINE.md`, *Editing the
career*). `check_invariants` is your proof that only the order moved.

## Lint, dry-run, apply

```powershell
python _tools\plan_lint.py --plan _work\kit_order\plan.json --cache-dir _work\cachetest
python _tools\cache_edit.py --dry-run --plan _work\kit_order\plan.json --cache-dir _work\cachetest
python _tools\cache_edit.py --plan _work\kit_order\plan.json --cache-dir _work\cachetest --verify --no-backup
```

Expected: `0 erros, 0 avisos` from the lint, `alvos avaliados: 2 (alterados: 2,
...)` and `verificacao: OK`. To see the change applied, run the read-back snippet
of the next section.

Then, for real (game **closed**, with backup):

```powershell
python _tools\cache_edit.py --dry-run --plan patches\<kit>\plan.json
python _tools\cache_edit.py --plan patches\<kit>\plan.json --verify
python _tools\cache_verify.py
python _tools\inventory.py
```

`cache_verify.py` must end with 0 errors; `python _tools\inventory.py --check`
tells you whether the inventory pages is current after the apply.

## Check in game, then roll back

Before the game, read the field back from the copy (this is the check a `json`
target does not give you):

```python
# _work\read_back.py - run from the repo root
import json, os, sys
sys.path.insert(0, os.path.join(os.getcwd(), "_tools"))
from fmlib import bcs
from fmlib.cache import Cache
from fmlib.crypto import decrypt

cache = Cache(r"_work\cachetest")
for snap in cache.snapshots:
    obj = json.loads(decrypt(cache.payload(snap, bcs.LOGICAL)).decode("utf-8"))
    cup = obj["Championships"][0]["ChampionshipCupData"][1]
    print(snap, cup["ChampionshipCupId"], cup["LadderOrderData"])
```

For the `json` recipe the line must read `2 [764, 22, 23, 24, 25]` on both
snapshots, and every id must still exist as a ladder of that cup.

Then open the career screen and confirm the new order (prices/entries unchanged,
no series missing). Undo with `python _tools\rollback_cache.py` (game closed).

A reorder does not change `EventDataId`s, so progress is untouched — ids are
what the save tracks (`docs\en\CONCEPTS.md` §3). Reusing or rewriting an event
id is the recipe for a "series already done" bug, not reordering.
