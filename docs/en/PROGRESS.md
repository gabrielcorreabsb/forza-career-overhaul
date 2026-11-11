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
| **v0.1.0 and v0.2.0** | 31 Oct | the pipeline: rename, reorder, unlock the whole career; new series from a JSON spec; safe apply (lint, dry-run, backup, verify, rollback); AI grids (pool or fixed list), spec races of 23 cars of one model, a trackday series, the audit of the vanilla career | verified |
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

State labels: **viable** (the mechanism is known), **to test** (plausible, needs a controlled run in game), **not possible**
(decided by the game or its server, not by the content data).

| item | why | state |
|---|---|---|
| **Own AI pools at scale** | one roster per series on the freeable documents (make, decade, country) | viable |
| **Entry path at E and D** | 209 of 711 cars are in no event; E (31 of 50 used) and D (50 of 106) are the worst served; short series for them, with an AI band that keeps the field in class | viable |
| **Car × event matrix** | a list that puts every car in at least one event turns the catalogue into the career; numeric limits (year, power) are untested | viable, partly to test |
| **Permanent event list** | the timed (Featured) content has no permanent home; re-parenting a series with fresh ids is proven, synthesising its lists is the open part | viable |
| **Race format** | wear and fuel, weather and time of day passing during a race, the AI's behaviour flags against the series' ones | to test |
| **Career tyre compound** | per-mode lists in the client flags set the default tyre for online modes but not the career; adding a career item is one entry | to test |
| **Grids above 24 cars** | no precedent: every vanilla document asks for 23 AI + the player ([OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md) 8) | to test |
| **Own art per series** | posters and banners are inherited from the donor series; the format is read, writing is untested | to test |
| **Other languages** | new strings go into the pt-BR table only; the other 19 locales have no keys yet | later |

**Not possible, do not repeat:** a real Qualifying (D33), prizes of our own and payout edits in the cache or install files
(the server grants them), manufacturer affinity (a server value; the substitute is the one-make series), physics, the
account economy and global AI switches that also reach multiplayer.

## How to help

- **Run the pipeline on a copy** and report what breaks: [GETTING_STARTED](GETTING_STARTED.md) takes about 15 minutes and never
  touches the game.
- **Build a series** from a spec and open an issue with the spec: a decade, a country, a one-make grid, an entry-class ladder.
- **Settle an open question**: each item in [OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md) names the experiment that decides it.
- **Improve a guide** with a symptom you hit and its cause: [TROUBLESHOOTING](../guides/TROUBLESHOOTING.md).

## Reading the evidence

Findings marked *observed* rest on one or two runs. If your result differs, open an
issue with the numbers (see the README, "Contributing"). Release history:
[CHANGELOG](../../CHANGELOG.md).
