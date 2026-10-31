# Tutorial 04 — AI roster and grid (summary)

This page is a map, not the manual. The guide for this topic is
[`guides/CUSTOM_RACE.md`](../guides/CUSTOM_RACE.md) (modes, class scale, recipe,
test protocol). The model, the XML structure, the survey
numbers and the per-car evidence live in `docs\AIFIELD_GRIDS.md`; read it before
touching a grid. The mc58 kit (23-car roster) is the worked example
(maintainer's lab).

## The one thing to know first

The AI field is **not** defined only by the BCS. Two targets exist and each has
its own tool:

| target | file | applied by |
|---|---|---|
| `AISelectableCars.Acceptlist` | `BuildersCupScheduleDataV4.json` (CmsCache) | `cache_edit.py` (Strategy S) |
| `AIField_117160001_Gen.xml` | group `cfa7698c`, **only in the install zip** | `install_edit.py` — `cache_edit.py` skips it (`[skip]`) |

The BCS alone does **not** change the grid (tested in game: still the donor's
cars). The XML is what pins the field. That asymmetry is why the mc58 kit
ships two plans: `plan.json` (complete intention) and `plan_bcs.json` (BCS only,
the one `cache_edit.py` applies).

## Choose a mode

| mode | you get | PI of each AI car |
|---|---|---|
| `AIDrivatarTemplate` — **pool** | up to `NumberOfDrivatars` cars drawn from `EligibleCars` | the PI window (shared) |
| `AIDrivatarList` — **fixed list** | exactly the cars you list, in order; repeat a car to weight it | its lowest `AI_` file (large speed gap between classes) |

Both are documented, with vanilla counts and the open questions, in
`AIFIELD_GRIDS.md` § *Pool vs fixed list*.

## Before you build a roster

Every car you put on the grid needs all of:

1. to exist in the car catalogue — the `CARROS` inventory page, `cars.json`;
2. to be free of always-active vetoes — `denylist.json`;
3. to have `AI_<car>_<pi>.xml` files in the game, otherwise the AI drives with
   a fallback or not at all.

`fmlib.aifield.validate(roster, by_car)` checks all three at once. To see a
car's ladder or the whole survey: `python _tools\aifield_survey.py [--car <id>…]`.

## Building a custom grid

1. Write a definition in `specs/aifield/` (examples: `trackday_pool56.json`,
   `trackday_list23.json`; fields are listed in the docstring of
   `_tools/build_aifield.py`). It names a **vanilla template of your own
   install** as the skeleton, the mode (pool or list), the roster or lineup,
   and for a pool the PI window, slot count and progression frames.
2. Build it: `python _tools\build_aifield.py --def specs\aifield\<name>.json`
   (`--check` validates without writing). The tool encrypts with the **current
   install payload** of the target entry as cipher template, asserts that every
   manifest row points to an existing `AI_` file, and writes
   `patches\<name>\XML.AIField_117160001_Gen.enc`. For custom logic use
   `aifield.rewrite_template` / `aifield.rewrite_list` from `fmlib` directly.
3. Review the roster against the catalogue and the vetoes
   (`aifield.validate` runs inside the build).
4. Keep the definition with your notes (roster with class/PI, how to revert).
5. Apply with the game **closed**:
   ```powershell
   python _tools\install_edit.py --dry-run --logical AIField_117160001_Gen.xml --payload patches\<kit>\XML.AIField_117160001_Gen.enc
   python _tools\install_edit.py --verify  --logical AIField_117160001_Gen.xml --payload patches\<kit>\XML.AIField_117160001_Gen.enc
   ```
   It backs up to `_backup\install_<time>`; undo with `--restore` or by applying
   the previous kit's payload. If the BCS part changed too, also run the usual
   `plan_lint` → `cache_edit.py --dry-run` → `--verify` loop.
6. `python _tools\test_aifield.py` after touching `fmlib.aifield`.

## Verifying in game

Enter the series and read the grid: the AI cars should be the ones in your
roster, and there should be no CMS error or empty career menu. For a pool, open
the event several times and note whether the grid is re-drawn. Record each run in
`AIFIELD_GRIDS.md` § *Test log*. If the field still shows the donor's cars, the
install XML was reverted (Steam "verify files", new snapshot) — run
`install_edit.py` again.
