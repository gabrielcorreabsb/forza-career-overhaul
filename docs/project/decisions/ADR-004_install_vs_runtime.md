# ADR-004 — The runtime source is the CmsCache, not the install

- **Status:** accepted (practice already validated in-game; recorded 2026-10-30)
- **Scope:** which copy of the CMS the pipeline is allowed to edit

## Context

The game ships a CMS in the install (`media\pcfamily\cms\`: a plaintext manifest,
8 content-group ZIPs and the encrypted `cache-manifest.json`). At runtime it
also keeps a CMS in the user profile:
`%LOCALAPPDATA%\Microsoft.ForzaMotorsport\CmsCache\`. Both use the same manifest
schema (`Version`, `CmsInstance`, `Files[{Id,Path,Size,Checksum}]`,
`ContentGroups`), both hold 8 groups with the same GUIDs, and they overlap only
partially — the cache manifest lists 10,434 logical files, of which 9,153 are
not present in the cache at all ("base" content that is read from the install).

That leaves the question every modder asks first: edit the install, or the
cache? The install feels canonical and is closer to the modding guides, but the
Steam copy is only the **seed** embedded in the build.

## Decision

The **CmsCache is the runtime source and the only edit target** for content that
exists there. The install is left untouched; it serves as fallback for content
the cache never materialized. Concretely:

- write to `%LOCALAPPDATA%\Microsoft.ForzaMotorsport\CmsCache\`;
- do not patch `media\pcfamily\cms\` to change anything the player sees;
- when a target's content group is not in the cache, `cache_edit.py` **cannot**
  change it and skips it (it reports "group not in the cache"). That case has
  its own tool, `install_edit.py` (see the addendum below); do not hand-edit the
  install.

## Evidence

- Direct experiment: a patch applied to the install changed nothing in the UI,
  while the series names the player saw exist **only** in
  `LocStrings_pt-BR.str` of the cache (blob `C0A94D09…`) and have 0 occurrences
  in the install or in `media\base\stringtables\`.
- Cross-check of the two manifests: 2,533 of 2,562 overlapping entries agree on
  `Size`+`Checksum`, and the 29 divergences are newer cache versions not yet
  propagated — same section of the research log.
- Every in-game validation from the proof of concept onwards (career reorder,
  unlock, new series 20003, trackday 20004) was applied to the cache only.
- The AI-field file shows the other side of the same coin: its content group is
  never materialized in the cache, so the game reads it from the install zip and
  `cache_edit.py` cannot reach it (`AI_GRIDS.md`).

## Consequences

- **Fast iteration, small blast radius.** Applies touch ~13 MB of cache
  (`_backup\cache_<timestamp>`), never gigabytes of install data, and Steam file
  verification never flags a modified game.
- **Two classes of targets exist.** Cache-resident files (BCS, `.str`, XML) are
  patchable by `cache_edit.py`; install-only groups (the AI field XML) need
  `install_edit.py`. Always check whether the group is in the cache before
  planning a change.
- **Cache can be missing recent content.** A server update adds entries to the
  cache; a kit built against the previous snapshot no longer matches
  ([ADR-002](ADR-002_checksum_mapping.md)).
- **Diagnosis starts with "which copy?".** Any "the mod does nothing" report is
  first answered by checking that the cache manifest holds the edited payload —
  `cache_verify.py` and the per-entry `Checksum` do that.

## Addendum 2026-10-30 — install-only groups

The "install-only" exception is now handled, and tested in game (mc58: the AI
grid changed). `_tools/install_edit.py` rewrites one entry of the install zip
and keeps the whole checksum chain consistent in one run: the zip entry, the
install manifest `faa126fd…` (logical entry + package), both
`prod\<snapshot>` files and the re-encrypted `cache-manifest.json`. It refuses
to run with the game open, needs a recent `--dry-run`, backs up to
`_backup\install_<time>` and undoes with `--restore`.

This does not reopen the decision: the CmsCache stays the edit target for
everything that lives there. Two practical notes: the install denies DELETE to
the user (so the tool rewrites files in place instead of renaming over them),
and Steam "verify files" or a new snapshot reverts the change — re-run the
tool. See `AI_GRIDS.md` and `docs/en/PIPELINE.md`.
