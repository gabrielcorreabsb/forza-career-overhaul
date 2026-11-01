# ADR-005 — Encrypt with the current payload as template (oracle, not Python)

- **Status:** accepted (practice already validated in-game; recorded 2026-10-30)
- **Scope:** how a changed logical file, and `cache-manifest.json`, are
  re-encrypted

## Context

A CMS payload is `AES-128-CBC(IV = 0×16)` over gzip, padded with zeros to a
multiple of 16. The gzip stream inside was produced by .NET
(`CompressionLevel.SmallestSize`), not by Python: `gzip`/`zlib` from Python
produces *smaller* payloads for the same plaintext (e.g. 136,192 B vs
147,120 B for `RacersCupMetaDataV4.json`). Python's output is *compatible* —
the game can read it — but it is not byte-identical.

Byte-identity matters here: `Size` and `Checksum` of every entry live in
`prod\<snapshot>`, and the pipeline's whole value proposition is a minimal diff
(Strategy S, [ADR-001](ADR-001_strategy_s.md)). Re-encrypting with a different
gzip implementation rewrites more bytes than necessary and multiplies the
places where the entry could drift.

Re-encryption alone is also not deterministic in the way needed: the cipher
takes an input and produces the same output only if it recompresses the same
way. A tool that just takes `<plaintext>` cannot recover the original
compressor's choices.

## Decision

Always re-encrypt a changed entry with the **oracle**, passing the entry's
**current encrypted payload as template**:

```powershell
_tools\cmsoracle\cmsoracle.exe enc <plain> <current_encrypted_payload> <out>
_tools\cacheoracle\cacheoracle.exe enc <plain> <current_cache_manifest> <out>
```

The template supplies the gzipator settings, so the output is the plaintext
edition packed exactly the way the original was and every untouched entry stays
byte-identical. `cache-manifest.json` follows the same rule (it is an asset
container with chunk 512 / slot 528).

The Python codec `_tools\cms_crypto.py` exists as a **fallback only** for
environments without the oracles; it is accepted functionally but is not
byte-identical, so its results must be treated as a bigger diff.

## Evidence

- The .NET oracle reproduces the original bytes exactly ("round-trip
  byte-idêntico"), while the Python codec is compatible but smaller.
- Every accepted apply used the current payload as template and ended with
  `cache_verify.py` at 0 errors, with the expected `Size`/`Checksum` deltas and
  nothing else moving.
- The PIPELINE notes record the rule as a verified fact: the template preserves the
  gzipator settings "so untouched entries stay byte-identical".
- The lab's `build_series` regression test replays kit mc55 byte for byte, which is
  only possible if encryption and packing are deterministic given the template.

## Consequences

- **Build the oracles first.** `dotnet build` of `_tools\cmsoracle\` and
  `_tools\cacheoracle\` is a prerequisite, not an optimization; both rely on
  the Forza Mod Tool material you keep locally (see `docs/project/THIRD_PARTY.md`).
- **Templates are per snapshot.** Each snapshot has its own current payload
  (`BuildersCupScheduleDataV4.json` is `Size=60736` live vs `46864` old), so a
  kit carries one `.enc` payload per snapshot and never reuses the other
  snapshot's bytes as template.
- **Never template from a stale copy.** The template must be the payload that
  is in the cache right now; regenerating after a server update means the
  template changed too.
- **Python stays fallback.** If `cms_crypto.py` is used, expect a larger
  diff and re-run `cache_verify.py`; do not mix outputs from both codecs in one
  plan.
