# Getting started

> 🌐 [Português](../pt-br/GETTING_STARTED.md) · **English**

Goal: in about 15 minutes, see the whole pipeline work on a **copy** of the
game cache, without touching the game. Then read [CONCEPTS](CONCEPTS.md) and
[PIPELINE](PIPELINE.md).

Every step below says what you should see. Quotes are the real output of a run
of this repository's tools; `<...>` marks the values that depend on your machine.

## 1. Requirements

- Windows, Forza Motorsport (2023) on Steam, launched at least once (this
  creates the CmsCache under `%LOCALAPPDATA%\Microsoft.ForzaMotorsport\`).
- Python 3.10+.
- The **.NET 10 SDK**: both oracle projects target `net10.0`, so an older SDK
  fails at build time. `dotnet --version` must print `10.`.
- The [Forza Mod Tool](https://github.com/HTTPJXRDN/Forza-Mod-Tool) v1.3.0 and
  the CMS key. They are **not** in this repository: you download the tool
  yourself and put it, with the key, in the git-ignored paths named in
  [THIRD_PARTY](../project/THIRD_PARTY.md) (that page also says why nothing of it is
  distributed here).
- A PowerShell terminal at the repo root.

## 2. One-time setup

```powershell
dotnet build _tools\cmsoracle\cmsoracle.csproj -c Release
dotnet build _tools\cacheoracle\cacheoracle.csproj -c Release
git config core.hooksPath .githooks          # pre-commit guards
```

What you should see: two `Build succeeded` blocks ending with
`... -> _tools\cmsoracle\bin\Release\net10.0\cmsoracle.exe` and the same for
`cacheoracle.exe`. If the build stops on a missing reference, the third-party
files of [THIRD_PARTY](../project/THIRD_PARTY.md) are not in place yet — the cache
oracle cannot be built without them.

**Where the game is.** The tools find the game install at
`F:\SteamLibrary\steamapps\common\Forza Motorsport` by default (the `FM_INSTALL`
environment variable, read by `_tools\install_edit.py`). If yours lives
elsewhere, set it for the session:

```powershell
$env:FM_INSTALL = "D:\Steam\steamapps\common\Forza Motorsport"
# or persist it for new terminals:
[Environment]::SetEnvironmentVariable("FM_INSTALL", "D:\Steam\steamapps\common\Forza Motorsport", "User")
```

The CmsCache path has no variable: it is always
`%LOCALAPPDATA%\Microsoft.ForzaMotorsport\CmsCache\`.

## 3. Copy the cache and look at it

```powershell
python _tools\snapshot_cache.py              # copies the cache to _work\cachetest
python _tools\inventory.py --check           # are the generated inventories current?
```

What you should see:

- the copy prints `copia: <CmsCache> -> <repo>\_work\cachetest (<N> B)`. It
  refuses to copy while the game runs, with
  `ERRO: jogo aberto (forza_steamworks_release_final.exe); feche antes de copiar`
  — a copy taken under a running game can be inconsistent.
- the inventory check prints `live snapshot: <snapshot> (<N> entries resolved)`
  and then either `inventory up to date` or a `STALE` list. Stale only means
  your cache moved on (you applied a kit, or the server shipped a snapshot):
  run `python _tools\inventory.py` to regenerate the generated data and the
  inventory pages.

Then open the `CARREIRA` inventory page (career tree), `PISTAS` (tracks),
`CARROS` (cars) and `ESTADO` (which kits are live in your cache).

**When does the game have to be closed?** Only for a write. Copying the cache
(above) and every `--dry-run` are read-only and work with the game open; the
first real write has to happen with it closed (step 6).

## 4. Build a demo series on the copy

`specs\_TEMPLATE.json` is a working spec: copy it and edit the ids. It adds
series **20005** and two events.

```powershell
python _tools\build_series.py --spec specs\_TEMPLATE.json --cache-dir _work\cachetest --out _work\kit_demo
```

What you should see: one block per snapshot (`series <id> -> ladder <id> |
events [...]`, `XML entry SeriesId=...`, `override ... -> <event>`,
`.str + IDS_...`), then

```
plan: <repo>\_work\kit_demo\plan.json (8 targets) | 1 warning(s)
```

Exit code **3** is normal: the warning says the showroom acceptlist contains
always-denied cars (the game skips them). Exit code 1 with
`ERROR: series id 20005 already in use` means that id is taken in your cache —
change `series.id` (≥ 20000) and `events[].id` (65897900–65899999) to free ones;
the id registry (`ids.json`) lists what is taken.

## 5. Lint, dry-run, then apply on the copy

```powershell
python _tools\plan_lint.py --plan _work\kit_demo\plan.json
python _tools\cache_edit.py --dry-run --plan _work\kit_demo\plan.json --cache-dir _work\cachetest
python _tools\cache_edit.py --plan _work\kit_demo\plan.json --cache-dir _work\cachetest --verify --no-backup
```

What you should see, in order:

- `_work\kit_demo\plan.json: 0 erros, 0 avisos` (exit 0; exit 3 = warnings only,
  exit 1 = the plan is rejected and the apply will refuse it too).
- the dry-run ends with `lint profundo: ok (multiplayer intocado, Strategy S,
  Size/Checksum)`, a per-target list and a `=== RESUMO ===` with
  `alvos avaliados: N (alterados: X, ja corretos: Y, ignorados: Z)`.
  `ja corretos` means "already in the desired state".
- the apply ends with `=== VERIFICACAO ===` showing `0 divergentes` per snapshot
  and `verificacao: OK`, then `blobs gravados: N`.

A real dry-run on a copy looks like this (trimmed):

```
snapshot 20260923t185113xwyk: 10434 arquivos, 8 grupos, 4 grupos no cache
  [+] LocStrings_pt-BR.str -> blob C0A94D0949D8 (...)
      payload 79920 -> 79968 B | plaintext 272894 -> 273026 B
lint profundo: ok (multiplayer intocado, Strategy S, Size/Checksum)
DRY-RUN: nenhuma escrita realizada.
marcador de dry-run gravado (valido por 30 min)
=== RESUMO ===
alvos avaliados: 2  (alterados: 2, ja corretos: 0, ignorados: 0)
  20260923t185113xwyk  LocStrings_pt-BR.str  blob=C0A94D0949D8  payload 79920->79968 B  [bytes]
blobs a gravar: 2 | snapshots a gravar: 2
```

and applying the same plan on the copy:

```
backup: desativado (--no-backup)
blobs gravados: 2
=== VERIFICACAO ===
  prod/20260923t185113xwyk: 10434 arquivos, 8 grupos, 9153 fora do cache (base), 0 divergentes
  verificacao: OK
```

Note the two strings that mean different layers: `lint profundo: ok` comes from
`cache_edit.py` (deep lint); `0 erros, 0 avisos` comes from `plan_lint.py`.
`9153 fora do cache (base)` are the entries the cache does not hold (the install
supplies them); it is not an error.

## 6. For real (game CLOSED)

Use the kit you generated (see [PIPELINE](PIPELINE.md)) and drop
`--cache-dir` and `--no-backup`:

```powershell
python _tools\cache_edit.py --dry-run --plan patches\<kit>\plan.json
python _tools\cache_edit.py --plan patches\<kit>\plan.json --verify
```

The apply backs the whole cache up to `_backup\cache_<timestamp>` and appends to
`patches\ledger.jsonl`; it refuses while a `forza*` process runs or when the
last clean dry-run for that exact plan is older than 30 minutes. To undo:
`python _tools\rollback_cache.py`.

## If something goes wrong

| symptom | cause / fix |
|---|---|
| `nenhum --dry-run sem erros encontrado` | run the `--dry-run` for the same plan and cache first (valid for 30 min) |
| `jogo aberto (ForzaMotorsport.exe)` | close the game completely (writes only) |
| `ERRO: jogo aberto (...)` from `snapshot_cache.py` | same: the copy also refuses while the game runs |
| `cmsoracle.exe not found` | build the oracles (step 2) |
| `ERROR: series id 20005 already in use` | pick free ids (id registry: `ids.json`) |
| `WinError 5` while writing | the game or another process holds the files: close it, then `rollback_cache.py` |
| `verificacao: FALHOU` | do not play: restore with `rollback_cache.py` and open an issue with the plan |
| series crashes when clicked | missing `BCSeriesSelectableCars.xml` entry; `build_series` adds it. See [TROUBLESHOOTING](../guides/TROUBLESHOOTING.md) |
