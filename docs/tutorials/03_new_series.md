# Tutorial 03 — New series from a spec, all the way into the game

Goal: add one career series with `build_series.py`, prove it on a copy of the
cache, then apply it for real and test it in game.

Canonical references: `specs\README.md` (every spec field + the checks the
builder runs); `docs\F3_TEMPLATE.md` (why each piece exists — ids, series
shell, events, overrides, car registration, name, art);
`docs\en\GETTING_STARTED.md` §5 (the same loop on a copy).

## 1. Write the spec

Copy `specs\_TEMPLATE.json` to `specs\<your_series>.json` and edit it. The
fields are documented in `specs\README.md` — the required ones are:

| field | rule |
|---|---|
| `kit` | output folder name, `patches/<kit>/` |
| `series.id` | ≥ 20000, never reused (`ids.json`, `ids_retired.json` in the `patches` folder) |
| `series.name` | displayed pt-BR name (becomes a new `IDS_` key) |
| `series.donor_series` | shell to clone, recommended 601 |
| `placement.ladder` | existing ladder id, or `{id, donor, name, cup}` |
| `events[].id` | 65897900–65899999, never reused |
| `events[].track` | `SerialTrackId` from the `PISTAS` inventory page |
| `cars.acceptlist` | `"showroom"` (682 cars) or an explicit list of ids |

Event ids are never reused because the save marks completion by
`EventDataId`; that is the "series already done" bug in `docs\F3_TEMPLATE.md`
§1.1.

## 2. Build the kit

```powershell
python _tools\build_series.py --spec specs\<your_series>.json            # -> patches\<kit>\
```

For a test run that does not touch the real cache:

```powershell
python _tools\build_series.py --spec specs\_TEMPLATE.json --cache-dir _work\cachetest --out _work\kit_demo
```

The builder refuses ids already in use, retired ids and ids outside the custom
ranges; it refuses an `AIFileName` missing from the manifest and any broken
ladder/order invariant; it warns about always-denied cars and about an
acceptlist with no cheap car (`specs\README.md`). It exits 3 when there are
warnings, and it prints the `plan_lint` command for the next step.

Expected output lines: `cache: … | snapshots: …`, `kit: …`, one block per
snapshot (`series … -> ladder … | events …`, `XML entry SeriesId=…`,
`.str + …`) and `plan: … (N targets)`.

## 3. Lint and dry-run

```powershell
python _tools\plan_lint.py --plan patches\<kit>\plan.json
python _tools\cache_edit.py --dry-run --plan patches\<kit>\plan.json --cache-dir _work\cachetest
```

The dry-run is not optional: the apply only accepts a clean dry-run from the
last 30 minutes for the same plan, payloads and cache state, and it refuses
while a `forza*` process runs (`docs\en\PIPELINE.md`). Exit code 3 means
warnings only.

## 4. Apply on the copy

```powershell
python _tools\cache_edit.py --plan patches\<kit>\plan.json --cache-dir _work\cachetest --verify --no-backup
```

Expected: `verificacao: OK`. You have just proved the payloads, the manifest
update and the re-encryption without risking the real cache.

The maintainers regression-test the generator against a private reference kit
after every `fmlib` change (lab only). The spec used for it is
`specs\examples\mc55_treino_20004.json`; use it as a worked example.

## 5. Apply for real

**Close the game.** The CmsCache blobs are locked while it runs; writing fails
with `WinError 5` and can leave the cache inconsistent.

```powershell
python _tools\cache_edit.py --dry-run --plan patches\<kit>\plan.json
python _tools\cache_edit.py --plan patches\<kit>\plan.json --verify
python _tools\cache_verify.py
python _tools\inventory.py
```

- The apply backs the whole cache up to `_backup\cache_<timestamp>` and appends
  to `patches\ledger.jsonl`.
- `cache_verify.py` must end with 0 errors.
- `inventory.py` refreshes `_data` and the inventory pages (including
  the `ESTADO` inventory page, which shows which kits are live).

Commit the kit together with its generator and the refreshed data.

## 6. Test in game (F3.7 sequence)

The series must, in this order: **appear** in the career → **open** → **enter
the track with an eligible car** → **complete** → **pay the prize**
(`docs\F3_TEMPLATE.md` §1.11).

If it does not:

| symptom | first thing to check |
|---|---|
| crash with `0xe06d7363` when clicking | missing `BCSeriesSelectableCars.xml` entry (`docs\F3_TEMPLATE.md` §1.6) |
| the game suggests buying an unexpected car | acceptlist has no cheap car / a denied car — rule in `docs\F3_TEMPLATE.md` §4 |
| series looks already completed | reused `EventDataId` |
| series is gone after a server update | kit is snapshot-bound: rebuild from the new snapshot |

Symptoms and causes already diagnosed are collected in [TROUBLESHOOTING](../TROUBLESHOOTING.md).

## 7. Rolling back

`python _tools\rollback_cache.py` restores the CmsCache from the newest
`_backup\cache_<timestamp>` (a safety copy of the current cache is taken
first). It is a **whole-cache** restore, not per kit: back up more than one
step and the later kits disappear too. To pick a specific backup, pass its
folder: `python _tools\rollback_cache.py _backup\cache_<timestamp>`.
