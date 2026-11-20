# Series intro videos

What plays when a career series opens, which parts we can change, and how to give a series an
intro video of our own. No game video or audio is held here: only names, counts and the method.

**Status: an own video, encoded by us, under its own name, plays in game (19/11/2026, D105–D114).**
Sound plays from one side only (see *Encoding*).

## Two ways a series intro plays

A series names its intro in `IntroVideoPath` (a file name such as `PracticalPerformance.bk2`). What the
game does with that name depends on `PlayIntroVideoFullScreen`:

| | `PlayIntroVideoFullScreen` false (what almost every series uses) | `PlayIntroVideoFullScreen` true |
|---|---|---|
| what you see | a **3D scene** in real time: cameras, up to three cars, lights | the **`.bk2` video**, full screen |
| sound | the scene's music and a narrator's line | none from the game (the video may carry its own audio track) |
| how the name is used | a script picks the scene **by the name**; an unknown name falls back to a default scene (an Open Tour intro, narrated about open events) | the file is opened by its name |
| our own content | scenes, music and narration are the game's (narration and music live in encrypted sound banks) | **any `.bk2` we install** |

After the intro the series goes to its car selection. Keep `FirstCarSelectEnabled` false and
`FirstCarSelectCars` empty: on our series the first-car screen fails when a car is confirmed (D105, D106).
A ladder's `IntroVideoPath` showed nothing; a cup's video field has no link to the narration.

## The video files

Loose files in the install, `media\base\ui\videos\1080\` and `...\2160\` (one copy per resolution, 48
each). Bink 2 (`KB2j` header), **not encrypted**; the game ships only the Bink player (`bink2w64.dll`,
playback calls only) and hands it files through its own file system.

| what most series videos are | value |
|---|---|
| size | 5600×2000 (a wide wall), a few at 1920×1080 or 3840×2160 |
| frame rate | 29.97 or 30 fps |
| length | 13 to 30 s |
| audio tracks | none on most |

## An intro video of our own

The standard way is one command, game **closed**; it encodes, installs and indexes:

```powershell
python _tools\encode_intro.py --mp4 my_clip.mp4 --name FCO_MyIntro --ffmpeg C:\path\ffmpeg.exe --apply
```

It only ever **creates new files**: a name that already exists is refused, so a video that works is never overwritten (pick a new name for each version). (`--mp4-1080` and `--mp4-2160` take a file per size; `--hq` finer video; `--no-audio` drops the sound; without
`--apply` it only shows the plan.) By hand, the same in three steps:

1. **Encode** the clip with the preset (see *Encoding*), one file per folder.
2. **Install** it under its own name:
   ```powershell
   python _tools\bk2_install.py --add FCO_MyIntro --from-file my_1080.bk2 --from-file-2160 my_2160.bk2 --apply
   ```
3. **Index** it, or the game will not see it ([INSTALL_INDEX](INSTALL_INDEX.md)):
   ```powershell
   python _tools\hash_manifest_edit.py --check ui\videos\1080\practicalperformance.bk2 ui\videos\2160\practicalperformance.bk2
   python _tools\hash_manifest_edit.py --add ui\videos\1080\fco_myintro.bk2 ui\videos\2160\fco_myintro.bk2 --value <v1080> <v2160> --apply
   ```

Then **point the series at it** in the round spec (`series_set`): `IntroVideoPath` `FCO_MyIntro.bk2`,
`PlayIntroVideoFullScreen` true, `FirstCarSelectEnabled` false, `FirstCarSelectCars` `[]`; build and apply the
kit as usual ([GETTING_STARTED](../en/GETTING_STARTED.md), step 8).

To drop a video: `bk2_install.py --remove FCO_MyIntro --apply`, then `hash_manifest_edit.py --remove ui\videos\1080\fco_myintro.bk2 ui\videos\2160\fco_myintro.bk2 --apply` (it only removes records the tool itself added). No vanilla video is overwritten. Without the index record the series shows a black screen and goes on (D109).

**Fallback without the index:** four videos are named by no game data (`3d_carselect_vw`, `softbox`,
`3d_carselect_focus`, `3d_carselect_subaru`); `bk2_install.py --replace <slot>` writes over one of them,
with a backup and `--restore`, and a series in full screen that names the slot plays the new content (D111).

## Encoding

Bink 2 is a closed codec, but an encoder that writes the revision the game ships exists (D114, D118).
**ffmpeg with a `bink2video` encoder** (the MobiPeg build of ffmpeg, AGPL-3.0; the project ships no binary)
writes `KB2j`, with the same container flags as the vanilla videos, and Bink audio.

**The project preset** (`encode_intro.py` applies it; one 16:9 MP4 in, two `.bk2` out):

| part | setting |
|---|---|
| video | `-c:v bink2video -pix_fmt yuv420p -quant 8` (`--hq`: `-quant 6`) |
| audio | `-c:a binkaudio_dct -ac 2 -ar 48000 -quality:a 10` (kept if the MP4 has audio) |
| sizes | 1920×1080 and 3840×2160, one file per video folder |
| frame rate | the source's (24 fps worked) |

The quantiser trades size for quality, with little gain past 8: on a 1080 clip measured against its own MP4,
quantiser 12 gave 10 MB and 41.5 dB, **8 gave 19 MB and 42.6 dB**, 6 gave 25 MB and 42.8 dB, 2 gave 42 MB and
43.3 dB. The ceiling is the source, so start from the highest-quality file you have.

**Sound caveat:** every sound we encoded (mono or stereo, the encoder's or RAD's) came out of one side only in
game, so plan on mono. RAD Video Tools (free, signed by Epic) writes revision `KB2n`, which the game's player
does not read (black screen), so it is not a way in.

`bk2_install.py` and `encode_intro.py` check that the file is `KB2j`.

## After a Steam update

*Verify files* or an update puts the vanilla index back (and removes nothing else of ours, or may remove
our files too): the series then shows a black screen and keeps working. Run steps 2 and 3 again.
