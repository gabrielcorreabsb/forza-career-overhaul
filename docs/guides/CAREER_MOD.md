# The career mod — what we are building, and how far it has come

> **Area: the whole project.** The vision, the stages of the career we are
> assembling, and which of them already run in game. Evidence for each claim is
> in [DISCOVERIES](../project/DISCOVERIES.md); what is next is in
> [PROGRESS](../en/PROGRESS.md). This page documents; it does
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
| **Series with several events** | a series of several races, points adding up, done after the last event | verified in game ([DISCOVERIES](../project/DISCOVERIES.md) D62) |
| **AI per class or per make** | a roster per class keeps the AI in your class; a closed pool of chosen models gives a grid of only those models | verified in game (D64, D65) |
| **Progression gates** | a series or a whole group opens only after another is done | verified in game |
| **A first own season** | a cup of our own with groups that unlock in order ("German Ovals", 6 series) | in game; first group played ([PROGRESS](../en/PROGRESS.md)) |
| **Entry ladder (E and D)** | four to six short series for the cars the career never lists (E: 31 of 50 cars used, D: 50 of 106) | planned, viable |
| **Spec races** | everyone in the same car: 23 AI of one model against you | verified in game |
| **Trackday** | pick a circuit, any class, no practice, a rolling start | verified in game |
| **Start type per event** | a standing or a rolling start, chosen event by event | verified in game |
| **Honest multi-class AI** | a pool that follows your PI, or a fixed list from D to R | verified in game |
| **Race weekend** | practice orders the AI's grid; the start-position wager places you | observed (no separate qualifying exists in the career) |
| **Start slot per event** | a free pick of your slot, or the generator places you last, whatever your lap | observed (several series; rank order with an index of 6 or more gives last) |
| **Start last and overtake** | a forced start at the back of the grid, in fields of 8 and 24 cars | observed (several series; fixed at index 23, [ADR-006](../project/decisions/ADR-006_grid_start_shapes.md)) |
| **Racers Cup rules in the career** | a class-restricted event; its regulation showed no visible effect in the career | observed (class bucket enforced; regulation ineffective) |
| **One-make and period series** | one manufacturer, one decade, one country | planned, viable |
| **Longer races with strategy** | wear, fuel, a pit stop, a tyre compound | a mandatory stop is a per-event switch (observed); wear and fuel to test |
| **Weather and time of day per event** | a set forecast and start hour for the race (heavy rain, a night start) | observed (race only; the practice keeps its own) |
| **Practice length per event** | 1 to 5 practice laps, apart from the race laps | observed |
| **Prize cars, the end of car level, manufacturer affinity** | — | not possible: they live in the game's account and server |

## 3. Examples that already run

These are series the project has built and played. They are examples of what the
tools make possible; the kits themselves are generated on your machine and are not
published ([PIPELINE](../en/PIPELINE.md)).

### Trackday (series 20004)
One event on the Nürburgring Nordschleife, rolling start, one lap, no practice,
any class up to X999 (`ClassRestriction 8`, `TargetPI 999`; an S car at PI 701 was
accepted), a 23-car acceptlist for the player and a mixed grid of 23 AI. It proves the
format "pick a circuit and drive it" (FM4's "pick a circuit, any class").

- **Placement:** a cup and ladder of its own ("Trackday"), the series cloned from a vanilla
  series; the event's `OpenPracticeLimitationTimeInSeconds` is 0. The same 0 on other
  series did **not** remove the practice (observed in two series), so the trackday relies
  on more than that field.
- **The AI is the interesting part**, and three grids were played in turn on the same
  document: the original 23 cars (window 600–700); a **pool** of 40 cars (window 500–800,
  the field sits 10–50 PI below you, in your class); a **fixed list** of 18 cars repeated
  to 23 slots, D to R, whatever you drive; and a **pool of 56 cars (E to P) with a wide band**
  (−350…+250), whose field follows your car and spans 4 to 7 classes. The last one stayed.
- The game draws from the list or pool (repeats beyond the listed weights were seen), so the
  weights of a list are a bias, not a guarantee.
- To build or switch such a grid: [AI_GRIDS](AI_GRIDS.md) §6 and
  [tutorial 04](../tutorials/04_ai_grid.md).

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

### Start slot, practice length and weather (bench series)
One field at a time on copies of the same event: where you start follows the session generator's grid shape (a free pick, first, or
last, whatever your lap); the practice has its own lap count, apart from the race; weather and time of day set for the race leave the
practice alone; and fields of 8, 12 and 16 cars run. See [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.4 and §2.17,
[ADR-006](../project/decisions/ADR-006_grid_start_shapes.md) and D46–D53 in [DISCOVERIES](../project/DISCOVERIES.md).

### A first season (cup of our own, "German Ovals")
Six series in three groups, in a cup of its own: the cup shows in the career, the second group stays locked until
the first is done, and the AI is German only, inside the player's class (one roster per class, caps on the game's
PI scale). A 3-event series ran in sequence with accumulated points, and a closed pool of five chosen models gave a
grid of only those models. See [PROGRESS](../en/PROGRESS.md) and D60–D67 in [DISCOVERIES](../project/DISCOVERIES.md).

## 4. What shapes the design

- **The career is top-heavy.** 209 of 711 cars are in no event, and 245 of 627
  events sit at a cap of 800 or 900. The entry classes are where a new profile
  starts and where the game gives the least ([CAREER_AUDIT](../project/CAREER_AUDIT.md)).
- **The AI is set by its roster document, not by the series.** Which cars you race,
  and how far from your PI, are decided in one XML ([AI_GRIDS](AI_GRIDS.md)).
- **Some things cannot be changed.** A brand-new CMS file is rejected (the game
  goes offline), so custom content reuses existing slots: a vanilla AI document with an identical copy can be
  freed and reused as a pool of ours (D67). Prizes, physics and the account economy stay out of reach and out of
  scope: the server grants prizes and credits against its own challenges.
- **Every claim carries a label**: verified, observed or to test. Findings that
  rest on one or two runs say so.

## 5. What is next

The next stages, in the order we expect to reach them: the entry ladder at E and D,
one-make and period series, longer races with wear and fuel, and the career economy.
The list with its reasons lives in [PROGRESS](../en/PROGRESS.md).

## 6. How to take part

The tools are public, so you can build the same pieces yourself on your own copy
of the game: start with [GETTING_STARTED](../en/GETTING_STARTED.md). The most useful
help is a result from a run: a series nobody tried, a number that disagrees with
ours, or one of the [open questions](../project/OPEN_QUESTIONS.md) settled.
