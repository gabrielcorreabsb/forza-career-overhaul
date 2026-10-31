#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""install_edit.py - troca UMA entrada CMS dentro do zip do INSTALL.

Para conteudo cujo ContentGroup nao existe no CmsCache (ex.: grupo CFA7698C /
AIField_*.xml) o cache_edit.py ignora o alvo e o jogo le o zip do install.
Esta ferramenta reescreve esse zip e mantem a cadeia de checksums coerente:

  1. <install>/media/pcfamily/cms/<grupo>.zip   (entrada trocada; demais iguais)
  2. <install>/media/pcfamily/cms/faa126fd...   (manifest do install:
        entrada logica Size/Checksum + pacote <GRUPO> Size/Checksum)
  3. <cache>/prod/<snapshot>                    (entrada logica Size/Checksum)
  4. <cache>/cache-manifest.json                (prod\\<snap> Size/Checksum,
        re-criptografado com o proprio arquivo como template)

Travas: jogo fechado; payload decripta; estado-base conferido nos 3 manifests;
--dry-run recente antes de aplicar; backup completo em _backup\\install_<ts>.
Reverter: --restore _backup\\install_<ts>.

Uso:
  python _tools\\install_edit.py --dry-run --logical AIField_117160001_Gen.xml ^
      --payload patches\\mc58\\XML.AIField_117160001_Gen.enc
  python _tools\\install_edit.py --logical ... --payload ... --verify
  python _tools\\install_edit.py --restore _backup\\install_<ts>
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cache_edit as ce  # noqa: E402

DEFAULT_INSTALL = os.environ.get(
    "FM_INSTALL", r"F:\SteamLibrary\steamapps\common\Forza Motorsport")
INSTALL_MANIFEST = "faa126fd30becf2d0acdca1e9d3f751d"
WORK = os.path.join(ce.ROOT, "_work", "install_edit")
DRYRUN_DIR = os.path.join(WORK, "dryrun")
MAX_AGE_MIN = 30
LEDGER = os.path.join(ce.ROOT, "patches", "ledger.jsonl")


class IeError(Exception):
    pass


def cms_dir(install):
    return os.path.join(install, "media", "pcfamily", "cms")


def load_json(raw, label):
    fmt = ce.detect_json_format(raw, label)
    if not fmt["matched"]:
        raise IeError("%s: formato JSON nao reproduzido byte a byte; "
                      "recuso reescrever" % label)
    return fmt


def entry_of(obj, logical, label):
    hits = [f for f in obj.get("Files", []) if f["Path"] == logical]
    if len(hits) != 1:
        raise IeError("%s: %d entradas para %s (esperado 1)"
                      % (label, len(hits), logical))
    return hits[0]


def group_of(obj, logical, label):
    gs = [g["GroupName"] for g in obj.get("ContentGroups", [])
          if logical in g.get("FileNames", [])]
    if len(gs) != 1:
        raise IeError("%s: %d grupos contem %s" % (label, len(gs), logical))
    return gs[0]


def dryrun_key(payload, files):
    h = hashlib.sha256()
    h.update(payload)
    for p in files:
        h.update(ce.read_bytes(p))
    return h.hexdigest()


def plan_edit(args):
    """Calcula tudo sem escrever. Retorna dict com os bytes novos."""
    cache = os.path.abspath(args.cache_dir)
    install = os.path.abspath(args.install)
    cdir = cms_dir(install)
    man_path = os.path.join(cache, "cache-manifest.json")
    inst_man_path = os.path.join(cdir, INSTALL_MANIFEST)
    for p in (man_path, inst_man_path):
        if not os.path.isfile(p):
            raise IeError("nao encontrado: %s" % p)

    payload_new = ce.read_bytes(args.payload)
    oracles = ce.Oracles(args.oracle_cms, args.oracle_cache,
                         os.path.join(WORK, "o_%d" % os.getpid()))
    try:
        plain_new = oracles.cms_dec(payload_new)
    except Exception as exc:  # noqa: BLE001
        raise IeError("payload nao decripta: %s" % exc)
    if not plain_new.lstrip(b"\xef\xbb\xbf").lstrip().startswith(b"<"):
        raise IeError("payload nao parece XML")
    new_sz, new_ck = len(payload_new), ce.b64sha(payload_new)

    # manifest do install
    inst_raw = ce.read_bytes(inst_man_path)
    inst_fmt = load_json(inst_raw, INSTALL_MANIFEST)
    inst = inst_fmt["obj"]
    group = group_of(inst, args.logical, "install manifest")
    zip_path = os.path.join(cdir, group.lower() + ".zip")
    if not os.path.isfile(zip_path):
        raise IeError("zip do grupo nao encontrado: %s" % zip_path)
    zip_bytes = ce.read_bytes(zip_path)
    e_inst = entry_of(inst, args.logical, "install manifest")
    e_pkg = entry_of(inst, group, "install manifest")
    if ce.b64sha(zip_bytes) != e_pkg["Checksum"] or \
            len(zip_bytes) != e_pkg["Size"]:
        raise IeError("zip do install nao bate com o manifest (ja editado "
                      "ou corrompido?)")
    entries = ce.zip_entries(zip_bytes)
    if args.logical not in entries:
        raise IeError("%s nao existe em %s" % (args.logical, zip_path))
    old_payload = entries[args.logical]
    old_sz, old_ck = len(old_payload), ce.b64sha(old_payload)
    if (e_inst["Size"], e_inst["Checksum"]) != (old_sz, old_ck):
        raise IeError("entrada do install manifest != payload do zip")
    if old_ck == new_ck:
        raise IeError("payload novo identico ao atual; nada a fazer")

    # zip novo (outras entradas inalteradas)
    new_zip = ce.rebuild_blob(zip_bytes, {args.logical: payload_new})
    chk = ce.zip_entries(new_zip)
    if set(chk) != set(entries) or any(
            chk[n] != entries[n] for n in entries if n != args.logical) \
            or chk[args.logical] != payload_new:
        raise IeError("zip reconstruido diverge do original fora da entrada")
    e_inst["Size"], e_inst["Checksum"] = new_sz, new_ck
    e_pkg["Size"], e_pkg["Checksum"] = len(new_zip), ce.b64sha(new_zip)
    new_inst = ce.dump_json(inst, inst_fmt)

    writes = {zip_path: new_zip, inst_man_path: new_inst}

    # prod das snapshots + cache-manifest
    prod_dir = os.path.join(cache, "prod")
    man_plain = oracles.cache_dec(man_path)
    man_fmt = load_json(man_plain, "cache-manifest.json")
    man = man_fmt["obj"]
    prod_man = {f["Path"].replace("/", "\\"): f for f in man["Files"]
                if f.get("Attributes") == 0}
    touched = []
    for snap in sorted(n for n in os.listdir(prod_dir)
                       if os.path.isfile(os.path.join(prod_dir, n))):
        p = os.path.join(prod_dir, snap)
        raw = ce.read_bytes(p)
        fmt = load_json(raw, "prod/" + snap)
        e = entry_of(fmt["obj"], args.logical, "prod/" + snap)
        if group_of(fmt["obj"], args.logical, "prod/" + snap) != group:
            raise IeError("prod/%s: grupo diferente do install" % snap)
        if (e["Size"], e["Checksum"]) != (old_sz, old_ck):
            raise IeError("prod/%s: entrada != estado-base do install" % snap)
        e["Size"], e["Checksum"] = new_sz, new_ck
        new_raw = ce.dump_json(fmt["obj"], fmt)
        pm = prod_man.get("prod\\" + snap)
        if pm is None:
            raise IeError("cache-manifest sem entrada para prod\\%s" % snap)
        pm["Size"], pm["Checksum"] = len(new_raw), ce.b64sha(new_raw)
        writes[p] = new_raw
        touched.append(snap)
    new_man = ce.dump_json(man, man_fmt)
    return {"writes": writes, "man_path": man_path, "new_man_plain": new_man,
            "man_plain": man_plain, "oracles": oracles, "group": group,
            "zip_path": zip_path, "inst_man_path": inst_man_path,
            "old": (old_sz, old_ck), "new": (new_sz, new_ck),
            "new_zip": new_zip, "old_zip": zip_bytes, "snaps": touched,
            "plain_new": plain_new, "payload_new": payload_new,
            "cache": cache}


def report(r, logical):
    print("grupo:      %s  (%s)" % (r["group"], os.path.basename(r["zip_path"])))
    print("entrada:    %s  Size %d -> %d" % (logical, r["old"][0], r["new"][0]))
    print("            Checksum %s... -> %s..." % (r["old"][1][:12],
                                                   r["new"][1][:12]))
    print("zip:        %d -> %d B" % (len(r["old_zip"]), len(r["new_zip"])))
    print("snapshots:  %s" % ", ".join(r["snaps"]))
    print("arquivos a gravar:")
    for p in r["writes"]:
        print("  " + p)
    print("  %s (re-criptografado)" % r["man_path"])


def make_backup(r):
    dst = os.path.join(ce.BACKUP_ROOT, "install_" + time.strftime("%Y%m%d_%H%M%S"))
    os.makedirs(dst)
    index = []
    paths = list(r["writes"]) + [r["man_path"]]
    for i, p in enumerate(paths):
        shutil.copy2(p, os.path.join(dst, "%02d_%s" % (i, os.path.basename(p))))
        index.append({"file": "%02d_%s" % (i, os.path.basename(p)), "dest": p})
    with open(os.path.join(dst, "index.json"), "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=1)
    return dst


def put(path, data):
    """Grava `data` em `path`. O install nega DELETE ao usuario (so RX,W), o
    que quebra o os.replace do cache_edit.write_bytes; nesse caso regrava no
    proprio arquivo (o backup cobre uma falha no meio)."""
    try:
        ce.write_bytes(path, data)
    except PermissionError:
        try:
            os.remove(path + ".tmp_cachedit")
        except OSError:
            pass
        with open(path, "r+b") as fh:
            fh.write(data)
            fh.truncate()


def restore(src):
    src = os.path.abspath(src)
    with open(os.path.join(src, "index.json"), encoding="utf-8") as fh:
        index = json.load(fh)
    running = ce.forza_processes()
    if running:
        raise IeError("jogo aberto (%s)" % ", ".join(running))
    for it in index:
        put(it["dest"], ce.read_bytes(os.path.join(src, it["file"])))
        print("restaurado: " + it["dest"])


def verify(r, logical):
    errs = []
    z = ce.zip_entries(ce.read_bytes(r["zip_path"]))
    if z.get(logical) != r["payload_new"]:
        errs.append("zip: entrada difere do payload")
    inst = json.loads(ce.read_bytes(r["inst_man_path"]).decode("utf-8-sig"))
    ent = entry_of(inst, logical, "install")
    pkg = entry_of(inst, r["group"], "install")
    zb = ce.read_bytes(r["zip_path"])
    if (ent["Size"], ent["Checksum"]) != r["new"]:
        errs.append("install manifest: entrada incoerente")
    if (pkg["Size"], pkg["Checksum"]) != (len(zb), ce.b64sha(zb)):
        errs.append("install manifest: pacote incoerente")
    for snap in r["snaps"]:
        pj = json.loads(ce.read_bytes(os.path.join(
            r["cache"], "prod", snap)).decode("utf-8-sig"))
        e = entry_of(pj, logical, "prod/" + snap)
        if (e["Size"], e["Checksum"]) != r["new"]:
            errs.append("prod/%s: entrada incoerente" % snap)
    ok, n = ce.verify_cache(r["cache"], r["oracles"])
    if not ok:
        errs.append("verify_cache: %d erros" % n)
    return errs


def main(argv=None):
    ap = argparse.ArgumentParser(prog="install_edit.py")
    ap.add_argument("--logical")
    ap.add_argument("--payload", help="payload CMS ja cifrado (.enc)")
    ap.add_argument("--install", default=DEFAULT_INSTALL)
    ap.add_argument("--cache-dir", default=ce.DEFAULT_CACHE)
    ap.add_argument("--oracle-cms", default=ce.DEFAULT_CMS_ORACLE)
    ap.add_argument("--oracle-cache", default=ce.DEFAULT_CACHE_ORACLE)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--restore", metavar="BACKUP_DIR")
    args = ap.parse_args(argv)
    try:
        if args.restore:
            return restore(args.restore) or 0
        if not (args.logical and args.payload):
            ap.error("--logical e --payload sao obrigatorios")
        r = plan_edit(args)
        report(r, args.logical)
        key = dryrun_key(r["payload_new"], list(r["writes"]) + [r["man_path"]])
        marker = os.path.join(DRYRUN_DIR, key + ".json")
        if args.dry_run:
            os.makedirs(DRYRUN_DIR, exist_ok=True)
            with open(marker, "w") as fh:
                json.dump({"time": time.time()}, fh)
            print("\nDRY-RUN: nada escrito (marcador valido por %d min)"
                  % MAX_AGE_MIN)
            return 0
        running = ce.forza_processes()
        if running:
            raise IeError("jogo aberto (%s); feche antes" % ", ".join(running))
        if not os.path.isfile(marker):
            raise IeError("sem --dry-run para este estado; rode antes")
        with open(marker) as fh:
            age = (time.time() - json.load(fh)["time"]) / 60
        if age > MAX_AGE_MIN:
            raise IeError("--dry-run de %.0f min atras; rode de novo" % age)
        bk = make_backup(r)
        print("\nbackup: " + bk)
        for p, data in r["writes"].items():
            put(p, data)
        ce.write_bytes(r["man_path"],
                       r["oracles"].cache_enc(r["new_man_plain"], r["man_path"]))
        os.remove(marker)
        errs = verify(r, args.logical) if args.verify else []
        entry = {"when": time.strftime("%Y-%m-%d %H:%M:%S"),
                 "kit": "install:" + args.logical,
                 "payload": os.path.relpath(os.path.abspath(args.payload),
                                            ce.ROOT).replace("\\", "/"),
                 "verify": (not errs) if args.verify else None,
                 "backup": os.path.basename(bk)}
        if ce.is_live_cache(args.cache_dir):
            with open(LEDGER, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        if errs:
            for e in errs:
                print("FALHA: " + e)
            print("Reverter: python _tools\\install_edit.py --restore " + bk)
            return 3
        print("OK" + (" (verificado)" if args.verify else ""))
        return 0
    except (IeError, RuntimeError) as exc:
        print("ERRO: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
