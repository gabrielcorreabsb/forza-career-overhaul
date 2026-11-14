# Mod toolkit

> 🌐 [Português](../pt-br/MOD_TOOLKIT.md) · **English**

**What this is.** A map of what the Career Overhaul can change today, how sure we
are of each lever, and what is still being tested. It is the short answer to
"what can the mod do?" — the evidence behind each row lives in
[DISCOVERIES](../project/DISCOVERIES.md), [MODDING_SURFACE](../reference/MODDING_SURFACE.md),
[RACE_SYSTEM](../reference/RACE_SYSTEM.md) and [OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md).

Evidence labels: **verified** (a change was made and the effect seen in game),
**observed** (seen, with few runs or indirectly), **hypothesis** (from data or
names, not run). Status: ✅ ready · 🧪 being tested · ⛔ closed.

## 1. Pillars

### Career structure and text
| lever | status | evidence | tool / guide |
|---|---|---|---|
| cup → ladder → series → event tree: order, names, art (reuse of existing art) | ✅ | verified | [tutorials 02](../tutorials/02_reorder.md), [03](../tutorials/03_new_series.md) |
| brand-new series with their own ids | ✅ | verified | `build_series.py` |
| names and descriptions (new text keys of any length) | ✅ | verified | `str_edit.py`, [tutorial 01](../tutorials/01_rename.md) |
| first-car selection screen | 🧪 | hypothesis | [CAREER_BASICS](../guides/CAREER_BASICS.md) |
| reward showcase series (a series type that drives a prize car): it **needs the prize car in the garage** to enter; it does not give the car | ⛔ | verified | — |

### Rewards and progression
| lever | status | evidence | tool / guide |
|---|---|---|---|
| unlock a series (ours or a vanilla one) only after another series or a whole group is done | ✅ | verified | the series' entry criteria ([CAREER_BASICS](../guides/CAREER_BASICS.md)) |
| a **series with several events** (2–8 in the vanilla game): the events run in sequence, series points add up per driver, the series is done after the last event, every race pays the same | ✅ | verified | the series' event list ([CAREER_BASICS](../guides/CAREER_BASICS.md)), [DISCOVERIES](../project/DISCOVERIES.md) |
| pay that grows with the race length (laps, distance) | ✅ | observed | [ECONOMY_MAP](../reference/ECONOMY_MAP.md) |
| placement bonus when a series ends (trophy plus credits by final position), (in the game data for every series; **not paid** when a new series of ours was won, so far) | 🧪 | hypothesis | open |
| races in our series count for the live vanilla challenges of the Challenge Hub (a monthly "5 races in a 2020s car" paid 75,000 credits) | ✅ | verified | pick cars and tracks that match the live challenges: laps, track and car count one for one, the progress lives on the server (the screen reads 0% after a restart until the first race), and finishing one pays the real prize (D69); a challenge that names only a track counts by the track alone (D71) |
| a prize of our own: edit a challenge's condition, prize or per-series objective | ⛔ | observed | the row shows **completed**, but nothing is paid; prizes are granted by the server against its own challenge list |

### Event
| lever | status | evidence | tool / guide |
|---|---|---|---|
| track and number of laps per event (the per-event override wins) | ✅ | verified | [CAREER_BASICS](../guides/CAREER_BASICS.md) |
| performance cap per event (the event value wins over the override) | ✅ | verified | [DISCOVERIES](../project/DISCOVERIES.md) |
| caps are on the **game's** PI scale (C 500, B 600, A 700, S 800, R 900); the catalogue's PI column is not | ✅ | verified | [CARS_AND_PI](../reference/CARS_AND_PI.md) §3.1 |
| car eligibility by accept list | ✅ | verified | [CAREER_BASICS](../guides/CAREER_BASICS.md) |
| numeric car limits: PI is inert and the accept list wins (year, power and weight untested) | ⛔ | observed | — |

### AI roster and behaviour
| lever | status | evidence | tool / guide |
|---|---|---|---|
| roster that follows the player's PI, or a fixed multiclass list | ✅ | verified | [AI_GRIDS](../guides/AI_GRIDS.md), [tutorial 04](../tutorials/04_ai_grid.md) |
| pools larger than the grid (a different field every race) and wide PI bands | ✅ | verified | [AI_GRIDS](../guides/AI_GRIDS.md) |
| **custom roster** in an existing, unused AI roster document (for example 23 cars of one model); one roster per document, shared by every event that points to it | ✅ | verified | [AI_GRIDS](../guides/AI_GRIDS.md) §6 |
| **custom roster through the cache**: the roster document is rewritten with `cache_edit.py` and the game reads the cache copy; per class, per make, or one pool of every car of a make | ✅ | verified | [AI_GRIDS](../guides/AI_GRIDS.md) §1, §6c |
| the AI's PI is clamped at the roster window's ceiling when the player's car is above it; a class series needs a window whose ceiling is the class ceiling | ✅ | observed | [AI_GRIDS](../guides/AI_GRIDS.md) §5 |
| a **closed pool of hand-picked models** in the roster document gives a grid of only those models, spread evenly (5 class-A models, 23 slots, PI 658–677) | ✅ | verified | [DISCOVERIES](../project/DISCOVERIES.md) D65 |
| a series' own AI car list as a **filter** on the roster document | ⛔ | verified | D66: the list does not filter; write the pool into the document |
| **free a vanilla roster document**: an event whose document has an identical copy can be pointed at the copy (same grid), and the freed document becomes a pool of ours; 313 are freeable | ✅ | verified | D67 |
| a **brand-new** AI roster file (a new entry the server does not know) | ⛔ | observed | the game went offline when the event was opened; the freed documents above are the way around it |
| how far the AI sits from the player (picked by the player's PI against the document's PI floor; the event's performance cap does not limit the AI) | ✅ | observed | [AI_GRIDS](../guides/AI_GRIDS.md) §5 |
| roster-document behaviour flags (catch-up, slow-down…) against the series ones: which wins | 🧪 | hypothesis | — |
| grids above 24 cars | 🧪 | to test | a 46-slot document still showed 24 drivers (D70) |
| AI rubber banding in the career generators | already off | observed | [MODDING_SURFACE](../reference/MODDING_SURFACE.md) |
| AI catch-up and slow-down off in the race: the AI got better, and both off is the career default (a player's report, no lap measurements) | ✅ | observed | [DISCOVERIES](../project/DISCOVERIES.md) D59 |
| global AI settings that also reach multiplayer | ⛔ | — | not touched without discussion |

### Session: practice and qualifying
| lever | status | evidence | tool / guide |
|---|---|---|---|
| limited practice laps → a timed session (there is **no separate qualifying session** in the career) | ✅ | observed | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.5 |
| trackday: no practice, rolling start, one lap | ✅ | verified | [CAREER_MOD](../guides/CAREER_MOD.md) |
| one-lap session | 🧪 | hypothesis | — |
| **practice laps per event**: the event's `NumberOfRequiredLaps` sets them, apart from the race laps (1 and 5 practice laps tested with a 2-lap race; 0 leaves no counted laps and still lets you race) | ✅ | observed | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.4 |
| weather and time of day in the event override act on the **race only**; the practice keeps its own block (heavy rain and a night start tested); pointing to another forecast works, editing a forecast's content is unproven | ✅ | observed | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.16 |
| mandatory pit stop: `Pits` 1 demands it; `Pits` 0 removes it only if the generator's `NumQuickStops` is also 0 (a generator with 1 still forced a stop) | ✅ | observed | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.6 |
| "no practice" by setting the practice budget to 0 | ⛔ | observed | only the Trackday reproduces it; two other series kept their practice |
| start type (standing or rolling): set by the session generator, **not** by the series' slot-car-start flag; a value in the event's override wins, so it is a choice per event (one pair tested) | ✅ | verified | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.8 |
| default tyre compound, fuel scale and tyre wear for the career | 🧪 | hypothesis | — |

### Grid and start position
| lever | status | evidence |
|---|---|---|
| the **AI** grid follows the practice classification | ✅ | observed |
| the **human's** slot is the slot picked on the start-position wager screen, when it is on | ✅ | verified |
| turning the wager screen on or off (one client flag) | ✅ | verified |
| **where the human starts is decided by the session generator's grid shape** (the slot the player picks on the screen is obeyed only when the generator imposes none) | ✅ | observed | [ADR-006](../project/decisions/ADR-006_grid_start_shapes.md) |
| estimated-lap-time order, no start index: the **picked slot is obeyed** (picked 12th, started 12th) | ✅ | observed | free start |
| rank order with index 0 to 5: **first**; index 6 or more: **last** (24th of 24, 8th of 8); no middle slot, and the picked slot is not obeyed | ✅ | observed | GT-style start |
| qualifying order: a **mid-grid value that varies** with the field, the AI document and the car (3rd of 8, 5th of 12 and 16, 7th of 24); the picked slot is not obeyed | ⛔ | observed | documented, not used |
| the slot the screen suggests | ⛔ constant | does not follow the player's practice time, the wager table or the projected-time term |
| how many slots the screen lists | ⛔ not data | the cache does not change it |
| the **bonus paid per slot** (wager table of the cup) | ⛔ | so far only the interface changes: a table set to 10.0 on every slot changed nothing in the credits paid at the end of the race (observed) |

The bonus table belongs to a **cup**, but it only changes what the screen shows, not the credits paid. The career base cell of a track and car class behaves the same way (see [ECONOMY_MAP](../reference/ECONOMY_MAP.md)).

### Client flags
The client reads its feature flags from the cache (verified). Per-mode lists (tyre
type, fuel scale) with an item for the career affect only the career. A flag shared
with Featured or multiplayer is not changed without discussion; after changing any
flag, open one Featured or multiplayer event to confirm nothing moved.

## 2. Recipes

| recipe | works today? | how |
|---|---|---|
| **Honest qualifying** | ✅ manual | keep the wager screen on; the AI already follows practice; read your place in the practice table and pick that slot |
| **GT-style start** (start last and overtake everyone) | ✅ forced (observed, several series) | a session generator set to rank order with start index 23 puts the player **last** whatever the practice lap, in grids of 8 and 24 cars; the project fixes this shape ([ADR-006](../project/decisions/ADR-006_grid_start_shapes.md)) |
| **Free start** (choose your slot) | ✅ | a generator with estimated-lap-time order and no start index; the screen's pick is obeyed |
| **Short practice** (1 to 5 laps) | ✅ | set the event's `NumberOfRequiredLaps`, apart from the race laps |
| **Trackday** | ✅ | [CAREER_MOD](../guides/CAREER_MOD.md) |
| **Multiclass grid in any series** | ✅ | [AI_GRIDS](../guides/AI_GRIDS.md) |
| **Automatic qualifying for the human** | ⛔ | no data lever found so far |

## 3. Closed — please do not repeat

- **"The generator's grid shape does not move the human"** was an early reading and is now wrong: later benches showed that the
  rank-order shape with its index and the qualifying shape do decide where the human starts (see the grid table). The Featured and
  multiplayer generators still use the qualifying shape, and the career generators the estimated one.
- **Removing the wager block** does not remove the screen; only the client flag does.
- **"The fixed slot is the wager's suggestion applied hidden"** is refuted: with the
  screen on, the suggestion differs from the hidden constant.
- **The projected-time term of the wager block** moved neither the suggestion, the
  bonus scale nor the AI grid.
- **Manual grid ordering flag**: its name belongs to multiplayer/freeplay lobby code;
  it is global and was not touched.
- **Series and event fields tried for a real Qualifying or a different AI**, all
  with no effect in the career: a wider-window AI roster for the event (the AI stayed
  capped at about class D), a smaller series field size (the grid stayed at 24), a
  series-level rules reference (the Featured series carry it, the career ignores it)
  and the practice limit type `Disabled` (practice stayed limited). The client has a
  Qualification activity of its own, but no career field we could reach selects it.
- **Regulation 103 on a career generator** showed no visible effect: no ghost, no off-track or wrong-way penalty; collisions were
  already punished with no regulation.
- **Practice length from the series or the generator** (lap limits of 1, 3 and 6 tried) did not change the practice; the event's
  required laps do.
- **The suggested slot** did not follow a best lap about six seconds ahead of the
  field or the class of the car either.
- **A prize of our own through challenges (four tests):** turning on per-series objectives, pointing a challenge at our series, changing a
  challenge's condition (laps, track, car division) and opening a reward showcase. The client reads the edited conditions and marks the
  row completed, but no car or credits arrive and the completion can vanish after a restart. Only the live, unedited challenges pay, and those keep their progress across restarts.
- **One field on a bench series, no effect on the credits paid:** the generator's payout modifier and overrides preset, and the
  series' AI difficulty. The player's own difficulty choice may mask the last one (hypothesis).

## 4. Next

Rewards are answered: the career rewards the player with what the game already pays (race length, placement bonus, live vanilla
challenges) and with unlocks by progression; a prize of our own is closed (see [ECONOMY_MAP](../reference/ECONOMY_MAP.md)). Next comes a
first playable series, then a season, built from the levers above. One change at a time, each reverted before the next. See [OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md).
