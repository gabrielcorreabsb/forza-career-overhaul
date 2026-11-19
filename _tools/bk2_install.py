#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bk2_install.py - instala/remove videos de introducao (.bk2) NOVOS no install.

Os videos de introducao sao arquivos soltos em
  <install>\\media\\base\\ui\\videos\\1080\\<nome>.bk2
  <install>\\media\\base\\ui\\videos\\2160\\<nome>.bk2
e a serie os nomeia em `IntroVideoPath` (so o nome do arquivo). Esta ferramenta
SO ADICIONA arquivos com nome proprio `FCO_<letras, digitos, _>` (gravados em
minusculas, como os vanilla) e remove so o que ela mesma gravou. Nunca
sobrescreve nem apaga um video vanilla, entao nao precisa de backup: o estado
(sha256 de cada arquivo gravado) fica em _work\\bk2_install\\state.json.

Fontes:
  --from-vanilla <nome.bk2>   copia um video vanilla (mesma resolucao) sob o novo
                              nome: serve para testar se o jogo acha um nome novo
                              sem precisar de codificador Bink 2.
  --from-file <1080.bk2> --from-file-2160 <2160.bk2>   video nosso, ja codificado
                              (RAD Video Tools); cabecalho Bink 2 conferido.

Travas: dry-run por padrao (--apply grava); jogo fechado; nome precisa de
prefixo FCO_ e nao pode existir fora do estado; cabecalho 'KB2' conferido.

Uso:
  python _tools\\bk2_install.py --add FCO_Test --from-vanilla PracticalPerformance.bk2
  python _tools\\bk2_install.py --add FCO_Test --from-vanilla PracticalPerformance.bk2 --apply
  python _tools\\bk2_install.py --list
  python _tools\\bk2_install.py --remove FCO_Test --apply

Ambiente: FM_INSTALL (raiz do install).
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cache_edit as ce  # noqa: E402

INSTALL = os.environ.get(
    "FM_INSTALL", r"F:\SteamLibrary\steamapps\common\Forza Motorsport")
WORK = os.environ.get("FM_BK2_WORK", os.path.join(ce.ROOT, "_work", "bk2_install"))
RES = ("1080", "2160")
NAME_RE = re.compile(r"^FCO_[A-Za-z0-9_]+$")
VANILLA_RE = re.compile(r"^[A-Za-z0-9_]+\.bk2$")


# Videos que nenhum dado do jogo cita (DISCOVERIES D111): os unicos
# que --replace aceita sobrescrever.
FREE_SLOTS = ("3d_carselect_vw", "softbox", "3d_carselect_focus",
              "3d_carselect_subaru")


class BkError(Exception):
    pass


def vdir(res):
    return os.path.join(INSTALL, "media", "base", "ui", "videos", res)


def state_path():
    return os.path.join(WORK, "state.json")


def load_state():
    try:
        with open(state_path(), encoding="utf-8") as fh:
            return json.load(fh)
    except OSError:
        return {}


def save_state(st):
    os.makedirs(WORK, exist_ok=True)
    with open(state_path(), "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=2, sort_keys=True)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_bink2(path):
    with open(path, "rb") as fh:
        head = fh.read(4)
    if head[:3] != b"KB2":
        raise BkError("%s nao e um Bink 2 (cabecalho %r)" % (path, head))


def put_file(src, dst):
    """Grava o conteudo de `src` em `dst` no lugar: o install nega apagar/renomear
    um arquivo existente (WinError 5), entao escreve por cima e trunca."""
    with open(src, "rb") as fh:
        data = fh.read()
    with open(dst, "r+b") as fh:
        fh.write(data)
        fh.truncate()


def target(res, name):
    return os.path.join(vdir(res), name.lower() + ".bk2")


def sources(args):
    out = {}
    if args.from_vanilla:
        if not VANILLA_RE.match(args.from_vanilla):
            raise BkError("nome vanilla invalido: %s" % args.from_vanilla)
        for res in RES:
            out[res] = os.path.join(vdir(res), args.from_vanilla.lower())
    else:
        if not (args.from_file and args.from_file_2160):
            raise BkError("--from-file (1080) e --from-file-2160 juntos, ou --from-vanilla")
        out = {"1080": args.from_file, "2160": args.from_file_2160}
    for res, p in out.items():
        if not os.path.isfile(p):
            raise BkError("fonte inexistente (%s): %s" % (res, p))
        check_bink2(p)
    return out


def do_add(args):
    if not NAME_RE.match(args.add):
        raise BkError("nome precisa ser FCO_<letras, digitos, _>: %s" % args.add)
    st = load_state()
    src = sources(args)
    plan = []
    for res in RES:
        dst = target(res, args.add)
        if os.path.exists(dst):
            mine = st.get(args.add, {}).get(res, {}).get("sha256")
            if mine is None or sha256_file(dst) != mine:
                raise BkError("ja existe e nao e nosso: %s" % dst)
        plan.append((res, src[res], dst, os.path.getsize(src[res])))
    for res, s, d, size in plan:
        print("%s  %s -> %s  (%d B)" % (res, s, d, size))
    if not args.apply:
        print("dry-run: nada gravado (use --apply)")
        return
    running = ce.forza_processes()
    if running:
        raise BkError("jogo aberto (%s); feche antes" % ", ".join(running))
    entry = {}
    for res, s, d, size in plan:
        tmp = d + ".tmp_bk2"
        shutil.copyfile(s, tmp)
        os.replace(tmp, d)
        if sha256_file(d) != sha256_file(s):
            raise BkError("copia divergente: %s" % d)
        entry[res] = {"path": d, "sha256": sha256_file(d), "size": size}
    st[args.add] = entry
    save_state(st)
    print("gravado: %s (%s)" % (args.add, ", ".join(RES)))


def do_remove(args):
    st = load_state()
    entry = st.get(args.remove)
    if not entry:
        raise BkError("%s nao esta no estado desta ferramenta" % args.remove)
    for res, info in entry.items():
        p = info["path"]
        ok = os.path.exists(p) and sha256_file(p) == info["sha256"]
        print("%s  remover %s  (%s)" % (res, p, "ok" if ok else "ausente ou alterado: nao mexe"))
    if not args.apply:
        print("dry-run: nada removido (use --apply)")
        return
    running = ce.forza_processes()
    if running:
        raise BkError("jogo aberto (%s); feche antes" % ", ".join(running))
    for res, info in entry.items():
        p = info["path"]
        if os.path.exists(p) and sha256_file(p) == info["sha256"]:
            os.remove(p)
    del st[args.remove]
    save_state(st)
    print("removido: %s" % args.remove)


def do_replace(args):
    slot = args.replace.lower()
    if slot.endswith(".bk2"):
        slot = slot[:-4]
    if slot not in FREE_SLOTS:
        raise BkError("--replace so aceita %s" % ", ".join(FREE_SLOTS))
    st = load_state()
    key = "replace:" + slot
    if key in st:
        raise BkError("%s ja foi trocado (use --restore %s antes)" % (slot, slot))
    src = sources(args)
    plan = []
    for res in RES:
        dst = os.path.join(vdir(res), slot + ".bk2")
        if not os.path.isfile(dst):
            raise BkError("alvo inexistente: %s" % dst)
        plan.append((res, src[res], dst))
        print("%s  %s -> %s  (%d B por cima de %d B)" % (
            res, src[res], dst, os.path.getsize(src[res]), os.path.getsize(dst)))
    if not args.apply:
        print("dry-run: nada gravado (use --apply)")
        return
    running = ce.forza_processes()
    if running:
        raise BkError("jogo aberto (%s); feche antes" % ", ".join(running))
    bdir = os.path.join(ce.BACKUP_ROOT, "bk2_%s_%s" % (slot, time.strftime("%Y%m%d_%H%M%S")))
    entry = {}
    for res, s_, d in plan:
        os.makedirs(os.path.join(bdir, res), exist_ok=True)
        bak = os.path.join(bdir, res, slot + ".bk2")
        shutil.copyfile(d, bak)
        orig = sha256_file(d)
        if sha256_file(bak) != orig:
            raise BkError("backup divergente: %s" % bak)
        put_file(s_, d)
        entry[res] = {"path": d, "backup": bak, "orig_sha256": orig,
                      "sha256": sha256_file(d), "size": os.path.getsize(d)}
    st[key] = entry
    save_state(st)
    print("trocado: %s (backup em %s)" % (slot, bdir))


def do_restore(args):
    slot = args.restore.lower()
    if slot.endswith(".bk2"):
        slot = slot[:-4]
    st = load_state()
    entry = st.get("replace:" + slot)
    if not entry:
        raise BkError("%s nao foi trocado por esta ferramenta" % slot)
    for res, info in entry.items():
        if not os.path.isfile(info["backup"]) or sha256_file(info["backup"]) != info["orig_sha256"]:
            raise BkError("backup ausente ou alterado: %s" % info["backup"])
        print("%s  %s <- %s" % (res, info["path"], info["backup"]))
    if not args.apply:
        print("dry-run: nada restaurado (use --apply)")
        return
    running = ce.forza_processes()
    if running:
        raise BkError("jogo aberto (%s); feche antes" % ", ".join(running))
    for res, info in entry.items():
        put_file(info["backup"], info["path"])
        if sha256_file(info["path"]) != info["orig_sha256"]:
            raise BkError("restauracao divergente: %s" % info["path"])
    del st["replace:" + slot]
    save_state(st)
    print("restaurado: %s" % slot)


def do_list(_args):
    st = load_state()
    if not st:
        print("nenhum video gravado por esta ferramenta")
    for name, entry in sorted(st.items()):
        if name.startswith("replace:"):
            for res, info in entry.items():
                print("%s %s trocado (backup %s)" % (name, res, info["backup"]))
            continue
        for res, info in entry.items():
            present = os.path.exists(info["path"])
            print("%s %s %s %d B %s" % (name, res, info["path"], info["size"],
                                        "presente" if present else "AUSENTE"))


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--add", metavar="FCO_NOME")
    g.add_argument("--remove", metavar="FCO_NOME")
    g.add_argument("--list", action="store_true")
    g.add_argument("--replace", metavar="SLOT")
    g.add_argument("--restore", metavar="SLOT")
    p.add_argument("--from-vanilla", metavar="NOME.bk2")
    p.add_argument("--from-file", metavar="1080.bk2")
    p.add_argument("--from-file-2160", metavar="2160.bk2")
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()
    try:
        if args.add:
            do_add(args)
        elif args.remove:
            do_remove(args)
        elif args.replace:
            do_replace(args)
        elif args.restore:
            do_restore(args)
        else:
            do_list(args)
    except BkError as exc:
        print("ERRO: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
