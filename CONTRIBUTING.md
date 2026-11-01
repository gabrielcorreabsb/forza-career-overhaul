<!-- docs_check: historical -->
# Contributing

Thanks for helping. Short version:

- **Scope:** tools in `_tools/`, specs in `specs/`, docs in `docs/`. Bug reports with
  the exact command, the output and your game/tool versions are the most useful thing.
- **This repo is a publication.** The source of truth is the maintainer's private lab; a
  pull request is reviewed here and ported there, then comes back on the next sync. Keep
  PRs small and focused (one idea each) so porting is easy.
- **Never include** the CMS key, anything from the Forza Mod Tool, game files or game
  text, encrypted/decrypted payloads, or inventories generated from your game. PRs with
  such content are closed and the content is not merged. See [THIRD_PARTY](docs/project/THIRD_PARTY.md).
- **Safety rules stay on:** do not weaken `--dry-run`/`--verify` requirements, the
  game-closed check or the plan linter to make something pass; fix the cause or open an issue.
- **Docs:** English only, except `PIPELINE`, `GETTING_STARTED` and `CONCEPTS`, which exist as
  `docs/en/` and `docs/pt-br/` pairs and must be changed together. Run
  `python _tools\docs_check.py` (it must end with 0 errors).
- **Style:** match the surrounding code (stdlib Python, `fmlib` for shared helpers). Commit
  messages: `feat:`, `fix:`, `docs:`, `chore:`.
- **License:** by contributing you agree your code is MIT and your docs CC BY 4.0.
