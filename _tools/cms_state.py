"""
cms_state.py — snapshot/compare do estado do CMS no disco.

Uso:
  python cms_state.py snap <label>     -> grava _tools/state/<label>.json
  python cms_state.py diff <a> <b>     -> compara dois snapshots
  python cms_state.py show <label>     -> imprime o snapshot

Cobre as duas fontes possiveis do CMS em runtime:
  A) install : media/pcfamily/cms/  (8 ZIPs por GUID + manifesto faa126fd...)
  B) cache   : %LOCALAPPDATA%/Microsoft.ForzaMotorsport/CmsCache/
               cache-manifest.json (criptografado) + prod/<snapshot>/*.json
               + blobs numericos/<sha256hex>
"""
import hashlib
import json
import os
import sys
import datetime

GAME = r"F:\SteamLibrary\steamapps\common\Forza Motorsport"
INSTALL_CMS = os.path.join(GAME, "media", "pcfamily", "cms")
CACHE = os.path.join(os.environ["LOCALAPPDATA"], "Microsoft.ForzaMotorsport", "CmsCache")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state")


def sha256(path, limit=None):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                b = f.read(1 << 20)
                if not b:
                    break
                h.update(b)
    except OSError:
        return None
    return h.hexdigest()


def snap_install():
    out = {}
    if not os.path.isdir(INSTALL_CMS):
        return out
    for name in sorted(os.listdir(INSTALL_CMS)):
        p = os.path.join(INSTALL_CMS, name)
        if os.path.isfile(p):
            st = os.stat(p)
            out["install/" + name] = {
                "sha256": sha256(p),
                "size": st.st_size,
                "mtime": datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
            }
    return out


def snap_cache():
    out = {}
    if not os.path.isdir(CACHE):
        return out
    for dirpath, _dirs, files in os.walk(CACHE):
        for f in sorted(files):
            p = os.path.join(dirpath, f)
            rel = os.path.relpath(p, CACHE).replace("\\", "/")
            st = os.stat(p)
            out["cache/" + rel] = {
                "sha256": sha256(p),
                "size": st.st_size,
                "mtime": datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
            }
    return out


def snap_gamedb():
    out = {}
    for rel in [r"media\base\db\gamedb.slt",
                r"media\base\gametunablesettings\forzathon.xml",
                r"media\base\gametunablesettings\gametunablesettings.ini"]:
        p = os.path.join(GAME, rel)
        if os.path.exists(p):
            st = os.stat(p)
            out[rel.replace("\\", "/")] = {
                "sha256": sha256(p),
                "size": st.st_size,
                "mtime": datetime.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
            }
    return out


def build():
    s = {
        "taken_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "files": {},
    }
    s["files"].update(snap_install())
    s["files"].update(snap_cache())
    s["files"].update(snap_gamedb())
    return s


def main():
    os.makedirs(OUT, exist_ok=True)
    cmd = sys.argv[1] if len(sys.argv) > 1 else "snap"
    if cmd == "snap":
        label = sys.argv[2] if len(sys.argv) > 2 else "snap"
        s = build()
        path = os.path.join(OUT, label + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=1)
        print("gravado:", path, "-", len(s["files"]), "arquivos")
        for k in sorted(s["files"]):
            if k.startswith("install/"):
                print(f"   {k}  {s['files'][k]['size']:>10}  {s['files'][k]['sha256'][:16]}")
        return

    if cmd == "show":
        label = sys.argv[2]
        s = json.load(open(os.path.join(OUT, label + ".json"), encoding="utf-8"))
        print("taken_at:", s["taken_at"])
        for k in sorted(s["files"]):
            v = s["files"][k]
            print(f"   {v['sha256'][:16]} {v['size']:>10} {v['mtime']}  {k}")
        return

    if cmd == "diff":
        a = json.load(open(os.path.join(OUT, sys.argv[2] + ".json"), encoding="utf-8"))
        b = json.load(open(os.path.join(OUT, sys.argv[3] + ".json"), encoding="utf-8"))
        ka, kb = set(a["files"]), set(b["files"])
        changed = [k for k in sorted(ka & kb)
                   if a["files"][k]["sha256"] != b["files"][k]["sha256"]]
        for k in sorted(ka - kb):
            print("  REMOVIDO:", k)
        for k in sorted(kb - ka):
            print("  NOVO    :", k, b["files"][k]["size"])
        for k in changed:
            print(f"  MUDOU   : {k}  {a['files'][k]['size']}->{b['files'][k]['size']}"
                  f"  {a['files'][k]['sha256'][:12]}->{b['files'][k]['sha256'][:12]}"
                  f"  mtime {a['files'][k]['mtime']} -> {b['files'][k]['mtime']}")
        if not changed and ka == kb:
            print("  (nenhuma mudanca)")
        return

    print(__doc__)


if __name__ == "__main__":
    main()
