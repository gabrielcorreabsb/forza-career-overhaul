#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_series.py - new career series kit from a declarative spec.

Implements docs/F3_TEMPLATE.md 1 (steps 1-9) on top of _tools/fmlib:
ids -> series shell clone -> ladder (existing or new, optionally new cup)
-> events cloned from existing tracks -> one BCEventOverrides sibling per
event -> BCSeriesSelectableCars.xml entry -> IDS_ key in LocStrings_pt-BR.str.

READ-ONLY on the game cache. Output: patches/<kit>/ (plan.json + .enc +
NOTA.md). Apply with cache_edit.py (dry-run first). Spec format:
specs/_TEMPLATE.json (documented in specs/README.md).

Usage:
  python _tools\\build_series.py --spec specs\\<serie>.json
  python _tools\\build_series.py --spec specs\\x.json --cache-dir _work\\cachetest --out _work\\kit_x
"""

import argparse
import copy
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fmlib import bcs as B  # noqa: E402
from fmlib import cars as C  # noqa: E402
from fmlib import carsxml, crypto, ids, nested, overrides, strs  # noqa: E402
from fmlib.cache import Cache  # noqa: E402
from fmlib.core import FmError, ROOT, WORK, json_dump, json_load_exact  # noqa: E402
from fmlib.kit import Kit  # noqa: E402

WARN = []

ROUND_FIELDS = ("kit", "title", "question", "mask", "min_condition", "refutes")
ROUND_MAX_SERIES = 5
ROUND_MAX_EVENTS = 5
ROUND_NAME_RE = re.compile(r"^Test: .+ \[(\d+)\]$")
ROUND_OPS = ("rename_cup", "rename_ladder", "remove_series", "remove_ladder",
             "remove_cup", "describe_cup", "set_cup",
             "set_series")
ROUND_MAX_TEXT = 2000
ROUND_EVENT_KEYS = ("event_id", "track", "laps")
ROUND_MAX_AIFIELD = 12
ROUND_RANGE_KEYS = ("PIMin", "PIMax", "PowerMin", "PowerMax", "WeightMin",
                    "WeightMax", "YearMin", "YearMax", "BaseCostMin",
                    "BaseCostMax", "CarLevelMin", "CarLevelMax")
ROUND_RANGE_FLOAT = {"PowerMin", "PowerMax", "WeightMin", "WeightMax"}
ROUND_RANGE_OFF255 = {"CarLevelMin", "CarLevelMax"}



def warn(msg):
    WARN.append(msg)
    print("  WARNING: " + msg)


# --------------------------------------------------------------------------- #
# spec
# --------------------------------------------------------------------------- #
def load_spec(path):
    with open(path, encoding="utf-8-sig") as fh:
        spec = json.load(fh)
    for k in ("kit", "series", "placement", "events", "cars"):
        if k not in spec:
            raise FmError("spec: missing '%s'" % k)
    s = spec["series"]
    for k in ("id", "name", "donor_series"):
        if k not in s:
            raise FmError("spec.series: missing '%s'" % k)
    if not spec["events"]:
        raise FmError("spec.events is empty")
    for i, e in enumerate(spec["events"]):
        for k in ("id", "track"):
            if k not in e:
                raise FmError("spec.events[%d]: missing '%s'" % (i, k))
    return spec


def name_key(label_or_name):
    return strs.key_for(label_or_name)


def desc_key(label):
    """IDS_ key of a description text (labels desc|<id>, desc|ladder|<id>,
    desc|cup|<id>; one key per target, so two series may share a text)."""
    return strs.key_for(label)


def lock_key(label):
    """IDS_ key of a lock text (label lock|<id>; one key per series, so a
    lock text is always ours)."""
    return strs.key_for(label)


def check_description(value, tag):
    """series[].description and series[].lock_text: "" (empty), a text, or
    {"from_series": <id>}."""
    if isinstance(value, str):
        if len(value) > ROUND_MAX_TEXT:
            raise FmError("%s: text has %d characters (max %d)"
                          % (tag, len(value), ROUND_MAX_TEXT))
        return value
    if isinstance(value, dict):
        unknown = set(value) - {"from_series"}
        if unknown or len(value) != 1:
            raise FmError("%s: an object must be exactly "
                          '{"from_series": <series id>}' % tag)
        v = value["from_series"]
        if isinstance(v, bool) or not isinstance(v, int):
            raise FmError("%s: 'from_series' must be an integer series id"
                          % tag)
        return value
    raise FmError("%s: must be a string (empty leaves it blank) or "
                  '{"from_series": <series id>}' % tag)


def check_text(value, tag):
    """group.description and ops.describe_cup.text: non-empty text."""
    if not isinstance(value, str) or not value:
        raise FmError("%s: must be a non-empty string" % tag)
    if len(value) > ROUND_MAX_TEXT:
        raise FmError("%s: text has %d characters (max %d)"
                      % (tag, len(value), ROUND_MAX_TEXT))
    return value


# --------------------------------------------------------------------------- #
# round spec (--round): one ladder per experiment, series cloned from a base
# --------------------------------------------------------------------------- #
POSTER_DIR = "GAME:\\Media\\UI\\Textures\\Data_Bound\\SeriesPosters\\"
POSTER_NAME_RE = re.compile(r"^FCO_[A-Za-z0-9_]{1,48}$")


def check_poster(item, tag):
    """series[].poster = {name: FCO_*, image, [image_hires]}: our own poster
    (D99-D104). The series gets ImagePath; the kit gets posters.json, the
    manifest that swatchbin_edit.py --manifest installs."""
    p = item["poster"]
    if not isinstance(p, dict) or set(p) - {"name", "image", "image_hires"} \
            or "name" not in p or "image" not in p:
        raise FmError("%s.poster: needs {name, image[, image_hires]}" % tag)
    if not isinstance(p["name"], str) or not POSTER_NAME_RE.match(p["name"]):
        raise FmError("%s.poster.name %r: must be FCO_<letters, digits, _> "
                      "(never a vanilla name)" % (tag, p["name"]))
    for k in ("image", "image_hires"):
        if k in p and (not isinstance(p[k], str) or not p[k].strip()):
            raise FmError("%s.poster.%s: a path to a PNG" % (tag, k))
    if "ImagePath" in item.get("series_set", {}):
        raise FmError("%s: poster and series_set.ImagePath both set the "
                      "poster (two sources) - keep one" % tag)


def poster_path(item):
    return POSTER_DIR + item["poster"]["name"] + ".png"


def write_poster_manifest(spec, spec_path, kit_dir):
    """posters.json next to the plan: the install half of the round."""
    base = os.path.dirname(os.path.abspath(spec_path))
    add, seen = [], set()
    for item in spec["series"]:
        p = item.get("poster")
        if not p:
            continue
        if p["name"].lower() in seen:
            continue              # two series may share one poster
        seen.add(p["name"].lower())
        ent = {"name": p["name"]}
        for k in ("image", "image_hires"):
            if k in p:
                src = os.path.normpath(os.path.join(base, p[k]))
                if not os.path.isfile(src):
                    raise FmError("poster %s: %s not found" % (p["name"], src))
                try:
                    ent[k] = os.path.relpath(src, kit_dir).replace("\\", "/")
                except ValueError:        # another drive: keep it absolute
                    ent[k] = src
        add.append(ent)
    if not add:
        return None
    out = os.path.join(kit_dir, "posters.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"_doc": "install half of %s: python _tools\\swatchbin_edit"
                           ".py --allow-install --manifest <this file> "
                           "(--dry-run first; game closed)" % spec["kit"],
                   "codec": "deflate", "add": add}, fh, indent=1)
        fh.write("\n")
    return out


def load_round_spec(path):
    """Validates a round spec; refuses before anything is written."""
    with open(path, encoding="utf-8-sig") as fh:
        spec = json.load(fh)
    for k in ROUND_FIELDS:
        v = spec.get(k)
        if not isinstance(v, str) or not v.strip():
            raise FmError("round spec: missing '%s' - question, mask, "
                          "min_condition and refutes fill the NOTA 'Para que "
                          "serve'; kit and title are required too" % k)
    for k in ("group", "base", "series"):
        if k not in spec:
            raise FmError("round spec: missing '%s'" % k)
    if isinstance(spec["group"], dict) and (
            "set" in spec["group"]
            or (isinstance(spec["group"].get("cup"), dict)
                and "set" in spec["group"]["cup"])):
        group_placement(spec["group"])          # validates group.set and group.cup.set
    if isinstance(spec["group"], dict) and "description" in spec["group"]:
        check_text(spec["group"]["description"],
                   "round spec.group.description")
    series = spec["series"]
    if not isinstance(series, list):
        raise FmError("round spec: 'series' must be a list")
    if len(series) > ROUND_MAX_SERIES:
        raise FmError("round spec: %d series (max %d per round)"
                      % (len(series), ROUND_MAX_SERIES))
    if not series and not spec.get("ops") and not spec.get("aifield"):
        raise FmError("round spec: nothing to do ('series', 'ops' and "
                      "'aifield' are all empty)")
    base = spec["base"]
    if not isinstance(base, dict) or not isinstance(base.get("series"), int):
        raise FmError("round spec.base: needs 'series' (the donor series id)")
    seen = set()
    seen_ev = set()
    for i, item in enumerate(series):
        multi = "events" in item
        if multi:
            if "event_id" in item:
                raise FmError("round spec.series[%d]: 'event_id' and 'events' "
                              "together are ambiguous (use events[].event_id)"
                              % i)
            for k in ("track", "donor_event", "track_alias_of"):
                if k in item:
                    raise FmError("round spec.series[%d]: top-level '%s' has "
                                  "no meaning with 'events' (each event "
                                  "declares its own track)" % (i, k))
            ev_specs = item["events"]
            if not isinstance(ev_specs, list) or not ev_specs:
                raise FmError("round spec.series[%d].events: needs a "
                              "non-empty list" % i)
            if len(ev_specs) > ROUND_MAX_EVENTS:
                raise FmError("round spec.series[%d]: %d events (max %d per "
                              "series)" % (i, len(ev_specs),
                                           ROUND_MAX_EVENTS))
            for j, ev_spec in enumerate(ev_specs):
                tag = "round spec.series[%d].events[%d]" % (i, j)
                if not isinstance(ev_spec, dict):
                    raise FmError("%s: must be an object" % tag)
                unknown = set(ev_spec) - set(ROUND_EVENT_KEYS)
                if unknown:
                    raise FmError("%s: unknown key(s) %s (expected %s)"
                                  % (tag, sorted(unknown),
                                     list(ROUND_EVENT_KEYS)))
                v = ev_spec.get("event_id")
                if isinstance(v, bool) or not isinstance(v, int):
                    raise FmError("%s: missing integer 'event_id'" % tag)
                for k in ("track", "laps"):
                    if k in ev_spec and (
                            isinstance(ev_spec[k], bool)
                            or not isinstance(ev_spec[k], int)):
                        raise FmError("%s: '%s' must be an integer"
                                      % (tag, k))
                if "laps" in ev_spec and ev_spec["laps"] < 1:
                    raise FmError("%s: 'laps' must be >= 1" % tag)
                if ev_spec["event_id"] in seen_ev:
                    raise FmError("round spec: event %d declared twice"
                                  % ev_spec["event_id"])
                seen_ev.add(ev_spec["event_id"])
        else:
            for k in ("event_id",):
                if k not in item:
                    raise FmError("round spec.series[%d]: missing '%s'"
                                  % (i, k))
            if item["event_id"] in seen_ev:
                raise FmError("round spec: event %d declared twice"
                              % item["event_id"])
            seen_ev.add(item["event_id"])
        if "track_alias_of" in item:
            tag = "round spec.series[%d].track_alias_of" % i
            a = item["track_alias_of"]
            if isinstance(a, bool) or not isinstance(a, int) or a < 1:
                raise FmError("%s: must be a positive integer (the existing "
                              "SerialTrackId whose event/override are cloned)"
                              % tag)
            t = item.get("track")
            if isinstance(t, bool) or not isinstance(t, int):
                raise FmError("%s: needs an integer 'track' (the new "
                              "SerialTrackId the clone runs on)" % tag)
            if t == a:
                raise FmError("%s: equals 'track' (an alias of itself is "
                              "just a normal series)" % tag)
        for k in ("id", "name"):
            if k not in item:
                raise FmError("round spec.series[%d]: missing '%s'" % (i, k))
        m = ROUND_NAME_RE.match(item["name"])
        if m is None:
            raise FmError("round spec.series[%d]: name %r must be "
                          "'Test: <variation> [<id>]'"
                          % (i, item["name"]))
        if int(m.group(1)) != item["id"]:
            raise FmError("round spec.series[%d]: the name says id %s but "
                          "'id' is %d" % (i, m.group(1), item["id"]))
        if item["id"] in seen:
            raise FmError("round spec: series %d declared twice" % item["id"])
        seen.add(item["id"])
        for k in ("event", "override", "series_set", "cars", "ai_cars"):
            if k in item and not isinstance(item[k], dict):
                raise FmError("round spec.series[%d].%s must be an object"
                              % (i, k))
        if "event" in item and "PointSpread" in item["event"]:
            ps = item["event"]["PointSpread"]
            if (not isinstance(ps, list) or len(ps) != 24
                    or any(isinstance(v, bool) or not isinstance(v, int)
                           or v < 0 for v in ps)):
                raise FmError("round spec.series[%d].event.PointSpread: must "
                              "be a list of exactly 24 integers >= 0 (never "
                              "bool, float or string) - the same table "
                              "applies to every event of the series" % i)
        if "cars" in item:
            c = item["cars"]
            tag = "round spec.series[%d].cars" % i
            unknown = set(c) - {"acceptlist", "blocklist", "class",
                                "division", "severity", "ranges", "ownership",
                                "spec_division"}
            if unknown:
                raise FmError("%s: unknown key(s) %s (expected "
                              "acceptlist|blocklist/[class]/[division]/"
                              "[severity]/[ranges]/[ownership]/[spec_division])"
                              % (tag, sorted(unknown)))
            if "ownership" in c and (
                    not isinstance(c["ownership"], str)
                    or not re.fullmatch(r"[A-Za-z]{1,24}", c["ownership"])):
                raise FmError("%s: 'ownership' must be a word of 1-24 "
                              "letters (the token the game reads, e.g. None)"
                              % tag)
            if ("acceptlist" in c) == ("blocklist" in c):
                raise FmError("%s: exactly one of 'acceptlist' (non-empty) "
                              "or 'blocklist' (may be empty)" % tag)
            lkey = "acceptlist" if "acceptlist" in c else "blocklist"
            al = c[lkey]
            if (not isinstance(al, list)
                    or (lkey == "acceptlist" and not al)
                    or any(isinstance(v, bool) or not isinstance(v, int)
                           for v in al)):
                raise FmError("%s: '%s' must be a list of car ids "
                              "(acceptlist: non-empty)" % (tag, lkey))
            if "spec_division" in c and (
                    isinstance(c["spec_division"], bool)
                    or not isinstance(c["spec_division"], int)
                    or not 0 <= c["spec_division"] <= 255):
                raise FmError("%s: 'spec_division' must be an integer 0-255 "
                              "(gamedb SeriesSpecDivisions id; XML only - the "
                              "BCS SelectableCars has no such field)" % tag)
            if "severity" in c and c["severity"] not in ("None", "Strict"):
                raise FmError("%s: 'severity' must be None or Strict" % tag)
            if "class" in c and (not isinstance(c["class"], str)
                                 or len(c["class"]) != 1):
                raise FmError("%s: 'class' must be a single letter "
                              "(C/B/A/S/R)" % tag)
            if "division" in c and not isinstance(c["division"], str):
                raise FmError("%s: 'division' must be a string" % tag)
            if "ranges" in c:
                r = c["ranges"]
                rtag = "%s.ranges" % tag
                if not isinstance(r, dict) or not r:
                    raise FmError("%s: must be a non-empty object" % rtag)
                unknown = set(r) - set(ROUND_RANGE_KEYS)
                if unknown:
                    raise FmError("%s: unknown key(s) %s (expected %s)"
                                  % (rtag, sorted(unknown),
                                     "|".join(ROUND_RANGE_KEYS)))
                for key, val in r.items():
                    if isinstance(val, bool) or \
                            not isinstance(val, (int, float)) or \
                            (isinstance(val, float) and
                             not math.isfinite(val)):
                        raise FmError("%s: '%s' must be a finite number "
                                      "(never bool)" % (rtag, key))
                for lo, hi in (("PIMin", "PIMax"), ("PowerMin", "PowerMax"),
                               ("WeightMin", "WeightMax"),
                               ("YearMin", "YearMax"),
                               ("BaseCostMin", "BaseCostMax")):
                    if lo in r and hi in r and r[lo] > 0 and r[hi] > 0 \
                            and r[lo] > r[hi]:
                        raise FmError("%s: '%s' (%s) > '%s' (%s)" %
                                      (rtag, lo, r[lo], hi, r[hi]))
                for key in sorted(ROUND_RANGE_OFF255):
                    v = r.get(key)
                    if v is not None and (isinstance(v, bool) or
                                          not isinstance(v, int) or
                                          not 0 <= v <= 255):
                        raise FmError("%s: '%s' must be an integer 0-255 "
                                      "(255 = off, never bool)"
                                      % (rtag, key))
                if "CarLevelMin" in r and "CarLevelMax" in r \
                        and r["CarLevelMin"] < 255 \
                        and r["CarLevelMax"] < 255 \
                        and r["CarLevelMin"] > r["CarLevelMax"]:
                    raise FmError("%s: 'CarLevelMin' (%s) > 'CarLevelMax' (%s)"
                                  % (rtag, r["CarLevelMin"],
                                     r["CarLevelMax"]))
        if "ai_cars" in item:
            a = item["ai_cars"]
            atag = "round spec.series[%d].ai_cars" % i
            unknown = set(a) - {"acceptlist"}
            if unknown:
                raise FmError("%s: unknown key(s) %s (expected "
                              "acceptlist)" % (atag, sorted(unknown)))
            al = a.get("acceptlist")
            if not isinstance(al, list) or not al or \
                    any(isinstance(v, bool) or not isinstance(v, int)
                        for v in al):
                raise FmError("%s: 'acceptlist' must be a non-empty list of "
                              "car ids" % atag)
        if "description" in item:
            check_description(item["description"],
                              "round spec.series[%d].description" % i)
        if "lock_text" in item:
            check_description(item["lock_text"],
                              "round spec.series[%d].lock_text" % i)
            ss = item.get("series_set", {})
            if "EntryCriteria.EntryCriteriaName" in ss:
                raise FmError("round spec.series[%d]: 'lock_text' and "
                              "series_set.EntryCriteria.EntryCriteriaName both "
                              "set the lock text (two sources) - keep one"
                              % i)
        if "poster" in item:
            check_poster(item, "round spec.series[%d]" % i)
        if "poster_brief" in item and (
                not isinstance(item["poster_brief"], str)
                or not item["poster_brief"].strip()):
            raise FmError("round spec.series[%d].poster_brief: a non-empty "
                          "line of text" % i)
        if multi and "donor" in item.get("override", {}):
            raise FmError("round spec.series[%d]: common 'override.donor' "
                          "has no meaning with 'events' (each event takes "
                          "its track donor)" % i)
    for i, op in enumerate(spec.get("ops", [])):
        if not isinstance(op, dict) or op.get("op") not in ROUND_OPS:
            raise FmError("round spec.ops[%d]: 'op' must be one of %s"
                          % (i, ", ".join(ROUND_OPS)))
        if not isinstance(op.get("id"), int):
            raise FmError("round spec.ops[%d]: missing integer 'id'" % i)
        if op["op"].startswith("rename") and not op.get("name"):
            raise FmError("round spec.ops[%d]: rename needs 'name'" % i)
        if op["op"] == "set_series":
            ss = op.get("set")
            if isinstance(op["id"], bool) or op["id"] < 20000                     or not isinstance(ss, dict) or not ss or any(
                        not isinstance(k, str) or not k for k in ss):
                raise FmError("round spec.ops[%d]: set_series needs the "
                              "integer 'id' of one of our series (>= 20000) "
                              "and 'set' = a non-empty object of existing "
                              "top-level series fields -> values" % i)
        if op["op"] == "set_cup":
            cs = op.get("set")
            if isinstance(op["id"], bool) or not isinstance(cs, dict)                     or not cs or any(
                        not isinstance(k, str) or not k
                        or isinstance(v, (dict, list)) for k, v in cs.items()):
                raise FmError("round spec.ops[%d]: set_cup needs an integer "
                              "'id' and 'set' = a non-empty object of "
                              "top-level cup fields -> scalar values" % i)
        if op["op"] == "describe_cup":
            if isinstance(op["id"], bool):
                raise FmError("round spec.ops[%d]: 'id' must be an integer"
                              % i)
            check_text(op.get("text"), "round spec.ops[%d].text" % i)
    repoint = spec.get("repoint")
    if repoint is not None:
        if not isinstance(repoint, list) or not repoint:
            raise FmError("round spec: 'repoint' must be a non-empty list of "
                          "{override_id, from, to}")
        for i, e in enumerate(repoint):
            tag = "round spec.repoint[%d]" % i
            if not isinstance(e, dict):
                raise FmError("%s: must be an object" % tag)
            unknown = set(e) - {"override_id", "from", "to"}
            if unknown:
                raise FmError("%s: unknown key(s) %s (expected "
                              "override_id/from/to)" % (tag, sorted(unknown)))
            for k in ("override_id", "from", "to"):
                if k not in e:
                    raise FmError("%s: missing '%s'" % (tag, k))
            if isinstance(e["override_id"], bool) or \
                    not isinstance(e["override_id"], int):
                raise FmError("%s: 'override_id' must be an integer" % tag)
            for k in ("from", "to"):
                if not isinstance(e[k], str) or not e[k].strip():
                    raise FmError("%s: '%s' must be a non-empty string"
                                  % (tag, k))
    aif = spec.get("aifield")
    if aif is not None:
        if not isinstance(aif, list) or not aif:
            raise FmError("round spec: 'aifield' must be a non-empty list of "
                          "definitions (specs/aifield/<name>.json)")
        if len(aif) > ROUND_MAX_AIFIELD:
            raise FmError("round spec: %d aifield definitions (max %d per "
                          "round)" % (len(aif), ROUND_MAX_AIFIELD))
        seen_def = set()
        for i, path in enumerate(aif):
            if not isinstance(path, str) or not path.strip():
                raise FmError("round spec.aifield[%d]: must be a path string"
                              % i)
            key = os.path.normcase(os.path.abspath(path))
            if key in seen_def:
                raise FmError("round spec.aifield[%d]: %s declared twice"
                              % (i, path))
            seen_def.add(key)
    return spec


def round_event_ids(item):
    """All event ids a round series declares (legacy or events[])."""
    if "events" in item:
        return [e["event_id"] for e in item["events"]]
    return [item["event_id"]]


def group_placement(group):
    """round 'group' -> the placement dict resolve_placement understands."""
    if isinstance(group, int):
        return {"ladder": group}
    if not isinstance(group, dict):
        raise FmError("round spec.group: an existing ladder id or "
                      "{name, donor, cup}")
    for k in ("name", "donor", "cup"):
        if k not in group:
            raise FmError("round spec.group: missing '%s'" % k)
    if "id" in group and (isinstance(group["id"], bool)
                         or not isinstance(group["id"], int)):
        raise FmError("round spec.group: 'id' must be an integer ladder id")
    if "description" in group:
        check_text(group["description"], "round spec.group.description")
    if isinstance(group["cup"], dict) and "set" in group["cup"]:
        cs = group["cup"]["set"]
        if not isinstance(cs, dict) or not cs or any(
                not isinstance(k, str) or not k or isinstance(v, (dict, list))
                for k, v in cs.items()):
            raise FmError("round spec.group.cup.set: a non-empty object of "
                          "top-level cup fields -> scalar values")
    lad = {"id": group.get("id", "auto"), "donor": group["donor"], "name": group["name"],
           "cup": group["cup"]}
    if "set" in group:
        gs = group["set"]
        if not isinstance(gs, dict) or not gs or any(
                not isinstance(k, str) or not k or isinstance(v, (dict, list))
                for k, v in gs.items()):
            raise FmError("round spec.group.set: a non-empty object of "
                          "top-level ladder fields -> scalar values")
        lad["set"] = gs
    if "key_label" in group:
        lad["key_label"] = group["key_label"]
    if "description" in group:
        lad["description"] = group["description"]
    return {"ladder": lad}


def spec_key_pairs(spec, ladder_id=None):
    """IDS_ keys a round adds: series names, group names, renames and the
    description texts (ladder_id = the resolved ladder of `group`)."""
    pairs = [(name_key(item.get("key_label", item["name"])), item["name"])
             for item in spec["series"]]
    for item in spec["series"]:
        d = item.get("description")
        if isinstance(d, str) and d:
            pairs.append((desc_key("desc|%d" % item["id"]), d))
    for item in spec["series"]:
        t = item.get("lock_text")
        if isinstance(t, str) and t:
            pairs.append((lock_key("lock|%d" % item["id"]), t))
    for op in spec.get("ops", []):
        if op["op"] in ("rename_cup", "rename_ladder"):
            pairs.append((name_key(op.get("key_label", op["name"])),
                          op["name"]))
        elif op["op"] == "describe_cup":
            pairs.append((desc_key("desc|cup|%d" % op["id"]), op["text"]))
    group = spec["group"]
    if isinstance(group, dict):
        pairs.append((name_key(group.get("key_label", group["name"])),
                      group["name"]))
        if isinstance(group["cup"], dict):
            c = group["cup"]
            pairs.append((name_key(c.get("key_label", c["name"])), c["name"]))
        if "description" in group:
            if ladder_id is None:
                raise FmError("round spec.group.description: the ladder id is "
                              "not resolved")
            pairs.append((desc_key("desc|ladder|%d" % ladder_id),
                          group["description"]))
    return pairs


def describe_series(bcs, item, ns, snap):
    """series[].description -> the series' Description (a key, or "")."""
    if "description" not in item:
        return
    d = item["description"]
    if isinstance(d, str):
        ns["Description"] = desc_key("desc|%d" % item["id"]) if d else ""
        print("  %s: series %d Description %s"
              % (snap, item["id"],
                 "cleared" if not d else "-> new key"))
        return
    src = B.find_series(bcs, d["from_series"])
    if src is None:
        raise FmError("%s: series %d (description from_series) does not exist "
                      "- refusing" % (snap, d["from_series"]))
    key = src.get("Description")
    if not isinstance(key, str) or not key:
        raise FmError("%s: series %d has an empty Description, there is "
                      "nothing to copy - refusing"
                      % (snap, d["from_series"]))
    ns["Description"] = key
    print("  %s: series %d Description <- the key of series %d"
          % (snap, item["id"], d["from_series"]))


def describe_lock(bcs, item, ns, snap):
    """series[].lock_text -> EntryCriteria.EntryCriteriaName (a key, or "").

    Without the key the field keeps the donor's text byte for byte; with it
    the text is ours (a new key), blank, or copied from another series."""
    if "lock_text" not in item:
        return
    v = item["lock_text"]
    path = "EntryCriteria.EntryCriteriaName"
    if isinstance(v, str):
        key = lock_key("lock|%d" % item["id"]) if v else ""
        nested.set_path(ns, path, key)
        print("  %s: series %d %s %s"
              % (snap, item["id"], path,
                 "cleared" if not v else "-> new key"))
        return
    src = B.find_series(bcs, v["from_series"])
    if src is None:
        raise FmError("%s: series %d (lock_text from_series) does not exist "
                      "- refusing" % (snap, v["from_series"]))
    ec = src.get("EntryCriteria")
    key = ec.get("EntryCriteriaName") if isinstance(ec, dict) else None
    if not isinstance(key, str) or not key:
        raise FmError("%s: series %d has an empty EntryCriteriaName, there is "
                      "nothing to copy - refusing" % (snap, v["from_series"]))
    nested.set_path(ns, path, key)
    print("  %s: series %d %s <- the key of series %d"
          % (snap, item["id"], path, v["from_series"]))


def apply_ops(bcs, ops, snap):
    """Renames and removals on the base tree. Returns the removed ids by
    kind (series/events/cups/ladders), for patches/ids_retired.json."""
    removed = {"series": [], "events": [], "cups": [], "ladders": []}
    for op in ops:
        kind = op["op"]
        if kind == "rename_cup":
            cup = B.find_cup(bcs, op["id"])
            if cup is None:
                raise FmError("%s: cup %d not found" % (snap, op["id"]))
            cup["Name"] = name_key(op.get("key_label", op["name"]))
        elif kind == "rename_ladder":
            _cup, lad = B.find_ladder(bcs, op["id"])
            if lad is None:
                raise FmError("%s: ladder %d not found" % (snap, op["id"]))
            lad["Name"] = name_key(op.get("key_label", op["name"]))
        elif kind == "set_series":
            hits = [x for _c, _l, x in B.iter_series(bcs)
                    if x.get("ChampionshipSeriesId") == op["id"]]
            if len(hits) != 1:
                raise FmError("%s: series %d found %d times"
                              % (snap, op["id"], len(hits)))
            for k, v in op["set"].items():
                if k not in hits[0]:
                    raise FmError("%s: set_series field %r is not in series "
                                  "%d (only existing fields)"
                                  % (snap, k, op["id"]))
                hits[0][k] = v
        elif kind == "set_cup":
            cup = B.find_cup(bcs, op["id"])
            if cup is None:
                raise FmError("%s: cup %d not found" % (snap, op["id"]))
            for k, v in op["set"].items():
                if k not in cup:
                    raise FmError("%s: set_cup field %r is not in cup %d "
                                  "(only existing cup fields)"
                                  % (snap, k, op["id"]))
                cup[k] = v
        elif kind == "describe_cup":
            cup = B.find_cup(bcs, op["id"])
            if cup is None:
                raise FmError("%s: cup %d not found" % (snap, op["id"]))
            cup["Description"] = desc_key("desc|cup|%d" % op["id"])
        elif kind == "remove_series":
            s = B.remove_series(bcs, op["id"])
            removed["series"].append(s["ChampionshipSeriesId"])
            removed["events"] += [e["EventDataId"]
                                  for e in s["ChampionshipEventData"]]
        elif kind == "remove_ladder":
            lad = B.remove_ladder(bcs, op["id"])
            removed["ladders"].append(lad["ChampionshipLadderId"])
            for s in lad["ChampionshipSeriesData"]:
                removed["series"].append(s["ChampionshipSeriesId"])
                removed["events"] += [e["EventDataId"]
                                      for e in s["ChampionshipEventData"]]
        elif kind == "remove_cup":
            cup = B.remove_cup(bcs, op["id"])
            removed["cups"].append(cup["ChampionshipCupId"])
            for lad in cup["ChampionshipLadder"]:
                removed["ladders"].append(lad["ChampionshipLadderId"])
                for s in lad["ChampionshipSeriesData"]:
                    removed["series"].append(s["ChampionshipSeriesId"])
                    removed["events"] += [e["EventDataId"]
                                          for e in s["ChampionshipEventData"]]
    return removed


def donor_xml_car_ids(raw, series_id):
    """Car list of the donor XML entry (round clones copy it, not rebuild)."""
    m = carsxml.block_re(series_id).search(raw)
    if m is None:
        raise FmError("XML has no donor entry SeriesId=%d" % series_id)
    block = m.group(0)
    if 'BlackOrWhitelistType="Whitelist"' not in block:
        raise FmError("XML entry SeriesId=%d is not a Whitelist; cloning a "
                      "blacklist as a whitelist would change its meaning"
                      % series_id)
    return [int(v) for v in re.findall(r'val="(\d+)"', block)]


def round_series_cars(xml, donor_id, item, ns):
    """XML entry for a round series, plus its SelectableCars and the AI
    filter.

    Without series[].cars the entry clones the donor list and the series
    keeps the donor's SelectableCars untouched; with cars the entry holds
    the declared acceptlist and SelectableCars points at it (Acceptlist +
    the optional class/division). Without series[].ai_cars the series
    keeps the donor's AISelectableCars untouched (vanilla shape:
    {"Acceptlist": [<guid>, ...]}); with ai_cars it holds the declared
    AI acceptlist."""
    cars = item.get("cars")
    xml_opts = {}
    if cars is None:
        car_ids = donor_xml_car_ids(xml, donor_id)
    else:
        blocklist = "blocklist" in cars
        car_ids = list(cars["blocklist" if blocklist else "acceptlist"])
        sc = ns["SelectableCars"]
        sc["BlockOrAcceptlistType"] = ("Blocklist" if blocklist
                                       else "Acceptlist")
        sc["BlockOrAcceptlist"] = [C.guid(c) for c in car_ids]
        if "class" in cars:
            sc["CarClassId"] = cars["class"]
        if "division" in cars:
            sc["CarDivisionId"] = cars["division"]
        if "severity" in cars:
            sc["SeverityType"] = cars["severity"]
        if "ranges" in cars:
            for key, val in cars["ranges"].items():
                if key in ROUND_RANGE_FLOAT:
                    sc[key] = float(val)
                else:
                    sc[key] = int(val)
        if "ownership" in cars:
            if "Ownership" not in sc:
                raise FmError("donor SelectableCars has no Ownership field")
            sc["Ownership"] = cars["ownership"]
        xml_opts = dict(list_type="Blacklist" if blocklist else "Whitelist",
                        class_id=cars.get("class"),
                        severity=cars.get("severity"),
                        ranges=cars.get("ranges"),
                        ownership=cars.get("ownership"),
                        spec_division=cars.get("spec_division"))
    ai = item.get("ai_cars")
    if ai is not None:
        ns["AISelectableCars"] = {"Acceptlist":
                                  [C.guid(c) for c in ai["acceptlist"]]}
    return carsxml.add_entry(xml, donor_id, item["id"], car_ids,
                             **xml_opts), len(car_ids)


def round_track_override(ovr, track, prod_files, snap):
    """First vanilla override on `track` with an AIFileName in the manifest."""
    cands = sorted((x for x in ovr if x.get("Track") == track
                    and not ids.is_custom_event(x["ID"])
                    and x.get("AIFileName") in prod_files),
                   key=lambda x: x["ID"])
    if not cands:
        raise FmError("%s: track %d has no vanilla override with AI"
                      % (snap, track))
    return cands[0]["ID"]


def edit_round_multi(bcs, ovr, xml, lad, item, base_series, base_event,
                     base_track, base_ovr, prod_files, snap, create):
    """Series with series[].events (1-5): one event + override per entry, in
    order. Same-track entries clone the base event/override; other tracks
    clone that track's donor event/override. Every event gets the base
    PointSpread table, unless series[].event declares its own PointSpread
    (validated: 24 ints >= 0; the same table lands on every event of the
    series). ID == override ID; OrderedEventIds follows the
    events array (vanilla pattern, TASK_g16_multievento)."""
    ov = item.get("override", {})
    events = []
    for ev_spec in item["events"]:
        track = ev_spec.get("track", base_track)
        if track == base_track:
            ev = B.clone_event(base_event, ev_spec["event_id"], item["id"])
        else:
            de = B.first_event_on_track(bcs, track,
                                        exclude=ids.is_custom_event)
            if de is None:
                raise FmError("%s: no donor event on track %d"
                              % (snap, track))
            ev = B.clone_event(de, ev_spec["event_id"], item["id"],
                               serial=track)
        if "laps" in ev_spec:
            ev["NumberOfRequiredLaps"] = ev_spec["laps"]
        if "PointSpread" in base_event:
            ev["PointSpread"] = copy.deepcopy(base_event["PointSpread"])
        for k, v in item.get("event", {}).items():
            nested.set_path(ev, k, v, create)
        events.append(ev)
    ns = copy.deepcopy(base_series)
    ns["ChampionshipSeriesId"] = item["id"]
    ns["Name"] = name_key(item.get("key_label", item["name"]))
    ns["ChampionshipEventData"] = events
    ns["OrderedEventIds"] = [e["EventDataId"] for e in events]
    for k, v in item.get("series_set", {}).items():
        nested.set_path(ns, k, v, create)
    if "poster" in item:
        ns["ImagePath"] = poster_path(item)
    describe_series(bcs, item, ns, snap)
    describe_lock(bcs, item, ns, snap)
    B.append_series(lad, ns)
    for ev, ev_spec in zip(events, item["events"]):
        track = ev_spec.get("track", base_track)
        donor_id = base_ovr if track == base_track else \
            round_track_override(ovr, track, prod_files, snap)
        d = overrides.find(ovr, donor_id)
        if d is None:
            raise FmError("%s: override donor %d not found"
                          % (snap, donor_id))
        new_ov = overrides.clone(ovr, donor_id, ev_spec["event_id"],
                                 prod_files, track=track)
        for k, v in ov.items():
            nested.set_path(new_ov, k, v, create)
        if "laps" in ev_spec:
            new_ov["FeatureRace"]["Laps"] = ev_spec["laps"]
        if new_ov.get("AIFileName") not in prod_files:
            raise FmError("%s: override %d AIFileName %s is not in the "
                          "manifest (the race would crash)"
                          % (snap, ev_spec["event_id"],
                             new_ov.get("AIFileName")))
    print("  %s: series %d -> ladder %d %s | events %s | overrides %s"
          % (snap, item["id"], lad["ChampionshipLadderId"],
             lad["OrderData"], ns["OrderedEventIds"], ns["OrderedEventIds"]))
    xml, n_cars = round_series_cars(xml,
                                    base_series["ChampionshipSeriesId"],
                                    item, ns)
    print("  %s: XML entry SeriesId=%d (%d cars)"
          % (snap, item["id"], n_cars))
    return xml


def edit_round(bcs, ovr, xml, spec, prod_files, new_ids, snap):
    """Ops + group + new series for one snapshot. Returns (xml, removed)."""
    removed = apply_ops(bcs, spec.get("ops", []), snap)
    removed_ids = set(removed["series"]) | set(removed["events"]) \
        | set(removed["ladders"]) | set(removed["cups"])
    if removed_ids:
        dangling = B.dangling_refs(bcs, removed_ids)
        if dangling:
            raise FmError("%s: removing these ids leaves %s pointing at them; "
                          "refusing instead of stripping the reference"
                          % (snap, dangling[:5]))
    base = spec["base"]
    base_series = B.find_series(bcs, base["series"])
    if base_series is None:
        raise FmError("%s: base series %d not found"
                      % (snap, base["series"]))
    base_events = base_series["ChampionshipEventData"]
    if "event" in base:
        base_event = next((e for e in base_events
                           if e["EventDataId"] == base["event"]), None)
        if base_event is None:
            raise FmError("%s: base event %d is not in series %d"
                          % (snap, base["event"], base["series"]))
    elif len(base_events) == 1:
        base_event = base_events[0]
    else:
        raise FmError("%s: base series %d has %d events; declare base.event"
                      % (snap, base["series"], len(base_events)))
    lad = resolve_placement(bcs, group_placement(spec["group"]), new_ids, snap)
    base_track = base_event["SerialTrackId"]
    base_ovr = base_event["EventDataId"]      # override ID == event ID
    for item in spec["series"]:
        create = bool(item.get("create", False))
        if "events" in item:
            xml = edit_round_multi(bcs, ovr, xml, lad, item, base_series,
                                   base_event, base_track, base_ovr,
                                   prod_files, snap, create)
            continue
        track = item.get("track", base_track)
        # track_alias_of: `track` is a SerialTrackId the BCS does not know
        # (a cloned track, TASK_track_clone); event and override are cloned
        # from the existing track `alias` and then moved to `track`.
        alias = item.get("track_alias_of")
        src_track = track if alias is None else alias
        if track == base_track and alias is None:
            ev = B.clone_event(base_event, item["event_id"], item["id"])
        else:
            donor_ev = item.get("donor_event")
            if donor_ev is None:
                de = B.first_event_on_track(bcs, src_track,
                                            exclude=ids.is_custom_event)
            else:
                _s, de = B.find_event(bcs, donor_ev)
            if de is None:
                raise FmError("%s: no donor event on track %d"
                              % (snap, src_track))
            if de["SerialTrackId"] != src_track:
                raise FmError("%s: donor event %d is on track %d, not %d"
                              % (snap, de["EventDataId"],
                                 de["SerialTrackId"], src_track))
            ev = B.clone_event(de, item["event_id"], item["id"], serial=track)
        for k, v in item.get("event", {}).items():
            nested.set_path(ev, k, v, create)
        ns = copy.deepcopy(base_series)
        ns["ChampionshipSeriesId"] = item["id"]
        ns["Name"] = name_key(item.get("key_label", item["name"]))
        ns["ChampionshipEventData"] = [ev]
        ns["OrderedEventIds"] = [ev["EventDataId"]]
        for k, v in item.get("series_set", {}).items():
            nested.set_path(ns, k, v, create)
        if "poster" in item:
            ns["ImagePath"] = poster_path(item)
        describe_series(bcs, item, ns, snap)
        describe_lock(bcs, item, ns, snap)
        B.append_series(lad, ns)
        ov = item.get("override", {})
        donor_id = ov.get("donor", base_ovr)
        d = overrides.find(ovr, donor_id)
        if d is None:
            raise FmError("%s: override donor %d not found"
                          % (snap, donor_id))
        if d.get("Track") != src_track:
            raise FmError("%s: override donor %d is on Track %s, not %d; a "
                          "series that changes track needs override.donor on "
                          "the target track" % (snap, donor_id,
                                                d.get("Track"), src_track))
        new_ov = overrides.clone(ovr, donor_id, item["event_id"], prod_files,
                                 track=src_track)
        if alias is not None:
            new_ov["Track"] = track
        for k, v in ov.items():
            if k == "donor":
                continue
            nested.set_path(new_ov, k, v, create)
        if new_ov.get("AIFileName") not in prod_files:
            raise FmError("%s: override %d AIFileName %s is not in the "
                          "manifest (the race would crash)"
                          % (snap, item["event_id"],
                             new_ov.get("AIFileName")))
        print("  %s: series %d -> ladder %d %s | event %d (track %d) | "
              "override %d from %d"
              % (snap, item["id"], lad["ChampionshipLadderId"],
                 lad["OrderData"], item["event_id"], track, item["event_id"],
                 donor_id))
        xml, n_cars = round_series_cars(
            xml, base_series["ChampionshipSeriesId"], item, ns)
        print("  %s: XML entry SeriesId=%d (%d cars)"
              % (snap, item["id"], n_cars))
    B.check_invariants(bcs, snap)
    return xml, removed



def load_aifield_defs(paths, owned):
    """The round's `aifield` definitions, validated by build_aifield itself.

    `owned` = the logical files the round already writes (a definition that
    rewrites one of them, or another definition's document, is refused)."""
    import build_aifield as BA
    out, logicals = [], set(owned)
    for path in paths:
        d = BA.load_def(path)
        if d["logical"] in logicals:
            raise FmError("round spec: aifield rewrites %s twice (or it is "
                          "already a target of the round)" % d["logical"])
        logicals.add(d["logical"])
        out.append((path, d))
    return out


def merge_aifield(spec, cache, kit, plan):
    """build_aifield --cache-plan for each round def, merged into the plan.

    Each definition lands as one `op="bytes"` target of its own document,
    encrypted with the current cache-blob payload as template, and the payload
    is copied next to the kit's own (merge_cache_plans: duplicate target or
    different bytes under the same name is refused)."""
    import build_aifield as BA          # lazy: public export has no cache route
    import merge_cache_plans as MCP     # lab tool (not in the public allowlist)
    defs = load_aifield_defs(spec["aifield"],
                             [t["logical"] for t in kit.targets])
    adds = []
    for path, d in defs:
        out = os.path.join(WORK, "aifield_" + kit.name + "_" + d["name"])
        print("  [aifield] %s -> %s" % (path, d["logical"]))
        BA.build(d, out, write=True, cache_plan=True, cache_dir=cache.dir)
        adds.append(os.path.join(out, BA.CACHE_PLAN))
    saved = sys.argv
    try:
        # merge_cache_plans.py is the documented joiner (payload copy + the
        # duplicate/different-bytes refusals); it reads its arguments from
        # sys.argv, so it is driven here exactly as the CLI would be.
        for add in adds:
            sys.argv = [saved[0], "--into", plan, "--add", add]
            MCP.main()
    finally:
        sys.argv = saved
    with open(plan, encoding="utf-8-sig") as fh:
        return len(json.load(fh).get("targets") or [])


def load_repoint_refs(cache):
    """Live-cache refs for round-spec repoint: (live snapshot, manifest
    paths, {logical: encrypted payload}), via inventory.load_live
    (checksum-resolved blobs, as in aifield_unused.py)."""
    import inventory
    _snaps, snap, _ck, prod, payloads = inventory.load_live(cache.dir)
    return snap, {f["Path"] for f in prod["Files"]}, payloads


def apply_repoint(ovr, repoint, cache, snap, live_refs):
    """Point override AIFileName entries at identical documents (G20: free
    a byte-identical copy for a custom roster without changing any grid).

    Refuses when the record does not exist, when its current file is not
    `from`, when `to` is absent from the live manifest, or when the
    decrypted payloads of `from` and `to` differ. Without `repoint` the
    caller writes the overrides untouched (byte-identical)."""
    live_snap, manifest, payloads = live_refs
    for e in repoint:
        o = overrides.find(ovr, e["override_id"])
        if o is None:
            raise FmError("%s: repoint: override %d does not exist - refusing"
                          % (snap, e["override_id"]))
        cur = o.get("AIFileName")
        if cur != e["from"]:
            raise FmError("%s: repoint: override %d cites %s, not %s - refusing"
                          % (snap, e["override_id"], cur, e["from"]))
        if snap == live_snap:
            if e["to"] not in manifest:
                raise FmError("%s: repoint: %s is not in the live manifest - "
                              "refusing" % (snap, e["to"]))
            missing = [n for n in (e["from"], e["to"]) if n not in payloads]
            if missing:
                raise FmError("%s: repoint: no cache payload for %s - refusing"
                              % (snap, ", ".join(missing)))
            old = crypto.decrypt(payloads[e["from"]])
            new = crypto.decrypt(payloads[e["to"]])
        else:
            files = set(cache.files(snap))
            if e["to"] not in files:
                raise FmError("%s: repoint: %s is not in the manifest - "
                              "refusing" % (snap, e["to"]))
            old = crypto.decrypt(cache.payload(snap, e["from"]))
            new = crypto.decrypt(cache.payload(snap, e["to"]))
        if old != new:
            raise FmError("%s: repoint: %s and %s differ - refusing"
                          % (snap, e["from"], e["to"]))
        o["AIFileName"] = e["to"]
        print("  %s: repoint override %d %s -> %s"
              % (snap, e["override_id"], e["from"], e["to"]))



def car_ids_from_spec(spec_cars, cars):
    al = spec_cars.get("acceptlist", "showroom")
    if al == "showroom":
        return C.showroom_ids(cars)
    if isinstance(al, list) and all(isinstance(c, int) for c in al):
        return list(al)
    raise FmError("spec.cars.acceptlist must be 'showroom' or a list of car ids")


# --------------------------------------------------------------------------- #
# per-snapshot edits
# --------------------------------------------------------------------------- #
def resolve_placement(bcs, pl, new_ids, snap):
    """Returns the target ladder, creating ladder/cup per spec."""
    lad_spec = pl["ladder"]
    if isinstance(lad_spec, int):
        _cup, lad = B.find_ladder(bcs, lad_spec)
        if lad is None:
            raise FmError("%s: ladder %d not found" % (snap, lad_spec))
        return lad
    # ladder nova
    cup_spec = lad_spec["cup"]
    if isinstance(cup_spec, int):
        cup = B.find_cup(bcs, cup_spec)
        if cup is None:
            raise FmError("%s: cup %d not found" % (snap, cup_spec))
    else:
        donor_cup = B.find_cup(bcs, cup_spec["donor"])
        if donor_cup is None:
            raise FmError("%s: donor cup %d not found" % (snap, cup_spec["donor"]))
        cup = B.clone_cup(donor_cup, new_ids["cup"],
                          name_key(cup_spec.get("key_label", cup_spec["name"])))
        for k, v in cup_spec.get("set", {}).items():
            if k not in cup:
                raise FmError("%s: group.cup.set field %r is not in donor "
                              "cup %d (only existing cup fields)"
                              % (snap, k, cup_spec["donor"]))
            cup[k] = v
        B.cups(bcs).append(cup)                      # tail, como o mc57
    _c, donor_lad = B.find_ladder(bcs, lad_spec["donor"])
    if donor_lad is None:
        raise FmError("%s: donor ladder %d not found" % (snap, lad_spec["donor"]))
    lad = B.clone_ladder(donor_lad, new_ids["ladder"],
                         name_key(lad_spec.get("key_label", lad_spec["name"])))
    if "description" in lad_spec:
        lad["Description"] = desc_key("desc|ladder|%d"
                                      % lad["ChampionshipLadderId"])
    for k, v in lad_spec.get("set", {}).items():
        if k not in lad:
            raise FmError("%s: group.set field %r is not in donor ladder %d "
                          "(only existing ladder fields)"
                          % (snap, k, lad_spec["donor"]))
        lad[k] = v
    B.append_ladder(cup, lad)
    return lad


def edit_bcs(bcs, spec, car_ids, new_ids, snap):
    s = spec["series"]
    used = B.all_ids(bcs)
    ids.check_new("series", s["id"], used["series"])
    for e in spec["events"]:
        ids.check_new("events", e["id"], used["events"])

    donor = B.find_series(bcs, s["donor_series"])
    if donor is None:
        raise FmError("%s: donor series %d not found" % (snap, s["donor_series"]))

    events = []
    for i, es in enumerate(spec["events"]):
        de = es.get("donor_event")
        if de is None:
            # evento da serie doadora na mesma pista, senao 1o da pista
            de_obj = next((e for e in donor["ChampionshipEventData"]
                           if e["SerialTrackId"] == es["track"]), None) \
                or B.first_event_on_track(bcs, es["track"],
                                          exclude=ids.is_custom_event)
        else:
            _s, de_obj = B.find_event(bcs, de)
        if de_obj is None:
            raise FmError("%s: no donor event for track %d" % (snap, es["track"]))
        ev = B.clone_event(de_obj, es["id"], s["id"], es["track"])
        if "practice_seconds" in es:
            ev["OpenPracticeLimitationTimeInSeconds"] = es["practice_seconds"]
        if "laps" in es:
            ev["NumberOfRequiredLaps"] = es["laps"]
        if "name" in es:
            ev["Name"] = es["name"]
        for k, v in es.get("set", {}).items():
            ev[k] = v
        events.append(ev)

    ns = B.clone_series(donor, s["id"],
                        name_key(s.get("key_label", s["name"])), events,
                        always_open=s.get("always_open", True),
                        clear_entry=s.get("clear_entry_criteria", True))
    ns["DefaultEventOverrides"].update(s.get("deo", {}))
    for k, v in s.get("set", {}).items():
        ns[k] = v
    sc = ns["SelectableCars"]
    sc["CarClassId"] = spec["cars"].get("class", "Any")
    sc["CarDivisionId"] = spec["cars"].get("division", "Open")
    sc["SeverityType"] = "None"
    sc["BlockOrAcceptlistType"] = "Acceptlist"
    sc["BlockOrAcceptlist"] = [C.guid(c) for c in car_ids]

    lad = resolve_placement(bcs, spec["placement"], new_ids, snap)
    B.append_series(lad, ns)
    B.check_invariants(bcs, snap)
    print("  %s: series %d -> ladder %d %s | events %s"
          % (snap, s["id"], lad["ChampionshipLadderId"], lad["OrderData"],
             ns["OrderedEventIds"]))
    return ns


def edit_overrides(ovr, spec, prod_files, bcs_before, snap):
    for es in spec["events"]:
        o = es.get("override", {})
        donor_id = o.get("donor")
        if donor_id is None:
            # 1o override vanilla da pista com AIField no manifesto
            cands = sorted((x for x in ovr if x.get("Track") == es["track"]
                            and not ids.is_custom_event(x["ID"])
                            and x.get("AIFileName") in prod_files),
                           key=lambda x: x["ID"])
            if not cands:
                raise FmError("%s: track %d has no vanilla override with AI"
                              % (snap, es["track"]))
            donor_id = cands[0]["ID"]
        new = overrides.clone(ovr, donor_id, es["id"], prod_files,
                              track=es["track"],
                              class_restriction=o.get("class_restriction"),
                              target_pi=o.get("target_pi"),
                              laps=o.get("laps"), pits=o.get("pits"))
        print("  %s: override %d -> %d (Track=%d, CR=%s, TPI=%s, AI=%s)"
              % (snap, donor_id, es["id"], new["Track"],
                 new["ClassRestriction"], new["TargetPI"], new["AIFileName"]))


# --------------------------------------------------------------------------- #
def alloc_new_ids(loaded, snaps, lad_spec):
    """Free cup/ladder ids for a spec: free in EVERY snapshot (like mc57)."""
    new_ids = {}
    if not isinstance(lad_spec, dict):
        return new_ids
    for kind, sub, rng in (("ladders", lad_spec, (761, 800)),
                           ("cups", lad_spec.get("cup"), (103, 200))):
        if not isinstance(sub, dict):
            continue
        used = set()
        for snap in snaps:
            used |= set(B.all_ids(loaded[snap][0])[kind])
        want = sub.get("id", "auto")
        if want == "auto":
            want = ids.next_free(kind, used, *rng)
        ids.check_new(kind, want, used)
        new_ids[kind[:-1]] = want
    return new_ids


def run_spec(spec, args):
    """--spec: one new series (the mc55 path, unchanged)."""
    cache = Cache(args.cache_dir)
    snaps = cache.snapshots if spec.get("snapshots", "all") == "all" \
        else spec["snapshots"]
    cars = C.load_cars()
    car_ids = car_ids_from_spec(spec["cars"], cars)
    for w in C.check_acceptlist(car_ids, cars=cars):
        warn(w)
    s = spec["series"]
    kit = Kit(spec["kit"], cache, args.out)
    print("cache: %s | snapshots: %s" % (cache.dir, ", ".join(snaps)))
    print("kit:   %s" % kit.dir)

    loaded = {}
    for snap in snaps:
        raw = crypto.decrypt(cache.payload(snap, B.LOGICAL))
        loaded[snap] = json_load_exact(raw, "%s BCS" % snap)
    lad_spec = spec["placement"]["ladder"]
    new_ids = alloc_new_ids(loaded, snaps, lad_spec)

    key_pairs = [(name_key(s.get("key_label", s["name"])), s["name"])]
    if isinstance(lad_spec, dict):
        key_pairs.append((name_key(lad_spec.get("key_label", lad_spec["name"])),
                          lad_spec["name"]))
        if isinstance(lad_spec.get("cup"), dict):
            c = lad_spec["cup"]
            key_pairs.append((name_key(c.get("key_label", c["name"])), c["name"]))

    for snap in snaps:
        print("[%s]" % snap)
        prod_files = set(cache.files(snap))
        bcs, style = loaded[snap]
        bcs_before = copy.deepcopy(bcs)
        edit_bcs(bcs, spec, car_ids, new_ids, snap)
        kit.add(snap, B.LOGICAL, json_dump(bcs, style))

        xml = crypto.decrypt(cache.payload(snap, carsxml.LOGICAL)).decode("utf-8")
        new_xml = carsxml.add_entry(xml, s.get("donor_xml_series",
                                               s["donor_series"]),
                                    s["id"], car_ids)
        kit.add(snap, carsxml.LOGICAL, new_xml.encode("utf-8"))
        print("  %s: XML entry SeriesId=%d (%d cars)" % (snap, s["id"],
                                                         len(car_ids)))

        ovr, ostyle = json_load_exact(
            crypto.decrypt(cache.payload(snap, overrides.LOGICAL)),
            "%s overrides" % snap)
        edit_overrides(ovr, spec, prod_files, bcs_before, snap)
        kit.add(snap, overrides.LOGICAL, json_dump(ovr, ostyle))

        st = crypto.decrypt(cache.payload(snap, strs.LOGICAL_PT))
        kit.add(snap, strs.LOGICAL_PT, strs.add_keys(st, key_pairs))
        print("  %s: .str + %s" % (snap, ", ".join("%s=%r" % kv
                                                   for kv in key_pairs)))

    kit.reread()
    ev_ids = [e["id"] for e in spec["events"]]
    meta = {"series_id": s["id"],
            "event_id": ev_ids[0] if len(ev_ids) == 1 else ev_ids}
    if "ladder" in new_ids:
        meta["ladder_id"] = new_ids["ladder"]
    if "cup" in new_ids:
        meta["cup_id"] = new_ids["cup"]
    meta["str_keys"] = dict(key_pairs)
    meta["spec"] = os.path.relpath(os.path.abspath(args.spec), ROOT
                                   ).replace("\\", "/")
    plan = kit.write_plan(
        "%s - serie %d gerada por _tools/build_series.py a partir de %s. "
        "Aplicar com o jogo FECHADO: dry-run, depois --verify."
        % (spec["kit"], s["id"], meta["spec"]), meta)
    kit.write_nota(spec.get("title", s["name"]), "_tools/build_series.py",
                   spec.get("scope", "Serie %d (%s), %d evento(s)."
                            % (s["id"], s["name"], len(ev_ids))),
                   spec.get("requires", "-"), spec=meta["spec"])
    print("")
    print("plan: %s (%d targets)%s" % (plan, len(kit.targets),
                                       " | %d warning(s)" % len(WARN)
                                       if WARN else ""))
    print("next: python _tools\\plan_lint.py --plan %s" % plan)
    return 3 if WARN else 0


def run_round(spec, args):
    """--round: ops on the base tree + one kit of series cloned from a base."""
    cache = Cache(args.cache_dir)
    snaps = cache.snapshots if spec.get("snapshots", "all") == "all" \
        else spec["snapshots"]
    kit = Kit(spec["kit"], cache, args.out)
    print("cache: %s | snapshots: %s" % (cache.dir, ", ".join(snaps)))
    print("kit:   %s" % kit.dir)

    loaded = {}
    for snap in snaps:
        raw = crypto.decrypt(cache.payload(snap, B.LOGICAL))
        loaded[snap] = json_load_exact(raw, "%s BCS" % snap)
    placement = group_placement(spec["group"])
    new_ids = alloc_new_ids(loaded, snaps, placement["ladder"])

    used = {"series": set(), "events": set()}
    for snap in snaps:
        got = B.all_ids(loaded[snap][0])
        used["series"] |= set(got["series"])
        used["events"] |= set(got["events"])
    for item in spec["series"]:
        ids.check_new("series", item["id"], used["series"])
        for eid in round_event_ids(item):
            ids.check_new("events", eid, used["events"])
    cars_db = C.load_cars()
    denied = C.denied_ids()
    for item in spec["series"]:
        for key in ("cars", "ai_cars"):
            if key not in item:
                continue
            al = item[key].get("acceptlist",
                               item[key].get("blocklist", []))
            ws = C.check_acceptlist(al, cars=cars_db)  # unknown ids raise
            if "blocklist" not in item[key]:
                for w in ws:
                    warn(w)
            bad = sorted(set(al) & denied)
            if bad:
                raise FmError("round spec: series %d %s.acceptlist has "
                              "always-denied cars %s - refusing"
                              % (item["id"], key, bad[:10]))

    key_pairs = spec_key_pairs(spec, new_ids.get("ladder"))
    removed_seen = None
    live_refs = load_repoint_refs(cache) if spec.get("repoint") else None
    for snap in snaps:
        print("[%s]" % snap)
        prod_files = set(cache.files(snap))
        bcs, style = loaded[snap]
        xml = crypto.decrypt(cache.payload(snap, carsxml.LOGICAL)).decode("utf-8")
        ovr, ostyle = json_load_exact(
            crypto.decrypt(cache.payload(snap, overrides.LOGICAL)),
            "%s overrides" % snap)
        new_xml, removed = edit_round(bcs, ovr, xml, spec, prod_files,
                                      new_ids, snap)
        if live_refs is not None:
            apply_repoint(ovr, spec["repoint"], cache, snap, live_refs)
        if removed_seen is None:
            removed_seen = removed
        elif removed != removed_seen:
            raise FmError("%s: removals differ between snapshots" % snap)
        kit.add(snap, B.LOGICAL, json_dump(bcs, style))
        kit.add(snap, carsxml.LOGICAL, new_xml.encode("utf-8"))
        kit.add(snap, overrides.LOGICAL, json_dump(ovr, ostyle))
        st = crypto.decrypt(cache.payload(snap, strs.LOGICAL_PT))
        kit.add(snap, strs.LOGICAL_PT,
                strs.add_keys(st, key_pairs, allow_existing=True))
        print("  %s: .str + %s" % (snap, ", ".join("%s=%r" % kv
                                                   for kv in key_pairs)))

    for kind in ("series", "events", "cups", "ladders"):
        added = ids.retire(kind, removed_seen.get(kind, []))
        if added:
            print("  retired %s: %s" % (kind, added))

    kit.reread()
    meta = {}
    if spec["series"]:
        meta["series_id"] = [i["id"] for i in spec["series"]]
        meta["event_id"] = [eid for i in spec["series"]
                            for eid in round_event_ids(i)]
    if "ladder" in new_ids:
        meta["ladder_id"] = new_ids["ladder"]
    if "cup" in new_ids:
        meta["cup_id"] = new_ids["cup"]
    meta["str_keys"] = dict(key_pairs)
    meta["spec"] = os.path.relpath(os.path.abspath(args.round), ROOT
                                   ).replace("\\", "/")
    plan = kit.write_plan(
        "%s - rodada '%s' gerada por _tools/build_series.py --round a partir "
        "de %s. Aplicar com o jogo FECHADO: dry-run, depois --verify."
        % (spec["kit"], spec["title"], meta["spec"]), meta)
    n_targets = len(kit.targets)
    if spec.get("aifield"):
        print("")
        print("[aifield] %d definition(s)" % len(spec["aifield"]))
        n_targets = merge_aifield(spec, cache, kit, plan)
    posters = write_poster_manifest(spec, args.round, kit.dir)
    if posters:
        print("posters: %s (install half: swatchbin_edit.py --manifest)"
              % posters)
    kit.write_nota(spec["title"], "_tools/build_series.py --round",
                   spec.get("scope", "Rodada '%s': %d serie(s) no cup/grupo."
                            % (spec["title"], len(spec["series"]))),
                   spec.get("requires", "-"), spec=meta["spec"],
                   purpose=(spec["question"], spec["mask"],
                            spec["min_condition"], spec["refutes"]))
    print("")
    print("plan: %s (%d targets)%s" % (plan, n_targets,
                                       " | %d warning(s)" % len(WARN)
                                       if WARN else ""))
    print("next: python _tools\\plan_lint.py --plan %s" % plan)
    return 3 if WARN else 0


# --------------------------------------------------------------------------- #
def main(argv=None):
    p = argparse.ArgumentParser(prog="build_series.py")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--spec", help="spec of ONE new series (mc55 path)")
    mode.add_argument("--round", help="round spec: kit of series cloned from a "
                                      "base series (see specs/README.md)")
    p.add_argument("--cache-dir", default=None)
    p.add_argument("--out", default=None,
                   help="kit directory (default patches/<kit>)")
    args = p.parse_args(argv)
    if args.round:
        return run_round(load_round_spec(args.round), args)
    return run_spec(load_spec(args.spec), args)



if __name__ == "__main__":
    try:
        sys.exit(main())
    except FmError as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        sys.exit(1)
