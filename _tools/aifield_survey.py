#!/usr/bin/env python3
# -*- coding: ascii -*-
"""aifield_survey.py - READ-ONLY survey behind docs/guides/AI_GRIDS.md.

Counts the AIField_*.xml documents in the install zip (group CFA7698C) and the
AI_<car>_<pi>.xml ladders of the live snapshot, so every number in the docs can
be reproduced instead of trusted:

  python _tools\\aifield_survey.py            # full survey
  python _tools\\aifield_survey.py --car 1429 3781   # ladders of given cars
"""

import argparse
import collections
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fmlib import aifield, crypto  # noqa: E402
from fmlib.cache import Cache  # noqa: E402
from fmlib.cars import denied_ids, load_cars  # noqa: E402
from fmlib.core import FmError  # noqa: E402

# entries our kits rewrite in the install: not vanilla, excluded from the survey
MODIFIED = {"AIField_117160001_Gen.xml"}
CLASS = {0: "E", 1: "D", 2: "C", 3: "B", 4: "A", 5: "S", 6: "R", 7: "P", 8: "X"}
# game class table (seen in game: PI 701 shows S, 686-689 show A)
GAME_CLASSES = [(0, 0, 300, "E"), (1, 301, 400, "D"), (2, 401, 500, "C"),
                (3, 501, 600, "B"), (4, 601, 700, "A"), (5, 701, 800, "S"),
                (6, 801, 900, "R"), (7, 901, 998, "P"), (8, 999, 999, "X")]


def game_class(pi):
    for i, lo, hi, _n in GAME_CLASSES:
        if lo <= pi <= hi:
            return i
    return 8 if pi >= 999 else 0


def top(counter, n=8):
    return ", ".join("%s x%d" % (k, v) for k, v in counter.most_common(n))


def survey_documents():
    modes, slots, ndriv = collections.Counter(), collections.Counter(), \
        collections.Counter()
    windows, elig = collections.Counter(), collections.Counter()
    list_elig = []
    partial = 0
    with zipfile.ZipFile(aifield.zip_path()) as zf:
        names = zf.namelist()
        names = [n for n in names if n not in MODIFIED]
        for n in names:
            text = crypto.decrypt(zf.read(n)).decode("utf-8")
            if "AIDrivatarConfiguration" not in text:
                modes["(no configuration)"] += 1
                continue
            try:
                st = aifield.parse(text)
            except FmError:
                st = None
                partial += 1
            mode = aifield.mode_of(text)
            modes[mode] += 1
            slots[len(re.findall(r"<AIDrivatar\s", text))] += 1
            cfg = dict(re.findall(r'(\w+)="([^"]*)"', re.search(
                r"<AIDrivatarConfiguration([^>]*)>", text).group(1)))
            if mode == "AIDrivatarTemplate":
                ndriv[cfg.get("NumberOfDrivatars")] += 1
                windows["%s-%s/%s" % (cfg.get("MinimumPI"),
                                      cfg.get("MaximumPI"),
                                      cfg.get("PIStep"))] += 1
                if st:
                    elig[len(st["elig"])] += 1
            elif st:
                distinct = len(set(st["drivatars"][:len(st["drivatars"]) // 2
                                                   or None]))
                list_elig.append((n, len(st["elig"]), distinct))
    print("== documents: %d vanilla AIField files in %s (excluded, modified "
          "by our kits: %s)" % (len(names), os.path.basename(
              aifield.zip_path()), ", ".join(sorted(MODIFIED))))
    print("modes:                 %s" % top(modes))
    print("no Eligible/Manifest:  %d (not parsed as a full document)" % partial)
    print("AIDrivatar slots:      %s" % top(slots))
    print("NumberOfDrivatars:     %s" % top(ndriv))
    print("template PI windows:   %s" % top(windows, 10))
    print("EligibleCars (templ.): %s" % top(elig, 12))
    if elig:
        print("EligibleCars min/max:  %d / %d" % (min(elig), max(elig)))
    if list_elig:
        ex = [x for x in list_elig if x[0] == "AIField_117150001_Gen.xml"]
        print("list-mode EligibleCars vs distinct lineup cars (117150001): %s"
              % (str(ex[0][1:]) if ex else "n/a"))
        print("list-mode EligibleCars sizes: %s" % top(
            collections.Counter(x[1] for x in list_elig)))


def survey_ladders(cache, cars):
    by_car = aifield.ai_files(aifield.manifest_files(cache))
    denied = denied_ids()
    cat = {c["id"]: c for c in cars}
    usable = [c for c in cars if c["id"] in by_car and c["id"] not in denied]
    print("\n== AI_<car>_<pi> ladders (snapshot %s)" % cache.live)
    print("cars with AI files: %d | usable (catalogue, no always-on veto): %d"
          % (len(by_car), len(usable)))
    print("usable per class:   %s" % ", ".join(
        "%s=%d" % (CLASS[k], v) for k, v in sorted(collections.Counter(
            c["class"] for c in usable).items())))
    hi = [c for c in usable if by_car[c["id"]][-1] >= 700]
    span = [c for c in usable if by_car[c["id"]][0] <= 700 <= by_car[c["id"]][-1]]
    print("with a file >= 700: %d | ladder crossing 700: %d" % (len(hi), len(span)))
    print("\n== class scale check (game table vs the data)")
    print("game table: " + " | ".join("%s %d-%d" % (n, lo, hi)
                                       for _i, lo, hi, n in GAME_CLASSES))
    with_ai = [c for c in cars if c["id"] in by_car]
    same_low = sum(game_class(by_car[c["id"]][0]) == c["class"] for c in with_ai)
    same_cat = sum(game_class(c["pi"]) == c["class"] for c in with_ai)
    print("catalogue class id == table(lowest AI file PI): %d / %d"
          % (same_low, len(with_ai)))
    print("catalogue class id == table(cars.json pi):      %d / %d  <- the "
          "catalogue pi is NOT on the game scale" % (same_cat, len(with_ai)))
    rng = collections.defaultdict(list)
    for c in with_ai:
        rng[c["class"]].append(by_car[c["id"]][0])
    print("lowest AI file PI per catalogue class id:")
    for k in sorted(rng):
        print("  %d=%s  %d-%d  (%d cars)" % (k, CLASS[k], min(rng[k]),
                                             max(rng[k]), len(rng[k])))
    return by_car, cat


def main():
    ap = argparse.ArgumentParser(prog="aifield_survey.py")
    ap.add_argument("--car", type=int, nargs="*", help="print these ladders")
    args = ap.parse_args()
    cache, cars = Cache(), load_cars()
    if not args.car:
        survey_documents()
    by_car, cat = survey_ladders(cache, cars)
    for cid in args.car or []:
        pis = by_car.get(cid)
        c = cat.get(cid, {})
        print("\ncar %d %s (class %s, catalogue PI %s): %s" % (
            cid, c.get("name"), CLASS.get(c.get("class")), c.get("pi"),
            "%d files, %d..%d" % (len(pis), pis[0], pis[-1]) if pis
            else "no AI files"))


if __name__ == "__main__":
    main()
