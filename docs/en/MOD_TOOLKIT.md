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
| free car choice vs locked car per series; first-car selection | 🧪 | hypothesis | [CAREER_BASICS](../guides/CAREER_BASICS.md) |

### Event
| lever | status | evidence | tool / guide |
|---|---|---|---|
| track and number of laps per event (the per-event override wins) | ✅ | verified | [CAREER_BASICS](../guides/CAREER_BASICS.md) |
| performance cap per event (the event value wins over the override) | ✅ | verified | [DISCOVERIES](../project/DISCOVERIES.md) |
| car eligibility by accept list | ✅ | verified | [CAREER_BASICS](../guides/CAREER_BASICS.md) |
| numeric car limits (PI, year, power, weight) | 🧪 | hypothesis | — |

### AI roster and behaviour
| lever | status | evidence | tool / guide |
|---|---|---|---|
| roster that follows the player's PI, or a fixed multiclass list | ✅ | verified | [AI_GRIDS](../guides/AI_GRIDS.md), [tutorial 04](../tutorials/04_ai_grid.md) |
| pools larger than the grid (a different field every race) and wide PI bands | ✅ | verified | [CUSTOM_RACE](../guides/CUSTOM_RACE.md) |
| **custom roster** in an existing, unused AI roster document (for example 23 cars of one model); one roster per document, shared by every event that points to it | ✅ | verified | [AI_GRIDS](../guides/AI_GRIDS.md) §6 |
| a **brand-new** AI roster file (a new entry the server does not know) | ⛔ | observed | the game went offline when the event was opened |
| how far the AI sits from the player (picked by the player's PI against the document's PI floor; the event's performance cap does not limit the AI) | ✅ | observed | [AI_GRIDS](../guides/AI_GRIDS.md) §5 |
| roster-document behaviour flags (catch-up, slow-down…) against the series ones: which wins | 🧪 | hypothesis | — |
| grids above 24 cars | 🧪 | to test | — |
| AI rubber banding in the career generators | already off | observed | [MODDING_SURFACE](../reference/MODDING_SURFACE.md) |
| AI catch-up and slow-down in the race and in practice | 🧪 | hypothesis | — |
| global AI settings that also reach multiplayer | ⛔ | — | not touched without discussion |

### Session: practice and qualifying
| lever | status | evidence | tool / guide |
|---|---|---|---|
| limited practice laps → a timed session (there is **no separate qualifying session** in the career) | ✅ | observed | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.5 |
| trackday: no practice, rolling start, one lap | ✅ | verified | [CIRCUIT_EXPERIENCE](../guides/CIRCUIT_EXPERIENCE.md) |
| one-lap session | 🧪 | hypothesis | — |
| **practice laps per event**: the event's `NumberOfRequiredLaps` sets them, apart from the race laps (1 and 5 practice laps tested with a 2-lap race; 0 leaves no counted laps and still lets you race) | ✅ | observed | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.4 |
| weather and time of day in the event override act on the **race only**; the practice keeps its own block (heavy rain and a night start tested) | ✅ | observed | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.16 |
| mandatory pit stop: `Pits` 1 demands it, `Pits` 0 does not | ✅ | observed | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.6 |
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
| the **bonus paid per slot** (wager table of the cup) | 🧪 | the screen reads it; a custom curve and the end-of-race credit are being tested |

The bonus table belongs to a **cup**, so it applies to every series of that cup.

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
| **Trackday** | ✅ | [CIRCUIT_EXPERIENCE](../guides/CIRCUIT_EXPERIENCE.md) |
| **Multiclass grid in any series** | ✅ | [CUSTOM_RACE](../guides/CUSTOM_RACE.md) |
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

## 4. Next

The career economy: scale one payout cell (track × class) and check that a series' credit follows, then a custom bonus curve on a
cup of its own with and without the wager screen (see [ECONOMY_MAP](../reference/ECONOMY_MAP.md)); the skip-completed-practice flag;
and a read of why a zero practice budget removes the practice only in the Trackday. One change at a time, each reverted before the
next. See [OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md).
