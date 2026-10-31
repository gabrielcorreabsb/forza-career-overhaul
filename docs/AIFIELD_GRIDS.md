# AIField — AI roster and custom grids (2026-10-30)

Found while investigating why series 20004 put only B-class classics into the
grid (Jag E-type, Shelby Daytona, Dino 246, AM DB4 GT, 250 GTO + C2 '67, 250LM,
Cobra 427), inherited from donor 11470.

Every fact below carries a status: **verified** (reproducible with
`python _tools\aifield_survey.py` or seen in game), **inferred** (follows from a
verified rule, not observed in game) or **to test** (open question, a kit
answers it). Do not promote an inferred fact to verified without a test log
entry at the end of this page.

## AI roster model (two targets)

1. **`AISelectableCars.Acceptlist` in `BuildersCupScheduleDataV4.json`**
   (CmsCache, applicable through the pipeline). It was `[]` in 20004.
2. **`AIField_117160001_Gen.xml`** — this one **actually pins the field**.
   Group `cfa7698c`, **never materialized in the CmsCache**; the game reads it
   from the install zip (`cfa7698cdd46663c19f66c30cbe63eba.zip`).
   `cache_edit.py` ignores this target (`grupo CFA7698C nao esta no cache`);
   `install_edit.py` writes it (see *Results*). That is why mc58 ships two
   plans: `plan.json` (full intent, 3 targets) and `plan_bcs.json` (BCS only —
   what `cache_edit.py` applies).

## Results (tested in game, 2026-10-30)

- **mc58 with the BCS alone did not change the grid** (still the 8 classics):
  the XML is what pins the field. *(verified)*
- **XML written to the install with `_tools/install_edit.py`**: the grid now
  uses the 23-car roster (the two substitutes, 2528 and 3534, showed up).
  *(verified)* The commands are in `docs/en/PIPELINE.md`.
  - It must update four places together: the zip entry, the install manifest
    (`faa126fd…`: logical entry + package), both `prod\<snapshot>` files and
    `cache-manifest.json` (re-encrypted).
  - The install denies DELETE to the user (only read/write), so the
    `os.replace` used by `cache_edit.py` fails with `WinError 5`;
    `install_edit.py` falls back to rewriting the file in place. The backup in
    `_backup\install_<ts>` covers a failure mid-write.
  - Steam "verify files" or a new server snapshot reverts it: run the tool
    again.
- **A700 cap (mc59)**: `ChampionshipEventData[65897913].TargetPI` 700 → 999
  in the BCS, both snapshots. The event now lists X999 and accepts a player car
  above 700 (BMW M4 '16 at PI 701, class S, in mc60 run 3). *(verified)*
- Plan B for the cap, not needed so far: `GameOptions_4716_*`
  (`CarClassId 4→8`, `PIMax 700→999`) — it contaminates donor event
  117160001, which uses the same PG.

## Document structure (vanilla survey, 645 files)

Source: `python _tools\aifield_survey.py` (reads the install zip; the entry
`AIField_117160001_Gen.xml` is excluded because our kits rewrite it).

| `AIDrivatarConfiguration Type` | files | how the field is built |
|---|---|---|
| `AIDrivatarTemplate` | 553 | PI window (`MinimumPI`..`MaximumPI`/`PIStep`) + `EligibleCars` fill `NumberOfDrivatars` slots |
| `AIDrivatarList` | 92 | explicit `Car` per slot, `TargetPI="-1"`; repeating a car weights it |

- Slots: 23 in 552 files; 46 in 83 (the list is written twice, see below); 24 in
  5; the rest are stubs. *(verified)* Vanilla never goes beyond 23 AI + the
  player = **24 cars**.
- Template windows, most common: `700-800/10` ×80, `800-900/10` ×76,
  `600-700/10` ×39, `400-500/10` ×25, `650-750/10` ×22; they go up to
  `900-998/10` ×20. *(verified)*
- Template `EligibleCars`: **1 to 22 cars** (most common 8–9, 94 files with 8),
  always fewer than the 23 slots — vanilla fills the slots by reusing cars.
  *(verified)* A pool larger than the slot count has **no vanilla precedent**
  *(to test, mc60)*.
- List documents: `<AIDrivatars>` appears **twice** (document root at indent 4,
  and inside `AIDrivatarConfiguration` at indent 6); `ContentManifest` has one
  `TargetPI=-1` row per distinct car; `EligibleCars` is a **separate, smaller
  subset** (`AIField_117150001_Gen.xml`: 7 of its 15 distinct cars). Its role is
  not proven. *(verified structure, unknown role)*
- Other fields: `AIDifficulty="NewRacer"`, `AIRubberBandingEnabled="False"` and a
  `BehaviorSettings` block, identical in both modes.
- Multi-class vanilla example: `AIField_117150001_Gen.xml` — D→S, 15 cars in 23
  slots (Monaco King Cobra S764, GT40 Mk II S708, Daytona Coupe A631, 250 GTO B593,
  Dino 246 D431…), each with its own `AI_<car>_<pi>` row.

## `AI_<car>_<pi>` ladders

Source: same script. Snapshot `20260923t185113xwyk`. *(verified)*

- 541 cars have `AI_` files; **508** are usable (in the catalogue, no
  always-active veto): E 22, D 69, C 45, B 59, A 75, S 93, R 87, P 52, X 6.
- Each car has a **ladder** of files, one per PI step: Nova SS 396 '69 334→699
  (38 files), M3 '91 331→599 (28), BRZ '13 331→699 (38), 911 GT3 RS 23 746→898
  (16), 911 GT2 RS 772→899 (14), Veyron SS 831→936 (12).
- 362 usable cars have a file ≥ 700; 156 have a ladder crossing 700. D/C ladders
  stop near 700, so a low car can be driven at a high PI if the window asks.
- **Game class scale** *(verified)*: E 0–300 · D 301–400 · C 401–500 ·
  B 501–600 · A 601–700 · S 701–800 · R 801–900 · P 901–998 · X 999. Class ids
  in `cars.json`: 0=E … 8=X. Evidence: in game PI 701 shows **S** and
  686/687/689 show **A**; the old event cap was `CarClassId=4` + `PIMax=700`
  (A700); and the lowest `AI_` file of each class falls inside the table (E
  214–293, D 288–383, C 359–471, B 441–571, A 531–670, S 638–785, R 742–863,
  P 828–962, X 966–999 — 362 of 541 cars match the table exactly).
- **Do not use `cars.json:pi` for classes.** It is on a different scale
  (only 300/541 cars match the table; D shows as 424–500, "S" from 686). The
  `AI_<car>_<pi>` file numbers **are** on the game scale, so the lowest file
  is about the car's real stock PI (BRZ '13: file 331 = a D car).
- Mapping rule (reproduces all 96 pairs of the original XML byte for byte):
  `TargetPI=-1` → the **lowest**-PI file; a window step → the highest-PI file
  `<= step`, clamped to the lowest. *(verified: file selection)*
  Expected consequence: cars whose ladder starts above the window (S/R/P) run
  **above it**; cars whose ladder ends below it are stuck at the top step.
  *(inferred — mc60 run 1 showed the 911 GT3 RS 23, lowest file 746, listed at
  PI 654, so the list shows the target PI, not the tune actually loaded)*

## Pool vs fixed list

| | template pool (`mc60`) | fixed list (`mc61`) |
|---|---|---|
| who is on the grid | up to `NumberOfDrivatars` of the `EligibleCars` | cars drawn from the list; **not** the literal slots (mc61 run 1) |
| PI of each AI car | player PI −50…−10, clamped by window and ladder | fixed per car (its `AI_` file PI +20…+77); multi-class D→R in one grid |
| variety per race | yes: the slots are drawn from the pool (mc60 run 2); run 1 was the mc58 roster, unexplained | yes: repeats and order differ from the list (mc61 run 1); to confirm in runs 2–3 |

- **verified (mc60, run 2)**: with a pool of 40 over 23 slots the game draws
  its AI cars from the whole pool: 8 of the 17 cars added after the mc58 roster
  showed up (GT-R NISMO '20, Vantage '19, 4C, 718 GTS, i8, NSX '17, MC12, WRX
  STI). A pool larger than the slots therefore works and gives a different
  grid per run. **Run 1 contradicts a plain random draw**: its 23 AI cars were
  exactly the 23 mc58 ids (one in ~10^10 by chance), most likely the game still
  held the previous XML. *(unexplained, to re-test after a fresh game start)*

- **verified (mc60, runs 1–3)**: the AI PI follows the **player's** PI, not the
  pool, and sits **10 to 50 below it**: player 668 → AI 619–656, player 678 →
  629–666, player 701 (S) → 652–689 (offsets −49…−12 every time). It matches the
  `AIProgressionFrame` with `PlayerPIRelativeToClass="100"` (`−50 … −10`), the
  last of the three frames in the XML (`40`: −40…+10, `80`: −40…0). The field
  is therefore always slightly weaker than the player and in the player's class
  (even a D-class BRZ '13 or M3 '91 is listed at 648–664, and a 701 S player
  still faces a field listed 652–689). A pool gives variety of cars, not of
  classes; the class of the grid is the class of the car you bring.
- **observed, not explained (mc60, runs 2–3)**: a car whose `AI_` ladder starts far
  above the listed PI (MC12, lowest file 723, listed 642) set an 8:08 lap, in
  the middle of a field of A-class cars (8:06–8:19). Pace seems to follow the
  target PI, not the lowest file; so the "S/R/P run above the window" claim is
  not supported so far.
- **verified (mc61, run 1)**: a fixed list gives a **real multi-class grid**,
  independent of the player's class. Player Toyota GR86 '22 (C, PI 404) faced
  S (737, 722, 731, 783), R (801), A (657, 608, 678), B (507), C (462, 405) and D
  (354) cars in one grid. Each car is listed at a **constant** PI (Nova '69 354
  five times, GT-R NISMO 722 three times), which is its lowest `AI_` file PI plus
  20–77 (Nova 334→354, RX-7 426→462, S2000 375→405, WRX 479→507, M3 '10 628→657,
  C8 637→678, 911 GT3 '21 706→737, GT-R NISMO 699→722, NSX 698→731, GT3 RS 23
  746→783, M-AMG GT 775→801, 718 GTS 531→608). The class/PI ladder therefore
  comes from the car, not from the player.
- **verified (mc61, run 1)**: the list is **not** followed literally. Cars
  repeat beyond their listed weight (Nova ×5, GT-R NISMO ×3, S2000 ×2, 718 GTS
  ×2, NSX ×2; the list has each once) and the order differs, while cars
  listed twice (BRZ '13, Civic, RX-7) are missing or single. The slots seem
  to be **drawn at random from the listed cars** each time. Needs runs 2–3.
- **to test (mc61)**: does the listed PI stay the same with a different player
  car (expected: yes, the list has no progression frames)?

## PI band model (template documents)

- Every drivatar draws its target PI inside `[player + lower, player + upper]`,
  then the window clamps it to `MinimumPI..MaximumPI` and the car's own ladder
  clamps it again (below the lowest file → the lowest file, above the highest →
  the highest). *(verified from 3 runs: offsets −49…−12 inside −50…−10)*
- The XML has three frames keyed by `PlayerPIRelativeToClass` (40/80/100):
  `40: −40…+10`, `80: −40…0`, `100: −50…−10`. All 3 runs (player PI 668–701)
  used the last one. What the key measures is unknown, so any experiment should
  set all three frames equal.
- Vanilla survey: 133 distinct frame sets in 553 templates; the widest band is
  60 wide (`−60…0`); common sets are the mc58 one (146 files) and
  `−20/−20/−30 … +10/0/−10` (63). Nothing vanilla comes close to a band of 250+,
  so a wide band is *to test*.
- Because the class of an AI car comes from its ladder clamps, a pool that spans
  E→P keeps its real classes even under a narrow band for the cars whose
  ladders sit outside it (a P car is always ≥ 828).
- **verified (mc60, run 1)**: the game accepts a pool of 40 and a 500–800
  window (no CMS error); the grid is 24 cars (23 AI + the player).
- **to test**: a fresh-start run of mc60 (does run 1's mc58-like grid come
  back?); whether the draw ever repeats a car (none seen in runs 2–3); what
  `EligibleCars` does in list mode (mc61); whether list mode ignores the
  player's PI (it has no progression frames).

## Final roster of 20004 (mc58, applied 2026-10-30)

AI = 20 player entries + 3 substitutes (player untouched, 23 originals):

| pos | original | substitute | reason |
|---|---|---|---|
| 3 | 2628 BMW M4 '16 | **2528** 911 GT3 RS '16 | 2618 GT-R '17 (first option) has **no `AI_` file at all** → fallback from the user list |
| 14 | 3129 Ren. Megane '08 | **3534** MINI JCW GP '21 | approved (31 `AI_` files) |
| 20 | 3761 Toyota GR86 '22 | **3735** Subaru BRZ '22 | approved (22 `AI_` files) |

`ContentManifest` covers 23/23 (276 entries, 0 dangling — hard-fail assert in the
generator). Window `600..700/10`. Cars with no file ≤ 700
(3781/3667/2654 + 2528) run above the window; 642/3533/3678 are stuck at the
lowest step. Possible change: 2528→3071 (M5 '18, inside the window).

## Building a grid with `fmlib.aifield`

`_tools/fmlib/aifield.py`; `_tools/test_aifield.py` proves it reproduces the mc58
XML and vanilla `117150001` byte for byte.

1. Pick the cars; `aifield.ai_files(aifield.manifest_files(Cache()))` gives the
   ladders; `aifield.validate(roster, by_car)` checks catalogue, vetoes and
   `AI_` coverage (an empty error list is required).
2. Template: `rewrite_template(base, roster, by_car, window=(min, max, step))`.
   List: `rewrite_list(base_list_doc, lineup, by_car, eligible=...)` with a
   vanilla list document as the layout.
3. `encrypt_for_install(text, current_enc, workdir)` — the cipher template is
   the **current payload of the entry in the install zip** (the group is not in
   the CmsCache); get it with `read_entry("AIField_117160001_Gen.xml")`.
4. Write `patches/<kit>/XML.AIField_117160001_Gen.enc` + the kit's notes file; apply with
   `install_edit.py --dry-run`, then `--verify` (game closed). To revert, apply
   the previous kit's payload.
5. Composition rules used so far: D→R, at most one car per make per class, mixed
   eras, the 23 mc58 cars kept in the pool.

## Rosters

- **mc60 — template pool, 40 cars, window `500..800/10`, 23 slots.** The 23 mc58
  ids plus 1655, 1429, 1009, 424, 2357, 2168, 2038, 3117, 2133, 3091, 2352,
  2289, 3622, 391, 2755, 3227, 3616 (D 4, C 7, B 9, A 9, S 8, R 3). Applied;
  the game draws 23 of the 40 per run — see the test log.
- **mc61 — fixed list, 23 slots, 18 distinct cars.** 3781, 1655, 2870, 424,
  3667, 1429, 1598, 2357, 2755, 1009, 3117, 2352, 1655, 3369, 424, 3227, 2005,
  2870, 3622, 2168, 3616, 3667, 1598 (1655, 2870, 424, 3667, 1598 twice). Runs
  only after the mc60 test. Both kits write the same entry: one is active at a
  time.

Per-car names, classes and PI are in each kit's the kit's notes file.

## Test log

One entry per run: kit, date, player car/PI, grid seen, number of cars, CMS
errors, conclusion.

- **mc60, run 1 (2026-10-30)** — player Porsche Cayman, PI 668 (A). Grid of 24.
  AI cars: the 23 mc58 ids exactly (M2 '23, S2000 '09, Supra '20, MX-5 '16,
  BRZ '22, M3 '97, M3 '91, M3 '05, 911 GT3 RS 23, 911 GT3 '07, Civic '18,
  Cayman, 911 GT3 RS '16, i30 N, M3 '10, M3 '21, MINI JCW GP, AMG GT R, C8,
  911 GT3 '21, TT RS, A110, Golf R), all class A, PI 619–656. None of the 17
  new cars. No CMS error. The AI PI tracks the player's PI. (An earlier
  reading of this run — "the pool excess is ignored" — was wrong; see run 2.)
- **mc60, run 2 (2026-10-30)** — player Chev. C8 '20, PI 678 (A). Grid of
  24, AI PI 629–666, all class A. AI cars seen (all 23): M2 '23, GT-R NISMO
  '20*, M3 '05, Vantage '19*, M3 '97, 4C '14*, Supra '20, 718 GTS '18*, BRZ
  '22, S2000 '09, M3 '91, i8 '15*, 911 GT3 RS '16, Civic '18, Cayman, 911 GT3
  '07, TT RS '20, NSX '17*, MC12 '04*, C8 '20 (a second C8 besides the player),
  M3 '10, WRX STI '15*, Golf R '22 (* = not in the mc58 roster). Conclusion: the
  pool is drawn per run; AI PI follows the player. Lap times in the first
  lap: A-class cars 8:06–8:19, MC12 8:08.

- **mc60, run 3 (2026-10-30)** — player BMW M4 '16, **PI 701 (S)**. Grid of 24,
  AI PI 652–689, all listed class A. 23 distinct AI cars, 9 of them from the 17
  added after mc58: BRZ '13, 718 GTS '18, M-AMG GT '20, GT-R NISMO '20, NSX '17,
  911 Turbo '14, MC12 '04, WRX STI '15, Ferrari 488 (Pista). Grid differs from
  runs 1–2. Conclusions: the draw is confirmed (3 runs, one session; run 1 still
  odd); the cap above 700 is gone (an S car entered); AI PI stays 10–50 below
  the player.

- **mc61, run 1 (2026-10-30)** — player Toyota GR86 '22, PI 404 (C). Grid of 24.
  AI cars seen (23): 911 GT3 '21 ×2 (737), GT-R NISMO '20 ×3 (722), M3 '10 ×2
  (657), RX-7 '97 (462), Nova '69 ×5 (354), S2000 '09 ×2 (405), 718 GTS '18 ×2
  (608), M-AMG GT '20 (801, R), 911 GT3 RS 23 (783), WRX STI '15 (507), NSX '17 ×2
  (731), C8 '20 (678). Classes D, C, B, A, S, R in one grid. No CMS error.
  Conclusions: multi-class grid works; PI is fixed per car; the list is a
  weighted/random source, not a literal lineup. Runs 2–3 pending.

- **mc63, run 1 (2026-10-30)** — player Toyota GR86 '22, PI 404 (C). Grid of 24.
  AI listed PI **310–637** (23 values, roughly uniform), classes D 4, C 8, B 6,
  A 5: 310 315 345 353 | 417 422 427 459 464 464 465 473 | 543 543 544 552 559
  573 | 610 615 622 626 637. Cars (12 distinct): Nova '69 ×5, GT-R NISMO ×3,
  718 GTS ×2, M3 '10 ×2, S2000 ×2, NSX ×2, 911 GT3 '21 ×2, RX-7, WRX STI, GT3 RS
  23, C8, M-AMG GT. No CMS error. Conclusions: (1) the **wide band works**:
  `404 + [−350, +250]` ∩ window `[300, 980]` = `[300, 654]`, observed `[310, 637]`;
  (2) **no pile-up at the floor** (a clamp would put ~40% of the drivers at 300,
  none did), so the draw is restricted to band ∩ window; (3) the PI is **per
  driver, not per car** (the same Nova at 315, 464, 543, 615, 622); (4) **the car
  multiset is exactly mc61 run 1's** (Nova ×5, GT-R ×3, …, all inside the mc61
  lineup, none of the 56-car pool's new cars), with the order and the PIs new:
  the first race after an install change reuses the previous grid's cars (as
  mc60 run 1 reused mc58's) while the PI is recomputed — treat run 1 as a warm-up
  (*hypothesis, re-test with runs 2–3*); (5) the listed PI is the **target**, not
  the tune: an M-AMG GT '20 (lowest file 775) is listed D 310 and a C8 (637) D 345.

- **mc63, run 2 (2026-10-30)** — player BMW M4 '16, PI 701 (S). Grid of 24.
  AI listed PI **368–931**, **7 classes** in one grid: P 3 (931, 923, 904), R 4
  (897, 886, 877, 814), S 5 (791, 778, 765, 764, 763), A 5 (645, 631, 629, 629,
  621), B 2 (558, 550), C 2 (441, 427), D 2 (376, 368). Predicted band
  `701 + [−350, +250] = [351, 951]`, observed `[368, 931]`. 23 **distinct** cars,
  no repeats, drawn from the whole 56-car pool (new ones seen: Agera, Jesko,
  BT62, Centenario, Scirocco '81, STI S209, Valkyrie). No CMS error. Conclusions:
  the band follows the player at both ends (C 404 → 310–637, S 701 → 368–931),
  so the grid is **dynamic and as diverse as the pool**; run 1 was the warm-up
  (it reused mc61's cars), run 2 is a fresh draw. Caveat: the listed class is
  the *target* — a BMW M2 '23 listed P 923 and a M3 '91 listed P 931 cannot load
  a tune that high (their ladders end near 800 and 599); on-track pace still to
  be checked.

- **mc63, run 3 (2026-10-30)** — player Chev. C8 '20, PI 678 (A). Grid of 24.
  AI listed PI **345–908**, 7 classes: D 1 (345), C 2 (418, 404), B 4 (598, 544,
  535, 527), A 4 (622, 608, 606, 606), S 6 (791, 768, 755, 742, 741, 740), R 5
  (900, 881, 874, 863, 854), P 1 (908). Predicted band `678 + [−350, +250] =
  [328, 928]`, observed `[345, 908]`. 23 distinct cars, no repeats (a second C8
  among them). No CMS error. The listing again shows the target, not the tune: a
  Porsche 962C (lowest file 936) is listed B 535, a BMW M3 '91 (highest file 599)
  is listed P 908. **Three runs, three player classes (C 404, A 678, S 701):
  the band follows the player every time and the grid spans 4–7 classes.**

- **mc63, pace (user report, 2026-10-30)** — on track the pace was good: the
  cars open gaps on each other, with the vanilla `CatchUp/SlowDown` flags left
  on. No lap-time table was recorded (kept as an open item).

## Next

Guides by area: [CAREER_BASICS](guides/CAREER_BASICS.md) (common career),
[CUSTOM_RACE](guides/CUSTOM_RACE.md) (multi-class grids in any series),
[CIRCUIT_EXPERIENCE](guides/CIRCUIT_EXPERIENCE.md) (trackday 20004) and the
findings log [DISCOVERIES](guides/DISCOVERIES.md).

Next kits: `mc63` — an E→P pool with a wide `AIProgressionFrame` band and a
200–998 window (`mc62` is taken by another experiment), then the behaviour
flags experiment; grids above 24 cars only after those (separate, reversible kit).
