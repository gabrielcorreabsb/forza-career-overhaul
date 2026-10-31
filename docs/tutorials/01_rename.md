# Tutorial 01 — Rename a text (`.str`) and ship a `bytes` kit

Goal: change one displayed string in the career and publish it as a kit whose
targets are `bytes` payloads. Time: ~20 min, most of it in the dry-run.

Canonical references (this page does not repeat them):
`docs\en\PIPELINE.md` → *Editing text (`.str`)*; `docs\en\CONCEPTS.md` →
glossary (`IDS_ key`, `payload`, `template`, `kit`, `Strategy S`);
`_tools\TOOLS.md` → `str_edit.py`, `fmlib/`.

## What you are changing

A `.str` is a string table asset. The game resolves a key by `ghash(name)`, so
**new keys of any length work** — that is why the old "same number of chars"
rule is gone (`docs\en\PIPELINE.md`). Only `LocStrings_pt-BR.str` receives the
project's new keys today; the other 19 languages do not (pending).

A career label is two pieces: the key stored in the BCS (`Name`,
`Description`) and the value stored in the table. Renaming a *vanilla* series
therefore means pointing `Name` at a new key — see step 3.

## 0. Prerequisites

- Oracles built (`cmsoracle` is the one that encrypts):
  `dotnet build _tools\cmsoracle\cmsoracle.csproj -c Release`.
- The game **closed** for anything that touches the real CmsCache.
  See `docs\en\GETTING_STARTED.md` §2–3.

## 1. Work on a copy of the cache

```powershell
python _tools\snapshot_cache.py            # -> _work\cachetest
```

## 2. Pull the plaintext table out of the cache

Payloads are resolved **by Checksum**, never by name or mtime
(`_tools\fmlib\cache.py`). Run from the repo root:

```python
# _work\dump_str.py
import os, sys
sys.path.insert(0, os.path.join(os.getcwd(), "_tools"))
from fmlib.cache import Cache
from fmlib.crypto import decrypt

cache = Cache(r"_work\cachetest")          # None = the live CmsCache
os.makedirs(r"_work\str", exist_ok=True)
for snap in cache.snapshots:
    raw = decrypt(cache.payload(snap, "LocStrings_pt-BR.str"))
    with open(r"_work\str\LocStrings_pt-BR.%s.str" % snap, "wb") as fh:
        fh.write(raw)
    print(snap, len(raw))
```

Inspect before editing:

```powershell
python _tools\str_edit.py info _work\str\LocStrings_pt-BR.20260923t185113xwyk.str
python _tools\str_edit.py roundtrip _work\str\LocStrings_pt-BR.20260923t185113xwyk.str
```

`roundtrip` must pass. If the table does not re-serialize byte-identically,
nothing downstream is safe (`_tools\str_edit.py` and
`fmlib.strs.add_keys` both refuse).

## 3. Pick the edit

**(a) Add a label (the normal case for a new series/cup).** Use the project
convention `IDS_<md5("MC44|<label>")>` — `fmlib.strs.key_for` generates it and
`add_keys` checks the `ghash` collision. New keys can be any length.

**(b) Rewrite an existing value in place.** `--set` replaces the value; every
reference to that key changes at once, so only do it when that is what you
want. Values that vanilla content uses are better left alone
(`docs\F3_TEMPLATE.md` §1.8).

```powershell
python _tools\str_edit.py edit _work\str\LocStrings_pt-BR.20260923t185113xwyk.str `
    _work\str\out.str --set "IDS_<key>=New text" --report _work\str\edit.txt
python _tools\str_edit.py roundtrip _work\str\out.str
```

**If the text belongs to a series or cup**, the BCS stores the key, not the
value: the plan needs a `json` target that sets `...ChampionshipSeriesData[N].Name`
in addition to the `bytes` target. Working example:
a kit's `plan.json` (e.g. `patches\<kit>\plan.json`) (two `json` targets + one `bytes` target per snapshot).

## 4. Build the kit

`fmlib.kit.Kit` writes `plan.json` + `<SHORT>.<snapshot>.enc` + the kit's notes file, and
encrypts each payload with the **current encrypted payload of the same entry as
template** (`_tools\fmlib\kit.py`) — the Strategy S guarantee that untouched
entries stay byte-identical.

```python
# _work\make_str_kit.py
import os, sys
sys.path.insert(0, os.path.join(os.getcwd(), "_tools"))
from fmlib.cache import Cache
from fmlib.crypto import decrypt
from fmlib.kit import Kit
from fmlib.strs import add_keys

PAIRS = [("IDS_<md5 of your label>", "New text")]   # key_for("your label")

cache = Cache(r"_work\cachetest")
kit = Kit("mc99_texto", cache, out_dir=r"_work\kit_texto")
for snap in cache.snapshots:
    raw = decrypt(cache.payload(snap, "LocStrings_pt-BR.str"))
    # in-place variant: raw = open(r"_work\str\out.%s.str" % snap, "rb").read()
    kit.add(snap, "LocStrings_pt-BR.str", add_keys(raw, PAIRS))
print(kit.write_plan("renomeia um texto pt-BR"))
```

`Kit.add` asserts the oracle round-trip, so a wrong template fails loudly here
instead of in game.

## 5. Lint, dry-run, apply (copy first)

```powershell
python _tools\plan_lint.py --plan _work\kit_texto\plan.json --cache-dir _work\cachetest
python _tools\cache_edit.py --dry-run --plan _work\kit_texto\plan.json --cache-dir _work\cachetest
python _tools\cache_edit.py --plan _work\kit_texto\plan.json --cache-dir _work\cachetest --verify --no-backup
```

Expected: lint `ok`, dry-run summary with one changed target per snapshot,
`verificacao: OK`. Exit code 3 means warnings only.

What a real run prints: `plan_lint` says
`_work\kit_texto\plan.json: 0 erros, 0 avisos`; the dry-run ends with
`lint profundo: ok (multiplayer intocado, Strategy S, Size/Checksum)` and
`alvos avaliados: 2  (alterados: 2, ja corretos: 0, ignorados: 0)` (one target
per snapshot); the apply ends with `verificacao: OK` and `blobs gravados: 2`.
`ja corretos` would mean the entry is already in the desired state.

## 6. For real

Game **closed**, drop `--cache-dir` and `--no-backup` (backup is ON by default;
every apply also writes `patches\ledger.jsonl`):

```powershell
python _tools\plan_lint.py --plan patches\<kit>\plan.json
python _tools\cache_edit.py --dry-run --plan patches\<kit>\plan.json
python _tools\cache_edit.py --plan patches\<kit>\plan.json --verify
python _tools\cache_verify.py
python _tools\inventory.py
```

`cache_verify.py` must end with 0 errors. `patches\ledger.jsonl` records what
happened (check history: `git log -- patches\ledger.jsonl`).

Kits are **snapshot-bound** — a new server snapshot means regenerating
(`docs\en\PIPELINE.md`, *Publishing a kit*).

## 7. Verify in game and roll back

Launch, open the career screen that shows the text, confirm the new string.
If something is wrong: `python _tools\rollback_cache.py` restores the newest
backup (game closed).

After editing the codec itself, run `python _tools\test_str_edit.py`.
