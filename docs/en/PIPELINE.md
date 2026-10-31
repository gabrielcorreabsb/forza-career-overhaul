# PIPELINE — applying a career mod to FM8

> 🌐 [Português](../pt-br/PIPELINE.md) · **English** — first time here? Start with [GETTING_STARTED](GETTING_STARTED.md).

One page, from a plan to a verified cache. Formats and the data model live in
[CONCEPTS](CONCEPTS.md); this page holds only the operational steps.

## Golden rules

1. **Close the game before writing.** It locks the CmsCache blobs; a write with
   the game open fails with `WinError 5` and can leave the cache inconsistent.
2. **The runtime source is the CmsCache**, not the install:
   `%LOCALAPPDATA%\Microsoft.ForzaMotorsport\CmsCache\`. The install
   (`media/pcfamily/cms/`) is only a seed and does not need changes.
3. **Every write makes an automatic backup** (`_backup\cache_<timestamp>`,
   ~13 MB). Rollback: `python _tools\rollback_cache.py`.
4. **Do not mirror `mediapc/`.** The game does not read it; the CmsCache is the
   only source (rule 2).
5. **Never commit the CMS AES key, the Forza Mod Tool or game files.** The repo
   is public; `.gitignore` and `docs/THIRD_PARTY.md` say what stays local.

## Prerequisites

Python 3, the .NET 10 SDK, and the compiled oracles. The oracles also need the
Forza-Mod-Tool v1.3.0 runtime and tables, which you keep locally (not in the
repo): see [THIRD_PARTY](../THIRD_PARTY.md).

```powershell
dotnet build _tools\cmsoracle\cmsoracle.csproj -c Release
dotnet build _tools\cacheoracle\cacheoracle.csproj -c Release
```

## Pieces

| piece | what | notes |
|---|---|---|
| `prod\<snapshot>` | plaintext manifest of a snapshot (10,434 files, 8 groups) | `Size` = **encrypted** payload length; `Checksum` = base64 SHA-256 of the encrypted payload |
| blob `<bucket>\<SHA256HEX>` | deflate ZIP holding the encrypted entries | content-addressed: the original name is the sha256 of its content. We keep the name and update only `Size`/`Checksum` in the manifests (Strategy S) |
| `cache-manifest.json` | snapshot→blob index (10 entries), **encrypted** (asset container) | re-encrypt with the original as template: `cacheoracle.exe enc <plain> <template> <out>` |
| `Id` (int64) in the manifest | opaque (not a hash of `Path`; fnv/murmur/crc/md5/sha tested) | never recompute; keep it |
| CMS payload | `AES-128-CBC(IV=0×16)` over `gzip` | encrypt with the oracle: `cmsoracle.exe enc <plain> <encrypted_template> <out>` (template = current payload); Python fallback `cms_crypto.py` |

## The loop

```powershell
# 1. build the kit (new series: spec + build_series; anything else: a generator on _tools/fmlib)
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

A plan is a list of targets; the commented example is
`_tools\cache_edit_plan_example.json` (four targets on one kit: two `json` on
`BuildersCupScheduleDataV4.json` plus two `bytes` on the pre-edited
`LocStrings_pt-BR.str`, one per snapshot).

## Guards enforced by the code

The apply refuses to run when:

- the game is open (any `forza*` process);
- there is no clean `--dry-run` from the last 30 minutes for the same plan,
  payloads and cache state;
- `plan_lint.py` rejects the plan (static checks, championship 1 untouched,
  Strategy S/Checksum, retired ids).

`cache_edit.py` resolves snapshot→blob **by the entries' Checksum in the
manifest**, never by name or mtime. Lint alone:
`python _tools\plan_lint.py --plan <plan.json>`.

## Text (`.str`)

`_tools\str_edit.py` parses and rewrites `.str` files with a byte-identical
round-trip. New keys are free-form (`IDS_<md5("MC44|<label>")>`, see
`fmlib.strs.key_for`; collisions are checked) and can have **any** length — the
game resolves a key by name hash. Only `LocStrings_pt-BR.str` gets the new keys
today; the other 19 languages do not (pending).

## Career (`BuildersCupScheduleDataV4.json`)

- Reorder = permute `cup.LadderOrderData` and `ladder.OrderData` (id lists).
  No new ids, no save risk.
- Unlock = zero `RequiredLadders/RequiredSeries/RequiredEvents` (+ counters) in
  every series.
- Re-serializing with `json.dump(obj, ensure_ascii=False, separators=(",",":"))`
  reproduces the original **byte for byte** (validated on all 1,197,441 B).

## Publishing a kit (`patches/<name>/`)

A kit holds `plan.json`, the `.enc` payloads, and a notes file that states the
scope and how to re-apply. A kit only works on a CmsCache with the **same
snapshots**; if the server ships a new snapshot, regenerate the kit.

## New series, trackday and AI grids

Nothing here changes the loop above (plan → `--dry-run` → apply with
`--verify`); only what goes inside the plan changes.

- **New series:** the default path is a spec plus `build_series.py`
  (`specs/README.md`); step-by-step in
  [tutorial 03](../tutorials/03_new_series.md); the recipe and its reasons are
  in [F3_TEMPLATE](../F3_TEMPLATE.md): new ids (`ChampionshipSeriesId` ≥ 20000,
  `EventDataId` 65897900–65899999, never reused), the series plus the ladder
  `OrderData`, events plus `BCEventOverrides`, an entry in
  `BCSeriesSelectableCars.xml` (without it, clicking the series crashes), and a
  new `IDS_` key in the `.str`.
- **Trackday:** a custom series whose event is a single lap of a long circuit,
  with no practice session (`OpenPracticeLimitationTimeInSeconds = 0`).
- **AI grid:** the AI does not come from the BCS alone. The field is pinned by
  `AIField_<n>_Gen.xml`, named per event by the override's `AIFileName`, which
  is **not in the CmsCache** (only in the install zip). Content in such a group
  is **not** applied by `cache_edit.py`; use
  `python _tools\install_edit.py --logical <file> --payload <.enc>` (`--dry-run`
  first, game closed, `--verify`; backup in `_backup\install_<ts>`, undo with
  `--restore`). It rewrites the zip, the install manifest and the two `prod\`
  snapshots + `cache-manifest.json` together — and unlike `cache_edit.py` it has
  no sandbox (`--cache-dir`): a real apply touches the real install. See
  [AIFIELD_GRIDS](../AIFIELD_GRIDS.md) and
  [CUSTOM_RACE](../guides/CUSTOM_RACE.md).

Symptoms and causes already diagnosed are in
[TROUBLESHOOTING](../TROUBLESHOOTING.md).

## Post-write verification

`python _tools\cache_verify.py` checks `Size`/`Checksum` of every file,
blob↔manifest consistency and divergences per snapshot. Every apply ends with
`verificacao: OK` and `0 divergentes`; anything else means restore
(`rollback_cache.py`) instead of playing.
