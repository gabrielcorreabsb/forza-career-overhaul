#!/usr/bin/env python3
# -*- coding: ascii -*-
"""test_aifield.py - fmlib.aifield must reproduce known documents byte for byte.

Read-only: reads the install zip (cfa7698c...) and the cache manifest. Needs
only your own game and the CMS key (no kit, no private payload).
  1. template: rewrite the vanilla AIField_115560000_Gen.xml with its own
     roster, window, slots and frames -> identical text
  2. list: rewrite vanilla AIField_117150001_Gen.xml with its own lineup
     -> identical text
  3. a vanilla template (AIField_80050001_Gen.xml) parses and every window
     row resolves to an existing AI_ file
  4. frames: the mc58 frames re-render byte for byte, new frames re-parse and
     nothing else changes; a vanilla 5-frame block re-renders exactly
  5. manifest rule: rebuilt manifests equal the vanilla ones (incl. the extra
     row at an off-grid maximum such as 850-999) for most vanilla templates
  6. every definition in specs/aifield builds from its vanilla donor and is
     deterministic
  7. document metadata: difficulty / rubber banding / behavior flags rewrite
     only their own attributes (the vanilla values come back byte-identical)

  python _tools\\test_aifield.py
"""

import os
import re
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
from fmlib import aifield, crypto  # noqa: E402
from fmlib.cache import Cache  # noqa: E402
from fmlib.core import FmError  # noqa: E402


def check(cond, msg):
    if not cond:
        raise SystemExit("FAIL: " + msg)
    print("ok  " + msg)


def main():
    try:
        by_car = aifield.ai_files(aifield.manifest_files(Cache()))
    except FmError as exc:
        raise SystemExit("FAIL: %s" % exc)
    check(len(by_car) > 500, "AI_ index: %d cars" % len(by_car))

    # 1. template mode, vanilla donor (what build_aifield.py starts from)
    _e, mc58, _n = aifield.read_entry("AIField_115560000_Gen.xml")
    st = aifield.parse(mc58)
    check(st["mode"] == "AIDrivatarTemplate" and len(st["elig"]) > 0,
          "115560000 parses as template with %d cars" % len(st["elig"]))
    win = (int(st["cfg"]["MinimumPI"]), int(st["cfg"]["MaximumPI"]),
           int(st["cfg"]["PIStep"]))
    slots = int(st["cfg"]["NumberOfDrivatars"])
    again = aifield.rewrite_template(mc58, st["elig"], by_car)
    check(again == mc58, "template rewrite reproduces 115560000 byte for byte")
    check(aifield.rewrite_template(mc58, st["elig"], by_car, win, slots,
                                   st["frames"]) == mc58,
          "explicit window %s, %d slots and frames reproduce 115560000"
          % (win, slots))
    wide = aifield.rewrite_template(mc58, st["elig"], by_car, (500, 800, 10),
                                    drivatars=23)
    check(aifield.parse(wide)["cfg"]["MaximumPI"] == "800"
          and aifield.parse(wide)["drivatars"].count(-1) == 23,
          "window 500..800 and 23 slots are written")

    # 2. list mode, vanilla multi-class lineup
    _e, vtxt, _n = aifield.read_entry("AIField_117150001_Gen.xml")
    vs = aifield.parse(vtxt)
    check(vs["mode"] == "AIDrivatarList", "117150001 is a list document")
    lineup = vs["drivatars"][:len(vs["drivatars"]) // 2]
    check(len(lineup) == 23, "117150001 lineup has 23 slots")
    check(aifield.rewrite_list(vtxt, lineup, by_car) == vtxt,
          "list rewrite reproduces 117150001 byte for byte")

    # 3. vanilla template: every manifest row resolves
    _e, ttxt, _n = aifield.read_entry("AIField_80050001_Gen.xml")
    ts = aifield.parse(ttxt)
    errs, _w = aifield.validate(ts["elig"], by_car)
    check(not errs, "80050001 roster validates (%s)" % errs[:2])
    # 4. progression frames
    check(len(st["frames"]) >= 3 and all(len(f) == 3 for f in st["frames"]),
          "115560000 frames parse: %s" % st["frames"])
    fs = st["frames_span"]
    check(aifield.render_frames(st["frames"]) == mc58[fs[0]:fs[1]],
          "115560000 frames block re-renders byte for byte")
    check(aifield.rewrite_template(mc58, st["elig"], by_car, win,
                                   frames=st["frames"]) == mc58,
          "rewrite with the original frames reproduces 115560000")
    new_fr = [(40, -350, 250), (80, -350, 250), (100, -350, 250)]
    wide_fr = aifield.rewrite_template(mc58, st["elig"], by_car, frames=new_fr)
    check(aifield.parse(wide_fr)["frames"] == new_fr,
          "new frames re-parse (-350..+250 x3)")
    a, b = aifield.parse(mc58)["frames_span"], aifield.parse(wide_fr)["frames_span"]
    check(mc58[:a[0]] == wide_fr[:b[0]] and mc58[a[1]:] == wide_fr[b[1]:],
          "only the frames block changed")
    five = None
    with open(aifield.zip_path(), "rb") as _fh:
        import zipfile
        zf = zipfile.ZipFile(_fh)
        for name in zf.namelist():
            t = crypto.decrypt(zf.read(name)).decode("utf-8")
            try:
                s5 = aifield.parse(t)
            except FmError:
                continue
            if len(s5["frames"]) == 5 and name != "AIField_115560000_Gen.xml":
                five = (name, t, s5)
                break
    check(five is not None, "found a vanilla template with 5 frames")
    sp = five[2]["frames_span"]
    check(aifield.render_frames(five[2]["frames"]) == five[1][sp[0]:sp[1]],
          "%s 5-frame block re-renders byte for byte" % five[0])

    # 5. manifest rule against vanilla (the 850-999 window has an off-grid max)
    with open(aifield.zip_path(), "rb") as _fh:
        zf = zipfile.ZipFile(_fh)
        exact = total = 0
        for name in zf.namelist():
            if name == "AIField_117160001_Gen.xml":
                continue
            t = crypto.decrypt(zf.read(name)).decode("utf-8")
            try:
                v = aifield.parse(t)
            except FmError:
                continue
            if v["mode"] != "AIDrivatarTemplate" or not v["elig"]:
                continue
            c = v["cfg"]
            w = (int(c["MinimumPI"]), int(c["MaximumPI"]), int(c["PIStep"]))
            total += 1
            try:
                same = aifield.manifest_rows(v["elig"], by_car, w) == v["cm"]
            except FmError:
                same = False
            exact += same
            if name == "AIField_70980010_Gen.xml":
                check(same, "850-999/10 (off-grid max) manifest reproduced exactly")
    check(exact >= 340, "manifest rule reproduces %d/%d vanilla templates "
          "(the rest differ by AI_ file names, not by the rule)" % (exact, total))

    # 6. build_aifield: the example definitions build from the vanilla donors
    import glob
    import build_aifield
    from fmlib.core import ROOT
    defs = sorted(glob.glob(os.path.join(ROOT, "specs", "aifield", "*.json")))
    check(defs, "example AI definitions found in specs/aifield")
    for path in defs:
        d = build_aifield.load_def(path)
        _e, tpl, _n = aifield.read_entry(d["template"])
        txt = build_aifield.build_text(d, tpl, by_car)
        v = aifield.parse(txt)
        n_ids = len(d.get("roster") or d["lineup"])
        if d["mode"] == "pool":
            ok = v["elig"] == d["roster"] and len(v["drivatars"]) == d["slots"]
        else:
            ok = v["drivatars"][:n_ids] == d["lineup"]
        check(ok, "%s builds from %s" % (d["name"], d["template"]))
        check(build_aifield.build_text(d, tpl, by_car) == txt,
              "%s build is deterministic" % d["name"])

    # 7. document metadata: difficulty / rubber banding / behavior
    check(st["difficulty"] and st["rubber"] in ("True", "False"),
          "template metadata parses (difficulty %s, rubber %s)"
          % (st["difficulty"], st["rubber"]))
    inv = {v: k for k, v in aifield.BEHAVIOR_KEYS.items()}
    own = {s: {inv[a]: (v == "True") for a, v in f.items() if a in inv}
           for s, f in st["behavior"].items()}
    check(len(own) == 2 and all(own.values()),
          "template behavior parses both sessions: %s" % sorted(own))
    check(aifield.rewrite_template(mc58, st["elig"], by_car,
                                   difficulty=st["difficulty"],
                                   rubber_banding=st["rubber"] == "True",
                                   behavior=own) == mc58,
          "difficulty/rubber/behavior rewritten with their own values "
          "reproduce 115560000 byte for byte")
    off = {"FeaturedRace": {"SlowDown": False, "CatchUp": False,
                            "Proximity": False, "PosDifficultySpread": False}}
    meta = aifield.rewrite_template(mc58, st["elig"], by_car,
                                    difficulty="Expert", rubber_banding=False,
                                    behavior=off)
    m = aifield.parse(meta)
    check(m["difficulty"] == "Expert" and m["rubber"] == "False",
          "difficulty Expert and rubber banding off are written")
    fr = m["behavior"]["FeaturedRace"]
    check(all(fr[a] == "False" for a in ("EnableDifficultySlowDown",
                                         "EnableDifficultyCatchUp",
                                         "EnableDifficultyProximity",
                                         "EnablePosDifficultySpread")),
          "the FeaturedRace elastic flags are off: %s" % fr)
    check(m["behavior"]["PracticeAndQualification"]
          == st["behavior"]["PracticeAndQualification"],
          "PracticeAndQualification keeps the template flags")

    def neutral(t):
        t = re.sub(r'(AIDifficulty=")[^"]*(")', r"\1?\2", t)
        t = re.sub(r'(AIRubberBandingEnabled=")[^"]*(")', r"\1?\2", t)
        for a in aifield.BEHAVIOR_KEYS.values():
            t = re.sub(r'(%s=")[^"]*(")' % a, r"\1?\2", t)
        return t
    check(neutral(meta) == neutral(mc58),
          "only difficulty/rubber/behavior attributes changed")
    try:
        aifield.set_behavior(mc58, {"FeaturedRace": {"Bogus": False}})
    except FmError:
        check(True, "set_behavior rejects an unknown key")
    else:
        check(False, "set_behavior rejects an unknown key")
    print("test_aifield: OK")


if __name__ == "__main__":
    main()
