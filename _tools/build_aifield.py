#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_aifield.py - AI grid payload from a declarative definition.

Builds the XML of one AIField entry from a VANILLA template that already
lives in YOUR install (nothing of the game is stored in this repository),
encrypts it with the target entry's current payload as cipher template, and
writes the .enc ready for install_edit.py.

Read-only on the cache and on the install. Output: <out>/XML.<logical>.enc.

Definition (JSON, see specs/aifield/):
  name         label, also the default output folder patches/<name>/
  logical      install entry to replace, e.g. AIField_117160001_Gen.xml
  template     vanilla AIField entry of the install used as the skeleton
  mode         "pool"  - EligibleCars drawn inside a PI window
               "list"  - explicit car per slot (fixed lineup)
 pool:
  roster       car ids (EligibleCars)
  window       [min_pi, max_pi, step]
  slots        NumberOfDrivatars (optional; template value if omitted)
  frames       [[player_pi_relative_to_class, lower, upper], ...] (optional;
               the PI band the AI follows; template frames if omitted)
 list:
  lineup       car per slot (repeats weight a car)
  eligible     EligibleCars (optional; default = distinct cars of the lineup)
 both:
  difficulty      root AIDifficulty (optional; e.g. "Expert")
  rubber_banding  root AIRubberBandingEnabled (optional; true/false)
  behavior        {SessionType: {SlowDown/CatchUp/Proximity/
                  PosDifficultySpread/SlotCarRaceStart: true/false}}
                  (optional; omitted = the template's own flags)

Usage:
  python _tools\\build_aifield.py --def specs\\aifield\\trackday_pool56.json
  python _tools\\build_aifield.py --def <file> --check     # build + validate, write nothing
Then, game closed:
  python _tools\\install_edit.py --dry-run --logical <logical> --payload <the .enc>
  python _tools\\install_edit.py --verify  --logical <logical> --payload <the .enc>
"""

import argparse
import json
import os
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)

from fmlib import aifield, crypto                       # noqa: E402
from fmlib.cache import Cache                           # noqa: E402
from fmlib.core import PATCHES, WORK, FmError           # noqa: E402


def check(cond, msg):
    if not cond:
        raise FmError(msg)


def load_def(path):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    for k in ("name", "logical", "template", "mode"):
        check(isinstance(d.get(k), str) and d[k], "definition: %r is required" % k)
    check(d["mode"] in ("pool", "list"), "definition: mode must be pool or list")
    if d["mode"] == "pool":
        check(d.get("roster"), "definition: pool needs 'roster'")
        w = d.get("window")
        check(isinstance(w, list) and len(w) == 3 and all(isinstance(x, int) for x in w)
              and w[0] < w[1] and w[2] > 0, "definition: window = [min, max, step]")
        for f in d.get("frames") or []:
            check(isinstance(f, list) and len(f) == 3, "definition: frame = [rel, lower, upper]")
    else:
        check(d.get("lineup"), "definition: list needs 'lineup'")
    ids = d.get("roster") or d.get("lineup")
    check(all(isinstance(c, int) for c in ids), "definition: car ids must be integers")
    _check_meta(d)
    return d


def _check_meta(d):
    """Optional document metadata: difficulty / rubber_banding / behavior."""
    if d.get("difficulty") is not None:
        check(isinstance(d["difficulty"], str) and d["difficulty"],
              "definition: difficulty must be a non-empty string")
    if d.get("rubber_banding") is not None:
        check(isinstance(d["rubber_banding"], bool),
              "definition: rubber_banding must be true/false")
    beh = d.get("behavior")
    if beh is None:
        return
    check(isinstance(beh, dict) and beh,
          "definition: behavior must be an object keyed by SessionType")
    for session, flags in beh.items():
        check(isinstance(flags, dict) and flags,
              "definition: behavior[%r] must be a non-empty object" % session)
        for key, val in flags.items():
            check(key in aifield.BEHAVIOR_KEYS,
                  "definition: behavior[%r] has unknown key %r (use %s)"
                  % (session, key, sorted(aifield.BEHAVIOR_KEYS)))
            check(isinstance(val, bool),
                  "definition: behavior[%r][%r] must be true/false"
                  % (session, key))


def build_text(d, template_text, by_car):
    """Pure function: the new document text (no I/O beyond the arguments)."""
    st = aifield.parse(template_text)
    if d["mode"] == "pool":
        check(st["mode"] == "AIDrivatarTemplate",
              "template %s is %s; pool mode needs a template-mode document"
              % (d["template"], st["mode"]))
        roster = d["roster"]
        dup = sorted({c for c in roster if roster.count(c) > 1})
        check(not dup, "roster has repeated ids: %s" % dup)
        errs, _ = aifield.validate(roster, by_car)
        check(not errs, "roster rejected: %s" % errs)
        frames = [tuple(f) for f in d["frames"]] if d.get("frames") else None
        slots = d.get("slots")
        return aifield.rewrite_template(template_text, roster, by_car,
                                        window=tuple(d["window"]),
                                        drivatars=slots, frames=frames,
                                        difficulty=d.get("difficulty"),
                                        rubber_banding=d.get("rubber_banding"),
                                        behavior=d.get("behavior"))
    check(st["mode"] == "AIDrivatarList",
          "template %s is %s; list mode needs a list-mode document"
          % (d["template"], st["mode"]))
    lineup = d["lineup"]
    check(len(lineup) * 2 == len(st["drivatars"]),
          "lineup has %d slots, the template has %d" % (len(lineup),
                                                         len(st["drivatars"]) // 2))
    errs, _ = aifield.validate(lineup, by_car)
    check(not errs, "lineup rejected: %s" % errs)
    eligible = d.get("eligible") or list(dict.fromkeys(lineup))
    return aifield.rewrite_list(template_text, lineup, by_car, eligible=eligible)


def _check_written_meta(d, st):
    """The document really carries the metadata the definition asked for."""
    if d.get("difficulty") is not None:
        check(st["difficulty"] == d["difficulty"],
              "difficulty not written (%r)" % st["difficulty"])
    if d.get("rubber_banding") is not None:
        check((st["rubber"] == "True") == d["rubber_banding"],
              "rubber_banding not written (%r)" % st["rubber"])
    for session, flags in (d.get("behavior") or {}).items():
        for key, val in flags.items():
            got = st["behavior"].get(session, {}).get(aifield.BEHAVIOR_KEYS[key])
            check(got == ("True" if val else "False"),
                  "behavior %s.%s not written (%r)" % (session, key, got))
    if d.get("difficulty") or d.get("rubber_banding") is not None or d.get("behavior"):
        print("  meta: difficulty=%s rubber=%s behavior=%s"
              % (st["difficulty"], st["rubber"],
                 "; ".join("%s=%s" % (s, {k: v for k, v in sorted(f.items())
                                          if k in aifield.BEHAVIOR_KEYS.values()})
                           for s, f in sorted(st["behavior"].items()))))


def build(d, out_dir, write=True):
    cache = Cache()
    by_car = aifield.ai_files(aifield.manifest_files(cache))
    print("AI_ index: %d cars (snapshot %s)" % (len(by_car), cache.live))
    _e, tpl, _n = aifield.read_entry(d["template"])
    text = build_text(d, tpl, by_car)
    st = aifield.parse(text)
    names = set(aifield.manifest_files(cache))
    dangling = [r for r in st["cm"] if r[2] + r[3] not in names]
    check(not dangling, "%d manifest rows point to a missing AI_ file (e.g. %s)"
          % (len(dangling), dangling[:3]))
    check(aifield.parse(text)["mode"] == aifield.parse(tpl)["mode"], "mode changed")
    print("%s: %s | %d EligibleCars | %d manifest rows | %d slots%s"
          % (d["name"], st["mode"], len(st["elig"]), len(st["cm"]),
             len(st["drivatars"]) // (2 if d["mode"] == "list" else 1),
             " | window %s..%s/%s" % (st["cfg"]["MinimumPI"], st["cfg"]["MaximumPI"],
                                      st["cfg"]["PIStep"]) if d["mode"] == "pool" else ""))
    _check_written_meta(d, st)
    if d["mode"] == "pool":
        for car, (low, used) in aifield.coverage(
                d["roster"], by_car, tuple(d["window"])).items():
            pis = by_car[car]
            check(all(pis[0] <= p <= pis[-1] for p in used),
                  "coverage of car %d left the AI_ catalogue" % car)
            print("  coverage %d: %d AI_ files %d..%d | window %d..%d/%d -> "
                  "files %d..%d (%d step(s))"
                  % (car, len(pis), pis[0], pis[-1], d["window"][0],
                     d["window"][1], d["window"][2], min(used), max(used),
                     len(used)))
    cur, _t, _n = aifield.read_entry(d["logical"])
    enc = aifield.encrypt_for_install(text, cur, os.path.join(WORK, d["name"]))
    check(crypto.decrypt(enc) == text.encode("utf-8"), "payload round-trip diverged")
    print("payload: %d B (current entry %d B)" % (len(enc), len(cur)))
    if not write:
        print("check only: nothing written")
        return None
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "XML." + d["logical"][:-4] + ".enc")
    with open(path, "wb") as fh:
        fh.write(enc)
    print("wrote " + path)
    print("next (game CLOSED):")
    print("  python _tools\\install_edit.py --dry-run --logical %s --payload %s"
          % (d["logical"], path))
    print("  python _tools\\install_edit.py --verify  --logical %s --payload %s"
          % (d["logical"], path))
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--def", dest="defn", required=True, metavar="FILE")
    ap.add_argument("--out", help="output folder (default patches/<name>)")
    ap.add_argument("--check", action="store_true",
                    help="build and validate, write nothing")
    a = ap.parse_args(argv)
    try:
        d = load_def(a.defn)
        build(d, a.out or os.path.join(PATCHES, d["name"]), write=not a.check)
    except FmError as exc:
        print("FAIL: %s" % exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
