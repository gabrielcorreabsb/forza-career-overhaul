# Third-party material (not distributed here)

This project reuses the crypto work of another open project. Its files are
**not in this repository** and the repository's license does not cover them.
You obtain them yourself, from the original source, and keep them in
git-ignored paths.

## Forza Mod Tool (recommended decrypt program)

- Project: [HTTPJXRDN/Forza-Mod-Tool](https://github.com/HTTPJXRDN/Forza-Mod-Tool),
  release **v1.3.0** (the version this project was built and tested against).
- Why: it is the program that knows how the game's CMS content is encrypted
  (AES-128-CBC over gzip) and how the cache container is laid out. We document
  and reimplement the formats; we rely on it for the key and the reference
  implementation. If you only want to look at the data, use the tool itself.
- License: the upstream repository declares **no license**, so by default all
  rights are reserved by its author. That is why none of its binaries, sources
  or resources are copied here. Please respect the author's terms.

## ForzaTech Studio (optional, reference and viewer)

- Project: [D3FEKT/ForzaTechStudio](https://github.com/D3FEKT/ForzaTechStudio),
  MIT license. It covers assets such as `.swatchbin`, `.str` and `.fxb`. It does
  not edit career data or decrypt CMS content.
- Its docs are a starting point for formats; what we confirmed for this game is
  in [SWATCHBIN](../reference/SWATCHBIN.md). We state those facts in our own
  words and copy none of its code.
- Its repository also carries native DLLs that the MIT license does not cover.
  `xcompress64.dll` is Microsoft's and not redistributable, and the origin of
  `xg.dll` and `granny2_x64.dll` is unchecked. Keep them local and never commit
  them. The optional method 21 reader loads `xcompress64.dll` from the
  `XCOMPRESS_DLL` variable or from a local copy under `_external/`.

## What you need locally

Local layout (every path below is git-ignored):

```text
Forza-Mod-Tool-ForzaModToolV1.3.0/         # upstream release, unzipped (repo root)
  lib/FH6LocalCrypto.Runtime.dll           # referenced by cmsoracle
_tools/fmtool/cms_key.hex                  # the CMS AES-128 key, 32 hex chars
```

| what | used by |
|---|---|
| Forza Mod Tool v1.3.0, unzipped as above | `cmsoracle` (references its runtime DLL) |
| the CMS AES-128 key: the `cms_key.hex` file above, **or** the `FM_CMS_KEY` environment variable | `_tools/cms_crypto.py` — the Python codec every decrypting tool imports |
| the .NET SDK version named in the `.csproj` files | building the two oracles |

The key is read at import time by `cms_crypto.py`; without it the tools stop
with a message pointing here. It is stored in the Forza Mod Tool's runtime
(`FH6LocalCrypto.Runtime.dll`); how to read it from there is up to you.

## The cache oracle

`_tools/cacheoracle/` re-encrypts `cache-manifest.json`. Its build needs
third-party classes and tables extracted from the Forza Mod Tool
(the `TOOL` sources and `res` JSON tables inside the cacheoracle project). They are
git-ignored and **not distributed**, so a fresh clone cannot build it until you
provide those files yourself. The maintainers keep a local copy; the extraction
steps are not published.

Without the cache oracle you cannot run `cache_edit.py` (not even `--dry-run`)
or `install_edit.py`. The Python tools that only decrypt CMS entries
(`fmlib`, `aifield_survey.py`, `test_aifield.py`, `build_aifield.py`, the kit generators) work with
just the key and a local game install.

## Paths that must never be committed

`.gitignore` blocks them. If one shows up staged, stop:

```text
_external/
Forza-Mod-Tool*/            _tools/fmtool/        _tools/decomp/
_tools/cacheoracle/TOOL/    _tools/cacheoracle/res/
cms_key.hex  *.key  .env  *.dll
patches/**/*pkod  patches/**/*xwyk   # plain-text per-snapshot copies of game files
```
