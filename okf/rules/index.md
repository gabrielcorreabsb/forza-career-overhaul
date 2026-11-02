# Golden rules

Violations of these caused real breakage. Source of truth: the linked docs.

- [Game closed before any CmsCache write](/rules/game_closed_before_write.md) — The game locks the blobs; writing while it is open fails with WinError 5 mid-apply and leaves the cache inconsistent. Close the game first.
- [Runtime source is the CmsCache, not the install](/rules/runtime_source_is_cmscache.md) — The game reads %LOCALAPPDATA%\Microsoft.ForzaMotorsport\CmsCache\; the install cms folder is only a seed and editing it has no effect in game.
- [Strategy S for blobs](/rules/strategy_s_for_blobs.md) — Keep the blob filename and update only Size + Checksum in the manifests; re-encrypt with the current payload as template.
- [Map snapshot to blob by Checksum, never by name or mtime](/rules/map_snapshots_by_checksum.md) — Two snapshots (old and live) hold same-shaped blobs; matching by name or mtime picked the wrong blob once.
- [cache_edit.py: --dry-run first, then apply with --verify](/rules/dry_run_then_verify.md) — Every apply backs up to _backup first. The code refuses to apply without a recent clean dry-run, with Forza running, or if plan_lint fails. Never work around these guards.
- [Never commit the CMS key, the Mod Tool or plain game files](/rules/never_commit_keys_or_game_text.md) — No AES key, no Forza Mod Tool or anything extracted from it, and no plain-text copies of game files in any contribution. Cite names, paths, counts and conclusions instead.
