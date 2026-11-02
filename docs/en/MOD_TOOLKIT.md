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
| start type (standing or rolling): set by the session generator, **not** by the series' slot-car-start flag; an override-level value may win (being tested) | ✅ | observed | [RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.8 |
| default tyre compound, fuel scale and tyre wear for the career | 🧪 | hypothesis | — |

### Grid and start position
| lever | status | evidence |
|---|---|---|
| the **AI** grid follows the practice classification | ✅ | observed |
| the **human's** slot is the slot picked on the start-position wager screen, when it is on | ✅ | verified |
| turning the wager screen on or off (one client flag) | ✅ | verified |
| the human's slot with the screen off is a constant per event | observed | origin unknown |
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
| **GT-style start** (start last and overtake everyone) | ✅ incentive · ⛔ forced | pick the last slot on the screen and make it pay the most with a custom bonus curve (being tested) |
| **Trackday** | ✅ | [CIRCUIT_EXPERIENCE](../guides/CIRCUIT_EXPERIENCE.md) |
| **Multiclass grid in any series** | ✅ | [CUSTOM_RACE](../guides/CUSTOM_RACE.md) |
| **Automatic qualifying for the human** | ⛔ | no data lever found so far |

## 3. Closed — please do not repeat

- **Grid-ordering shape of the session generators.** The qualifying shape (with a
  human cluster slot) changed neither the human's slot nor the AI order. Featured
  and multiplayer generators all use it and have no AI cars; the career generators
  use the estimated shape and share no generator with Featured. The likely reading:
  multiplayer qualifies because every car is human and clusters by time, and the
  career ignores that setting.
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
- **The suggested slot** did not follow a best lap about six seconds ahead of the
  field or the class of the car either.

## 4. Next

A custom bonus curve on one cup (with the credit checked after the race), one more
read-only search of the install for a data source of the human's slot, then the
one-lap session, the AI catch-up control and the tyre and fuel flags — one change at
a time, each reverted before the next. See [OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md).
