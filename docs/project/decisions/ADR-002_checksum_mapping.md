# ADR-002 — Resolve snapshot → blob by `Checksum`, never by name or mtime

- **Status:** accepted (practice already validated in-game; recorded 2026-10-30)
- **Scope:** how `cache_edit.py` and every generator locate the blob holding a
  logical file

## Context

A CmsCache holds **two snapshots** at the same time — `20251124t234605pkod`
(old) and `20260923t185113xwyk` (live). Both contain the *same logical files*
(`BuildersCupScheduleDataV4.json`, `LocStrings_pt-BR.str`, …), with different
content, and both are described by a plaintext `prod\<snapshot>` manifest with
`Files[{Id,Path,Size,Checksum}]` plus `ContentGroups`.

The blobs have the same shape across snapshots: same buckets, same number of
groups, and in-place rewrites (Strategy S) mean a blob name no longer says
anything about the bytes inside. Picking a blob by filename or by modification
time is therefore a guess with a 50% chance of being the wrong snapshot.

## Decision

The snapshot→blob mapping is done **by the entry's `Checksum`**: read the
target `prod\<snapshot>` manifest, find the entry (`Path` + `Size` +
`Checksum`), and match that checksum against the payload bytes actually stored
in the candidate blobs. Filesystem timestamps and blob filenames are never used
to select a target.

Corollaries:

- the same logical file is a **separate target per snapshot** (different
  payload, different checksum);
- a mismatch between expected and found checksum aborts the operation instead
  of patching the wrong blob;
- generators start from the **current cache state**, re-reading manifests on
  every run.

## Evidence

- The first version of the ModCarrera 1 generator matched by name and wrote the
  **old** snapshot's blob, so the edit landed on the snapshot the game does not
  read. The fix was the checksum lookup described in
  [PIPELINE](../../en/PIPELINE.md) ("`cache_edit.py` resolves snapshot→blob by the
  entries' Checksum in the manifest, never by name or mtime").
- The PIPELINE golden rules carry the same rule, because re-learning it
  cost a full diagnostic cycle.
- The lab diagnostics show the two snapshots differing only in values, exactly the
  shape that fools name-based matching: `BuildersCupScheduleDataV4.json` is
  `Size=60736` on the live snapshot and `46864` on the old one; the `.str` is
  `79696` vs `73472`.
- `cache_verify.py` reports divergences **per snapshot**; after a correct apply
  every snapshot's manifest matches its own blob.

## Consequences

- **Two-target plans are mandatory.** Every BCS/`.str`/XML edit appears twice
  in `plan.json` (one payload per snapshot). Forgetting one snapshot leaves the
  other cached version untouched.
- **No timestamp shortcuts.** mtime is only used as a forensic hint during a
  diagnosis (e.g. deciding whether the server downloaded something after an
  apply), never for selection.
- **`Checksum` is the real contract.** All validation — `cache_verify.py`,
  `plan_lint.py`, the apply guard — is phrased in terms of `Size`/`Checksum`,
  which is also what makes Strategy S
  ([ADR-001](ADR-001_strategy_s.md)) workable.
- **Regeneration is cheap and expected.** Because resolution is state-based,
  the honest reaction to "cache changed" is re-running the generator against
  the current cache, not editing a stored kit.
