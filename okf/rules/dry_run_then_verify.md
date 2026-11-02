---
type: "Rule"
title: "cache_edit.py: --dry-run first, then apply with --verify"
description: "Every apply backs up to _backup first. The code refuses to apply without a recent clean dry-run, with Forza running, or if plan_lint fails. Never work around these guards."
resource: "../docs/en/PIPELINE.md"
tags: ["rule", "golden"]
---

# cache_edit.py: --dry-run first, then apply with --verify

Every apply backs up to _backup first. The code refuses to apply without a recent clean dry-run, with Forza running, or if plan_lint fails. Never work around these guards.

Full text and rationale: `docs/en/PIPELINE.md`.
