#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hash_manifest_edit.py - acrescenta registros no indice de arquivos do install.

`media\\<raiz>\\hash.manifest` (raiz = base ou pcfamily): cabecalho de 12 bytes +
registros de 12 bytes {hash64 do caminho, valor de 4 bytes} (D112). O hash e um
DJB2 modificado em duas passadas de 32 bits sobre o caminho relativo a
media\\<raiz>, minusculo, com '\\' (a 2a passada semeada pela 1a; lo = 1a).

So ACRESCENTA registros de arquivos que existem no disco e ainda nao estao no
indice, no fim da tabela; nunca muda nem remove um registro vanilla. A volta e
o backup inteiro do manifest.

Travas: dry-run por padrao (--apply grava); jogo fechado; o caminho tem de
existir no disco e nao pode estar no indice; o manifest tem de ser o vanilla
ou o ultimo escrito por esta ferramenta; backup em _backup\\hashmanifest_<ts>
na 1a escrita; grava no lugar (o install nega renomear sobre arquivo existente).

Uso:
  python _tools\\hash_manifest_edit.py --add ui\\videos\\1080\\fco_test.bk2 --value 4289 [--apply]
  python _tools\\hash_manifest_edit.py --check ui\\videos\\1080\\practicalperformance.bk2
  python _tools\\hash_manifest_edit.py --restore [--apply]
"""

import argparse
import hashlib
import json
import os
import shutil
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cache_edit as ce  # noqa: E402

INSTALL = os.environ.get(
    "FM_INSTALL", r"F:\SteamLibrary\steamapps\common\Forza Motorsport")
WORK = os.path.join(ce.ROOT, "_work", "hash_manifest_edit")
HEADER = 12
REC = 12


class HmError(Exception):
    pass


def _pass(s, h=5381):
    for ch in s:
        h = (h ^ ((ord(ch) + (h >> 2) + (h * 32)) & 0xFFFFFFFF)) & 0xFFFFFFFF
    return h


def path_hash(rel):
    """hash64 do caminho relativo (normalizado: minusculo, '\\')."""
    s = rel.replace("/", "\\").strip("\\").lower()
    lo = _pass(s)
    return (_pass(s, lo) << 32) | lo


def manifest_path(root):
    return os.path.join(INSTALL, "media", root, "hash.manifest")


def read_records(buf):
    if len(buf) < HEADER or (len(buf) - HEADER) % REC:
        raise HmError("tamanho inesperado do hash.manifest: %d" % len(buf))
    n = (len(buf) - HEADER) // REC
    return [struct.unpack_from("<QI", buf, HEADER + REC * i) for i in range(n)]


def sha(buf):
    return hashlib.sha256(buf).hexdigest()


def state_file():
    return os.path.join(WORK, "state.json")


def load_state():
    try:
        with open(state_file(), encoding="utf-8") as fh:
            return json.load(fh)
    except OSError:
        return {}


def save_state(st):
    os.makedirs(WORK, exist_ok=True)
    with open(state_file(), "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=2, sort_keys=True)


def write_in_place(path, data):
    with open(path, "r+b") as fh:
        fh.write(data)
        fh.truncate()


def require_closed():
    running = ce.forza_processes()
    if running:
        raise HmError("jogo aberto (%s); feche antes" % ", ".join(running))


def do_check(args):
    buf = open(manifest_path(args.root), "rb").read()
    recs = dict(read_records(buf))
    for rel in args.check:
        h = path_hash(rel)
        print("%s  hash %016x  %s" % (rel, h, ("valor %d" % recs[h]) if h in recs else "AUSENTE"))


def do_add(args):
    mpath = manifest_path(args.root)
    buf = open(mpath, "rb").read()
    st = load_state()
    ours = st.get(args.root)
    cur = sha(buf)
    if ours and cur != ours["last_sha256"]:
        raise HmError("o manifest mudou desde a ultima escrita desta ferramenta "
                      "(Steam?); rode --restore ou apague o estado depois de conferir")
    recs = read_records(buf)
    have = {h for h, _v in recs}
    new = []
    for rel, val in zip(args.add, args.value):
        disk = os.path.join(INSTALL, "media", args.root, rel.replace("/", "\\"))
        if not os.path.isfile(disk):
            raise HmError("arquivo nao existe no disco: %s" % disk)
        h = path_hash(rel)
        if h in have:
            raise HmError("ja esta no indice: %s" % rel)
        if not 0 <= val < 2 ** 32:
            raise HmError("valor fora de 32 bits: %d" % val)
        new.append((rel.lower().replace("/", "\\"), h, val))
        have.add(h)
    out = buf + b"".join(struct.pack("<QI", h, v) for _r, h, v in new)
    if read_records(out)[:len(recs)] != recs:
        raise HmError("conferencia falhou: registros vanilla mudaram")
    for rel, h, v in new:
        print("%s: + %s  hash %016x  valor %d" % (args.root, rel, h, v))
    print("registros %d -> %d; sha %s -> %s" % (len(recs), len(recs) + len(new), cur[:12], sha(out)[:12]))
    if not args.apply:
        print("dry-run: nada gravado (use --apply)")
        return
    require_closed()
    if not ours:
        bdir = os.path.join(ce.BACKUP_ROOT, "hashmanifest_%s_%s" % (args.root, time.strftime("%Y%m%d_%H%M%S")))
        os.makedirs(bdir, exist_ok=True)
        bak = os.path.join(bdir, "hash.manifest")
        shutil.copyfile(mpath, bak)
        if sha(open(bak, "rb").read()) != cur:
            raise HmError("backup divergente: %s" % bak)
        ours = {"backup": bak, "orig_sha256": cur, "added": []}
    write_in_place(mpath, out)
    if sha(open(mpath, "rb").read()) != sha(out):
        raise HmError("gravacao divergente: %s" % mpath)
    ours["added"] += [{"path": r, "value": v} for r, _h, v in new]
    ours["last_sha256"] = sha(out)
    st[args.root] = ours
    save_state(st)
    print("gravado (backup do original: %s)" % ours["backup"])


def do_remove(args):
    """Tira do indice so registros que ESTA ferramenta acrescentou (estado)."""
    mpath = manifest_path(args.root)
    buf = open(mpath, "rb").read()
    st = load_state()
    ours = st.get(args.root)
    if not ours:
        raise HmError("nada escrito por esta ferramenta em %s" % args.root)
    if sha(buf) != ours["last_sha256"]:
        raise HmError("o manifest mudou desde a ultima escrita desta ferramenta")
    mine = {path_hash(a["path"]): a["path"] for a in ours["added"]}
    drop = {}
    for rel in args.remove:
        h = path_hash(rel)
        if h not in mine:
            raise HmError("nao e um registro acrescentado por esta ferramenta: %s" % rel)
        drop[h] = mine[h]
    recs = read_records(buf)
    keep = [(h, v) for h, v in recs if h not in drop]
    if len(keep) != len(recs) - len(drop):
        raise HmError("conferencia falhou: contagem de registros")
    out = buf[:HEADER] + b"".join(struct.pack("<QI", h, v) for h, v in keep)
    for h, rel in drop.items():
        print("%s: - %s  hash %016x" % (args.root, rel, h))
    print("registros %d -> %d; sha %s -> %s" % (len(recs), len(keep), sha(buf)[:12], sha(out)[:12]))
    if not args.apply:
        print("dry-run: nada gravado (use --apply)")
        return
    require_closed()
    write_in_place(mpath, out)
    if sha(open(mpath, "rb").read()) != sha(out):
        raise HmError("gravacao divergente: %s" % mpath)
    ours["added"] = [a for a in ours["added"] if path_hash(a["path"]) not in drop]
    ours["last_sha256"] = sha(out)
    st[args.root] = ours
    save_state(st)
    print("removido")


def do_restore(args):
    st = load_state()
    ours = st.get(args.root)
    if not ours:
        raise HmError("nada escrito por esta ferramenta em %s" % args.root)
    bak = open(ours["backup"], "rb").read()
    if sha(bak) != ours["orig_sha256"]:
        raise HmError("backup alterado: %s" % ours["backup"])
    print("%s <- %s (%d registros nossos saem)" % (manifest_path(args.root), ours["backup"], len(ours["added"])))
    if not args.apply:
        print("dry-run: nada restaurado (use --apply)")
        return
    require_closed()
    write_in_place(manifest_path(args.root), bak)
    if sha(open(manifest_path(args.root), "rb").read()) != ours["orig_sha256"]:
        raise HmError("restauracao divergente")
    del st[args.root]
    save_state(st)
    print("restaurado")


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--add", nargs="+", metavar="CAMINHO")
    g.add_argument("--check", nargs="+", metavar="CAMINHO")
    g.add_argument("--restore", action="store_true")
    g.add_argument("--remove", nargs="+", metavar="CAMINHO")
    p.add_argument("--value", nargs="+", type=int)
    p.add_argument("--root", choices=("base", "pcfamily"), default="base")
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()
    try:
        if args.add:
            if not args.value or len(args.value) != len(args.add):
                raise HmError("--value precisa de um valor por caminho de --add")
            do_add(args)
        elif args.check:
            do_check(args)
        elif args.remove:
            do_remove(args)
        else:
            do_restore(args)
    except HmError as exc:
        print("ERRO: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
