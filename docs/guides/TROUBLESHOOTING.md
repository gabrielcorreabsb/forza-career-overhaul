# Troubleshooting

Symptom → cause → fix for the failures already seen while building career
mods. This page is a router: every entry points to the doc that explains the
reasoning, so read that one before changing anything.

Canonical references: [PIPELINE](../en/PIPELINE.md) (apply rules and guards),
[CONCEPTS](../en/CONCEPTS.md) (glossary), `SERIES_CHECKLIST.md` (new-series
checklist), `AI_GRIDS.md` (AI roster). Evidence logs are kept in the
maintainer's lab.

## 0. Before diagnosing

Run these three; they separate "bad payload" from "bad cache" from "stale
data" without touching the game.

```powershell
python _tools\cache_verify.py                                  # Size/Checksum, blob<->manifest, per snapshot
python _tools\inventory.py --check                             # the generated inventories stale?
python _tools\plan_lint.py --plan patches\<kit>\plan.json       # static + multiplayer + Strategy S/Checksum
```

If the cache is inconsistent, restore the newest automatic backup before
anything else:

```powershell
python _tools\rollback_cache.py
```

## 1. Symptom table

| symptom | cause | fix |
|---|---|---|
| Clicking a custom series kills the game (C++ throw `0xe06d7363`) | no `CarSelectCarRestrictions` block for that `SeriesId` in `BCSeriesSelectableCars.xml` (or `ArrayLength` not incremented) | clone a working block, mirror the acceptlist, `ArrayLength`+1, re-apply on both snapshots (mc40) |
| Apply dies with `WinError 5` halfway | game was running; it locks the cache blobs | close the game, verify the cache, roll back, redo dry-run then apply |
| Cache inconsistent / `cache_verify.py` reports divergences after an interrupted apply | partial write: blob replaced but `prod\<snapshot>` not updated (or the reverse) | `rollback_cache.py`, then a clean dry-run + apply; re-running the same plan may not converge the already-written entry |
| New series does not appear in the cup, or the cup will not open | expired `StartEndDate.To`/`CloseTime`, `AIFileName` that does not exist, `ParentGeneratorId` with no data, id missing from the ladder `OrderData` | `9999-12-31 23:59:59.999` dates, donor events + AI from the same track, id at the end of `OrderData` |
| Series shows as "already completed" right after being added | reused `EventDataId`: the save marks completion per event id | allocate fresh ids in 65897900–65899999; check `ids.json` and `ids_retired.json` (in the `patches` folder) (mc50) |
| Series name is a vanilla name, or the art says another series ("CLASSIC ENDURANCE") | not a `.str` bug — poster/banner/intro were inherited from the donor series | neutral poster + `IntroVideoPath: ""` (mc48, mc32) |
| Title shows a raw `IDS_…` string, or a plain-text title is ignored | `Name` must be an `IDS_` key; the key is missing from `LocStrings_pt-BR.str` | add `IDS_<md5("MC44|label")>` with `str_edit.py` (any length) |
| "You do not own {0}" names a car you did not expect | without an owned eligible car the game names the **lowest CarId** in the acceptlist, not the cheapest; an empty/invalid list falls back to the MP4/4 (1670) | put a cheap car you own in the acceptlist; ban-check with `denylist.json` |
| No eligible car at all, though the list looks right | acceptlist larger than the vanilla maximum (23 entries; one block had 682) — the selection layer drops/truncates it | reduce the acceptlist to ≤23 ids in the BCS **and** the XML, on both snapshots |
| AI grid uses the donor's cars | `AISelectableCars` empty in the BCS, and the field is really pinned by `AIField_117160001_Gen.xml`, which is not in the CmsCache | set `AISelectableCars` **and** write the XML with `install_edit.py` — see `AI_GRIDS.md` |
| `install_edit.py` dies with `WinError 5` writing the zip | the install denies DELETE to the user, so a rename-over (`os.replace`) fails | current `install_edit.py` rewrites the file in place; make sure the game is closed and re-run |
| AI grid went back to the old cars after it worked | Steam "verify files" or a new server snapshot restored the install zip / manifests | re-run `install_edit.py` with the kit's payload |
| Career menu empty or CMS error after an install edit | zip/manifest/prod checksums out of step, or a payload the game rejects | `install_edit.py --restore _backup\install_<time>`, then re-run `cache_verify.py` |
| Apply refuses: missing/expired dry-run | no clean `--dry-run` for the same plan, payloads and cache state in the last 30 minutes | re-run `python _tools\cache_edit.py --dry-run --plan patches\<kit>\plan.json` |
| Apply refuses: lint failure | `plan_lint.py` rejected the plan (multiplayer touched, Strategy S/Checksum, retired id) | fix the plan, then `python _tools\plan_lint.py --plan patches\<kit>\plan.json` |
| Nothing changes in game after a successful apply | an install path or `mediapc/` was edited instead of the CmsCache | edit only `%LOCALAPPDATA%\Microsoft.ForzaMotorsport\CmsCache\` |
| Every target diverges while the kit used to work | the server shipped a new snapshot; kits are snapshot-bound | regenerate the kit from the current cache |

## 2. Crashes and locked files

### 2.1 Throw `0xe06d7363` when clicking the series

The career screen builds its car-selection widget from
`BCSeriesSelectableCars.xml`. A series that exists in the BCS but has no
`CarSelectCarRestrictions` block there throws a native C++ exception the moment
you click it. The vanilla series 11520 had the same gap. Fix = clone the block
of a working series, keep the acceptlist mirrored with
`SelectableCars.BlockOrAcceptlist`, and increment `ArrayLength` (mc40; steps in
`SERIES_CHECKLIST.md` §1 item 6).

### 2.2 `WinError 5` during an apply

The game holds the cache blobs open. `cache_edit.py` refuses to start while a
`forza*` process exists, so this means the guard was bypassed or the game was
started mid-write. Close the game, then:

```powershell
python _tools\cache_verify.py
python _tools\rollback_cache.py
python _tools\cache_edit.py --dry-run --plan patches\<kit>\plan.json
python _tools\cache_edit.py --plan patches\<kit>\plan.json --verify
```

The first time this happened the apply left the old snapshot's blob written but
its `prod\` manifest untouched. Re-running the plan skipped that blob as
"identical" and did not converge the manifest, so a repair pass was needed by
hand. Treat any interrupted apply as "cache state unknown" and start from the
backup. See [PIPELINE](../en/PIPELINE.md) golden rule 1.

## 3. The series exists but is invisible or unplayable

### 3.1 Series/cup missing from the list

Three independent causes were confirmed (mc25, mc31, mc36):

- **Expired dates.** `StartEndDate.To` and `CloseTime` in the past hide the cup.
  Use `9999-12-31 23:59:59.999`.
- **AI without data.** An override whose `AIFileName` is not a real manifest
  entry, or whose `ParentGeneratorId` points at a generator with no data, makes
  the cup fail to open. Clone events **and** overrides from a track that has a
  valid donor (`track_events.json`).
- **Ladder not updated.** The series object must be appended to
  `ChampionshipSeriesData` **and** its id to the ladder's `OrderData`; the
  invariant is `OrderData == ids of its series`.

### 3.2 "Already completed"

The player profile marks progress per `EventDataId`, so an event id reused from
an older kit makes the new series look finished. Allocate ids from the custom
range 65897900–65899999, check `ids.json` (live ids) and
`ids_retired.json` (in the `patches` folder) (retired), and let `plan_lint.py` reject retired ones
(mc50 generated 65897910‑12 for series 20003).

## 4. Name and art

The localized **name** and the **art** are separate systems, and a wrong-looking
entry is usually art, not text.

- `Name` is an `IDS_` key resolved through `.str` (game key hash, so any length
  works). A literal string in `Name` is not displayed. New keys go in
  `LocStrings_pt-BR.str` only; the other 19 locales stay without them.
- Poster, banner, intro video and intro car colors are copied from the donor
  series. They are **not** localized: a pt-BR game can show "CLASSIC ENDURANCE"
  while the localized title is correct (lab diagnostics). Fix by pointing
  `ImagePath`/`BannerImagePath` at a neutral existing poster (mc48) and setting
  `IntroVideoPath: ""` (precedent mc32). Own art means repacking a
  `.swatchbin`, which is deferred.

## 5. Car eligibility and the suggested car

Confirmed rules (mc49/mc51/mc52, `SERIES_CHECKLIST.md` §4):

- The series requires an **owned** eligible car. Without one, the message
  `IDS_BuildersCup_MissingCarForRewardShowcase` names the car with the **lowest
  CarId** in the acceptlist — not the cheapest (Veloster 54k lost to Astra 61k).
- An empty or invalid acceptlist falls back to the **MP4/4 (1670)**. Vanilla
  "Open Class" tours (`Blocklist` empty) land there too.
- Check every id against the 32 global vetoes in `denylist.json`.
- Keep the acceptlist at ≤ 23 ids. Series 20004 shipped 682 (the only block in
  the game above the vanilla maximum of 23, mirrored in the XML) and the layer
  discarded the list, so the player got "no eligible car" even though the ids
  were right (lab diagnostics).
- There is no purchase popup to force: `Ownership`/`Upgrades`/`Tuning` are
  `None` across all vanilla series and the flow is informational only. Buying
  the car is manual.

## 6. AI grid

`AISelectableCars` in the BCS is only half of the roster. The field is pinned by
`AIField_117160001_Gen.xml`, a file whose content group is never materialized in
the CmsCache — the game reads it from the install zip, and `cache_edit.py`
skips it. That is why the AI still looked like the donor's classics after the
BCS change, and why the mc58 kit carries two plans (`plan.json` with the
intention, `plan_bcs.json` with what `cache_edit.py` can actually write); the XML
is written by `install_edit.py`. Rules for
car eligibility, `TargetPI` mapping and `AI_<car>_<pi>.xml` coverage are in
`AI_GRIDS.md`. Do not duplicate them here.

## 7. Guard refusals

`cache_edit.py` will not write unless a clean `--dry-run` for the same plan,
payloads and cache state happened in the last 30 minutes, no `forza*` process
runs, and `plan_lint.py` passes. Both refusals are expected behaviour, not bugs:
re-run the dry-run (optionally against a copy of the cache) and fix the plan.

```powershell
python _tools\snapshot_cache.py
python _tools\cache_edit.py --dry-run --plan patches\<kit>\plan.json --cache-dir _work\cachetest
```

## 8. Stale snapshot

Kits are bound to the snapshots present in the CmsCache (`prod\` entries). When
the server delivers a new snapshot, the recorded `Size`/`Checksum` no longer
match, blobs change shape, and inventory data goes stale. Regenerate the kit
from the current cache and refresh the generated data:

```powershell
python _tools\inventory.py
```
