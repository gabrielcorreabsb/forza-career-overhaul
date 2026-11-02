# Discoveries — what we learned and what it unlocks

> **Area: all three.** The running log of what we learned, with its evidence and
> status, plus what each finding makes possible. Read next the guide for your
> area: [CAREER_BASICS](../guides/CAREER_BASICS.md) (common career),
> [CUSTOM_RACE](../guides/CUSTOM_RACE.md) (multi-class grids in any series),
> [CIRCUIT_EXPERIENCE](../guides/CIRCUIT_EXPERIENCE.md) (the series 20004 trackday).

Status labels: **verified** (seen in game or reproduced by a script),
**inferred** (follows from a verified rule), **to test**. Numbers come from
`python _tools\aifield_survey.py` and the in-game runs summarised in
[AI_GRIDS](../guides/AI_GRIDS.md) (the per-run log stays in the maintainer's lab).

## In short

| # | finding | status | detail |
|---|---|---|---|
| 1 | The CmsCache is what the game reads at runtime; the install is only a seed | verified | §1 (D1) |
| 2 | A blob can be rewritten in place: keep the name, update `Size` + `Checksum`, re-encrypt with the current payload as template (Strategy S) | verified | §1 (D2–D4) |
| 3 | Content the cache never holds — the AI grid XML — can be edited in the install zip, if the zip, the install manifest and both snapshots move together | verified | §1 (D5) |
| 4 | The AI grid is pinned by the `AIField` XML, not by the series' car list (`AISelectableCars` alone changes nothing) | verified | §1 (D9) |
| 5 | Two grid modes: a **pool** whose difficulty follows the player's car, and a **fixed list** that pins the classes whatever the player drives | verified | §1 (D13, D18, D21) |
| 6 | **209 of 711** cars appear in no acceptlist, and E (31/50) and D (50/106) are the worst served — the entry classes are the gap | verified (audit) | §2, [CAREER_AUDIT](CAREER_AUDIT.md) |
| 7 | Still open: a lap-time table per class, grids above 24 cars, and whether a fixed list reacts to the player's PI | to test | §3, [OPEN_QUESTIONS](OPEN_QUESTIONS.md) |
| 8 | A **custom single-car roster** works by overwriting an existing, unused roster document; a brand-new file with an invented `Id` is rejected (the game goes offline) | verified / observed | §1 (D35, D36) |
| 9 | The career has **no data switch for a real Qualifying** (tested through the session generator, the practice limit type, series rules and field size) | observed | §1 (D33) |

## 1. Discoveries

### Platform and pipeline

| # | finding | status | evidence | unlocks |
|---|---|---|---|---|
| D1 | The CmsCache is the runtime source; the install is only a seed | verified | [ADR-004](decisions/ADR-004_install_vs_runtime.md) | edit one copy, with a small blast radius |
| D2 | Strategy S: keep the blob name, update only `Size`+`Checksum` | verified | [ADR-001](decisions/ADR-001_strategy_s.md) | in-place edits the game accepts |
| D3 | Entries are matched by `Checksum`, never by name/mtime (two snapshots) | verified | [ADR-002](decisions/ADR-002_checksum_mapping.md) | kits that hit the right blob |
| D4 | Re-encrypt with the **current** payload as template | verified | [ADR-005](decisions/ADR-005_cipher_template.md) | untouched entries stay byte-identical |
| D5 | Groups the cache never holds (the AIField XML) can be edited in the install zip, if the **zip, install manifest, both `prod\` files and `cache-manifest.json`** move together | verified | mc58 XML; `install_edit.py` | any install-only content: AI grids, and likely others |
| D6 | The install denies DELETE to the user, so renames fail with `WinError 5`; rewriting in place works | verified | `install_edit.py` first apply | the tool needs no admin rights |
| D7 | Steam "verify files" or a new snapshot undoes install edits | inferred | design of the install | re-run the tool; kits stay versioned |
| D36 | **A new CMS entry with an invented `Id` is rejected**: with a brand-new AI roster file added to the zip, both snapshots and the manifests, the other series opened normally but opening the event that used the file put the game **offline**. Changing an existing entry's bytes (same `Id` and name) works. Hypothesis: the client asks the server for files whose `Id` it does not know | observed (n=1) | roster file added by a purpose-made tool, event pointed at it; rolled back in cache-then-install order | edit existing entries only; custom content needs an existing slot (D35) |

### Series and career

| # | finding | status | evidence | unlocks |
|---|---|---|---|---|
| D8 | Event `TargetPI` / `ClassRestriction` are the real caps; the override value was ignored | verified | A700 cap, mc59; S 701 entered | open any series to higher classes |
| D9 | `AISelectableCars` alone does not change the AI grid | verified | mc58 BCS-only run | stop editing the wrong file |
| D10 | Acceptlist ≤ 23; suggested car = lowest CarId | verified | mc49–mc52 | predictable "you do not own" prompts |
| D11 | New series need fresh ids (≥ 20000 / 65897900–65899999) and a `BCSeriesSelectableCars` block | verified | F3 | safe custom series with `build_series.py` |
| D12 | Poster/banner/intro come from the donor series | verified | lab diagnostics | proper art per series |
| D28 | Race length comes from the **override**, not the event (both directions) | verified | bench series, 2 runs | write laps once, in the right field |
| D29 | The cap a player sees comes from the **event's** `TargetPI`; the override's class restriction did not apply | verified | bench series, before/after raising the event value | open or close a series by one value |
| D30 | **Qualifying through practice**, with two separate rules: limited practice laps + the series' qualification options produce a limited, timed session and no separate qualifying screen; the race grid then lines the **AI** up in practice-classification order, while the **player's** slot comes from the **Challenge the Grid wager** — with the wager screen on, it suggests a start position of its own and the slot the player picks there is the slot he starts from; with the screen off the slot falls back to a per-event constant that ignores his practice time | **observed** for the practice/AI half (n=2: one run on the live baseline, one with the wager screen switched back on); **verified** for the player half (n=1: a control pick away from the suggestion was honoured in full, and the AI kept the practice order) | bench series: the practice classification and the race grid read side by side; then the same event with the wager screen on, reading the suggested slot, picking another one and watching the start | a real qualifying weekend for the AI order; the wager as the lever for the player's slot; the suggestion itself is a constant (the middle slot of a 24 grid) that did not follow the player's best lap, the car or the wager block ([OPEN_QUESTIONS](OPEN_QUESTIONS.md) 16) |
| D33 | **No career data field turns on a real Qualifying.** The client has a Qualification event activity (own cinematic, report and provisional-grid screens, a Qualify pre-race entry) but the career runs without it; the practice limit type `Disabled`, a series-level rules reference, the series field size, the AI roster document and the generator's grid shape all had **no effect** in the career | **observed** (four one-field tests, each applied and read back; n=1 each) | one field per test on the bench series, applied to the live cache and read back after the run | stop hunting a data lever for the qualifying: the practical routes are the wager-based recipes ([MOD_TOOLKIT](../en/MOD_TOOLKIT.md)) |
| D31 | The client reads its **feature flags** from the cache; one flag removed the Challenge the Grid wager screen that the cup data could not | verified | one flag, n=1 | screens and modes switched by one value |
| D34 | The **start type** (standing or rolling) comes from the session generator's attribute, not from the series flag for a slot-car start; the override's race block can carry the same attribute (about a third do, 31 disagree with their generator), and **that override value beats the shared generator** | generator part observed (two bench series, one run each); override part **verified** (n=1: a twin pair identical but for `FeatureRace._321Type = "Rolling"` — the one with the key started rolling, the other standing) | the series on a rolling generator rolled; the one with the flag on but a standing generator started standing; the pair differing by one key split rolling/standing | the start type is a choice **per event** by one override field, no generator edit needed ([RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.8, lever table §2.16) |

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
| D32 | No Featured, Rivals or Meetup generator cites a career AI field document; the career's race generators share no id with Featured | verified (data) | lab survey | career-only grid and session edits |
| D26 | With the vanilla flags (`EnableDifficultyCatchUp/SlowDown` = `True`) the pace is **not** flattened: faster cars pull away from slower ones | observed (user report, mc63) | in-game play, no lap table | no flag change needed; real class gaps |
| D35 | **A custom roster works**: writing a single-car roster (23 slots of one model, window and a narrow band around the player's PI) over an existing roster document that no reachable series uses gave a lobby of 23 cars of that model — the Subaru BRZ '22 (class C) in one series and the Porsche 911 GT3 RS '23 (class S) in another, each series on its own document. One roster per document; any number of events can share it. A car needs AI tune files to be eligible (the Toyota GR86 '22 has none; its twin BRZ '22 has 22) | verified (2 documents, 2 series, lobby read in game) | lobby of series 20009 and 20010 | spec races and any per-series grid; `build_aifield.py` + `install_edit.py` ([AI_GRIDS](../guides/AI_GRIDS.md) §6) |
| D37 | The override's `AIFileName` **chooses the roster document** of an event (the lobby changed when the event was pointed at the custom document) | verified (n=1; an earlier swap to a similar vanilla document looked inert, probably the warm-up of D20) | series 20009 lobby before/after | per-event rosters through a one-field cache edit |
| D38 | **The AI's distance from the player is set by the roster document's band table**: the frame whose key is the highest one not above (player PI − the document's `MinimumPI`) applies, clamped to the window. The event's `TargetPI` does **not** cap the AI (an event with a 300 cap met AI at 400–412) | observed (3 runs, 2 documents) | player 404 vs minimum 320 → AI 354–394; player ≈406 vs minimum 400 → AI 400–412 | keep the AI in the player's class by choosing the window floor and a narrow band |
| D39 | The class badge in the lobby is the car's **real** class, the number is the target PI: a roster whose cars have a lowest AI tune above the window floor lists B cars at 400–412 and they run at their lowest (B) tune | observed (lobby capture: 5 of 13 badges B at PI 400–412) | 17 of 21 cars of that roster have a lowest tune above 412 | pick roster cars whose lowest tune is at or below the window floor |
| D40 | The roster document carries its **own** behaviour flags (catch-up, slow-down, proximity, position spread, slot-car start) for the race and for practice — the same set as the series' AI-behaviour block. Which one wins is untested; one vanilla document used in a bench series had them on while the series had them off | hypothesis | document read, one inconclusive race | a second place to switch the rubber band off |
| D41 | A mirror grid with a −10…+10 band is **not** even when the player sits below the window ceiling: two cars well ahead, then a pack to about 12th and a second pack behind. With the player's car raised to the ceiling (PI 800, window maximum 800) the whole field landed between 792 and 800 and the grid was balanced — so the spread was the **PI spread** of the band, not driver skill | observed (two races, user reports) | series 20010 at the player's PI 756, then at 800 | a spec race is fairest with the event cap equal to the window maximum and the player at the cap; a 0…0 band should give the same at any PI (to test) |
| D42 | **`FeatureRace.Pits = 1` makes the stop mandatory for the AI as well.** On a 2-lap race many AI cars were disqualified for not making it; on a 4-lap race all 24 cars stopped (22 once, 2 twice) and nobody was disqualified for it | observed (one run each; no 4-lap control with `Pits 0`, so stops driven by tire wear are not ruled out) | the 2-lap and 4-lap bench pair, identical but for the laps | a mandatory stop needs a race long enough to fit it (4 laps worked); a short race with `Pits ≥ 1` is a way to disqualify the AI ([RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.6, §2.16) |
| D43 | **A session generator's grid options set the human's start slot, and only `AIDriverRank` moves it.** With `GridOrderingType = AIDriverRank`, `ClusterHumansAtIndex` acts as a **cut**, not a position: index 0, 2 and 5 put the player **1st**; index 11 and 23 put him **24th (last)**, and a fast practice lap did not move the 24th. With `Qualifying` and index 2 the slot was **fixed from the start of practice (7th)** and the index did not move it. The same **7th** came back with `Qualifying` and index 10 in the Racers Cup generator at another track (class R car, any lap), and on the old test oval: a constant of the `Qualifying` path. The AI order does not follow lap time under `AIDriverRank`. The wager screen's pick is overridden in every case | observed (n=1 per series; index 2 on the 20012 bench n=3; P1 held with a slow lap (index 5) and the 7th held with the best lap; the cut lies between 5 and 11) | a bench of six single-field series on six generators: indices 0, 2, 5 → 1st; 11, 23 → 24th; `Qualifying` + 2 → 7th fixed | a per-event start slot without the wager screen, and **a forced "start last and overtake"** (index ≥ 11, to repeat); finding where the cut lies (6–10) is next ([OPEN_QUESTIONS](OPEN_QUESTIONS.md) 16) |
| D44 | **A session generator's car restriction is enforced in the career.** The Racers Cup generator 59107 carries a strict class-R bucket (`CarRestrictions` class R, `Strict`): an event on it gave "no valid car" to a class C car that the series' own acceptlist allowed, and the same event design with class R cars (PI cap 900, class ceiling R) accepted a class R Porsche, which then started 7th whatever the lap | observed (n=1 pair: one refusal, one acceptance; the pair also differs in the PI cap and the AI document, but the C car sat under both caps) | the 20020 (C car, refused) against the 20040 (R car, accepted), same generator | a Racers Cup event can be reproduced in the career if its class bucket is respected (cars of that class, matching cap); the generator, not the series, decides which cars enter ([RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.13) |
| D45 | **An AI document with an empty driver list does not make a solo race: the event opens and the practice runs, but the race session crashes the game.** `MaxAIPlayers = 0` on the series and on the generator had done nothing in earlier runs; pointing the override at a vanilla document whose list is empty removed the AI from the practice, and the race then crashed | observed (n=1; where exactly it crashed — grid, start or first lap — was not recorded) | a bench event identical to the class-R Racers Cup one but with an AI document of 0 drivers: it opened at Daytona with the same car, the practice ran, the race crashed | the race session needs at least one AI driver (hypothesis); a solo event would need a document with a minimal roster, not an empty one; **do not use an empty-list document for a race** ([RACE_SYSTEM](../reference/RACE_SYSTEM.md) §2.16) |

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
| model, ids, what to touch | [CAREER_BASICS](../guides/CAREER_BASICS.md) |
| modes, classes, band, recipe, protocol | [CUSTOM_RACE](../guides/CUSTOM_RACE.md) |
| series 20004, kits, switching grids | [CIRCUIT_EXPERIENCE](../guides/CIRCUIT_EXPERIENCE.md) |
| AI grid model, survey numbers, how to build | [AI_GRIDS](../guides/AI_GRIDS.md) |
| what can be modded, where, with which tool | [MODDING_SURFACE](../reference/MODDING_SURFACE.md) |
| symptom → cause → fix | [TROUBLESHOOTING](../guides/TROUBLESHOOTING.md) |
