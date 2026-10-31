# PIPELINE — applying a career mod to FM8

> 🌐 [Português](../pt-br/PIPELINE.md) · **English** — first time here? Start with [GETTING_STARTED](GETTING_STARTED.md).

Operational manual for the validated pipeline. Research and format details
are kept in the maintainer's lab log; this page holds only what you need to
**reproduce** a mod.

## Golden rules

1. **Close the game before writing.** It locks the CmsCache blobs. Writing
   with the game open fails with `WinError 5` and leaves the cache
   inconsistent; that is how the first unlock attempt broke.
2. **The runtime source is the CmsCache**, not the install:
   `%LOCALAPPDATA%\Microsoft.ForzaMotorsport\CmsCache\`.
   The install (`media/pcfamily/cms/`) is only a seed and does **not** need
   changes. The proof of concept showed the game ignores it for text.
3. **Every write makes an automatic backup** (`_backup\cache_<timestamp>`,
   ~13 MB). Rollback: `python _tools\rollback_cache.py`.
4. **Do not mirror `mediapc/`.** Discontinued on 2026-10-30: the game does
   not read `mediapc/`; the CmsCache is the only source (rule 2).
5. **Never commit the CMS AES key, the Forza Mod Tool or game files.** The
   repo is public; the ignore rules and `docs/THIRD_PARTY.md` say what stays local.

## Prerequisites

Python 3, the .NET 10 SDK, and the compiled oracles:

```powershell
dotnet build _tools\cmsoracle\cmsoracle.csproj -c Release
dotnet build _tools\cacheoracle\cacheoracle.csproj -c Release
```

The oracles rely on the Forza-Mod-Tool v1.3.0 runtime and tables, which you
keep locally (not in the repo): see `docs/THIRD_PARTY.md` and the README.

## Minimal concepts

See [CONCEPTS](CONCEPTS.md) for the full picture.

| piece | what | notes |
|---|---|---|
| `prod\<snapshot>` | plaintext manifest of a snapshot (10,434 files, 8 groups) | `Size` = **encrypted** payload length; `Checksum` = base64 SHA-256 of the encrypted payload |
| blob `<bucket>\<SHA256HEX>` | deflate ZIP holding the encrypted entries | **content-addressed**: the original name is the sha256 of its content. We keep the name and only update `Size`/`Checksum` in the manifests (Strategy S), which the game accepts |
| `cache-manifest.json` | snapshot→blob index (10 entries), **encrypted** (asset container) | re-encrypt using the original as template: `cacheoracle.exe enc <plain> <template> <out>` |
| `Id` (int64) in the manifest | opaque (not a hash of `Path`; fnv/murmur/crc/md5/sha tested) | never recompute; keep it |
| CMS payload | `AES-128-CBC(IV=0×16)` over `gzip` | encrypt with the oracle: `cmsoracle.exe enc <plain> <encrypted_template> <out>` (template = current payload); Python fallback `cms_crypto.py` |

## Building and applying a mod

```powershell
# 1. build the kit (new series: spec + build_series; others: a generator on _tools/fmlib)
python _tools\build_series.py --spec specs\<series>.json   # writes patches\<kit>\
# 2. lint + simulate
python _tools\plan_lint.py --plan patches\<kit>\plan.json
python _tools\cache_edit.py --dry-run --plan patches\<kit>\plan.json
# 3. apply + verify (GAME CLOSED)
python _tools\cache_edit.py --plan patches\<kit>\plan.json --verify
# 4. refresh inventory/state and commit (ledger + _data + docs/inventario)
python _tools\inventory.py
# 5. roll back if needed
python _tools\rollback_cache.py
```

To test without touching the game: run `python _tools\snapshot_cache.py` and
add `--cache-dir _work\cachetest` to the commands above.

The code enforces these guards for Claude, opencode, and humans alike. The
apply **refuses** to run without a clean `--dry-run` from the last 30 minutes
for the same plan, payloads, and cache state. It also refuses while a `forza*`
process is running, or when `_tools\plan_lint.py` rejects the plan. The lint
covers static checks, the multiplayer staying untouched, and Strategy
S/Checksum. To run the lint alone: `python _tools\plan_lint.py --plan <plan.json>`.

For `plan.json`, see the commented example in `_tools\cache_edit_plan_example.json`.
`cache_edit.py` resolves snapshot→blob **by the entries' Checksum in the
manifest**, never by name or mtime. The first version picked the old blob
because it matched by name.

## Editing text (`.str`)

`_tools\str_edit.py` parses and rewrites `.str` files with a byte-identical
round-trip. New keys are free-form (`IDS_<md5("MC44|<label>")>` since mc44;
see `fmlib.strs.key_for`; collisions are checked) and can have **any length**. The
old "same number of chars" rule only applied to the proof of concept's
byte-level patch. Only `LocStrings_pt-BR.str` gets the new keys today; the
other 19 languages do not (pending).

## Editing the career (`BuildersCupScheduleDataV4.json`)

- Reorder = permute `cup.LadderOrderData` and `ladder.OrderData` (id lists).
  This is cheap, needs no new ids, and carries no save risk.
- Unlock = zero `RequiredLadders/RequiredSeries/RequiredEvents` (+ counters)
  in every series.
- Re-serializing with `json.dump(obj, ensure_ascii=False, separators=(",",":"))`
  reproduces the original **byte for byte** (validated on all 1,197,441 B).

## Publishing a kit (`patches/<name>/`)

A kit holds `plan.json`, the `.enc` payloads, and a notes file that states the
scope and how to re-apply. A kit only
works on a CmsCache with the **same snapshots**; if the server ships a new
snapshot, regenerate the kit.

## New series (F3) and trackday (F6)

None of this changes the apply pipeline above (plan → `--dry-run` →
`--verify`); only what goes inside the plan changes.

- **New series (F3):** the default path is a spec plus `build_series.py`
  (`specs/README.md`). The recipe and its reasons are in
  **`docs/F3_TEMPLATE.md`**: new ids (`ChampionshipSeriesId` ≥20000,
  `EventDataId` 65897900–65899999, never reused), the series plus the ladder
  `OrderData`, events plus `BCEventOverrides`, an entry in
  `BCSeriesSelectableCars.xml` (without it, clicking the series crashes), and
  a new `IDS_` key in the `.str`. Symptoms and causes seen so far are in
  [TROUBLESHOOTING](../TROUBLESHOOTING.md).
- **Trackday and AI grid (F6):** series 20004 in cup 103 "7. Trackday" (kits
  mc55–mc58 in the maintainer's lab). The AI does not come only from the BCS: the field
  is pinned by `AIField_117160001_Gen.xml`, which is **not in the CmsCache**
  (only in the install zip). Content in such a group is **not** applied by
  `cache_edit.py`; use `python _tools\install_edit.py --logical <file> --payload
  <.enc>` (`--dry-run` first, game closed, `--verify`; backup in
  `_backup\install_<ts>`, undo with `--restore`). It rewrites the zip, the
  install manifest and the two `prod\` snapshots + `cache-manifest.json`
  together. Tested in game with mc58. See **`docs/AIFIELD_GRIDS.md`**.

## Post-write verification

`python _tools\cache_verify.py` checks `Size`/`Checksum` of every file,
blob↔manifest consistency and divergences per snapshot. Every apply must end
with 0 errors.
