# ADR-001 — Strategy S: rewrite blobs in place, update `Size`/`Checksum` only

- **Status:** accepted (practice already validated in-game; recorded 2026-10-30)
- **Scope:** how `cache_edit.py` and every generator write to the CmsCache

## Context

In the CmsCache a blob file is named after the SHA-256 of its content
(`<bucket>\<SHA256HEX>`, see [CONCEPTS](../en/CONCEPTS.md) §1). That name is
therefore a *content hash*, not a stable identifier: any edit to an entry inside
the blob changes the blob's bytes and breaks the `name == sha256(content)`
relation.

Three ways out were considered:

1. write the new blob under its correct hash, update the `cache-manifest.json`
   entry and the `ContentGroups`;
2. keep the old name and rewrite the bytes;
3. write a whole new blob and a second snapshot entry.

The `Id` (int64) in the manifest is opaque — it is not a hash of `Path`
(fnv/murmur/crc/md5/sha were tested) — so it cannot be recomputed and must be
preserved. Renaming a blob therefore means touching the encrypted
`cache-manifest.json`, the per-snapshot `prod\<snapshot>` manifest and the
`ContentGroups` lists of two snapshots at once, on every apply.

## Decision

**Strategy S**: keep the blob filename exactly as it is, rewrite the blob in
place, and update only `Size` and `Checksum` of the changed entries in
`prod\<snapshot>`, then re-encrypt `cache-manifest.json` with the original file
as template. `Path`, `Id` and `ContentGroups` are never modified.

Each changed logical file is re-encrypted with its **current encrypted payload
as template** (see [ADR-005](ADR-005_cipher_template.md)), so the gzip settings
and every untouched entry inside the same blob stay byte-identical.

## Evidence

- The game accepts a blob whose name no longer matches its content: every apply
  from the proof of concept onwards used Strategy S and loaded in-game. See the
  [PIPELINE](../en/PIPELINE.md) table entry for `blob`.
- Keeping `Path`/`Id` is safe because `Id` is opaque; only `Size`/`Checksum`
  describe the payload (`Size` = encrypted payload length, `Checksum` = base64
  SHA-256 of the encrypted payload).
- `cache_verify.py` walks every entry after each apply and reports `Size`,
  `Checksum`, blob↔manifest consistency and per-snapshot divergences; every
  accepted apply ended with 0 errors ([PIPELINE](../en/PIPELINE.md)
  "Post-write verification").
- `patches/ledger.jsonl` records each real apply, which is what made the
  "same-shape blobs, two snapshots" problem visible in the first place.

## Consequences

- **Cheap and reversible.** One entry → one blob rewrite; the previous cache is
  in `_backup\cache_<timestamp>` and `rollback_cache.py` restores it.
- **Blob names stop being content hashes.** Never validate a blob by
  `sha256(name)`; always compare the entry's `Checksum` from the manifest
  ([ADR-002](ADR-002_checksum_mapping.md)). External tools that assume
  content-addressing will misread the cache.
- **Plans must target both snapshots.** The same logical file exists once per
  snapshot with different bytes, so a kit carries one payload per snapshot and
  updates two `prod\` manifests.
- **Blast radius is bounded but not zero.** A partial write leaves blob and
  manifest out of sync; the write is transactional (backup → blobs → `prod` →
  cache-manifest), and an interrupted run is treated as "unknown state" and
  repaired from the backup.
- **Kits are snapshot-bound.** When the server ships a new snapshot the stored
  `Size`/`Checksum` no longer match and the kit must be regenerated.
