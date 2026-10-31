# ADR-003 — Stop mirroring the install's `mediapc/`

- **Status:** accepted 2026-10-30 (supersedes the earlier mirror step)
- **Scope:** documented workflow; no script does this anymore

## Context

Forza Horizon 6 loads loose modified files from `MediaPC\stripped`, so the
habit from FH modding is to mirror the modified CMS into the install's
`mediapc\` tree. The first version of this project did exactly that after every
apply: it copied the CmsCache plus the install files into
`F:\SteamLibrary\...\Forza Motorsport\mediapc\` in two candidate layouts
(loose at the root, or `mediapc\pcfamily\cms\`).

FM8 (2023) has no override folder at all. The binary contains **zero** hits for
`MediaPC` (ASCII and UTF-16); `PC_x64|PC_UWP|PC_Steam` is only a platform list.
The Forza Mod Tool's advanced guide states the same for Motorsport: "FM has no
override folder". Changing content therefore only works by in-place
replacement — and the runtime copy is the CmsCache, not the install
([ADR-004](ADR-004_install_vs_runtime.md)).

## Decision

**Do not mirror `mediapc/`.** It was discontinued on 2026-10-30: the game does
not read it. The CmsCache is the only write target, and the mirror step is
removed from the documented workflow (PIPELINE golden rule 4).

## Evidence

- Exe string scan: `MediaPC` = 0 hits, both ASCII and UTF-16; no "mods",
  "patch" or "overrides" folder is referenced by the game.
- Forza Mod Tool documentation, quoted in the same section: FH6 uses
  `MediaPC\stripped`, Motorsport has no override folder.
- Runtime behaviour: the text/order changes were already visible with the
  CmsCache alone, before any mirror existed; the mirrored tree had no in-game
  effect.
- `PIPELINE.md` and the research log record the discontinuation on
  2026-10-30; the old mirror script is gone from `_tools/`.

## Consequences

- **One write target.** Applies are shorter and touch only `_backup\` plus the
  cache; there is no second copy to keep in sync and no risk of the player
  reasoning about a tree that does nothing.
- **The install stays pristine.** Nothing in `media\pcfamily\cms\` is modified
  by the pipeline, which also keeps Steam file verification clean.
- **Docs must not resurrect the step.** Historic logs still mention the mirror
  script; treat those passages as history (the research log is marked
  historical), not as instructions.
- **If a future title does read `mediapc/`,** this decision has to be retaken
  explicitly — it is a fact about FM8's loader, not a preference.
