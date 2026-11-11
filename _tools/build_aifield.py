#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_aifield.py - AI grid payload from a declarative definition.

Builds the XML of one AIField entry from a VANILLA template that already
lives in YOUR install (nothing of the game is stored in this repository),
encrypts it with the target entry's current payload as cipher template, and
writes the .enc ready for install_edit.py.

Read-only on the cache and on the install. Output: <out>/XML.<logical>.enc.

Cache route (--cache-plan): the SAME document is also delivered through the
CmsCache, where the entry lives in a blob. That payload can differ from the
install zip entry, so the cipher template is the CURRENT cache-blob payload of
the live snapshot (resolved by Checksum, as in inventory.load_live), never the
install one. Output, next to the install payload:
  <out>/CACHE.<logical>.enc  payload encrypted with the cache blob as template
  <out>/plan.json            cache_edit.py plan (one op="bytes" target) whose
                             "file" is CACHE.<logical>.enc and "snapshots" are
                             the snapshots that resolve to that blob payload

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
  python _tools\\build_aifield.py --def <file> --cache-plan  # + cache route
Then, install route, game closed:
  python _tools\\install_edit.py --dry-run --logical <logical> --payload <the .enc>
  python _tools\\install_edit.py --verify  --logical <logical> --payload <the .enc>
Or, cache route (--cache-plan), game closed:
  python _tools\\cache_edit.py --dry-run --plan <out>\\plan.json
  python _tools\\cache_edit.py --plan <out>\\plan.json --verify
"""

import argparse
import json
import os
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)

from fmlib import aifield, crypto                       # noqa: E402
from fmlib.cache import Cache                           # noqa: E402
from fmlib.core import PATCHES, WORK, FmError, b64sha  # noqa: E402
import inventory    # noqa: E402  (load_live: checksum-resolved cache blobs)

CACHE_PLAN = "plan.json"


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


def build_cache_plan(d, text, cache):
    """Cache route: payload + cache_edit plan for the SAME document.

    Cipher template = the CURRENT payload of `d["logical"]` inside the cache
    blob of the live snapshot (resolved by Checksum through
    inventory.load_live), never the install zip entry: the two can differ.
    Returns dict(enc, name, plan, snapshot, template).
    """
    logical = d["logical"]
    snaps, snap, _ck, prod, payloads = inventory.load_live(cache.dir)
    check(logical in payloads,
          "%s has no Checksum-matching payload in the cache blobs of snapshot "
          "%s (install-only content: there is no cache payload to use as "
          "cipher template)" % (logical, snap))
    template = payloads[logical]
    ck = b64sha(template)
    group = None
    for g in prod.get("ContentGroups", []):
        if logical in g.get("FileNames", []):
            group = g["GroupName"]
            break
    check(group, "%s is in no ContentGroup of snapshot %s"
          % (logical, snap))
    old_mode = aifield.mode_of(crypto.decrypt(template).decode("utf-8"))
    new_mode = aifield.parse(text)["mode"]
    check(old_mode == new_mode,
          "cache entry %s is %s, the new document is %s"
          % (logical, old_mode, new_mode))
    enc = crypto.encrypt(text.encode("utf-8"), template,
                         os.path.join(WORK, d["name"]), tag="cache")
    check(crypto.decrypt(enc) == text.encode("utf-8"),
          "cache payload round-trip diverged")
    snaps_hit = [s for s in snaps
                 if any(f["Path"] == logical and f["Checksum"] == ck
                        for f in cache.prod(s).get("Files", []))]
    check(snaps_hit, "the blob payload of %s resolves to no snapshot" % logical)
    name = "CACHE." + logical[:-4] + ".enc"
    plan = {"targets": [{"logical": logical, "group": group, "op": "bytes",
                         "file": name, "snapshots": snaps_hit}]}
    print("cache template: live blob payload of %s (%d B, snapshot %s)"
          % (logical, len(template), snap))
    print("  group %s | snapshots %s" % (group, ", ".join(snaps_hit)))
    print("  payload: %d B (cache template %d B)" % (len(enc), len(template)))
    return {"enc": enc, "name": name, "plan": plan, "snapshot": snap,
            "template": template}


def build(d, out_dir, write=True, cache_plan=False, cache_dir=None):
    cache = Cache(cache_dir)
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
    cplan = build_cache_plan(d, text, cache) if cache_plan else None
    if cplan is not None:
        print("  blob vs install template: %s"
              % ("same" if cplan["template"] == cur
                 else "differs (the install carries another edit)"))
    if not write:
        if cplan is not None:
            print("  plan (check only, not written): %s"
                  % json.dumps(cplan["plan"]))
        print("check only: nothing written")
        return None
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "XML." + d["logical"][:-4] + ".enc")
    with open(path, "wb") as fh:
        fh.write(enc)
    print("wrote " + path)
    print("next (install route, game CLOSED):")
    print("  python _tools\\install_edit.py --dry-run --logical %s --payload %s"
          % (d["logical"], path))
    print("  python _tools\\install_edit.py --verify  --logical %s --payload %s"
          % (d["logical"], path))
    if cplan is not None:
        cpath = os.path.join(out_dir, cplan["name"])
        with open(cpath, "wb") as fh:
            fh.write(cplan["enc"])
        print("wrote " + cpath)
        ppath = os.path.join(out_dir, CACHE_PLAN)
        with open(ppath, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(cplan["plan"], fh, indent=2)
            fh.write("\n")
        print("wrote " + ppath)
        print("next (cache route, game CLOSED):")
        print("  python _tools\\cache_edit.py --dry-run --plan %s" % ppath)
        print("  python _tools\\cache_edit.py --plan %s --verify" % ppath)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--def", dest="defn", required=True, metavar="FILE")
    ap.add_argument("--out", help="output folder (default patches/<name>)")
    ap.add_argument("--check", action="store_true",
                    help="build and validate, write nothing")
    ap.add_argument("--cache-plan", action="store_true",
                    help="also emit the cache route for the same document: "
                         "<out>/CACHE.<logical>.enc, encrypted with the CURRENT "
                         "cache-blob payload of the live snapshot as template, "
                         "plus <out>/plan.json for cache_edit.py; the install "
                         "payload <out>/XML.<logical>.enc is still written")
    ap.add_argument("--cache-dir", default=None,
                    help="cache read by --cache-plan (default: the live "
                         "CmsCache)")
    a = ap.parse_args(argv)
    try:
        d = load_def(a.defn)
        build(d, a.out or os.path.join(PATCHES, d["name"]),
              write=not a.check, cache_plan=a.cache_plan,
              cache_dir=a.cache_dir)
    except FmError as exc:
        print("FAIL: %s" % exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
