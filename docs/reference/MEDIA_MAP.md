# Media map — what is in the install's `media\` folder and what we can do with it

One page that answers, for every folder of `media\base` and `media\pcfamily`: what it is, what
format it has, how the game finds it, **who the game reads it from** (the install or the cache), and
what we have proven. It holds no game data and no game text: only names, counts, places and status.
Counts were measured on the install of 19/11/2026. Field-level detail of the career data lives in
[MODDING_SURFACE](MODDING_SURFACE.md); this page is the map of the **install** side.

**Status labels** (same as [MODDING_SURFACE](MODDING_SURFACE.md)): **verified** = changed by a tool
and the effect was seen in game; **observed** = seen, cause not isolated; **hypothesis** = readable
and writable, effect not tested; **closed** = cannot be written today or off-limits by project rule;
**not surveyed** = we have not looked at it for writing.

## 1. The three rules that decide everything here

1. **Which copy does the game read?** The live cache is the runtime source for every CMS file that
   has a local blob; the install copy of those is only a seed
   ([ADR-004](../project/decisions/ADR-004_install_vs_runtime.md)). Everything in this page that is **not** a CMS
   file (videos, posters, render settings, AI statics, string tables of the theme tables…) has no cache
   twin: the install is the only copy, so editing it works, and Steam's *verify files* undoes it.
2. **A file that is new needs an index record.** The game opens files through its own file system, which only
   knows the paths listed in `hash.manifest` ([INSTALL_INDEX](INSTALL_INDEX.md)). Changing the
   **content** of an existing file needs nothing else; **adding** a file needs one record. Files
   inside a zip need no record: the zip is the file.
3. **A zip can be edited in place, a container cannot.** Plain zips (store/deflate) and the method-21 zips of
   the UI textures can be edited by our tools, **in place**: the edited entry stays in its own slot and every other entry keeps its offset and bytes (moving entries took the menu's animated background away, D120); the encrypted containers
   (`physics`, `prizes`, `unlocks`, part of the tunables) and the zips in a compression method the Python
   `zipfile` cannot open are **closed** to us. Reading a method-21 entry needs Microsoft's `xcompress64.dll`,
   which this repository does not distribute ([THIRD_PARTY](../project/THIRD_PARTY.md)): without it the
   published poster tool can only add new entries (Deflate), not read or replace a vanilla one.

## 2. `media\base` (shared by every platform, ≈ 8.3 GB)

| folder / file | what it is | format | indexed by | status | tool |
|---|---|---|---|---|---|
| `ui\videos\1080`, `2160` | series intro videos, 48 each | Bink 2 `KB2j`, loose, not encrypted | `hash.manifest` (new names only) | **verified**: overwrite in place (D111); new name + record (D113); own encoded video (D114–D119) | `encode_intro.py`, `bk2_install.py`, `hash_manifest_edit.py` |
| `ui\videos\subtitles.zip` | subtitles of those videos, 736 XML | zip, readable | zip | **hypothesis** (needed only if an own video gets speech) | — |
| `ui\fonts.zip`, `ui\credits.xml`, `ui.zip` | fonts, credits, UI scenes (XAML) | zip / XML | zip / manifest | **hypothesis**; XAML only names the flags, the data is the lever ([UI career notes in MODDING_SURFACE §6](MODDING_SURFACE.md)) | — |
| `gametunablesettings\` | 68 files: tunables, level/affinity configs, regulation tables, forzathon, client flags | 32 JSON, 31 XML, 3 XSD, 1 INI; part encrypted | manifest | the **cache copy wins** where one exists; the install copy is a seed. Prize and economy tables: server decides ([ECONOMY_MAP](ECONOMY_MAP.md)) | a dedicated tool for the loose encrypted container |
| `stringtables\<lang>.zip` | 23 language zips; the theme tables (about 126 per language) exist only here | zip of `.str` | zip | the cache `LocStrings` tables win and are **verified**; whether an install theme table can be rewritten is a **hypothesis** (`install_edit.py` never accepted a `.str`) | `str_edit.py` (codec) |
| `ai\aistatics.zip` | AI behaviour statics (`Default` and per-track INI) | zip of INI | zip | **verified**: the game reads it, narrowing the speed band and raising the off-track limit changed the AI (D76, D77) | a dedicated AI-statics tool |
| `ai\series.zip`, `carandcontrollertuning.zip`, `racinglines.zip`, `tracks.zip`, `racinglinekeyscales.xml` | AI series data, car/controller tuning, racing lines | zip / XML | zip | **not surveyed** for writing | — |
| `cinematics.zip` | 3,319 XML + 1,856 `.fcx`, the 3D series-intro scenes and other cinematics, routed by the game database | zip, compression method the Python `zipfile` cannot open | zip | **closed** today (cannot read) | — |
| `weather.zip`, `proceduralsky.zip`, `camera.zip`, `fxparticles.zip` | weather recipes, sky, camera stacks, particles | zip, mostly readable XML/INI | zip | **hypothesis**; global, not career-scoped; the career lever for weather is the forecast in the cache | — |
| `lensflare\`, `entitymodel\`, `entitymodel*.zip` | lens flares, entity templates | XML | manifest / zip | **hypothesis**, visual or structural, global | — |
| `db\gamedb.slt` | the game database | encrypted SQLite | not indexed (loaded by a separate path) | **closed** for writing; a readable twin is the project's reference | read-only |
| `physics\`, `prizes\`, `unlocks\`, `objectives\`, `profileschema\` | physics, prize packs, unlock rules | encrypted asset containers | manifest | **closed** by project rule and by the server's authority | — |
| `audio\` | descriptors, subtitles and voice tables (readable); sound banks (encrypted) | XML/INI + `.bank` | manifest | readable parts **hypothesis**, global; banks **closed** | — |
| `controllerffb-*.ini` (86), `inputmappingprofiles\` (149), `speech\` | wheel force feedback, input maps, speech | INI / XML / compiled | manifest | global, **not career**; kept out of scope | — |
| `cars\`, `brakes\`, `characters\`, `championship\`, `tracks\`, `_library\` | shared car and driver assets, small track tables | models, textures, tables | manifest | **not surveyed**; assets are never opened by the project | — |
| `hash.manifest` | the file index | 12-byte header + 12-byte records, 2,261 records | — | **verified** (D112, D113) | `hash_manifest_edit.py` |

## 3. `media\pcfamily` (the PC build, ≈ 120 GB)

| folder / file | what it is | format | indexed by | status | tool |
|---|---|---|---|---|---|
| `cms\` | the CMS seed: manifest + 8 content-group zips + encrypted manifest | zips of encrypted payloads | the CMS manifest chain | **seed** for groups with a cache blob (ignored at runtime, ADR-004); **runtime source** for groups with no cache blob (AI grids) — **verified** | `install_edit.py` (replace), an add-entry tool |
| `ui\textures\data_bound\seriesposters.zip` + `hires\…` (and the two banner archives) | series art, 1,107 entries in 4 archives | zip, method 21 (LZX), each entry a `.swatchbin` BC7 | zip | **verified**: swap in place (D99), our own art (D100), a new entry name (D101), Deflate entries (D102), several at once and a removal (D103). Banners and buttons do not change the series card (D98) | `swatchbin_edit.py` |
| `ui\textures\` other folders | the rest of the UI textures (219 files, 3.9 GB) | `.swatchbin` zips | zip | **not surveyed** (event art — track map, loading screen — probably lives here) | — |
| `renderscenarios\<tier>\*.xml` | the five quality tiers (19 XML each) and `presets\` (114) | loose XML | manifest | **hypothesis → applied, not measured**: the first kits were applied; gain and cost are not measured, and two keys caused artefacts | graphics kit tool (see [§5](#5-the-graphics-work)) |
| `tracks\<track>\tracksettings*.xml` and `bin*.zip` | per-track look; track geometry and textures (76.6 GB) | XML + zips of `.swatchbin`/`.modelbin` | manifest / zip | look: **hypothesis**, global; geometry: **closed** | graphics kit tool |
| `skies\`, `_library\`, `posteffects.zip`, `proceduralsky.zip` | skies, shaders, post effects | zips | zip | **not surveyed** | — |
| `cars\` (992 files, 34 GB), `characters\`, `characters.zip`, `crowds.zip`, `livery.zip`, `particles.zip`, `dedupe.zip` (8.4 GB) | car, driver and crowd assets | zips of binaries; `dedupe` uses a method we cannot open | zip | **closed / not surveyed**: assets are never read by the project | — |
| `audio\fmod\` | 861 FMOD banks, 3.5 GB | encrypted banks | manifest | **closed** | — |
| `focusspace\` | one asset | — | manifest | **not surveyed** | — |
| `hash.manifest` | the file index | same format, 2,927 records | — | readable and rebuilt for every record; adding a record here is **untested** (`--root pcfamily`) | `hash_manifest_edit.py` |

## 4. What each kind of change costs

| you want to… | what to do | undone by |
|---|---|---|
| change the content of a loose file or a zip entry | write it in place with the tool of its kind, game **closed**, backup first | the tool's restore; Steam *verify files* |
| add a new loose file the game must open | add it, **and** add its record to the right `hash.manifest` | `hash_manifest_edit.py --remove`; Steam *verify files* |
| add an entry to a zip | the zip tool for that kind (`swatchbin_edit.py`, the CMS add-entry tool) | the tool's restore; Steam *verify files* |
| change a career value | not here: it is a cache kit ([PIPELINE](../en/PIPELINE.md)) | the cache rollback |
| touch an encrypted container, the game database, physics, prizes | do not: closed | — |

After a Steam update or *verify files* every install edit must be applied again; cache edits are not
affected.

## 5. The graphics work

The visual settings (`renderscenarios`, `tracksettings`, the options file) are install-only loose XML
and global to the game, so they serve the player's machine rather than the career. They have their own
kit tool and a plan kept outside this repository. The rule that matters here: a kit only changes
attributes the file already defines or inserts a key the game's executable is known to read; the
original of every edited file is kept before the first edit.

## 6. Tools at a glance (install side)

| tool | touches | creates / replaces |
|---|---|---|
| `encode_intro.py` | video encode + `bk2_install.py` + `hash_manifest_edit.py` in one command | creates only |
| `bk2_install.py` | `ui\videos\{1080,2160}\FCO_*.bk2` | creates only; removes only its own |
| `hash_manifest_edit.py` | `hash.manifest` (base or pcfamily) | appends records; never touches a vanilla record |
| `swatchbin_edit.py` | the poster archives, normal and hires together | replaces an entry or adds one |
| `install_edit.py` (replace), an add-entry tool | one entry of a CMS zip of the install + the manifest chain | replaces / adds |

Each keeps its own backup and state today; the plan to unify them is lab-only.

See also: [INSTALL_INDEX](INSTALL_INDEX.md), [INTRO_VIDEO](INTRO_VIDEO.md), [SWATCHBIN](SWATCHBIN.md),
[MODDING_SURFACE](MODDING_SURFACE.md), [DISCOVERIES](../project/DISCOVERIES.md).
