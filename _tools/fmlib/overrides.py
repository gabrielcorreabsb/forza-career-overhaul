"""BCEventOverrides.json: one sibling override per event (ID == EventDataId)."""

import copy

from .core import FmError

LOGICAL = "BCEventOverrides.json"


def find(ovr, override_id):
    hits = [o for o in ovr if o.get("ID") == override_id]
    return hits[0] if len(hits) == 1 else None


def clone(ovr, donor_id, new_id, ai_files, track=None, class_restriction=None,
          target_pi=None, laps=None, pits=None):
    """Appends a clone of `donor_id` as `new_id`. `ai_files` = manifest paths;
    the AIFileName must exist there (ladder 736 crashed on missing AI)."""
    if find(ovr, new_id) is not None or any(o.get("ID") == new_id for o in ovr):
        raise FmError("override %d already exists" % new_id)
    d = find(ovr, donor_id)
    if d is None:
        raise FmError("donor override %d not found (or duplicated)" % donor_id)
    if track is not None and d.get("Track") != track:
        raise FmError("donor override %d is on Track %s, not %d"
                      % (donor_id, d.get("Track"), track))
    if d["AIFileName"] not in ai_files:
        raise FmError("donor override %d: AIFileName %s not in manifest"
                      % (donor_id, d["AIFileName"]))
    new = copy.deepcopy(d)
    new["ID"] = new_id
    if class_restriction is not None:
        new["ClassRestriction"] = class_restriction
    if target_pi is not None:
        new["TargetPI"] = target_pi
    if laps is not None:
        new["FeatureRace"]["Laps"] = laps
    if pits is not None:
        new["FeatureRace"]["Pits"] = pits
    ovr.append(new)
    return new
