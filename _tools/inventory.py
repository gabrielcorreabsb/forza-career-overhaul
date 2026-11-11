#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""inventory.py - regenerates _data/*.json and docs/inventario/*.md.

Single source for the inventories (replaces mc54_cardump.py, mc54_tracks.py,
gen_lista_carros.py and the ad-hoc dumps of ladders/tracks/posters/divisions).
READ-ONLY: never writes to the game cache or install.

Sources:
  * game cache (live snapshot = newest prod/<snapshot>, entries resolved by
    Checksum, never by name/mtime): BuildersCupScheduleDataV4.json,
    BCEventOverrides.json, CarDenyLists.json, LocStrings_pt-BR.str
  * install (optional, --install / env FM_INSTALL): gamedb.decrypted.sqlite
    + base/stringtables/br.zip -> cars.json, divisions_full.json
    (if missing, the existing files are kept and a warning is printed)
  * patches/*/plan.json metadata + patches/ids_retired.json + patches/ledger.jsonl

Outputs (_data/): ladders, tracks, posters, divisions, track_events, denylist,
cars, divisions_full, career (new), ids (new), kits_state (new), _meta (new).
Outputs (docs/inventario/): CARROS, PISTAS, CARREIRA, POSTERS, ESTADO, KITS (.md).

Usage:
  python _tools\\inventory.py                       # live cache, write all
  python _tools\\inventory.py --cache-dir _work\\cachetest
  python _tools\\inventory.py --check               # exit 1 if _data/docs are stale

Exit codes: 0 ok, 1 stale (--check) or error, 3 ok with warnings.
"""

import argparse
import base64
import collections
import glob
import hashlib
import json
import os
import sqlite3
import sys
import time
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cms_crypto import cms_decrypt  # noqa: E402
from str_edit import StrTable  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "_data")
DOCS = os.path.join(ROOT, "docs", "inventario")
PATCHES = os.path.join(ROOT, "patches")
DEFAULT_CACHE = os.path.join(
    os.environ.get("LOCALAPPDATA", ""), r"Microsoft.ForzaMotorsport\CmsCache")
DEFAULT_INSTALL = os.environ.get(
    "FM_INSTALL", r"F:\SteamLibrary\steamapps\common\Forza Motorsport")

BCS = "BuildersCupScheduleDataV4.json"
CLASSES = {0: "E", 1: "D", 2: "C", 3: "B", 4: "A", 5: "S", 6: "R", 7: "P", 8: "X"}
SERIES_CUSTOM_MIN = 20000
# faixa custom de EventDataId: vanilla usa ids maiores (7xxxxxxx, 65896xxxx...)
EVENT_CUSTOM_RANGE = (65897900, 65900000)


def is_custom_event(eid):
    return EVENT_CUSTOM_RANGE[0] <= eid < EVENT_CUSTOM_RANGE[1]

WARN = []


def warn(msg):
    WARN.append(msg)
    print("WARNING: " + msg)


def b64sha(data):
    return base64.b64encode(hashlib.sha256(data).digest()).decode("ascii")


# --------------------------------------------------------------------------- #
# sources
# --------------------------------------------------------------------------- #
def load_live(cache_dir):
    """Returns (snapshot, prod_checksum, prod, {logical: encrypted payload})."""
    prod_dir = os.path.join(cache_dir, "prod")
    snaps = sorted(n for n in os.listdir(prod_dir)
                   if os.path.isfile(os.path.join(prod_dir, n)))
    if not snaps:
        raise SystemExit("no snapshot in %s" % prod_dir)
    snap = snaps[-1]
    raw = open(os.path.join(prod_dir, snap), "rb").read()
    prod = json.loads(raw.decode("utf-8-sig"))
    want = {f["Path"]: f["Checksum"] for f in prod["Files"]}
    payloads = {}
    for dp, _, fs in os.walk(cache_dir):
        for f in fs:
            try:
                zf = zipfile.ZipFile(os.path.join(dp, f))
            except (zipfile.BadZipFile, OSError):
                continue
            with zf:
                for n in zf.namelist():
                    if n in want and n not in payloads:
                        d = zf.read(n)
                        if b64sha(d) == want[n]:
                            payloads[n] = d
    return snaps, snap, b64sha(raw), prod, payloads


def dec_json(payloads, name):
    if name not in payloads:
        raise SystemExit("%s not found in the live snapshot" % name)
    return json.loads(cms_decrypt(payloads[name]).decode("utf-8-sig"))


def load_install(install):
    db_path = os.path.join(install, "media", "base", "db",
                           "gamedb.decrypted.sqlite")
    br_path = os.path.join(install, "media", "base", "stringtables", "br.zip")
    if not (os.path.isfile(db_path) and os.path.isfile(br_path)):
        warn("install data not found under %s - keeping existing cars.json "
             "and divisions_full.json" % install)
        return None, None
    with zipfile.ZipFile(br_path) as z:
        vals = StrTable.load(z.read("Data_Car.str")).values_by_name()
    db = sqlite3.connect("file:%s?mode=ro" % db_path.replace("\\", "/"),
                         uri=True)
    try:
        cur = db.cursor()
        cars = []
        for r in cur.execute("SELECT Id,Year,MakeID,ClassID,PerformanceIndex,"
                             "BaseCost FROM Data_Car ORDER BY Id"):
            i = r[0]
            cars.append({"id": i, "name": vals.get("IDS_DisplayName_%d" % i),
                         "short": vals.get("IDS_ModelShort_%d" % i),
                         "year": r[1], "make": r[2], "class": r[3],
                         "pi": round(r[4] * 999), "price": r[5]})
        divs = {}
        for r in cur.execute("SELECT Id,TestName,Name,RestrictionId "
                             "FROM CarDivisions"):
            divs[str(r[0])] = {"test": r[1], "name": r[2], "restriction": r[3]}
    finally:
        db.close()
    return cars, divs


def read_json(path, default=None):
    if not os.path.isfile(path):
        return default
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def load_kits():
    kits = collections.OrderedDict()
    for p in sorted(glob.glob(os.path.join(PATCHES, "*", "plan.json"))):
        kits[os.path.basename(os.path.dirname(p))] = (p, read_json(p))
    return kits


def load_ledger():
    path = os.path.join(PATCHES, "ledger.jsonl")
    out = []
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    out.append(json.loads(line))
    return out


# --------------------------------------------------------------------------- #
# builders
# --------------------------------------------------------------------------- #
def walk(bcs):
    for ch in bcs["Championships"]:
        for cup in ch["ChampionshipCupData"]:
            for lad in cup["ChampionshipLadder"]:
                for ser in lad["ChampionshipSeriesData"]:
                    yield cup, lad, ser


def build_bcs(bcs, names):
    cups = [c for ch in bcs["Championships"] for c in ch["ChampionshipCupData"]]
    ladders = [{"cup": c["ChampionshipCupId"], "ladder": l["ChampionshipLadderId"],
                "order": l["OrderData"],
                "series": [s["ChampionshipSeriesId"]
                           for s in l["ChampionshipSeriesData"]],
                "close": l["CloseTime"]}
               for c in cups for l in c["ChampionshipLadder"]]
    series = [s for _, _, s in walk(bcs)]
    tracks = collections.OrderedDict()
    for s in series:
        for e in s["ChampionshipEventData"]:
            tracks.setdefault(str(e["SerialTrackId"]), {
                "trackId": e["TrackId"], "exemplo": e["Name"],
                "poster": e["TrackEnvironmentImagePath"],
                "ribbon": e["TrackRibbonImagePath"]})
    posters = dict(collections.Counter(s["ImagePath"] for s in series))
    divisions = dict(collections.Counter(
        s["SelectableCars"].get("CarDivisionId") for s in series))

    nm = lambda k: names.get(k) if isinstance(k, str) and k else None
    career = []
    for c in cups:
        lad_by_id = {l["ChampionshipLadderId"]: l for l in c["ChampionshipLadder"]}
        order = [i for i in c.get("LadderOrderData", []) if i in lad_by_id]
        order += [i for i in lad_by_id if i not in order]
        cup_out = {"cup": c["ChampionshipCupId"], "name": nm(c["Name"]),
                   "close": c["CloseTime"], "ladders": []}
        for lid in order:
            l = lad_by_id[lid]
            ser_by_id = {s["ChampionshipSeriesId"]: s
                         for s in l["ChampionshipSeriesData"]}
            sorder = [i for i in l.get("OrderData", []) if i in ser_by_id]
            sorder += [i for i in ser_by_id if i not in sorder]
            lad_out = {"ladder": lid, "name": nm(l["Name"]), "series": []}
            for sid in sorder:
                s = ser_by_id[sid]
                lad_out["series"].append({
                    "series": sid, "name": nm(s["Name"]),
                    "custom": sid >= SERIES_CUSTOM_MIN,
                    "division": s["SelectableCars"].get("CarDivisionId"),
                    "poster": s["ImagePath"],
                    "events": [{"event": e["EventDataId"],
                                "track": e["SerialTrackId"],
                                "name": e["Name"],
                                "laps": e.get("NumberOfRequiredLaps"),
                                "pi": e.get("TargetPI")}
                               for e in s["ChampionshipEventData"]]})
            cup_out["ladders"].append(lad_out)
        career.append(cup_out)
    return ladders, tracks, posters, divisions, career


def build_track_events(ovr, prod_names):
    by_track = collections.defaultdict(list)
    for o in ovr:
        by_track[o["Track"]].append(o)
    out = collections.OrderedDict()
    for t, lst in sorted(by_track.items()):
        # doador = override vanilla com AIField existente (eventos custom nao)
        good = [o for o in lst if o["AIFileName"] in prod_names
                and not is_custom_event(o["ID"])]
        out[str(t)] = {
            "entries": len(lst), "com_ia": len(lst) and len(good),
            "doadores": [{"id": o["ID"], "cr": o["ClassRestriction"],
                          "pi": o["TargetPI"], "pg": o["ParentGeneratorId"],
                          "ai": o["AIFileName"]}
                         for o in sorted(good, key=lambda x: x["ID"])[:4]]}
    return out


def build_denylist(d):
    return [{"carros": e.get("DeniedCars"), "sempre": e.get("AlwaysDeny"),
             "de": e.get("StartEndDenyTime", {}).get("From"),
             "ate": e.get("StartEndDenyTime", {}).get("To")}
            for e in d["DeniedCars"]]


def build_ids(bcs, kits, retired):
    series = sorted({s["ChampionshipSeriesId"] for _, _, s in walk(bcs)
                     if s["ChampionshipSeriesId"] >= SERIES_CUSTOM_MIN})
    events = sorted({e["EventDataId"] for _, _, s in walk(bcs)
                     for e in s["ChampionshipEventData"]
                     if is_custom_event(e["EventDataId"])})
    by_kit = collections.OrderedDict()
    for kit, (_p, plan) in kits.items():
        meta = {k: v for k, v in plan.items()
                if k.endswith("_id") and not k.endswith("_donor_id")
                and isinstance(v, int)}
        if isinstance(plan.get("str_keys"), dict):
            meta["str_keys"] = sorted(plan["str_keys"])
        if meta:
            by_kit[kit] = meta
    return {"custom_ranges": {"series_min": SERIES_CUSTOM_MIN,
                              "events": list(EVENT_CUSTOM_RANGE)},
            "live": {"series": series, "events": events},
            "kits": by_kit,
            "retired": retired}


def build_kits_state(kits, snap, prod, in_cache):
    """in_cache: logicals resolvidos no cache (o resto vive no install e o
    cache_edit.py ignora - nao conta para o status do kit)."""
    live = {f["Path"]: f["Checksum"] for f in prod["Files"]}
    out = collections.OrderedDict()
    for kit, (path, plan) in kits.items():
        rows = []
        for t in plan.get("targets", []):
            if t.get("snapshots") and snap not in t["snapshots"]:
                continue
            if t.get("logical") not in in_cache:
                rows.append({"logical": t.get("logical"),
                             "status": "install-only"})
                continue
            if t.get("op") != "bytes":
                rows.append({"logical": t.get("logical"), "status": "n/a"})
                continue
            f = t["file"]
            f = f if os.path.isabs(f) else os.path.join(os.path.dirname(path), f)
            if not os.path.isfile(f):
                rows.append({"logical": t["logical"], "status": "missing-file"})
                continue
            ok = b64sha(open(f, "rb").read()) == live.get(t["logical"])
            rows.append({"logical": t["logical"],
                         "status": "live" if ok else "not-live"})
        st = [r["status"] for r in rows if r["status"] != "install-only"]
        if not st:
            kit_status = "other-snapshot"
        elif all(s == "live" for s in st):
            kit_status = "live"
        elif any(s == "live" for s in st):
            kit_status = "partial"
        elif all(s == "n/a" for s in st):
            kit_status = "n/a"
        else:
            kit_status = "not-live"
        out[kit] = {"status": kit_status, "targets": rows}
    return out


# --------------------------------------------------------------------------- #
# markdown (bilingual headers, single data)
# --------------------------------------------------------------------------- #
def md_header(title, meta):
    return ["# %s" % title, "",
            "> Gerado por / generated by `_tools/inventory.py` - nao editar / "
            "do not edit. Snapshot `%s`." % meta["live_snapshot"], ""]


def md_cars(cars, deny, meta):
    vet = {c for e in deny if e.get("sempre") for c in (e.get("carros") or [])}
    L = md_header("Carros / Cars (%d)" % len(cars), meta)
    L += ["Tag: `VETADO`/`DENIED` = negado sempre (CarDenyLists) - "
          "`SWAP` = motor/engine swap, sem listing / no listing.", "",
          "**PI do catalogo / catalogue PI is NOT the game's PI.** Escala do jogo / "
          "game scale: E 0-300, D 301-400, C 401-500, B 501-600, A 601-700, "
          "S 701-800, R 801-900, P 901-998, X 999. Use a classe e, para um numero "
          "por carro, `aifield_survey.py --car <id>` (menor arquivo de IA) / "
          "use the class and the lowest AI tune.", "",
          "| id | carro / car | classe / class | PI cat. (nao e o do jogo / not game PI) | ano / year | preco / price | tag |",
          "|---:|---|:-:|---:|---:|---:|---|"]
    for c in sorted(cars, key=lambda c: (c["class"], c["price"], c["id"])):
        tag = "VETADO/DENIED" if c["id"] in vet else (
            "SWAP" if c["make"] == 160 or c["id"] == 3385 else "")
        L.append("| %d | %s | %s | %d | %s | %s | %s |" % (
            c["id"], c["short"] or c["name"] or "?",
            CLASSES.get(c["class"], c["class"]), c["pi"], c["year"],
            c["price"], tag))
    return L


def md_tracks(tracks, tev, meta):
    L = md_header("Pistas / Tracks (%d)" % len(tracks), meta)
    L += ["Doador / donor = override com IA valida (BCEventOverrides) - "
          "base para eventos novos / base for new events.", "",
          "| SerialTrackId | exemplo / example | overrides | com IA / with AI | "
          "doador / donor (id, CR, PI, AIField) |",
          "|---:|---|---:|---:|---|"]
    for sid, t in sorted(tracks.items(), key=lambda kv: kv[1]["exemplo"]):
        te = tev.get(sid, {})
        d = te.get("doadores") or []
        donor = ("%d, %d, %d, `%s`" % (d[0]["id"], d[0]["cr"], d[0]["pi"],
                                       d[0]["ai"]) if d else "-")
        L.append("| %s | %s | %s | %s | %s |" % (
            sid, t["exemplo"], te.get("entries", 0), te.get("com_ia", 0), donor))
    return L


def md_career(career, meta):
    L = md_header("Carreira / Career (championship 500)", meta)
    L += ["Ordem = `LadderOrderData`/`OrderData` (como no jogo / as in game). "
          "`*` = serie custom (id >= %d)." % SERIES_CUSTOM_MIN, ""]
    for c in career:
        L.append("## Cup %d - %s" % (c["cup"], c["name"] or "?"))
        L.append("")
        for l in c["ladders"]:
            L.append("- **Ladder %d** - %s" % (l["ladder"], l["name"] or "?"))
            for s in l["series"]:
                tr = ", ".join(sorted({e["name"] for e in s["events"]}))
                L.append("  - %s%d %s - %d evento(s)/event(s): %s" % (
                    "*" if s["custom"] else "", s["series"], s["name"] or "?",
                    len(s["events"]), tr))
        L.append("")
    return L


def md_posters(posters, meta):
    L = md_header("Posters de serie / Series posters (%d)" % len(posters), meta)
    L += ["| uso / uses | ImagePath |", "|---:|---|"]
    for p, n in sorted(posters.items(), key=lambda kv: (-kv[1], kv[0])):
        L.append("| %d | `%s` |" % (n, p.split("\\")[-1]))
    return L


def md_state(kstate, ledger, meta):
    L = md_header("Estado / State", meta)
    L += ["## Kits x cache live / Kits vs live cache", "",
          "`live` = payload do kit e o atual / kit payload is current - "
          "`not-live` = substituido ou nao aplicado / superseded or not applied - "
          "`n/a` = op json (sem payload / no payload) - `install-only` = "
          "arquivo fora do cache, ignorado pelo `cache_edit.py` / not in cache, "
          "skipped by `cache_edit.py`.", "",
          "| kit | status | alvos / targets |", "|---|---|---|"]
    for kit, st in kstate.items():
        L.append("| %s | %s | %s |" % (kit, st["status"], ", ".join(
            "%s=%s" % (t["logical"], t["status"]) for t in st["targets"])))
    L += ["", "## Ledger (ultimos / last 15)", ""]
    if not ledger:
        L.append("_vazio / empty_ (`patches/ledger.jsonl` e preenchido pelo "
                 "`cache_edit.py` a cada apply / filled on each apply)")
    else:
        L += ["| quando / when | kit | verify | backup |", "|---|---|---|---|"]
        for e in ledger[-15:]:
            L.append("| %s | %s | %s | %s |" % (
                e.get("when"), e.get("kit"), e.get("verify"),
                os.path.basename(e.get("backup") or "") or "-"))
    return L


def load_kit_status():
    """Class of each kit (patches/kit_status.json); {} when the file is absent."""
    data = read_json(os.path.join(PATCHES, "kit_status.json"), {}) or {}
    return data.get("kits", {})


def md_kits(status, kstate, meta):
    L = md_header("Kits por classe / Kits by class", meta)
    L += ["Fonte / source: `patches/kit_status.json`. `core` = receita que a "
          "carreira usa / recipe the career builds on - `evidence` = achado ou "
          "etapa util / useful finding or step - `legacy` = negativo, "
          "inconclusivo ou abandonado / negative, inconclusive or dropped - "
          "`never_played` = sem resultado no jogo / no in-game result.", ""]
    for cls in ("core", "evidence", "legacy", "never_played"):
        rows = [(k, v) for k, v in status.items() if v.get("class") == cls]
        L += ["## %s (%d)" % (cls, len(rows)), "",
              "| kit | motivo / basis |", "|---|---|"]
        L += ["| %s | %s |" % (k, v.get("basis", "")) for k, v in rows]
        L.append("")
    missing = sorted(k for k in kstate if k not in status)
    if missing:
        L += ["## sem classe / no class (%d)" % len(missing), "",
              ", ".join(missing), ""]
    return L[:-1]


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(prog="inventory.py")
    p.add_argument("--cache-dir", default=DEFAULT_CACHE)
    p.add_argument("--install", default=DEFAULT_INSTALL)
    p.add_argument("--check", action="store_true",
                   help="compare with files on disk, write nothing")
    args = p.parse_args(argv)

    snaps, snap, prod_ck, prod, payloads = load_live(os.path.abspath(args.cache_dir))
    print("live snapshot: %s (%d entries resolved)" % (snap, len(payloads)))
    bcs = dec_json(payloads, BCS)
    names = {}
    if "LocStrings_pt-BR.str" in payloads:
        names = StrTable.load(cms_decrypt(payloads["LocStrings_pt-BR.str"])
                              ).values_by_name()
    else:
        warn("LocStrings_pt-BR.str not in live snapshot - names will be empty")

    ladders, tracks, posters, divisions, career = build_bcs(bcs, names)
    tev = build_track_events(dec_json(payloads, "BCEventOverrides.json"),
                             {f["Path"] for f in prod["Files"]})
    deny = build_denylist(dec_json(payloads, "CarDenyLists.json"))
    cars, divs_full = load_install(args.install)
    install_used = cars is not None
    if not install_used:
        cars = read_json(os.path.join(DATA, "cars.json"), [])
        divs_full = read_json(os.path.join(DATA, "divisions_full.json"), {})
    kits = load_kits()
    retired = read_json(os.path.join(PATCHES, "ids_retired.json"), {})
    ids = build_ids(bcs, kits, retired)
    kstate = build_kits_state(kits, snap, prod, set(payloads))
    ledger = load_ledger()
    meta = {"live_snapshot": snap, "snapshots": snaps, "prod_checksum": prod_ck,
            "install_used": install_used,
            "counts": {"cars": len(cars), "tracks": len(tracks),
                       "ladders": len(ladders), "posters": len(posters),
                       "series": sum(len(l["series"]) for c in career
                                     for l in c["ladders"])}}

    data = collections.OrderedDict([
        ("ladders", ladders), ("tracks", tracks), ("posters", posters),
        ("divisions", divisions), ("track_events", tev), ("denylist", deny),
        ("cars", cars), ("divisions_full", divs_full), ("career", career),
        ("ids", ids), ("kits_state", kstate), ("_meta", meta)])
    docs = collections.OrderedDict([
        ("CARROS.md", md_cars(cars, deny, meta)),
        ("PISTAS.md", md_tracks(tracks, tev, meta)),
        ("CARREIRA.md", md_career(career, meta)),
        ("POSTERS.md", md_posters(posters, meta)),
        ("ESTADO.md", md_state(kstate, ledger, meta)),
        ("KITS.md", md_kits(load_kit_status(), kstate, meta))])

    stale = []
    for name, obj in data.items():
        path = os.path.join(DATA, name + ".json")
        cur = read_json(path)
        if json.loads(dump(obj)) != cur:
            stale.append(os.path.relpath(path, ROOT))
            if not args.check:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(dump(obj))
    os.makedirs(DOCS, exist_ok=True)
    for name, lines in docs.items():
        path = os.path.join(DOCS, name)
        text = "\n".join(lines) + "\n"
        cur = open(path, encoding="utf-8").read() if os.path.isfile(path) else None
        if cur != text:
            stale.append(os.path.relpath(path, ROOT))
            if not args.check:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(text)

    if args.check:
        if stale:
            print("STALE (rode / run `python _tools\\inventory.py`):")
            for s in stale:
                print("  " + s)
            return 1
        print("inventory up to date")
        return 3 if WARN else 0
    print("written: %d file(s)%s" % (len(stale), "" if not stale else
                                      "\n  " + "\n  ".join(stale)))
    return 3 if WARN else 0


if __name__ == "__main__":
    t0 = time.time()
    rc = main()
    print("(%.1fs)" % (time.time() - t0))
    sys.exit(rc)
