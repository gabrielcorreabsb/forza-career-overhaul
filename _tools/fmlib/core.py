"""Paths, errors and byte-exact JSON helpers."""

import base64
import hashlib
import json
import os

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(TOOLS)
DATA = os.path.join(ROOT, "_data")
PATCHES = os.path.join(ROOT, "patches")
WORK = os.path.join(ROOT, "_work")
DEFAULT_CACHE = os.path.join(
    os.environ.get("LOCALAPPDATA", ""), r"Microsoft.ForzaMotorsport\CmsCache")
ORACLE = os.path.join(TOOLS, "cmsoracle", "bin", "Release", "net10.0",
                      "cmsoracle.exe")

CHAMPIONSHIP_CAREER = 500
ALWAYS_OPEN = "9999-12-31 23:59:59.999"

# serializacoes candidatas do CMS (o BCS original e minificado, utf-8 cru)
JSON_STYLES = (dict(ensure_ascii=False, separators=(",", ":")),
               dict(ensure_ascii=True, separators=(",", ":")))


class FmError(Exception):
    """Invariant violated: the generator must stop, nothing is written."""


def b64sha(data):
    return base64.b64encode(hashlib.sha256(data).digest()).decode("ascii")


def json_load_exact(raw, label="json"):
    """Parses raw bytes and returns (obj, style) such that
    json_dump(obj, style) == raw. Fails if no known style reproduces it."""
    obj = json.loads(raw.decode("utf-8"))
    for kw in JSON_STYLES:
        if json.dumps(obj, **kw).encode("utf-8") == raw:
            return obj, kw
    raise FmError("%s: not byte-reproducible with known JSON styles" % label)


def json_dump(obj, style):
    return json.dumps(obj, **style).encode("utf-8")
