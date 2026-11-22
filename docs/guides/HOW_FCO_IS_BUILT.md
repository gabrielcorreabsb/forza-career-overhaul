# How FCO is built — architecture, base profile, and workflow

> **Area: Forza Career Overhaul (FCO) architecture.** How every FCO series is
> designed and assembled from our own documented **base profile**, which game
> files and layers control each setting, what the hard limits are, and how a
> series goes from spec to in-game testing. Evidence labels follow
> [MOD_TOOLKIT](../en/MOD_TOOLKIT.md): **verified** (changed and seen in game
> or reproducible by script), **observed** (seen in play or data, small sample),
> **hypothesis** (inferred, not yet isolated), **closed** (impossible or out of
> scope).

---

## 1. What FCO is and why it uses a base profile

Forza Career Overhaul (FCO) adds its own cup (**Cup 115**) inside Championship
500 alongside the vanilla Builders Cup. Vanilla cups, ladders, and series stay
untouched.

Early custom series were cloned directly from a **vanilla donor series** with a
few spec overrides on top. Whatever the spec did not explicitly set was
silently inherited from the donor — its car-list mode, AI switches, session
generator, practice settings, or PI cap — which led to broken car lists and
wrong AI behavior.

**Rule:** Every FCO series is built from one **base profile** owned by the
project and kept as plain data:

```text
vanilla skeleton (JSON/XML shape only) + FCO base profile + series spec overrides
```

- **No silent inheritance:** every field that matters is written explicitly in
  the base profile. The donor skeleton supplies only the JSON/XML container
  shape the game expects.
- **Self-documenting fields (`_doc`):** because JSON has no comments, every
  field `X` in the base profile and season specs carries a sibling `X_doc`
  explaining what it does, its evidence id, and why that value was chosen. Build
  tools strip `_doc` keys when generating payloads and reject undocumented
  fields.
- **Portable plain data:** keeping the base profile as pure JSON data (with no
  encrypted `.enc` payloads and no game files) allows a future installer to
  rebuild FCO series directly on a player's machine against their current cache
  snapshot.

---

## 2. Layers of a series and who wins

A single career series spans multiple files across the runtime content cache
(`CmsCache`) and the install folder. When two layers define the same setting,
the winner is fixed by the game's precedence rules:

| layer | file (CmsCache unless noted) | what it decides | precedence / notes |
|---|---|---|---|
| **Series** | `BuildersCupScheduleDataV4.json` (BCS) | name key (`IDS_`), gates (`EntryCriteria`), player car list (`SelectableCars`), race/practice AI switches (`AIRaceBehaviors`), series defaults (`DefaultEventOverrides`), poster/intro video paths | `Name` is the only text drawn on cards (`Description` is ignored, **observed** D92) |
| **Car block** | `BCSeriesSelectableCars.xml` | mirror of the player car list (`Acceptlist` or `Blacklist`) | required; clicking a series without its XML block crashes the game (`0xe06d7363`, **verified**) |
| **Event** | BCS `ChampionshipEventData` | track ids, **practice laps** (`NumberOfRequiredLaps`), **effective performance cap** (`TargetPI`) | event `TargetPI` is the real car-select cap (**verified** D8/D29); `NumberOfRequiredLaps` sets practice laps (**observed** D49) |
| **Event override** | `BCEventOverrides.json` | **race laps** (`FeatureRace.Laps`), AI document (`AIFileName`), race/practice weather and start time, race clock speed, **start type** (`_321Type`), generator (`ParentGeneratorId`), mandatory pits | **wins over the event and generator** for race laps (**verified** D28), start type (**verified** D34), and override `TargetPI` gate (**verified** D81) |
| **Session generator** | `GameOptions_<id>_FeaturedRace.xml` / `_PracticeAndQualification.xml` | generator `CarRestrictions` (class, PI), pit stops (`NumQuickStops`), grid ordering (`GridOrderingType` + `ClusterHumansAtIndex`), default start type | can restrict the car list if stricter than the series; `NumQuickStops > 0` forces a pit stop even when override `Pits = 0` (**observed** D54); sets human grid slot ([ADR-006](../project/decisions/ADR-006_grid_start_shapes.md)) |
| **AI document** | `AIField_<id>_Gen.xml` | AI car roster, PI window, PI progression band per frame, 23 AI slots | decides the AI field completely (**verified** D66/D82); `MaxAIPlayers` and `AIDifficulty` on the series do not act (**verified** D79) |
| **AI global** | install `media\base\ai\aistatics.zip` | AI per-driver speed band (`SpeedScaleTendencyMin/Max`) and off-track/crash recovery keys | global install edit (`Default.ini` + 11 `Track_*.ini`); Steam *verify files* restores it ([AI_STATICS](../reference/AI_STATICS.md), **verified/observed** D76–D86) |
| **Player preset** | game difficulty settings | masks series damage (`DamageDifficulty`) and whether tyre wear applies | player's own settings override or mask series-level damage/wear defaults (**observed** D72/D79) |
| **Server** | online service | credits granted, cars/prizes awarded, Car Points (CP), live Challenge Hub progress | **server-authoritative** ([ECONOMY_MAP](../reference/ECONOMY_MAP.md), **verified/observed** D56–D58/D75) |

---

## 3. The base profile defaults

### 3.1 Player cars (open list via blocklist)

- **Open eligibility (`Blocklist` / `Blacklist`):** the base profile sets
  `SelectableCars.BlockOrAcceptlistType` to `Blocklist` in BCS and `Blacklist`
  in `BCSeriesSelectableCars.xml`, with `CarClassId: Any`, `CarDivisionId: Open`,
  event/override `TargetPI: 999` / class `8`, and an open-class session
  generator (class 8, PI 0..999, no restriction list) (**verified/observed**
  D81, D96).
- **Why not a full acceptlist:** vanilla acceptlists cap out at **23** entries.
  Trying to list hundreds of cars in an `Acceptlist` fails eligibility or gets
  silently truncated (682 entries failed in early testing and cut down to 98
  cars in an unprofiled build) (**verified** D10).
- **Exclusions & suggested car:** the base blocklist leaves out disruptive
  cars starting with the 6 class X prototypes. Note that when a player owns no
  eligible car in an open blocklist, the fallback suggested car defaults to the
  MP4/4 (`1670`) unless blocked (**observed**).
- **Numeric filters (when needed):** with an empty `Blocklist` and `CarClassId: Any`,
  series can filter by `YearMin/Max`, `PIMin/Max` (game scale), `PowerMin/Max`
  (horsepower, though UI shows kW), `WeightMax` (units of 100 kg), and
  `BaseCostMax`. `BaseCostMin` and `Ownership` have no effect in Builders Cup
  (**observed** D88, D121, D126).

### 3.2 AI (standard + one document per grid)

The FCO AI standard combines three layers (**verified/observed** D76–D78, D86, D97):

1. **Race & practice switches (`AIRaceBehaviors`):** `EnableDifficultySlowDown`
   **on**, `EnableDifficultyCatchUp` **on**, `EnableDifficultyProximity` **off**,
   `EnablePosDifficultySpread` **off**, `EnableSlotCarRaceStart` **off**. Practice
   switches mirror the race.
2. **Global AI tuning (`aistatics.zip`):** narrowed per-driver speed tendency
   band (`SpeedScaleTendencyMin/Max`) and raised off-track/crash recovery speeds
   in `Default.ini` and the 11 `Track_*.ini` files ([AI_STATICS](../reference/AI_STATICS.md)).
3. **AI roster document (`AIField_<id>_Gen.xml`):**
   - **Class-free / open series:** `pool` mode over eligible catalogue cars that
     have `AI_<car>_<pi>` tunes (498 cars excluding class X and pre-1960),
     window `300..980` (step 20), 23 slots, and progression band **`-20..0`** so
     the AI follows the player's PI (**observed** D38; known risk: cars whose
     lowest AI tune sits above a low player PI run stronger than listed, D39,
     so verify with low/mid/high player cars).
   - **Class-pinned series:** 10-PI window ending at the class ceiling (e.g.
     A 700, S 800) with band **`0..0`** for a levelled field (**verified** D78).
   - **One document per grid:** a data audit of vanilla Builders Cup shows
     that vanilla multi-event series repeat the exact same AI roster, 23 slots,
     and switches across every event, only raising the PI window floor event by
     event (a difficulty ramp). FCO uses **one AI document per grid** (or one
     per ramp step), never one per event (**verified**).
   - **Document pool:** brand-new `AIField` files with invented ids are rejected
     (game goes offline, **observed** D36). Every custom grid reuses an unused
     existing document or a vanilla document freed by repointing byte-identical
     copies (~302 identical copies exist across cups, freeable in stages,
     **verified** D67).

### 3.3 Session, weather, clock, and practice

- **Practice is independent of the race:** `NumberOfRequiredLaps` on the event
  sets practice laps (default `1`; `0` runs one lap plus a 10-minute timed free
  practice, **observed** D49, D95). Practice start hour, minute, and weather
  forecast live in `PracticeAndQualifying` (default: `08:00` under clear sky) and
  remain untouched by race overrides (**verified** D83, D87, D90).
- **Race format in the override:** `FeatureRace.Laps` sets race laps (**verified**
  D28), `_321Type: "Full"` enforces standing starts (**verified** D34), and
  `WeatherForecast` / `TimeOfDayHour` / `TimeOfDayMinute` control race sky and
  start time (**verified** D81, D83).
- **Timed weather & accelerated clock:** existing forecast bodies can be
  edited, and **phase durations are real seconds** (**observed** D74; use long
  transitions when returning to clear sky so the track does not dry instantly).
  The race clock runs via the override pair `TimeOfDayTimeScale` +
  `TimeOfDayTimeScaleOverride` up to **x144** (**observed** D73; series-level
  `TimeOfDayTimeScale` alone does nothing).
- **Pits & physics flags:** `Pits = 0` avoids mandatory stops only when the
  session generator also has `NumQuickStops = 0` (**observed** D54).
  `DraftingEnabled` and `DynamicTrackEnabled` stay `true` (100% of vanilla
  career series).

### 3.4 Art, intro video, and lock text

- **Series poster:** custom art (`FCO_*`) added to both `seriesposters.zip`
  archives (`424x660` / `848x1320` or `1296x660` / `2592x1320` depending on
  target) with `swatchbin_edit.py` and linked via `ImagePath` (**observed**
  D98–D104, [SWATCHBIN](../reference/SWATCHBIN.md)). `BannerImagePath` and
  `ButtonImagePath` show nothing on career screens (**observed** D98).
- **Intro video:** full-screen Bink 2 (`KB2j`) video (`PlayIntroVideoFullScreen: true`,
  `FirstCarSelectEnabled: false`) installed via `bk2_install.py` / `encode_intro.py`
  and registered in `hash.manifest` via `hash_manifest_edit.py` (**verified/observed**
  D105–D119, [INTRO_VIDEO](../reference/INTRO_VIDEO.md), [INSTALL_INDEX](../reference/INSTALL_INDEX.md)).
  Cup-level `IntroVideoPath` does not play on entry (**observed** D122).
- **Lock text (no win gates):** `Description` is never drawn in the career
  (**observed** D92). For gated series (`RequiredSeries`, `RequiredLadders`,
  `RequiredEvents`), `EntryCriteria.EntryCriteriaName` renders custom lock text
  on the card — keep it under ~2 lines (~120 characters) so the header does not
  overlap poster art, never leave it empty, and **never promise a win** because
  any finishing position unlocks gates (**observed** D94, D123, D127). Driver-level
  locks always show the game's own message (**observed** D93).

### 3.5 Hard limits (do not repeat)

1. **Game CLOSED before any write:** applying cache edits while Forza Motorsport
   is running ("live career") fails on the very first blob swap with
   `WinError 5` (access denied) because the game locks cache files (**verified**).
   Dynamic variety comes from oversized AI pools (D19), multi-condition forecasts,
   progression gates, and applying before launch.
2. **Server owns economy & rewards:** credits, prizes, Car Points (CP), and
   Challenge Hub completions are server-side (**verified/observed** D56–D58,
   D69, D75, [ECONOMY_MAP](../reference/ECONOMY_MAP.md)).
3. **No brand-new `AIField` files:** reuse unused or repointed vanilla
   documents only (**observed** D36, **verified** D67).
4. **No Steam/update persistence for install files:** install-side assets
   (posters, `.bk2` videos, `hash.manifest`, `aistatics.zip`) are reset by
   Steam *verify files* or game updates; CmsCache kits must be regenerated after
   a new server cache snapshot.

---

## 4. How a series is born (spec → build → apply)

1. **Author the spec:** define only what differs from the base profile (series
   id `21000–21999`, fresh `EventDataId`s, tracks, race laps, weather/clock
   overrides, gates, poster/video names, pt-BR/en-US strings). Never reuse
   retired ids.
2. **Snapshot the live cache (game closed):**
   ```powershell
   python _tools\snapshot_cache.py
   ```
3. **Build payloads & plan:** generate the CmsCache kit (and any custom AI
   document via `python _tools\build_aifield.py --def specs\aifield\<name>.json --cache-plan`,
   or standalone series via `python _tools\build_series.py --spec ...`).
   Install-side posters (`swatchbin_edit.py`) and intro videos (`encode_intro.py`
   / `bk2_install.py` + `hash_manifest_edit.py`) must be installed before opening
   the game so cards and intros are not blank.
4. **Validate & dry-run:**
   ```powershell
   python _tools\plan_lint.py --plan <plan.json>
   python _tools\cache_edit.py --dry-run --plan <plan.json>
   ```
5. **Apply & verify (game closed):**
   ```powershell
   python _tools\cache_edit.py --plan <plan.json> --verify
   python _tools\cache_verify.py
   python _tools\inventory.py
   ```
   `cache_verify.py` must report 0 errors. If anything goes wrong, revert cleanly
   with `python _tools\rollback_cache.py` ([PIPELINE](../en/PIPELINE.md)).

---

## 5. In-game test checklist

Before considering a new FCO series ready:

- [ ] **Navigation & art:** FCO cup tab appears, ladder opens, series card shows
      its localized title and custom poster (and plays its intro video if set).
- [ ] **Car eligibility:** car select offers the expected car count (e.g., all
      eligible cars except blocked ones) and the suggested car behaves sensibly.
- [ ] **AI grid (3 car test):** run quick checks with low-, mid-, and high-class
      player cars; verify 23 AI cars appear near the expected PI band without
      unexpected spikes.
- [ ] **Session rules:** practice laps/time/sky, race laps, weather timing,
      start hour, clock speed, start type, and pit requirement match the spec.
- [ ] **Progression & online:** completing event 1 unlocks event 2; gated series
      unlock upon completion; Challenge Hub and online modes still open normally.

---

## See also

[MOD_TOOLKIT](../en/MOD_TOOLKIT.md) · [AI_GRIDS](AI_GRIDS.md) ·
[AI_STATICS](../reference/AI_STATICS.md) · [RACE_SYSTEM](../reference/RACE_SYSTEM.md) ·
[SERIES_FIELD_VALUES](../reference/SERIES_FIELD_VALUES.md) · [SWATCHBIN](../reference/SWATCHBIN.md) ·
[INTRO_VIDEO](../reference/INTRO_VIDEO.md) · [INSTALL_INDEX](../reference/INSTALL_INDEX.md) ·
[ECONOMY_MAP](../reference/ECONOMY_MAP.md) · [PIPELINE](../en/PIPELINE.md)
