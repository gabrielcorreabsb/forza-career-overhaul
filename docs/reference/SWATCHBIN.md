# Series art — the `.swatchbin` format

What a career poster or banner file looks like in Forza Motorsport (2023), and
what is still unproven before a series can ship its own art. It holds no game
images and no game text, only the layout, counts and status.

**Status: the read side is verified; nothing has been written to the game.**
Today a series reuses an existing poster or banner path
([MODDING_SURFACE](MODDING_SURFACE.md)).

## Where the files are

Four archives under `media\pcfamily\ui\textures\`, all with entries in ZIP
method 21 (XMem LZX). A read-only survey of all 1,107 entries, in the install,
found no exception to the layout below.

| Archive | Entries | Sizes (width×height: entries) |
|---|---|---|
| `data_bound\seriesposters.zip` | 332 | 424×660: 323 · 440×140: 5 · 1296×660: 3 · 440×302: 1 |
| `data_bound\seriesbanners.zip` | 196 | 380×100: 196 |
| `hires\data_bound\seriesposters.zip` | 386 | 848×1320: 325 · 880×280: 57 · 2592×1320: 3 · 880×604: 1 |
| `hires\data_bound\seriesbanners.zip` | 193 | 760×200: 193 |

The `hires` sizes are exactly double the others, but the entry counts differ, so
a name is not guaranteed to exist in both.

## Layout

Every surveyed file is one texture, encoding 9 (BC7), one slice, one mip, with a
144-byte header followed by the pixels. BC7 is 1 byte per pixel, so the file size
is `144 + width × height`. All numbers are little-endian.

| Offset | Field | Value in every surveyed file |
|---|---|---|
| 0 | bundle magic | `burG` on disk (the upstream docs write it as `Grub`) |
| 4 | bundle version, major and minor | 1, 1 |
| 16 | blob count | 1 |
| 20 | blob tag | `BCXT` on disk (`TXCB` upstream) |
| 24 | blob version, major and minor | 0, 0 |
| 26 | metadata count | 1 |
| 32 | offset of the pixel data | 144 |
| 44 | metadata tag | `HCXT` on disk (`TXCH` upstream) |
| 52 | start of the texture header, called `P` below | |
| P+24, P+28, P+32 | width, height, depth | see the table above; depth 1 |
| P+36 | slice count (low 14 bits), platform (high 2 bits) | 1, 0 |
| P+38 | mip count | 1 |
| P+39 | flags (cube map, premultiplied alpha) | 0 |
| P+40 to P+52 | transcoding, two colour profiles, domain | all 0 |
| P+56 | offset of the slice record, from `P` | |
| slice +0 | encoding | 9 (BC7) |
| slice +4 | offset of the mip record, from `P` | |
| mip +0 | mip size in bytes | equals file size minus 144 |

## What is not proven

Each of these needs a test in the game before anything is called working:

- **Writing the archive.** The archives are method 21. ForzaTech Studio cannot
  write that method, and its rebuild helpers fall back to Deflate. The Forza Mod
  Tool source has a repack path for existing entries. Nobody has shown that the
  game accepts either result.
- **New entries.** A repack of existing entries replaces art; adding a name for a
  new series is a separate question.
- **The two archives.** Which of the normal and `hires` files the game reads, and
  when, is unknown. A replacement should cover both.
- **Colour.** The colour profile fields are 0 in every file. How that maps to the
  colour space an encoder should target has not been checked.
- **Reach.** The art lives in the install, not in the cache, so it does not travel
  with a cache kit.

The smallest useful test replaces one existing poster, in both archives, with an
image of the same size, and looks at it on the series screen.

## Using the upstream documentation

The [ForzaTech Studio docs](https://github.com/D3FEKT/ForzaTechStudio/tree/Main/docs)
(MIT) cover many Forza titles, so check each claim against this game. Compared
with Motorsport (2023), as surveyed above and in the install inventory:

- The structure and the encoding table in its Swatchbin page match.
- Its rule "blob version 1.x is PC, 2.x is Xbox" does not: these PC files are 0.0.
  Do not detect the platform from the version alone.
- Its Create Zip page says the engine requires Store archives. The install has
  about 16,500 Deflate and 1.4 million method 21 entries, so that does not hold
  here. It also calls the builder's output Store, while the code uses Deflate when
  that compresses better.
- The install has no `.minizip` and no `.pb` files. Those sections do not apply.
- Its BXML page warns that a `.xml` can be binary. None of the 72,099 `.xml` files
  in the local decrypted dump is.
