# The career mod — what we are building, and how far it has come

> **Area: the whole project.** The vision, the stages of the career we are
> assembling, and which of them already run in game. Evidence for each claim is
> in [DISCOVERIES](../project/DISCOVERIES.md); what is next is in
> [PROJECT_STATUS](../project/PROJECT_STATUS.md). This page documents; it does
> not ship anything: no game files and no mod payloads are distributed (see
> [NOTICE](../../NOTICE.md)).

## 1. The idea: Forza Motorsport 4 meets Gran Turismo 4

The career of Forza Motorsport (2023) is a calendar of timed events and open-class
races. We want the career people remember from two older games, taking the best
of each:

| from | what we take |
|---|---|
| **Forza Motorsport 4** | a **permanent event list** (nothing expires), the **right car for each event**, one-make series instead of an affinity system, a race weekend where practice sets the grid |
| **Gran Turismo 4** | a **ladder you climb from the entry classes**: short, cheap races in ordinary cars first (the Sunday Cup spirit), then regional and one-make cups, then endurance and themed events |

Both games are design references only; nothing from them is distributed here.

The mod is a *career*, not a single tweak: a set of series placed in the game's
own cup → ladder → series → event tree ([CAREER_MODEL](../reference/CAREER_MODEL.md)),
each with its own cars, cap, AI grid and rules. It is built piece by piece, and each
piece is tested in game before it counts.

## 2. The stages

| stage | what the player gets | state |
|---|---|---|
| **Own place in the career** | a cup and ladder of our own; renamed, reordered, unlocked content | verified in game |
| **Entry ladder (E and D)** | four to six short series for the cars the career never lists (E: 31 of 50 cars used, D: 50 of 106) | planned, viable |
| **Spec races** | everyone in the same car: 23 AI of one model against you | verified in game |
| **Trackday** | pick a circuit, any class, no practice, a rolling start | verified in game |
| **Start type per event** | a standing or a rolling start, chosen event by event | verified in game |
| **Honest multi-class AI** | a pool that follows your PI, or a fixed list from D to R | verified in game |
| **Race weekend** | practice orders the AI's grid; the start-position wager places you | observed (no separate qualifying exists in the career) |
| **One-make and period series** | one manufacturer, one decade, one country | planned, viable |
| **Longer races with strategy** | wear, fuel, a pit stop, a tyre compound | to test |
| **Weather and time of day per event** | a set forecast per event | to test |
| **Prize cars, the end of car level, manufacturer affinity** | — | not possible: they live in the game's account and server |

## 3. Examples that already run

These are series the project has built and played. They are examples of what the
tools make possible; the kits themselves are generated on your machine and are not
published ([PIPELINE](../en/PIPELINE.md)).

### Trackday (series 20004)
One event on the Nürburgring Nordschleife, rolling start, one lap, no practice,
any class up to X999, with a mixed grid of 23 AI. It proves the format "pick a
circuit and drive it". Details: [CIRCUIT_EXPERIENCE](CIRCUIT_EXPERIENCE.md).

### Spec race with a custom roster (series 20009 and 20010)
The AI grid is 23 cars of a single model: a Subaru BRZ '22 in one series, a
Porsche 911 GT3 RS '23 in another. The player sits in the same car as the field.
Two things make it fair:
- keep the AI in your class by choosing the roster's window floor and a narrow band;
- set the event cap equal to the top of the window and drive at the cap. At PI 800
  with a window maximum of 800 the whole field finished between 792 and 800.

Recipe and limits: [AI_GRIDS](AI_GRIDS.md) §6, and findings D35–D41 in
[DISCOVERIES](../project/DISCOVERIES.md).

### Start type per event (series 20010 and 20011)
Two copies of the same spec race: one starts standing, the other rolling. The
event override beats the session generator that the two events share, so the start
type is a choice **per event**, not per generator. See
[RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.8.

### Race weekend (bench series)
Limited practice laps give a timed session; the race grid then lines the AI up in
practice order, while your own slot comes from the *Challenge the Grid* wager. The
game has no separate qualifying screen in the career, and we found no data field
that turns one on. See [RACE_SYSTEM](../reference/RACE_SYSTEM.md) and
[DISCOVERIES](../project/DISCOVERIES.md) D30 and D33.

## 4. What shapes the design

- **The career is top-heavy.** 209 of 711 cars are in no event, and 245 of 627
  events sit at a cap of 800 or 900. The entry classes are where a new profile
  starts and where the game gives the least ([CAREER_AUDIT](../project/CAREER_AUDIT.md)).
- **The AI is set by its roster document, not by the series.** Which cars you race,
  and how far from your PI, are decided in one XML ([AI_GRIDS](AI_GRIDS.md)).
- **Some things cannot be changed.** A brand-new CMS file is rejected (the game
  goes offline), so custom content reuses existing slots. Prizes, physics and the
  account economy stay out of reach and out of scope.
- **Every claim carries a label**: verified, observed or to test. Findings that
  rest on one or two runs say so.

## 5. What is next

The next stages, in the order we expect to reach them: the entry ladder at E and D,
one-make and period series, longer races with a pit window, and weather per event.
The list with its reasons lives in [PROJECT_STATUS](../project/PROJECT_STATUS.md)
§4.

## 6. How to take part

The tools are public, so you can build the same pieces yourself on your own copy
of the game: start with [GETTING_STARTED](../en/GETTING_STARTED.md). The most useful
help is a result from a run: a series nobody tried, a number that disagrees with
ours, or one of the [open questions](../project/OPEN_QUESTIONS.md) settled.
