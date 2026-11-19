# Series intro videos

What plays when a career series opens, which parts we can change, and how to give a series an
intro video of our own. No game video or audio is held here: only names, counts and the method.

**Status: an own video under its own name plays in game (19/11/2026, D105–D113).** The last step,
encoding a clip in Bink 2, is done with RAD's own tool (see *Encoding*).

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

1. **Encode** the clip in Bink 2 (*Encoding*), at 1920×1080 or 5600×2000, 30 fps; one file can serve both
   folders, or give a 2160 version.
2. **Install** it under its own name, game closed:
   ```powershell
   python _tools\bk2_install.py --add FCO_MyIntro --from-file my_1080.bk2 --from-file-2160 my_2160.bk2 --apply
   ```
3. **Index** it, or the game will not see it ([INSTALL_INDEX](INSTALL_INDEX.md)):
   ```powershell
   python _tools\hash_manifest_edit.py --check ui\videos\1080\practicalperformance.bk2 ui\videos\2160\practicalperformance.bk2
   python _tools\hash_manifest_edit.py --add ui\videos\1080\fco_myintro.bk2 ui\videos\2160\fco_myintro.bk2 --value <v1080> <v2160> --apply
   ```
4. **Point the series at it** in the round spec (`series_set`): `IntroVideoPath` `FCO_MyIntro.bk2`,
   `PlayIntroVideoFullScreen` true, `FirstCarSelectEnabled` false, `FirstCarSelectCars` `[]`; build and
   apply the kit as usual ([GETTING_STARTED](../en/GETTING_STARTED.md), step 8).

No vanilla video is overwritten. Without step 3 the series shows a black screen and goes on (D109).

**Fallback without the index:** four videos are named by no game data (`3d_carselect_vw`, `softbox`,
`3d_carselect_focus`, `3d_carselect_subaru`); `bk2_install.py --replace <slot>` writes over one of them,
with a backup and `--restore`, and a series in full screen that names the slot plays the new content (D111).

## Encoding

Bink 2 is a closed codec: no free encoder exists, `ffmpeg` cannot decode or encode it, and writing one is
not realistic. RAD's own *RAD Video Tools* (free download from RAD Game Tools) turns an MP4 or an image
sequence into a `.bk2`. Check its terms when you download it; the project ships no encoder and no game
video. `bk2_install.py` checks that the file is a Bink 2 before installing it.

## After a Steam update

*Verify files* or an update puts the vanilla index back (and removes nothing else of ours, or may remove
our files too): the series then shows a black screen and keeps working. Run steps 2 and 3 again.
