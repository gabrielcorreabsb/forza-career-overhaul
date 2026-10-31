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
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fmlib import bcs as B  # noqa: E402
from fmlib import cars as C  # noqa: E402
from fmlib import carsxml, crypto, ids, overrides, strs  # noqa: E402
from fmlib.cache import Cache  # noqa: E402
from fmlib.core import FmError, ROOT, json_dump, json_load_exact  # noqa: E402
from fmlib.kit import Kit  # noqa: E402

WARN = []


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
        B.cups(bcs).append(cup)                      # tail, como o mc57
    _c, donor_lad = B.find_ladder(bcs, lad_spec["donor"])
    if donor_lad is None:
        raise FmError("%s: donor ladder %d not found" % (snap, lad_spec["donor"]))
    lad = B.clone_ladder(donor_lad, new_ids["ladder"],
                         name_key(lad_spec.get("key_label", lad_spec["name"])))
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
def main(argv=None):
    p = argparse.ArgumentParser(prog="build_series.py")
    p.add_argument("--spec", required=True)
    p.add_argument("--cache-dir", default=None)
    p.add_argument("--out", default=None,
                   help="kit directory (default patches/<kit>)")
    args = p.parse_args(argv)

    spec = load_spec(args.spec)
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

    # ids novos de cup/ladder: livres em TODAS as snapshots (como o mc57)
    loaded = {}
    for snap in snaps:
        raw = crypto.decrypt(cache.payload(snap, B.LOGICAL))
        loaded[snap] = json_load_exact(raw, "%s BCS" % snap)
    new_ids = {}
    lad_spec = spec["placement"]["ladder"]
    if isinstance(lad_spec, dict):
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


if __name__ == "__main__":
    try:
        sys.exit(main())
    except FmError as exc:
        print("ERROR: %s" % exc, file=sys.stderr)
        sys.exit(1)
