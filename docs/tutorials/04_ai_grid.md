# Tutorial 04 — AI roster and grid (summary)

This page is a map, not the manual. The guide for this topic is
[`guides/CUSTOM_RACE.md`](../guides/CUSTOM_RACE.md) (modes, class scale, recipe,
test protocol). The model, the XML structure, the survey
numbers and the per-car evidence live in `AI_GRIDS.md`; read it before
touching a grid. The mc58 kit (23-car roster) is the worked example
(maintainer's lab).

## The one thing to know first

The AI field is **not** defined only by the BCS. Two targets exist and each has
its own tool:

| target | file | applied by |
|---|---|---|
| `AISelectableCars.Acceptlist` | `BuildersCupScheduleDataV4.json` (CmsCache) | `cache_edit.py` (Strategy S) |
| `AIField_117160001_Gen.xml` | group `cfa7698c`; **in the cache since the clean snapshot of 08/11/2026, and the game reads that copy** (older cache: install zip only) | current route: `build_aifield.py --cache-plan` + `cache_edit.py`; on a cache without the group, `install_edit.py` ([AI_GRIDS](../guides/AI_GRIDS.md) §1) |

Unlike `cache_edit.py`, **`install_edit.py` has no sandbox**: it takes no
`--cache-dir`, and a real apply rewrites the install zip, the install manifest,
both `prod\` snapshots and `cache-manifest.json` of the **live** game. There is
no way to rehearse a grid on a copy of the cache; the write-free steps are
`build_aifield.py --check` and `install_edit.py --dry-run`, and the only test of
the result is the game itself. The install path comes from `FM_INSTALL`
(`docs\en\GETTING_STARTED.md` §2).

The BCS alone does **not** change the grid (tested in game: still the donor's
cars). The XML is what pins the field. That asymmetry is why the mc58 kit
ships two plans: `plan.json` (complete intention) and `plan_bcs.json` (BCS only,
the one `cache_edit.py` applies).

## Choose a mode

| mode | you get | PI of each AI car |
|---|---|---|
| `AIDrivatarTemplate` — **pool** | up to `NumberOfDrivatars` cars drawn from `EligibleCars` | the PI window (shared) |
| `AIDrivatarList` — **fixed list** | a weighted random draw from the cars you list (not the slot order); repeat a car to weight it | its lowest `AI_` file (large speed gap between classes) |

Both are documented, with vanilla counts and the open questions, in
`AI_GRIDS.md` §4.

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
   `--check` prints the shape of the definition, e.g. for the shipped list:

   ```
   AI_ index: 541 cars (snapshot 20260923t185113xwyk)
   trackday_list23: AIDrivatarList | 18 EligibleCars | 18 manifest rows | 23 slots
   payload: 944 B (current entry 8768 B)
   check only: nothing written
   ```
3. Review the roster against the catalogue and the vetoes
   (`aifield.validate` runs inside the build).
4. Keep the definition with your notes (roster with class/PI, how to revert).
5. Apply with the game **closed** (no sandbox: this writes the real install):
   ```powershell
   python _tools\install_edit.py --dry-run --logical AIField_117160001_Gen.xml --payload patches\<kit>\XML.AIField_117160001_Gen.enc
   python _tools\install_edit.py --verify  --logical AIField_117160001_Gen.xml --payload patches\<kit>\XML.AIField_117160001_Gen.enc
   ```
   The dry-run lists exactly what the apply would write — the install zip, the
   install manifest, both `prod\<snapshot>` files and `cache-manifest.json` — and
   ends with `DRY-RUN: nada escrito (marcador valido por 30 min)`. It backs up to
   `_backup\install_<time>`; undo with `--restore` or by applying the previous
   kit's payload. If the BCS part changed too, also run the usual `plan_lint` →
   `cache_edit.py --dry-run` → `--verify` loop.
6. `python _tools\test_aifield.py` after touching `fmlib.aifield`.

## Verifying in game

Enter the series and read the grid: the AI cars should be the ones in your
roster, and there should be no CMS error or empty career menu. For a pool, open
the event several times and note whether the grid is re-drawn. Write each run down with your kit (player car and PI, the cars and PIs
seen, CMS errors). If the field still shows the donor's cars, the
install XML was reverted (Steam "verify files", new snapshot) — run
`install_edit.py` again.
