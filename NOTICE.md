<!-- docs_check: historical -->
# Notice

**Forza Career Overhaul** is an independent, fan-made research project. It is
**not affiliated with, endorsed by or sponsored by** Microsoft, Xbox Game
Studios or Turn 10 Studios. *Forza*, *Forza Motorsport* and related names and
marks are trademarks of Microsoft Corporation. Forza Motorsport 4 is cited only
as a design reference for the career structure; nothing from it is included or
distributed.

## What this repository does and does not contain

- It contains **our own code and documentation** (see `LICENSE` and
  `LICENSE-DOCS.md`).
- It contains **our own poster art** (`art/posters/`): images generated with
  Google's Nano Banana image model for this project, released under
  [CC BY 4.0](LICENSE-DOCS.md) like the documentation. They show no game
  asset, logo, real car, real driver or third-party text. Copyright in
  AI-generated images is uncertain in many countries; the license states how
  we want them used, not a guarantee.
- It contains **no game assets and no game executables**. Everything extracted
  from your own installation (`_extract/`, `_backup/`, `_out/`, `_work/`, the
  CmsCache copies) is generated locally and git-ignored.
- It contains **no third-party binaries, no decompiled third-party code and no
  encryption keys**. The CMS AES key and the Forza Mod Tool material must be
  obtained by you, from the original source, for your own use. See
  [docs/project/THIRD_PARTY.md](docs/project/THIRD_PARTY.md).
- It contains **no mod payloads**: kits are generated on your machine, from
  your own copy of the game, and are git-ignored. The game data they derive
  from belongs to its rights holders.

## Third-party credit

The camera settings in our install-only visual recipes (a free photo-mode camera and a softer race vignette)
were read from **Better Photo mode** by **GmSV2** on Nexus Mods
([Forza Motorsport mod 12](https://www.nexusmods.com/forzamotorsport/mods/12)). We reproduce only the setting
names and the direction of the changes, as our own recipe, and credit the author; none of the mod's files is
included. See [docs/reference/INSTALL_VISUAL_MODS.md](docs/reference/INSTALL_VISUAL_MODS.md).

The first-person camera values in the same recipes (field of view, gaze pitch, hood and bumper offsets and
the camera-physics tuning of the cockpit view and the driver eye position per car) were read from **Better Chaser and First Person Cam REWORKED**
by **Yar** on Nexus Mods ([Forza Horizon 6 mod 324](https://www.nexusmods.com/forzahorizon6/mods/324)) and
adapted to Forza Motorsport. The camera-tweak tutorial by **Wonder2k19**
([Forza Motorsport mod 35](https://www.nexusmods.com/forzamotorsport/mods/35)) documents the layer format we
edit. Same terms: only setting names and the direction of the changes, as our own recipe; none of the mods'
files is included.

## Your responsibility

Modding may violate the game's Terms of Use and can get you banned from online
features. Use it at your own risk, only on a copy of the game you own, and keep
the backups the pipeline makes before every write.

If you are a rights holder and want something removed, open an issue.
