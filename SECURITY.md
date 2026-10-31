<!-- docs_check: historical -->
# Security

This project edits game content on your own machine. It runs no service and
stores no user data, so "security" here means two things.

## Never post, commit or attach

- The **CMS AES key**.
- Anything from the **Forza Mod Tool**.
- **Game files or game text**, encrypted or decrypted payloads (`.enc`),
  inventories generated from your game, cache copies.

If you posted one by mistake in an issue or PR, edit it out and tell us in the
same thread; we will remove the content from the history we control. If a key or
tool leaks, it is the rights holders' material: we do not host or mirror it.
See [THIRD_PARTY](docs/THIRD_PARTY.md).

## Reporting a problem in the tools

- A bug that could **corrupt the cache or bypass a safety rule** (the
  game-closed check, `--dry-run`/`--verify`, the plan linter): open an issue with
  the exact command and the last lines of output, without any of the material
  above. Describe the effect rather than attaching files.
- A flaw you would rather not disclose publicly: open a minimal issue saying you
  have a security report and ask for a private channel. Do not put details in it.

## Supported versions

Only the latest `main` is maintained. Kits are bound to a server snapshot; when
the server ships a new one, regenerate your kit.
