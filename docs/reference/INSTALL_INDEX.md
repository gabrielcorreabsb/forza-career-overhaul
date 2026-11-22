# The install's file index — `hash.manifest`

Why a new file dropped into the game's install is ignored, and how to make the game see it.
It holds no game data: only the layout, the counts and the method, all checked on the
install of 19/11/2026.

**Status: verified (D112, D113).** The record format and the hash were rebuilt from the disk for
every record of both index files; a video under a new name, invisible before, played in game once
its path had a record.

## What it is

The game does not open files from `media\` through Windows directly: it asks its own file system,
and that file system only knows the paths listed in an index. There is one index per media root:

| Index | Records | Files | Folders |
|---|---|---|---|
| `media\base\hash.manifest` | 2,261 | 2,186 | 75 |
| `media\pcfamily\hash.manifest` | 2,927 | 2,859 | 68 |

A file that exists on disk but has no record is, for the game, not there. That is why a copy of a
working intro video under a new name gave a black screen (D109), and why the same copy played as soon
as its record was added (D113). An existing file whose **content** changes keeps its record, so
overwriting a file in place has always worked (posters, videos, `.ini` files).

## Layout

A 12-byte header, then fixed 12-byte records, with no count field (the count is the file size minus
the header, divided by 12) and in no particular order:

| bytes | field |
|---|---|
| 8 | hash of the path (64-bit, little-endian) |
| 4 | a value: the content chunk the file belongs to (for car files it matches the chunk id in `contentmanifest.xml`); 0 for a folder |

Folders have records too (value 0), so a new file in an existing folder needs only its own record.

## The hash

A modified DJB2, run twice over the path:

- the path is **relative to the media root** (`ui\videos\1080\name.bk2` for a file under
  `media\base`), in **lower case**, with **backslashes**, no leading or trailing slash;
- one 32-bit pass starts at 5381 and, for each character `c`, does
  `h = h XOR (c + (h >> 2) + h * 32)`, all modulo 2^32;
- a second pass runs over the same path, starting from the result of the first;
- the 64-bit hash is `(second << 32) | first`.

This is the method the community tool *ForzaTools* calls `HashManifestHasher`; our check rebuilt every
record of both indexes from the files on disk, with no record left over.

## Adding a record

[`_tools/hash_manifest_edit.py`](../../_tools/hash_manifest_edit.py) appends records and never touches a
vanilla one:

```powershell
python _tools\hash_manifest_edit.py --check ui\videos\1080\practicalperformance.bk2
python _tools\hash_manifest_edit.py --add ui\videos\1080\fco_myintro.bk2 ui\videos\2160\fco_myintro.bk2 --value <v1080> <v2160>
python _tools\hash_manifest_edit.py --add ... --apply          # game CLOSED
python _tools\hash_manifest_edit.py --remove ui\videos\1080\fco_myintro.bk2 --apply   # drops a record this tool added
python _tools\hash_manifest_edit.py --restore --apply          # puts the original index back
```

It refuses a path that is not on disk or is already indexed, and an index that changed since its last
write (a Steam update). The first write keeps a backup of the original. For the value, reuse the one of
a file of the same kind (`--check` on a vanilla video shows it); what the game does with a wrong value is
untested.

## Limits

- Steam's *verify files* or an update brings the vanilla index back: the new file is then ignored again
  (a video shows a black screen; nothing else breaks) until the record is added again.
- Some files the game reads are not in the index (the game database and one zip manifest), so other
  loading paths exist; this index is the one that gated the intro videos.
- It changes nothing in the cache (`CmsCache`): career data still goes through the kits.
