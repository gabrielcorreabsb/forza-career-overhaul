# Custom Race — multi-class grids in any series

> **Area: multiserie.** Everything about building an AI grid — pool, fixed
> list, PI per class — that applies to **any** series, not just the trackday.
> The ordinary-career basics are in [CAREER_BASICS](CAREER_BASICS.md); the series that uses
> this today is in [CIRCUIT_EXPERIENCE](CIRCUIT_EXPERIENCE.md); raw numbers and
> the per-run test log are in [AIFIELD_GRIDS](../AIFIELD_GRIDS.md).

**FM4 equivalent:** a custom race where you build the field yourself — here it
is the AI grid of a career series. Status labels: **verified** (seen in game or
reproduced by a script), **inferred** (follows from a verified rule), **to
test**.

## 1. What decides the grid

Two places hold the AI roster; only one wins.

| place | effect |
|---|---|
| `AISelectableCars.Acceptlist` (BCS) | does **not** change the grid *(verified, mc58)* |
| `AIField_<n>_Gen.xml`, named by the event override's `AIFileName` | **pins the field** *(verified)* |

The XML lives in content group `CFA7698C`, which the CmsCache never holds, so it
is edited inside the install zip with `install_edit.py` (see §7).

## 2. The two modes

| | pool (`AIDrivatarTemplate`) | fixed list (`AIDrivatarList`) |
|---|---|---|
| vanilla use | 553 files, the career default | 92 files, 23 series (endurance/showcase) |
| how the XML says it | PI window + `EligibleCars` + 23 `Car="-1"` slots | explicit `Car` per slot, `TargetPI="-1"` |
| who is on the grid | cars **drawn** from the pool *(verified, mc60 runs 2–3)* | cars **drawn** from the list; repeats and order differ from the list *(verified once, mc61 run 1)* |
| AI PI | **player PI −50…−10**, clamped by window and ladder *(verified, 3 runs)* | **fixed per car**: its lowest `AI_` file + 20…77 *(verified, mc61 run 1)* |
| classes on the grid | the **player's** class (A player → all listed A, even D cars lifted) | the **cars'** own classes, whatever the player drives (C player faced D→R) |
| scales with the player | yes | no |
| pool bigger than 23 slots | works, grid differs per run | n/a |

Rule of thumb: **pool = difficulty that follows the player; list = a real
multi-class field.** Vanilla uses the list for endurance-style series, which is
why a trackday with D→R cars is the same pattern, not an invention.

## 3. Class scale (use this, not `cars.json`)

E 0–300 · D 301–400 · C 401–500 · B 501–600 · A 601–700 · S 701–800 · R 801–900 ·
P 901–998 · X 999. Class ids in `cars.json`: 0=E … 8=X. *(verified)*
Evidence: PI 701 shows **S** and 686–689 show **A** in game; the old event cap
was `CarClassId 4` + `PIMax 700`; the lowest `AI_` file of each class sits in
its table band (`aifield_survey.py`: 362/541 exact).
`cars.json:pi` is **not** on this scale (300/541) — never derive classes
from it.

## 4. AI files and how a PI becomes a tune

Each car has a ladder `AI_<car>_<pi>.xml` (541 cars; 508 usable = in the
catalogue and no always-on veto). Its lowest file is about the car's real stock
PI (BRZ '13: 331 = D; 911 GT2 RS: 772 = S).
Mapping, byte-exact against 96 vanilla pairs *(verified)*:
`TargetPI = -1` → the **lowest** file; a window step → the **highest** file
≤ the step, clamped to the lowest. Above a car's highest file it stays on the
highest. So a pool of E→P cars keeps its real classes: a P car (lowest ≥ 828) is
always fast, a D car (highest ≈ 699) is never faster than that.

## 5. The PI band (pool documents)

Each AI driver draws its target PI inside `[player + lower, player + upper]`
of the active `AIProgressionFrame`, then the window and the ladder clamp it.
The XML has three frames keyed by `PlayerPIRelativeToClass` (40/80/100); all
our runs (player PI 404–701) used the last, `−50…−10` *(verified)*. What the key
measures is unknown *(to test)*. Vanilla bands are ≤ 60 wide; a wide band is
unprecedented *(to test)*.

## 6. Choosing and composing

- **Pool** when the series should get harder as the player's car does. Put
  cars of the classes you want represented; the draw is random, so order does
  not matter beyond the first run's anomaly.
- **List** when the series is *about* the mix (trackday, endurance). Repeating
  a car raises its weight, but expect the draw to deviate *(inferred)*.
- Every car needs: in the catalogue, no always-active veto, and `AI_` files
  (`aifield.validate` checks all three).
- Keep **23 AI slots**: vanilla never exceeds 24 cars on the grid; more is
  *to test*.
- One car per make per class and mixed eras were the rules used so far.

## 7. Recipe

```powershell
# 1. definition in specs/aifield/ (pool or list), built from a vanilla template
#    of your install; encrypted with the CURRENT install payload as template
python _tools\build_aifield.py --def specs\aifield\<name>.json
# 2. apply (game CLOSED); every apply backs up to _backup\install_<time>
python _tools\install_edit.py --dry-run --logical AIField_117160001_Gen.xml --payload patches\<kit>\XML.AIField_117160001_Gen.enc
python _tools\install_edit.py --verify  --logical AIField_117160001_Gen.xml --payload patches\<kit>\XML.AIField_117160001_Gen.enc
# 3. undo = apply the previous kit's payload, or --restore _backup\install_<time>
```

The kit is just `patches/<kit>/XML.…enc` + the kit's notes file; the
XML is built by `_tools/build_aifield.py` from a definition in `specs/aifield/`. Steam "verify files" or a new snapshot reverts the install:
run the tool again.

## 8. Test protocol

Three runs per kit, ideally with player cars of different classes. Record per
run: player car/PI, the 23 AI cars with their listed class/PI, repeats, whether
the grid changed, grid size, CMS errors, and the first-lap pace of a few cars.
Add the entry to the *Test log* in [AIFIELD_GRIDS](../AIFIELD_GRIDS.md).

## 9. Open questions and future optimization

- ~~Does a wide frame band work?~~ **Yes** (mc63: band −350…+250, window 300–980 step 20; spread 310–637 for a PI 404 player, 368–931 and 7 classes for a PI 701 player). On-track pace was good in play (faster cars pull away from slower ones, vanilla flags untouched). Still open: a lap-time table, pool/band tuning, and grids above 24.
- Does the **list** react to the player's PI? (expected no)
- Run 1 after an install change shows the previous grid's cars (mc60 run 1, mc63 run 1) while the PI is new; treat run 1 as a warm-up *(hypothesis, 2 cases)*.
- A car listed far from its ladder (M-AMG GT '20 at D 310, lowest file 775): the game still ran it as the car it is *(observed, no lap table)*.
- Flags `EnableDifficultyCatchUp/SlowDown` (always `True` in vanilla) did **not** flatten the pace in mc63; no change needed unless that changes.
- Grids above 24 cars; the role of `EligibleCars` in list documents.
