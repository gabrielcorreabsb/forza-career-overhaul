# Circuit Experience — the trackday package (series 20004)

> **Area: trackday.** The one custom series this project ships today: a single
> Nordschleife event with a multi-class AI grid. How the grids work in general
> is in [CUSTOM_RACE](CUSTOM_RACE.md); the basics are in [CAREER_BASICS](CAREER_BASICS.md).

**FM4 equivalent:** pick a circuit, drive it — here one career series, one
circuit, any class.

## 1. What it is

| item | value |
|---|---|
| series | **20004** "ModCarrera Treino 1", clone of vanilla series 11470 |
| placement | cup **103** "7. Trackday", ladder **761** "Trackday Nordschleife" |
| event | **65897913**, Nürburgring Nordschleife; rolling start, 1 lap, no pits |
| practice | none (`OpenPracticeLimitationTimeInSeconds = 0`, works in game). The same 0 on other series did **not** remove the practice (observed in two series), so the Trackday relies on more than that field |
| event limits | `ClassRestriction 8`, `TargetPI 999` — any class up to X999 |
| player cars | 23-car acceptlist (kit mc56); an S car at PI 701 was accepted |
| AI | `AIField_117160001_Gen.xml` (install-only), 23 AI + the player = 24 cars |

## 2. Kit timeline (all applied; `patches/<kit>/NOTA.md` has the detail)

| kit | what it did | tested in game |
|---|---|---|
| mc55 | pilot series 20004 in cup 2 / ladder 22, Nordschleife event, challenge 100963 + group 554 | yes |
| mc56 | trims the acceptlist to 23 cars, new art (`BC_GermanRivals`), clears the intro video | yes |
| mc57 | new cup 103 + ladder 761, moves 20004 there, practice limit 0 | yes |
| mc58 | AI roster of 23 cars (BCS acceptlist + AIField XML) | yes — the XML, not the BCS, changed the grid |
| mc59 | event `TargetPI` 700 → 999 (lifts the A700 cap) | yes — S 701 entered |
| mc60 | AI **pool** of 40 cars, window 500–800 | yes, 3 runs |
| mc61 | AI **fixed list**, 23 slots, 18 cars, D→R | yes, run 1 |
| mc63 | AI **pool of 56 cars (E→P) with a wide PI band** (−350…+250), window 300–980 step 20 | yes, 3 runs (C 404, A 678, S 701); pace fine |

(`mc62` is an unrelated test of the user's and is not part of this package.)

## 3. What is installed now, and how to switch

Only **one** AIField payload is active at a time; they all rewrite the same
entry. The active one is **mc63**. To switch (game **closed**):

```powershell
python _tools\install_edit.py --dry-run --logical AIField_117160001_Gen.xml --payload patches\<kit>\XML.AIField_117160001_Gen.enc
python _tools\install_edit.py --verify  --logical AIField_117160001_Gen.xml --payload patches\<kit>\XML.AIField_117160001_Gen.enc
```

| `<kit>` | grid you get |
|---|---|
| `mc63` (active) | 23 drawn from 56 cars (E→P); target PI = **your PI −350…+250**, so the grid follows your car and spans 4–7 classes |
| `mc61` | multi-class D→R, PI fixed per car, independent of your car |
| `mc60` | 23 drawn from 40 cars (D→R), listed 10–50 PI below yours: the field is in your class |
| `mc58` | the original 23 cars, window 600–700 |

Steam "verify files" or a new server snapshot reverts the install: re-run the
last command. Every apply backs up to `_backup\install_<time>`
(`--restore` returns to a backup).

## 4. mc61 lineup (23 slots, 18 cars)

3781 911 GT3 RS 23 · 1655 BRZ '13 ×2 · 2870 Civic Type R ×2 · 424 RX-7 '97 ×2 ·
3667 911 GT3 '21 ×2 · 1429 Nova SS '69 · 1598 M3 '10 ×2 · 2357 Focus RS ·
2755 911 GT2 RS · 1009 Lancer Evo X · 3117 718 Cayman GTS · 2352 NSX '17 ·
3369 C8 '20 · 3227 Ferrari 488 Pista · 2005 S2000 · 3622 GT-R NISMO ·
2168 WRX STI · 3616 AMG GT Black Series. Exact order and the `AI_` file of each
car: the mc61 kit notes (lab). The game draws from these (repeats beyond the
listed weights were seen), so treat the weights as a bias, not a guarantee.

The mc60 pool (40 cars) and its draw results are in the mc60 kit notes (lab).

## 5. What a run looks like

mc61 run 1, player Toyota GR86 '22 (PI 404, C): the AI grid held D (Nova '69,
354), C (RX-7 462, S2000 405), B (WRX 507), A (M3 '10 657, 718 GTS 608, C8 678),
S (GT-R NISMO 722, NSX 731, 911 GT3 '21 737, GT3 RS 23 783) and R (AMG GT 801).
mc60 runs 2–3: a different set each time, always 10–50 PI below the player.
The model behind these runs: [AI_GRIDS](AI_GRIDS.md); the maintainer's lab keeps the per-run test log.

## 6. Open for future optimization

The package is **finished and playable** (mc63 active). What is left is tuning,
listed in [DISCOVERIES](../project/DISCOVERIES.md) § 3 and [CUSTOM_RACE](CUSTOM_RACE.md) § 9:

- measure real lap times per listed class (pace looked right in play: the faster
  cars pull away from the slower ones, but no table was recorded);
- tune the pool (weights, drop cars that rarely suit a trackday) and the band
  (`−350…+250` is the maximum tried; asymmetric bands, per-class pools);
- try step 10 instead of 20, and the behaviour flags if the pace ever flattens;
- grids above 24 cars (experiment only);
- re-run mc61 with other player cars to confirm its PIs never move.
