# Discoveries — what we learned and what it unlocks

> **Area: all three.** The running log of what we learned, with its evidence and
> status, plus what each finding makes possible. Read next the guide for your
> area: [CAREER_BASICS](CAREER_BASICS.md) (common career),
> [CUSTOM_RACE](CUSTOM_RACE.md) (multi-class grids in any series),
> [CIRCUIT_EXPERIENCE](CIRCUIT_EXPERIENCE.md) (the series 20004 trackday).

Status labels: **verified** (seen in game or reproduced by a script),
**inferred** (follows from a verified rule), **to test**. Numbers come from
`python _tools\aifield_survey.py` and the *Test log* in
[AIFIELD_GRIDS](../AIFIELD_GRIDS.md).

## In short

| # | finding | status | detail |
|---|---|---|---|
| 1 | The CmsCache is what the game reads at runtime; the install is only a seed | verified | §1 (D1) |
| 2 | A blob can be rewritten in place: keep the name, update `Size` + `Checksum`, re-encrypt with the current payload as template (Strategy S) | verified | §1 (D2–D4) |
| 3 | Content the cache never holds — the AI grid XML — can be edited in the install zip, if the zip, the install manifest and both snapshots move together | verified | §1 (D5) |
| 4 | The AI grid is pinned by the `AIField` XML, not by the series' car list (`AISelectableCars` alone changes nothing) | verified | §1 (D9) |
| 5 | Two grid modes: a **pool** whose difficulty follows the player's car, and a **fixed list** that pins the classes whatever the player drives | verified | §1 (D13, D18, D21) |
| 6 | **209 of 711** cars appear in no acceptlist, and E (31/50) and D (50/106) are the worst served — the entry classes are the gap | verified (audit) | §2, [CAREER_AUDIT](../CAREER_AUDIT.md) |
| 7 | Still open: a lap-time table per class, grids above 24 cars, and whether a fixed list reacts to the player's PI | to test | §3, [OPEN_QUESTIONS](../OPEN_QUESTIONS.md) |

## 1. Discoveries

### Platform and pipeline

| # | finding | status | evidence | unlocks |
|---|---|---|---|---|
| D1 | The CmsCache is the runtime source; the install is only a seed | verified | [ADR-004](../decisions/ADR-004_install_vs_runtime.md) | edit one copy, with a small blast radius |
| D2 | Strategy S: keep the blob name, update only `Size`+`Checksum` | verified | [ADR-001](../decisions/ADR-001_strategy_s.md) | in-place edits the game accepts |
| D3 | Entries are matched by `Checksum`, never by name/mtime (two snapshots) | verified | [ADR-002](../decisions/ADR-002_checksum_mapping.md) | kits that hit the right blob |
| D4 | Re-encrypt with the **current** payload as template | verified | [ADR-005](../decisions/ADR-005_cipher_template.md) | untouched entries stay byte-identical |
| D5 | Groups the cache never holds (the AIField XML) can be edited in the install zip, if the **zip, install manifest, both `prod\` files and `cache-manifest.json`** move together | verified | mc58 XML; `install_edit.py` | any install-only content: AI grids, and likely others |
| D6 | The install denies DELETE to the user, so renames fail with `WinError 5`; rewriting in place works | verified | `install_edit.py` first apply | the tool needs no admin rights |
| D7 | Steam "verify files" or a new snapshot undoes install edits | inferred | design of the install | re-run the tool; kits stay versioned |

### Series and career

| # | finding | status | evidence | unlocks |
|---|---|---|---|---|
| D8 | Event `TargetPI` / `ClassRestriction` are the real caps; the override value was ignored | verified | A700 cap, mc59; S 701 entered | open any series to higher classes |
| D9 | `AISelectableCars` alone does not change the AI grid | verified | mc58 BCS-only run | stop editing the wrong file |
| D10 | Acceptlist ≤ 23; suggested car = lowest CarId | verified | mc49–mc52 | predictable "you do not own" prompts |
| D11 | New series need fresh ids (≥ 20000 / 65897900–65899999) and a `BCSeriesSelectableCars` block | verified | F3 | safe custom series with `build_series.py` |
| D12 | Poster/banner/intro come from the donor series | verified | lab diagnostics | proper art per series |

### AI and grids

| # | finding | status | evidence | unlocks |
|---|---|---|---|---|
| D13 | Two AIField modes: template (553 files) and fixed list (92) | verified | `aifield_survey.py` | choose the kind of field per series |
| D14 | Vanilla: 522 template events, 85 list events in 23 series; pools of 1–22 cars, 23 slots, max grid 24 | verified | survey + BCS | known safe envelope |
| D15 | Each car has an `AI_<car>_<pi>` ladder (541 cars, 508 usable); `-1` → lowest file, window step → highest ≤ step | verified | 96 vanilla pairs byte for byte | build any manifest by rule |
| D16 | Class scale E 0–300 … P 901–998, X 999; `cars.json:pi` is on another scale | verified | prints (701 = S, 689 = A), `CarClassId 4`/`PIMax 700`, 362/541 | classes that match the game |
| D17 | Lowest `AI_` file ≈ the car's real stock PI | verified (data) | per-class bands | pick cars by true class |
| D18 | Template AI PI = player PI −50…−10 (frame 100) | verified | 3 runs, player 404–701 | difficulty that follows the player |
| D19 | A pool bigger than the slots is drawn from, a different grid per run | verified | mc60 runs 2–3 | variety without more slots |
| D20 | The first race after an install change reuses the previous grid's cars while the PI is recomputed (mc60 run 1 = mc58's cars; mc63 run 1 = mc61 run 1's car multiset) | inferred (3 cases; mc63 run 2 was a fresh draw) | mc60 run 1, mc63 runs 1–2 | treat run 1 after a change as a warm-up |
| D21 | A fixed list gives a real multi-class grid D→R regardless of the player's car | verified | mc61 run 1 (C 404 player) | trackday, endurance, themed events |
| D22 | Listed PI per car is constant and = lowest file + 20…77 | verified | mc61 run 1 | predict a list's PIs |
| D23 | The game draws from the list: repeats exceed the listed weights, order differs | verified once | mc61 run 1 | weights are a bias only |
| D24 | The list ignores the player's PI | to test | needs a second player car | confirm static fields |
| D25 | A wide `AIProgressionFrame` band (−350…+250) and a 300–980 step-20 window are accepted; the PI follows the player: C 404 → 310–637 (4 classes), A 678 → 345–908 (7), S 701 → 368–931 (7), no pile-up at the floor, 23 distinct cars from the 56-car pool | verified (3 runs, 3 classes) | mc63 runs 1–3 | PI dynamic **and** diverse; difficulty dial per series |
| D25b | Grids above 24 cars | to test | no vanilla precedent | bigger fields |
| D27 | The listed PI is the target, not the tune loaded (M-AMG GT '20 listed D 310, lowest file 775; Porsche 962C listed B 535, lowest 936) | observed | mc63 runs 1 and 3 | the car, not the label, sets the pace (see D26); a lap-time table is still to record |
| D26 | With the vanilla flags (`EnableDifficultyCatchUp/SlowDown` = `True`) the pace is **not** flattened: faster cars pull away from slower ones | observed (user report, mc63) | in-game play, no lap table | no flag change needed; real class gaps |

## 2. How this helps the Career Overhaul

1. **A field per series, not one recipe.** Any series can be pointed at a pool
   (hardness follows the player) or a list (classes pinned). 23 vanilla series
   already use a list, so the format is proven. (D13, D14, D21)
2. **Difficulty curve by design.** The frame band (`−50…−10` today) is the dial:
   a lower band for early leagues, up to `+10` for late ones, without changing
   cars. (D18, D25)
3. **FM4-style progression, built from data.** `build_series.py` plus per-series
   class limits and acceptlists lets each league target one class of the official
   scale (D → X), with the AI matching it. (D8, D10, D11, D16)
4. **Themed multi-class events.** Trackday, endurance and showcase events use a
   list with weights; the classes come from the cars. (D21, D22)
5. **No hidden caps.** Check the event's `TargetPI`/`ClassRestriction` first;
   one number held the whole series at A700. (D8)
6. **Reusable, reversible tooling.** `fmlib.aifield`, `install_edit.py` and
   `aifield_survey.py` build, validate, apply and undo any AIField, with catalogue,
   veto and `AI_` coverage checks. (D5, D6, D15)
7. **Honest limits.** Install edits can be undone by Steam (re-apply); 24 cars on
   the grid; each car needs `AI_` files; a list does not scale with the player.
   (D7, D14, D23)
8. **Suggested next kits.** mc63 wide-band E→P pool → flag experiment for real
   class pace → pilot the pattern on 2–3 ordinary series → grids above 24.
   (D25, D26)

## 3. Open for future optimization

The grid work is closed for now (mc63 active). Left on the table:

1. **Lap-time table per listed class** to turn D26/D27 from observed into measured.
2. **Pool curation**: weights, cars that rarely suit a trackday, more E/P cars; per-class pools.
3. **Band shape**: asymmetric bands, a per-series difficulty dial, and what
   `PlayerPIRelativeToClass` really measures (all three frames are equal today).
4. **Window/step**: step 10 instead of 20 (3570 manifest rows), and the window edges.
5. **Grids above 24 cars** and the role of `EligibleCars` in list documents.
6. **List mode with other player cars** (mc61): do the listed PIs ever move?
7. **Behaviour flags** (`BehaviorSettings`) only if the pace ever flattens.
8. **Pilot on ordinary series**: apply a pool/list to 2–3 vanilla series.
9. Housekeeping: Steam "verify files" or a new snapshot reverts the install (re-apply).

## 4. Where each thing lives

| topic | doc |
|---|---|
| model, ids, what to touch | [CAREER_BASICS](CAREER_BASICS.md) |
| modes, classes, band, recipe, protocol | [CUSTOM_RACE](CUSTOM_RACE.md) |
| series 20004, kits, switching grids | [CIRCUIT_EXPERIENCE](CIRCUIT_EXPERIENCE.md) |
| raw survey numbers, per-run test log | [AIFIELD_GRIDS](../AIFIELD_GRIDS.md) |
| symptom → cause → fix | [TROUBLESHOOTING](../TROUBLESHOOTING.md) |
