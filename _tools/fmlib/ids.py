"""Custom id ranges and retired ids (patches/ids_retired.json)."""

import json
import os

from .core import PATCHES, FmError

SERIES_MIN = 20000
EVENT_RANGE = (65897900, 65900000)   # vanilla usa ids maiores (7xxxxxxx...)


def is_custom_event(eid):
    return EVENT_RANGE[0] <= eid < EVENT_RANGE[1]


def retired():
    path = os.path.join(PATCHES, "ids_retired.json")
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def check_new(kind, value, used):
    """kind in series/events/cups/ladders; raises if used, retired or (for
    series/events) outside the custom range."""
    if value in used:
        raise FmError("%s id %d already in use" % (kind, value))
    if value in retired().get(kind, []):
        raise FmError("%s id %d is retired (patches/ids_retired.json)"
                      % (kind, value))
    if kind == "series" and value < SERIES_MIN:
        raise FmError("series id %d below custom range (>= %d)"
                      % (value, SERIES_MIN))
    if kind == "events" and not is_custom_event(value):
        raise FmError("event id %d outside custom range %s"
                      % (value, EVENT_RANGE))


def next_free(kind, used, start, stop):
    ret = set(retired().get(kind, []))
    for i in range(start, stop):
        if i not in used and i not in ret:
            return i
    raise FmError("no free %s id in [%d, %d)" % (kind, start, stop))


RETIRED_ORDER = ("_doc", "series", "events", "cups", "ladders")


def retire(kind, values):
    """Appends ids to patches/ids_retired.json (sorted, idempotent).
    Returns the ids actually added (empty when everything was retired)."""
    if kind not in RETIRED_ORDER[1:]:
        raise FmError("unknown id kind %r (expected one of %s)"
                      % (kind, list(RETIRED_ORDER[1:])))
    path = os.path.join(PATCHES, "ids_retired.json")
    data = retired() if os.path.isfile(path) else {}
    current = set(data.get(kind, []))
    wanted = set(int(v) for v in values)
    added = sorted(wanted - current)
    if not added:
        return []
    data[kind] = sorted(current | wanted)
    ordered = dict((k, data[k]) for k in RETIRED_ORDER if k in data)
    for k in sorted(data):
        ordered.setdefault(k, data[k])
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(ordered, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    return added
