---
type: "Rule"
title: "Game closed before any CmsCache write"
description: "The game locks the blobs; writing while it is open fails with WinError 5 mid-apply and leaves the cache inconsistent. Close the game first."
resource: "../docs/en/PIPELINE.md"
tags: ["rule", "golden"]
---

# Game closed before any CmsCache write

The game locks the blobs; writing while it is open fails with WinError 5 mid-apply and leaves the cache inconsistent. Close the game first.

Full text and rationale: `docs/en/PIPELINE.md`.
