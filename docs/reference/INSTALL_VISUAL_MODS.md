# Install-only visual modifications

What we changed in the game's **install** (`media\`) to raise its visual quality: render settings, track look,
car level of detail, camera settings and one UI texture. These changes are not career data (the CmsCache);
they touch no physics, no online play and no account economy, and Steam's *verify files* removes them. This
page lists **what** we changed (file, field name and direction), the rules that keep it safe, the status of
each change and the credits. It holds no game value and no game text: our own values are chosen per machine
and are not published here.

**Status.** Tested in game by the maintainer on one machine (an RX 9070 XT, 1728p with DLSS Quality, 60 FPS at
about 80% GPU; 4K runs out of VRAM). The set is aimed at high-end hardware: it raises quality and costs GPU and
VRAM (the cubemap and sky step alone cost about 300 MB of VRAM on the maintainer's machine). For where each file lives and what is known about it see [MEDIA_MAP](MEDIA_MAP.md).

## What we changed

Direction: **up** = a higher value than the game's own Ultra, **down** = lower, **new** = a key the file did
not define. Status: **approved** = tested in game by the maintainer and approved.

### Render settings (`pcfamily\renderscenarios\ultra\global.xml` and `race.xml`, with the matching menu options)

| group | fields | direction | status |
|---|---|---|---|
| shadows | `PSSMShadowsResolution`, `CSMShadowsResolution` (levels), `ShadowMapResolution` | up | approved |
| shadows | `EnableNightMoonShadows`, `AllowAICarHeadlightShadow` | new / on | approved |
| cubemaps and sky | `CarCubemapResolution`, `CarCubemapMSAA`, `GlobalCubemapResolution` | up | approved |
| cubemaps and sky | `GlobalCubemapResolution` (second step), `ProceduralSkyResolution` | up | approved |
| reflections (ray tracing) | `EnvMapDistanceScale`, `EnvMapMeshLimitScale`, `EnvMapFrequencyScale`, `DXRRTBufferPassCarMaxViewDistance`, `DXRMaxUpdatableModelsProcessedPerFrame`, `DXRResolutionScale` | up | approved |
| reflections (ray tracing) | `DXRCockpitTransparentPassEnabled`, `EnvMapMeshSizeLimitScale` | new | approved |
| car detail | `OpponentCarLiveryResolution`, `DensityCullCutoffValueLevel`, `MaxDynamicTrackLevel`, AI particle detail | up | approved |
| car detail | `CarDrawRenderedAO`, `DayUltraShaders` | new | approved |
| rain on the camera lens | `EnableWaterOnCameraLens` (race scene) | new / on | approved |
| scene reflection (cubemap) on the tracks the first pack missed | faces per frame, far distance, mesh limit, limit per face, mesh size threshold | up, back to the base value | approved |
| crowd shadows and models | `Crowds.VisibleDistanceFor*` | up, back to the base value | approved |
| falling rain on screen | `FallingRainParams` opacity and drop width | up, back to the base value | approved |
| cockpit GPU load | `DXRCockpitTransparentPassEnabled` (race scene) | off | approved |
| rain drops on the inside of the windscreen | `Interior_RainDropTuningData` (rate, life, mass, sizes, edge spawn) | retuned as a block | approved |
| car texture sharpness | `CarAnisoFilterOverride` (one step, to the top of the menu scale) | up | approved |
| car level of detail | `CarAnimLODThresholds` (race) | equalled to the global Ultra value | approved |
| car level of detail | `CarFocusLODMinMax`, `CarNonFocusLODMinMax` (maximum), `CarPlanarLODOverride`, `CarShaderLODBias` | down | approved |

### Track look (`pcfamily\tracks\<track>\tracksettings.xml`, `base\tracks\basetracksettings.xml`)

| fields | direction | status |
|---|---|---|
| `Cubemap` (`FacesPerFrame`, `FarDistance`, `MeshLimit`), `ShadowSettings.DistantShadowsPerFrame`, `ShadowEnds.InGameShadowEnd` | up | approved |
| `HeadlightShadows.HeadlightShadowDistance`, `ShadowMapAniso` | up | approved |
| `ForceEnableGTAO` (base only) | new | approved |
| `CollidableDropDistance` (16 tracks that lowered it) | up, back to the base value | approved |
| `cockpitBloomScale` (base and the 9 tracks that define it) | down, x0.75 | approved |
| `CockpitLensFlareIntensity` (base and the 7 tracks that define it above zero) | down, x0.7 | approved |
| `WaterOnLens.RefractionScalar`, `WaterOnLens.RefractionIndex` (base and the 15 tracks that define them) | down, x0.75 | approved |

A track is only edited where it already defines the field; a missing attribute inherits the base.

### Camera (`base\camera.zip`: `CameraSettings.ini`, `CameraPhysics.xml`, `ShowroomPhotomode.ini`)

| what | fields | direction | status |
|---|---|---|---|
| free photo-mode camera | `PhotoModeCam`: collision iterations and radius, `MaxHeight`, boundary radius, ceiling and floor, `MinFOVPhotoMode` | limits removed | approved |
| free showroom photo camera | `ShowroomPhotomode.ini`: collision, ceiling, floor, `MaxDistance`, `MinFOV`, `MaxFOV` | limits removed | approved |
| softer vignette on the race cameras | `FollowLowCam`, `FollowHighCam`, `HoodCam`, `BumperHighCam`: vignette alpha and colour | down | approved |
| cockpit camera | `DriverCam` and `NoWheelDriverCam` layers: gaze pitch, speed and acceleration FOV, shake, impacts; `Driver` FOV in the ini (only counts with the in-game custom camera FOV off: with it on, the FOV comes from the player's slider) | softer, higher gaze | approved |
| driver eye position per car | `Locators.xml` inside each car zip (`media/pcfamily/cars/<id>.zip`): the two driver-eye locators, a few centimetres, 111 cars | moved | approved |
| hood and bumper cameras | `HoodCam`, `BumperHighCam`: pitch, bumper height and offset, near clip, and the ini FOV (again only with the custom camera FOV off) | closer | approved |

### UI texture (`ui\textures\Data_Bound.zip` and `hires\Data_Bound.zip`)

| what | entry | status |
|---|---|---|
| photo-mode watermark | `logo_fm` (and `logo_fm_chs` for Chinese): the photo-mode scene shows the Forza logo through a localized image path; the texture is replaced by a transparent one | approved |

The logo texture may also show on other screens; if a menu loses its logo, that is the cause.

Every change is a value the game already reads. A key the game executable does not contain would be ignored,
so the tool for loose XML refuses it.

## The tool we publish

[`_tools/graphics/apply_kit.py`](../../_tools/graphics/apply_kit.py) applies a **kit** (a small JSON of edits) to the
loose XML files: it keeps the original of each file before the first edit, restores one kit at a time or all,
refuses to write with the game open, does a dry-run first and stops if the file no longer matches the state it
recorded (a Steam update, another tool). It never touches a zip. The originals and the state of applied kits go
to a `graphics` folder next to the repository (set `FM_GRAPHICS` to move it); keep it, because restoring needs
it. A kit holds only the values you choose:

```json
{"id": "EXAMPLE", "description": "one value, as a template",
 "edits": [{"file": "pcfamily/renderscenarios/ultra/race.xml",
            "key": "SomeKeyTheGameKnows", "attr": "value", "value": "1"}]}
```

```powershell
python _tools\graphics\apply_kit.py --dry-run EXAMPLE      # game closed; FM_GRAPHICS_KITS points to your kit folder
python _tools\graphics\apply_kit.py --apply EXAMPLE
python _tools\graphics\apply_kit.py --restore EXAMPLE
```

The zip edits (camera, UI texture) are **documented here but their tool is not published**: reading and
rewriting those archives needs the game's method-21 compression, which is handled by a Microsoft runtime
library we cannot distribute (see [THIRD_PARTY](../project/THIRD_PARTY.md)). The kits themselves are not
published either: the lists above give the file, the field and the direction, so you can write your own.

## The rule for zip edits

A zip of the install must keep **the same size and every entry at the same offset**. Rewriting a zip so that
entries moved took the menu's animated background away (the game reads some entries at 4096-byte aligned
offsets); putting the vanilla file back restored it ([D120](../project/DISCOVERIES.md)). Our zip edits therefore
write the edited entry into its own slot, pad the rest with zeros and refuse an edit that does not fit. Posters
follow the same rule ([SWATCHBIN](SWATCHBIN.md)).

## Credits

- The camera settings (a free photo-mode camera and the softer race vignette) were read from **Better Photo
  mode** by **GmSV2**, on Nexus Mods
  ([Forza Motorsport mod 12](https://www.nexusmods.com/forzamotorsport/mods/12)). We reproduce only the setting
  names and the direction of each change, as our own recipe; none of the mod's files is included. Please
  credit the author wherever you reuse it.
- Other visual mods were read for ideas only (which keys exist and which direction they move); nothing from
  them is distributed.

## Limits

- Steam's *verify files* or an update removes every edit: apply again.
- A change that works on one machine can cost too much on another: raise one value at a time and watch GPU
  and VRAM.
- Effects come from the maintainer's own runs (n=1); if yours differ, open an issue with the numbers.
- The meaning of some fields (for example the four numbers of `CarAnimLODThresholds`) is inferred from the
  game's own tiers, not documented.

See also: [MEDIA_MAP](MEDIA_MAP.md), [INSTALL_INDEX](INSTALL_INDEX.md), [MODDING_SURFACE](MODDING_SURFACE.md).
