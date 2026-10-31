"""Read-only view of the game cache: snapshots, manifests, payloads.

Payloads are resolved by Checksum (never by name/mtime): two snapshots share
same-shaped blobs and matching by name picked the wrong blob once.
"""

import json
import os
import zipfile

from .core import DEFAULT_CACHE, FmError, b64sha


class Cache:
    def __init__(self, cache_dir=None):
        self.dir = os.path.abspath(cache_dir or DEFAULT_CACHE)
        prod_dir = os.path.join(self.dir, "prod")
        if not os.path.isdir(prod_dir):
            raise FmError("prod\\ not found in %s" % self.dir)
        self.snapshots = sorted(
            n for n in os.listdir(prod_dir)
            if os.path.isfile(os.path.join(prod_dir, n)))
        if not self.snapshots:
            raise FmError("no snapshot in %s" % prod_dir)
        self._prod = {}
        self._index = {}    # logical -> [payload bytes] (every blob copy)

    @property
    def live(self):
        return self.snapshots[-1]

    def prod(self, snap):
        if snap not in self._prod:
            with open(os.path.join(self.dir, "prod", snap), "rb") as fh:
                self._prod[snap] = json.loads(fh.read().decode("utf-8-sig"))
        return self._prod[snap]

    def files(self, snap):
        return {f["Path"]: f for f in self.prod(snap).get("Files", [])}

    def group_of(self, snap, logical):
        for g in self.prod(snap).get("ContentGroups", []):
            if logical in g.get("FileNames", []):
                return g["GroupName"]
        return None

    def _ensure_index(self, logicals):
        missing = [n for n in logicals if n not in self._index]
        if not missing:
            return
        for n in missing:
            self._index[n] = []
        for dp, _dirs, fs in os.walk(self.dir):
            for f in fs:
                try:
                    zf = zipfile.ZipFile(os.path.join(dp, f))
                except (zipfile.BadZipFile, OSError):
                    continue
                with zf:
                    names = set(zf.namelist())
                    for n in missing:
                        if n in names:
                            self._index[n].append(zf.read(n))

    def in_cache(self, snap, logical):
        """True if the snapshot's entry lives in a cache blob (not install)."""
        ck = self.files(snap).get(logical, {}).get("Checksum")
        self._ensure_index([logical])
        return ck is not None and any(b64sha(p) == ck
                                      for p in self._index[logical])

    def payload(self, snap, logical):
        """Encrypted payload of `logical` in `snap` (unique, by Checksum)."""
        f = self.files(snap).get(logical)
        if f is None:
            raise FmError("%s: %s not in the snapshot manifest" % (snap, logical))
        self._ensure_index([logical])
        hits = {p for p in self._index[logical] if b64sha(p) == f["Checksum"]}
        if not hits:
            raise FmError("%s: no cache blob has %s with the snapshot Checksum "
                          "(%s...)" % (snap, logical, f["Checksum"][:12]))
        if len(hits) != 1:
            raise FmError("%s: %d distinct payloads for %s"
                          % (snap, len(hits), logical))
        return hits.pop()
