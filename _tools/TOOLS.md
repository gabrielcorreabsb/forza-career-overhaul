<!-- docs_check: historical -->
# Tools (`_tools/`)

Role of each script. Everything here runs against **your** game install and cache.

## 1. Pipeline (apply)

| script | what it does |
|---|---|
| `cache_edit.py` | applies a `plan.json` to the game cache (career data, texts, and the AIField roster documents, which the game reads from the cache); guarded: lint, game closed, recent `--dry-run`; backup and ledger |
| `install_edit.py` | swaps one CMS entry inside the **install** zip and the manifests; the fallback for a group a cache does not hold (AIField on a cache older than the 08/11/2026 snapshot); `--dry-run`, backup, `--restore` |
| `plan_lint.py` | plan linter (static, multiplayer untouched, Strategy S, retired ids) |
| `cache_verify.py` | full cache consistency check (Size/Checksum of every entry; must end with 0 errors) |
| `rollback_cache.py` | restores the newest backup |
| `snapshot_cache.py` | copies the cache to `_work\cachetest` for tests |

## 2. Kit generation

| script | what it does |
|---|---|
| `build_series.py` | new series from a spec in `specs/` |
| `build_aifield.py` | AI grid payload from a definition in `specs/aifield/` (pool or list), built on a vanilla template of your game; `--cache-plan` also writes the plan for `cache_edit.py` |
| `fmlib/` | shared library: `cache`, `crypto`, `bcs`, `carsxml`, `overrides`, `strs`, `cars`, `ids`, `kit`, `aifield` |
| `str_edit.py` | `.str` codec (byte-identical round-trip; `IDS_` keys of any length) |
| `cms_crypto.py` | Python CMS codec; the key comes from `FM_CMS_KEY` or a local `cms_key.hex` (never versioned; see `docs/project/THIRD_PARTY.md`) |
| `cmsoracle/`, `cacheoracle/` | .NET oracles (`dotnet build <x>.csproj -c Release`); the cache oracle needs third-party files you supply |

## 3. Inventory and checks

| script | what it does |
|---|---|
| `inventory.py` | generates the inventories of your game; `--check` says whether they are stale |
| `audit_career.py` | read-only audit of your game's career and Featured data; writes `docs/audit/*` and `docs/data/*`; `--check` says whether they are stale |
| `cms_state.py` | install vs cache state snapshots |
| `aifield_survey.py` | read-only survey of the vanilla AIFields and the `AI_<car>_<pi>` ladders (`--car <id>` shows one ladder) |

## 4. Tests and docs

| script | what it does |
|---|---|
| `test_aifield.py` | `fmlib.aifield` and `build_aifield` reproduce vanilla AIField documents byte for byte (needs only your game and the key) |
| `test_str_edit.py` | self-test of `str_edit.py` |
| `docs_check.py` | docs consistency: cited paths exist, language pairs, index complete |
