"""BuildersCupScheduleDataV4.json: navigation, invariants and clone helpers.

Model: Championships[ChampionshipId=500] -> ChampionshipCupData (cups)
-> ChampionshipLadder (ladders) -> ChampionshipSeriesData (series)
-> ChampionshipEventData (events). Order lives in cup.LadderOrderData and
ladder.OrderData; invariant: ladder.OrderData == ids of its series.
"""

import copy

from .core import ALWAYS_OPEN, CHAMPIONSHIP_CAREER, FmError
from .ids import SERIES_MIN

LOGICAL = "BuildersCupScheduleDataV4.json"


def career(bcs):
    hits = [c for c in bcs["Championships"]
            if c.get("ChampionshipId") == CHAMPIONSHIP_CAREER]
    if len(hits) != 1:
        raise FmError("ChampionshipId=%d: %d occurrences"
                      % (CHAMPIONSHIP_CAREER, len(hits)))
    return hits[0]


def cups(bcs):
    return career(bcs)["ChampionshipCupData"]


def find_cup(bcs, cup_id):
    hits = [c for c in cups(bcs) if c.get("ChampionshipCupId") == cup_id]
    return hits[0] if len(hits) == 1 else None


def find_ladder(bcs, ladder_id):
    """(cup, ladder) or (None, None)."""
    for cup in cups(bcs):
        for lad in cup.get("ChampionshipLadder", []):
            if lad["ChampionshipLadderId"] == ladder_id:
                return cup, lad
    return None, None


def iter_series(bcs):
    for cup in cups(bcs):
        for lad in cup.get("ChampionshipLadder", []):
            for s in lad.get("ChampionshipSeriesData", []):
                yield cup, lad, s


def find_series(bcs, series_id):
    hits = [s for _c, _l, s in iter_series(bcs)
            if s["ChampionshipSeriesId"] == series_id]
    return hits[0] if len(hits) == 1 else None


def find_event(bcs, event_id):
    for _c, _l, s in iter_series(bcs):
        for e in s["ChampionshipEventData"]:
            if e["EventDataId"] == event_id:
                return s, e
    return None, None


def all_ids(bcs):
    out = {"cups": [], "ladders": [], "series": [], "events": []}
    for cup in cups(bcs):
        out["cups"].append(cup["ChampionshipCupId"])
        for lad in cup.get("ChampionshipLadder", []):
            out["ladders"].append(lad["ChampionshipLadderId"])
            for s in lad.get("ChampionshipSeriesData", []):
                out["series"].append(s["ChampionshipSeriesId"])
                out["events"] += [e["EventDataId"]
                                  for e in s["ChampionshipEventData"]]
    return out


def check_invariants(bcs, label=""):
    """Unique ids + ladder.OrderData == series + OrderedEventIds == events."""
    for kind, ids in all_ids(bcs).items():
        if len(set(ids)) != len(ids):
            dup = sorted({i for i in ids if ids.count(i) > 1})
            raise FmError("%s: duplicated %s ids: %s" % (label, kind, dup))
    for cup in cups(bcs):
        lids = [l["ChampionshipLadderId"] for l in cup["ChampionshipLadder"]]
        if sorted(cup.get("LadderOrderData", [])) != sorted(lids):
            raise FmError("%s: cup %d LadderOrderData %s != ladders %s"
                          % (label, cup["ChampionshipCupId"],
                             cup.get("LadderOrderData"), lids))
        for lad in cup["ChampionshipLadder"]:
            sids = [s["ChampionshipSeriesId"]
                    for s in lad["ChampionshipSeriesData"]]
            if lad["OrderData"] != sids:
                raise FmError("%s: ladder %d OrderData %s != series %s"
                              % (label, lad["ChampionshipLadderId"],
                                 lad["OrderData"], sids))


def first_event_on_track(bcs, serial, exclude=lambda eid: False):
    """First (BCS order) existing event on SerialTrackId=serial."""
    for _c, _l, s in iter_series(bcs):
        for e in s["ChampionshipEventData"]:
            if e["SerialTrackId"] == serial and not exclude(e["EventDataId"]):
                return e
    return None


def clone_event(donor, event_id, series_id, serial=None):
    ev = copy.deepcopy(donor)
    ev["EventDataId"] = event_id
    ev["ChampionshipSeriesId"] = series_id
    if serial is not None:
        ev["SerialTrackId"] = serial
        ev["TrackId"] = "00000003-0000-0000-0000-%012d" % serial
    if not str(ev["TrackId"]).endswith("-%012d" % ev["SerialTrackId"]):
        raise FmError("event %d: TrackId/SerialTrackId mismatch" % event_id)
    return ev


def clone_series(donor, series_id, name_key, events, always_open=True,
                 clear_entry=True):
    """Series shell clone (F3_TEMPLATE 2): new id/name/events; optionally
    always-open dates and empty EntryCriteria."""
    ns = copy.deepcopy(donor)
    ns["ChampionshipSeriesId"] = series_id
    ns["Name"] = name_key
    ns["ChampionshipEventData"] = events
    ns["OrderedEventIds"] = [e["EventDataId"] for e in events]
    if always_open:
        ns["CloseTime"] = ALWAYS_OPEN
        ns["StartEndDate"]["To"] = ALWAYS_OPEN
    if clear_entry:
        ec = ns["EntryCriteria"]
        for k in ("RequiredLadders", "RequiredSeries", "RequiredEvents"):
            ec[k] = []
        for k in ("RequiredLaddersCount", "RequiredSeriesCount",
                  "RequiredEventsCount", "MinDriverLevel"):
            ec[k] = 0
    return ns


def append_series(ladder, series):
    ladder["ChampionshipSeriesData"].append(series)
    ladder["OrderData"].append(series["ChampionshipSeriesId"])


def clone_ladder(donor, ladder_id, name_key):
    lad = copy.deepcopy(donor)
    lad["ChampionshipLadderId"] = ladder_id
    lad["Name"] = name_key
    lad["ChampionshipSeriesData"] = []
    lad["OrderData"] = []
    return lad


def clone_cup(donor, cup_id, name_key):
    cup = copy.deepcopy(donor)
    cup["ChampionshipCupId"] = cup_id
    cup["Name"] = name_key
    cup["ChampionshipLadder"] = []
    cup["LadderOrderData"] = []
    return cup


def append_ladder(cup, ladder):
    cup["ChampionshipLadder"].append(ladder)
    cup["LadderOrderData"].append(ladder["ChampionshipLadderId"])


# --------------------------------------------------------------------------- #
# removals (round base): never a vanilla node
# --------------------------------------------------------------------------- #
def remove_series(bcs, series_id):
    """Removes a custom series (and its OrderData entry); returns the series
    object. Vanilla series (< SERIES_MIN) are refused."""
    if series_id < SERIES_MIN:
        raise FmError("refusing to remove vanilla series %d (< %d)"
                      % (series_id, SERIES_MIN))
    for cup in cups(bcs):
        for lad in cup.get("ChampionshipLadder", []):
            hit = [s for s in lad["ChampionshipSeriesData"]
                   if s["ChampionshipSeriesId"] == series_id]
            if not hit:
                continue
            if len(hit) > 1:
                raise FmError("series %d appears %d times in ladder %d"
                              % (series_id, len(hit),
                                 lad["ChampionshipLadderId"]))
            lad["ChampionshipSeriesData"] = [
                s for s in lad["ChampionshipSeriesData"]
                if s["ChampionshipSeriesId"] != series_id]
            lad["OrderData"] = [i for i in lad["OrderData"]
                                if i != series_id]
            return hit[0]
    raise FmError("series %d not found" % series_id)


def remove_ladder(bcs, ladder_id):
    """Removes a ladder (and its LadderOrderData entry); returns the ladder.
    A ladder holding a vanilla series is refused."""
    for cup in cups(bcs):
        hit = [l for l in cup.get("ChampionshipLadder", [])
               if l["ChampionshipLadderId"] == ladder_id]
        if not hit:
            continue
        if len(hit) > 1:
            raise FmError("ladder %d appears %d times in cup %d"
                          % (ladder_id, len(hit), cup["ChampionshipCupId"]))
        lad = hit[0]
        vanilla = sorted(s["ChampionshipSeriesId"]
                         for s in lad["ChampionshipSeriesData"]
                         if s["ChampionshipSeriesId"] < SERIES_MIN)
        if vanilla:
            raise FmError("refusing to remove ladder %d: it holds vanilla "
                          "series %s" % (ladder_id, vanilla))
        cup["ChampionshipLadder"] = [l for l in cup["ChampionshipLadder"]
                                     if l["ChampionshipLadderId"] != ladder_id]
        cup["LadderOrderData"] = [i for i in cup.get("LadderOrderData", [])
                                  if i != ladder_id]
        return lad
    raise FmError("ladder %d not found" % ladder_id)


def remove_cup(bcs, cup_id):
    """Removes a cup; returns it. A cup holding a vanilla series is refused."""
    cup = find_cup(bcs, cup_id)
    if cup is None:
        raise FmError("cup %d not found" % cup_id)
    vanilla = sorted(s["ChampionshipSeriesId"]
                     for lad in cup.get("ChampionshipLadder", [])
                     for s in lad["ChampionshipSeriesData"]
                     if s["ChampionshipSeriesId"] < SERIES_MIN)
    if vanilla:
        raise FmError("refusing to remove cup %d: it holds vanilla series %s"
                      % (cup_id, vanilla))
    cups(bcs).remove(cup)
    return cup


REF_LISTS = ("RequiredLadders", "RequiredSeries", "RequiredEvents")


def dangling_refs(bcs, removed_ids):
    """[(path, id)] where a gate/onboarding pointer still names a removed id.

    check_invariants does not look at EntryCriteria or career.OnboardingSeries,
    so a round that removes a series must refuse when one of them still points
    at it (refuse, never strip silently)."""
    removed = set(removed_ids)
    hits = []

    def walk(obj, path):
        if isinstance(obj, dict):
            for key, value in obj.items():
                sub = "%s.%s" % (path, key) if path else key
                if key in REF_LISTS and isinstance(value, list):
                    hits.extend((sub, i) for i in value if i in removed)
                elif key == "OnboardingSeries" and value in removed:
                    hits.append((sub, value))
                else:
                    walk(value, sub)
        elif isinstance(obj, list):
            for i, value in enumerate(obj):
                walk(value, "%s[%d]" % (path, i))

    walk(bcs, "")
    return hits
