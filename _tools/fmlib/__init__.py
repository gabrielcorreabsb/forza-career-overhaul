"""fmlib - shared library for kit generators (Forza Career Overhaul).

Replaces the helpers copied across _tools/mc30..mc58 (load_prod, index_blobs,
resolve, champ500, find_cup/ladder/series, key_for, encrypt...). Generators
read the game cache (never write it) and produce a kit in patches/<kit>/;
applying is always done by _tools/cache_edit.py.

Modules:
  core     paths, FmError, b64sha, exact JSON round-trip
  cache    Cache: snapshots, prod manifests, payload resolution by Checksum
  crypto   decrypt / encrypt (cmsoracle, template = current payload)
  bcs      BuildersCupScheduleDataV4 navigation, invariants, clones
  carsxml  BCSeriesSelectableCars.xml entries
  overrides BCEventOverrides.json clones
  strs     IDS_ keys for LocStrings_*.str
  cars     _data/cars.json + denylist -> acceptlists
  ids      custom id ranges, retired ids, free-id allocation
  kit      Kit writer: .enc + plan.json + NOTA.md skeleton
"""
