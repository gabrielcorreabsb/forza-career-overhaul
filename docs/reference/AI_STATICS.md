# AI statics — the AI's global tuning in the install

The game keeps a set of global tuning files for the AI drivers in the install: `media\base\ai\aistatics.zip`, a
zip of INI files with one `Default.ini` and one `Track_<id>.ini` per track. It is read by the game (D76, D77 in
[DISCOVERIES](../project/DISCOVERIES.md)), it has no twin in the content cache, and so it is an **install-only**
change: Steam's *verify files* restores it. This page says what we changed in it and why. It holds no game file and
no game text: only key names and the direction of each change.

## What we changed

| key | direction | what it does | state |
|---|---|---|---|
| `SpeedScaleTendencyMax` | down | ceiling of the speed factor each AI driver gets | verified (D76) |
| `SpeedScaleTendencyMin` | up | floor of that factor: together with the ceiling it **narrows the speed band** of the AI | verified (D76) |
| `PredictiveRaceController\OffTrackSpeedLimitPercent` | up | how fast the AI may go while a wheel is off the track | observed (D77) |
| `PredictiveRaceController\OffTrackWaitForTrafficThisManySecondsBehind` | down | how long the AI waits for traffic behind it before rejoining | observed (one report) |
| `PredictiveRaceController\OffDirectionSpeedLimitPercent` | up | speed limit while the car points the wrong way | observed (one report) |
| `CrashRecoveryDriver\MaxSpeed` | up | speed allowed while recovering from a crash | observed (one report) |

- **Where.** The same edit goes into `Default.ini` and into each `Track_<id>.ini`, except a track whose own file
  already sets a different value for the key (the track file wins over the default).
- **Effect in game.** The AI of a series used to leave the track at the same corner, alone and with no contact.
  The narrow speed band cut that a lot at Brands Hatch GP and held on Lime Rock South Chicane, an oval and a class A
  field. The four recovery keys were raised together (a maintainer report: the AI "comes back faster and loses less
  control"), so which of the four counts is not known.
- **Part of a standard.** This is the *global tuning* part of the AI standard described in the
  [README](../../README.md): a levelled field at the class ceiling, a narrow speed band, a gentler recovery and a set
  of race switches.

## What is and is not published

The archive's content belongs to the game and is **not** in this repository, and neither is the tool we use to edit
it: reading the archive's entries needs the game's method-21 compression, which is handled by a Microsoft runtime
library we cannot distribute (see [THIRD_PARTY](../project/THIRD_PARTY.md)). The table above gives the keys and
the direction so you can make the same change to your own copy with a tool of your own. Keep the original of the
archive first, and apply the edit with the game closed.

## Limits

- Tested on Brands Hatch GP, Lime Rock South Chicane, the Eaglerock oval and a class A field, one run each; other
  tracks and classes are open ([OPEN_QUESTIONS](../project/OPEN_QUESTIONS.md)).
- The rewritten archive worked in game because it has almost no entries aligned to 4096 bytes. Archives that do
  have them must keep every entry at its offset ([D120](../project/DISCOVERIES.md), [MEDIA_MAP](MEDIA_MAP.md)).
- It is a global file, not a per-series switch: the edit applies wherever the game reads these AI settings.

See also: [MEDIA_MAP](MEDIA_MAP.md), [INSTALL_VISUAL_MODS](INSTALL_VISUAL_MODS.md), [MODDING_SURFACE](MODDING_SURFACE.md).
