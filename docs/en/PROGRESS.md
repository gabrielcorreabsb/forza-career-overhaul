# Progress

> 🌐 [Português](../pt-br/PROGRESS.md) · **English**

**What this is.** The project's story so far, phase by phase: what was built, what
was tested in game, what turned out to be closed. For the vision see
[CAREER_MOD](../guides/CAREER_MOD.md); for the lever-by-lever map see
[MOD_TOOLKIT](MOD_TOOLKIT.md); the evidence is in
[DISCOVERIES](../project/DISCOVERIES.md). Labels: **verified** (change made, effect
seen in game), **observed** (seen with few runs), **closed** (tested, does not work).

## Timeline

| phase | when | what changed for the player | state |
|---|---|---|---|
| **v0.1.0** | Oct 2026 | the pipeline: rename, reorder, unlock the whole career; new series from a JSON spec; safe apply (lint, dry-run, backup, verify, rollback) | verified |
| **v0.2.0** | 31 Oct | AI grids (pool or fixed list), spec races of 23 cars of one model, a trackday series, the audit of the vanilla career | verified |
| **Test batteries 3–5** | early Nov | where you start (free pick or last), practice length apart from the race, weather and time of day for the race, a mandatory pit stop per event, small fields (8, 12, 16 cars) | observed |
| **Phase 0.2 — rewards** | 6–9 Nov | the career's pay and prizes mapped. Editing payout tables, bonuses or challenge conditions changes only what the screens show; **credits and cars are granted by the server against its own challenges**. What works instead: pay that grows with race length, unlocks by progression, and live vanilla challenges that count races run in our series | closed for prizes of our own; observed for the rest |
| **Phase 0.3 — an own season** | 9–11 Nov | a cup of our own that plays like the vanilla ones (below) | in progress |

## Phase 0.3, finding by finding

| finding | what it enables | state | evidence |
|---|---|---|---|
| A series of ours with **several events** runs in sequence, adds series points per driver, is done after the last event | seasons made of multi-race series | verified | D62 |
| **The game reads the AI roster from the cache**, not the install; the AI sits at the roster window's ceiling | AI grids rebuilt with the normal apply tool, no install edits | verified | D60, D61 |
| **The game's PI scale** (C 500, B 600, A 700, S 800, R 900) is not the catalogue's PI column | correct caps and windows | verified | D63 |
| **One AI roster per class** keeps the field inside the player's class (German only, C to S) | class series with an honest field | verified | D64 |
| **A closed pool of hand-picked models** gives a grid of only those models | one-make, one-brand, themed championships | verified | D65 |
| A series' own car list **does not filter** the roster document | the roster must be written in the document itself | closed | D66 |
| **A vanilla roster document with an identical copy can be freed** (point its event at the copy) and reused as a pool of ours | own pools at scale: 313 documents are freeable | verified | D67 |
| **First season, "German Ovals"** (6 series in 3 groups, in a cup of its own): the cup shows, the second group stays locked until the first is done, the German-only AI sits in the player's class | the first playable season | first group played; groups 2–3 not yet | — |

## What is next

- **Own AI pools at scale**: one roster per series on the freeable documents (make, decade, country).
- **Race format**: wear and fuel, weather and time of day passing during a race, the AI's behaviour flags against the series' ones.
- **Grids above 24 cars**: no precedent yet ([OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md)).
- **Own art per series** (posters and banners): the format is read, writing is untested.
- **Closed, do not repeat**: a real Qualifying, prizes of our own, payout edits in the cache or install files.

## Reading the evidence

Findings marked *observed* rest on one or two runs. If your result differs, open an
issue with the numbers (see the README, "Contributing"). Release history:
[CHANGELOG](../../CHANGELOG.md).
