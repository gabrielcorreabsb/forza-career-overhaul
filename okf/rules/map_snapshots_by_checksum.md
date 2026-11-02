---
type: "Rule"
title: "Map snapshot to blob by Checksum, never by name or mtime"
description: "Two snapshots (old and live) hold same-shaped blobs; matching by name or mtime picked the wrong blob once."
resource: "../docs/en/PIPELINE.md"
tags: ["rule", "golden"]
---

# Map snapshot to blob by Checksum, never by name or mtime

Two snapshots (old and live) hold same-shaped blobs; matching by name or mtime picked the wrong blob once.

Full text and rationale: `docs/en/PIPELINE.md`.
