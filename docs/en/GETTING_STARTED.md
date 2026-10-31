# Getting started

> 🌐 [Português](../pt-br/GETTING_STARTED.md) · **English**

Goal: in about 15 minutes, see the whole pipeline work on a **copy** of the
game cache, without touching the game. Then read [CONCEPTS](CONCEPTS.md) and
[PIPELINE](PIPELINE.md).

## 1. Requirements

- Windows, Forza Motorsport (2023) on Steam, launched at least once (this
  creates the CmsCache under `%LOCALAPPDATA%\Microsoft.ForzaMotorsport\`).
- Python 3.10+ and the .NET 10 SDK.
- The [Forza Mod Tool](https://github.com/HTTPJXRDN/Forza-Mod-Tool) v1.3.0 and
  the CMS key, kept locally and git-ignored: see
  [THIRD_PARTY](../THIRD_PARTY.md).
- A PowerShell terminal at the repo root.

## 2. One-time setup

```powershell
dotnet build _tools\cmsoracle\cmsoracle.csproj -c Release
dotnet build _tools\cacheoracle\cacheoracle.csproj -c Release
git config core.hooksPath .githooks          # pre-commit guards
# only if the game is NOT in F:\SteamLibrary\steamapps\common\Forza Motorsport:
$env:FM_INSTALL = "D:\...\Forza Motorsport"
```

## 3. Look before you touch

```powershell
python _tools\snapshot_cache.py              # copies the cache to _work\cachetest (game must be closed)
python _tools\inventory.py --check           # are the generated inventories current?
```

Open the `CARREIRA` inventory page (career tree), the `PISTAS` inventory page
(tracks), the `CARROS` inventory page (cars) and the `ESTADO` inventory page
(which kits are live in your cache).

## 4. Dry-run a kit on the copy

Use any kit you have built (step 5 builds one; the kit folder is `patches\<kit>\`).

```powershell
python _tools\plan_lint.py --plan patches\<kit>\plan.json
python _tools\cache_edit.py --dry-run --plan patches\<kit>\plan.json --cache-dir _work\cachetest
```

Expected: `lint profundo: ok` and a summary line. `ja corretos` means
"already in the desired state". Exit code 3 only means warnings, such as targets
that live in the install and are skipped.

## 5. Build a series from a spec (still on the copy)

```powershell
python _tools\build_series.py --spec specs\_TEMPLATE.json --cache-dir _work\cachetest --out _work\kit_demo
python _tools\cache_edit.py --dry-run --plan _work\kit_demo\plan.json --cache-dir _work\cachetest
python _tools\cache_edit.py --plan _work\kit_demo\plan.json --cache-dir _work\cachetest --verify --no-backup
```

Expected: `verificacao: OK`. You just added series 20005 to a copy of the
cache. The maintainers also check the generator against a private regression kit
(lab only; not part of this repository).

## 6. For real (game CLOSED)

Use your own spec in `specs/` (see `specs/README.md`), choose a kit name, and
follow [PIPELINE](PIPELINE.md) without `--cache-dir`. The apply makes a backup,
writes `patches/ledger.jsonl`, and refuses to run if the game is open or no
recent dry-run exists. To undo: `python _tools\rollback_cache.py`.

## If something goes wrong

| symptom | cause / fix |
|---|---|
| `nenhum --dry-run sem erros encontrado` | run the `--dry-run` for the same plan and cache first (valid for 30 min) |
| `jogo aberto (ForzaMotorsport.exe)` | close the game completely |
| `cmsoracle.exe not found` | build the oracles (step 2) |
| `WinError 5` while writing | the game or another process holds the files: close it, then `rollback_cache.py` |
| series crashes when clicked | missing `BCSeriesSelectableCars.xml` entry; `build_series` adds it. See [TROUBLESHOOTING](../TROUBLESHOOTING.md) |
