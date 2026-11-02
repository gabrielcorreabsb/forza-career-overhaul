# Tools (`_tools/`)

Scripts of the pipeline, by role. Source: _tools/TOOLS.md.

- [cache_edit.py](/tools/cache_edit_py.md) — applies a plan.json to the game cache; guarded: lint, game closed, recent --dry-run; backup and ledger
- [install_edit.py](/tools/install_edit_py.md) — swaps one CMS entry inside the install zip (groups outside the CmsCache, e.g. AIField) and the manifests; --dry-run, backup, --restore
- [plan_lint.py](/tools/plan_lint_py.md) — plan linter (static, multiplayer untouched, Strategy S, retired ids)
- [cache_verify.py](/tools/cache_verify_py.md) — full cache consistency check (Size/Checksum of every entry; must end with 0 errors)
- [rollback_cache.py](/tools/rollback_cache_py.md) — restores the newest backup
- [snapshot_cache.py](/tools/snapshot_cache_py.md) — copies the cache to _work\cachetest for tests
- [build_series.py](/tools/build_series_py.md) — new series from a spec in specs/
- [build_aifield.py](/tools/build_aifield_py.md) — AI grid payload from a definition in specs/aifield/ (pool or list), built on a vanilla template of your install; hand it to install_edit.py
- [fmlib/](/tools/fmlib.md) — shared library: cache, crypto, bcs, carsxml, overrides, strs, cars, ids, kit, aifield
- [str_edit.py](/tools/str_edit_py.md) — .str codec (byte-identical round-trip; IDS_ keys of any length)
- [cms_crypto.py](/tools/cms_crypto_py.md) — Python CMS codec; the key comes from FM_CMS_KEY or a local cms_key.hex (never versioned; see docs/project/THIRD_PARTY.md)
- [cmsoracle/](/tools/cmsoracle.md) — .NET oracles (dotnet build <x>.csproj -c Release); the cache oracle needs third-party files you supply
- [cacheoracle/](/tools/cacheoracle.md) — .NET oracles (dotnet build <x>.csproj -c Release); the cache oracle needs third-party files you supply
- [inventory.py](/tools/inventory_py.md) — generates the inventories of your game; --check says whether they are stale
- [audit_career.py](/tools/audit_career_py.md) — read-only audit of your game's career and Featured data; writes docs/audit/ and docs/data/; --check says whether they are stale
- [cms_state.py](/tools/cms_state_py.md) — install vs cache state snapshots
- [aifield_survey.py](/tools/aifield_survey_py.md) — read-only survey of the vanilla AIFields and the AI_<car>_<pi> ladders (--car <id> shows one ladder)
- [test_aifield.py](/tools/test_aifield_py.md) — fmlib.aifield and build_aifield reproduce vanilla AIField documents byte for byte (needs only your game and the key)
- [test_str_edit.py](/tools/test_str_edit_py.md) — self-test of str_edit.py
- [docs_check.py](/tools/docs_check_py.md) — docs consistency: cited paths exist, language pairs, index complete
