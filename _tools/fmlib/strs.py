"""IDS_ keys in LocStrings_*.str (game resolves by ghash, any length works)."""

import hashlib
import sys

from .core import TOOLS, FmError

sys.path.insert(0, TOOLS)
from str_edit import StrTable, ghash  # noqa: E402

LOGICAL_PT = "LocStrings_pt-BR.str"
KEY_PREFIX = "MC44"


def key_for(label, prefix=KEY_PREFIX):
    """Deterministic key: IDS_<md5("MC44|<label>")> (convention since mc44)."""
    return "IDS_" + hashlib.md5(("%s|%s" % (prefix, label)).encode("utf-8")
                                ).hexdigest()


def add_keys(raw, pairs, allow_existing=False):
    """Adds [(key, value)] to a .str; existing values never change.
    Returns the new bytes (round-trip checked)."""
    table = StrTable.load(raw)
    if table.to_bytes() != raw:
        raise FmError(".str does not round-trip byte-exact")
    before = table.values_by_name()
    keys = set(table.sections[0].keys) | set(table.sections[1].keys)
    added = []
    for name, value in pairs:
        cur = table.get(name)
        if cur is not None:
            if allow_existing and cur == value:
                continue
            raise FmError(".str key %s already exists (%r)" % (name, cur))
        if ghash(name) in keys:
            raise FmError("ghash collision for %s" % name)
        table.set_value(name, value)
        keys.add(ghash(name))
        added.append((name, value))
    new_raw = table.to_bytes()
    check = StrTable.load(new_raw)
    after = check.values_by_name()
    for name, value in before.items():
        if after.get(name) != value:
            raise FmError(".str existing key %s changed" % name)
    for name, value in added:
        if check.get(name) != value:
            raise FmError(".str new key %s did not survive reparse" % name)
    if check.to_bytes() != new_raw:
        raise FmError(".str output does not re-serialize byte-exact")
    return new_raw


def get(raw, name):
    return StrTable.load(raw).get(name)
