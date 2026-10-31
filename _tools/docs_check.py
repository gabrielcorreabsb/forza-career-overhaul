#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""docs_check.py - keeps the docs from rotting (zero tokens, stdlib).

Checks every tracked .md (except generated docs/inventario/):
  1. referenced paths exist: `inline code` paths under `_tools/`, `docs/`,
     `patches/`, `specs/`, `_data/`, markdown links, bare `X.md` / `x.py` names
     (resolved next to the doc, in docs/, docs/pt-br/, _tools/, patches/*/...).
     Skipped: ``` fenced blocks, placeholders/ranges/prefixes, and docs marked
     `<!-- docs_check: historical -->` (research logs keep old names);
  2. bilingual pairs: docs/en/<f>.md <-> docs/pt-br/<f>.md both exist;
  3. docs/INDICE.md mentions every doc under docs/ (except inventario/,
     tasks/, archive/);
and warns (does not fail) when one side of a bilingual pair has a newer
commit than the other, or only one side is staged.

Usage: python _tools\\docs_check.py      (exit 0 ok, 1 errors)
       python _tools\\docs_check.py --allow-missing "patches/*" [...]
The option tolerates MISSING paths matching a glob (reported as notes, not
errors). Only publish.py passes it, for the public export where patches/ does
not exist; never use it in the lab.
"""

import argparse
import fnmatch
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOTS = ("_tools/", "docs/", "patches/", "specs/", "_data/", ".claude/",
         ".githooks/")
SKIP_PREFIX = ("_work/", "_out/", "_backup/", "_extract/", "_build/")
SKIP_DOCS = ("docs/inventario/", "docs/archive/")
BARE_DIRS = ("", "docs", "docs/pt-br", "docs/en", "_tools", "_tools/probes",
             "patches", "specs")
# placeholders, faixas (mc30..mc53) e prefixos (TASK_, task-)
PLACEHOLDER = re.compile(r"[*<>…{}]|NN|_x\b|\bx\.|\.\.|[_-]$")
# arquivos que nascem no uso (ledger: 1o apply no cache real)
ALLOW_MISSING = {"patches/ledger.jsonl"}
# logs de pesquisa citam scripts apagados de proposito
HISTORICAL = "<!-- docs_check: historical -->"
# globs de caminhos ausentes tolerados (--allow-missing; so o publish usa)
TOLERATED = []
NOTES = []

FENCE = re.compile(r"```.*?```", re.S)
TICK = re.compile(r"`([^`\s]+)`")
LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")
BARE = re.compile(r"^[\w.-]+\.(?:md|py)$")


def git(*args):
    return subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True,
                          text=True).stdout


def tracked_md():
    # rastreados + novos ainda nao commitados (respeitando o .gitignore)
    out = git("ls-files", "--cached", "--others", "--exclude-standard", "*.md")
    return sorted({p for p in out.splitlines()
                   if not p.startswith(SKIP_DOCS) and exists(p)})


def exists(rel):
    return os.path.exists(os.path.join(ROOT, rel.rstrip("/")))


def missing(errors, md, path, msg):
    """Registra caminho ausente, a menos que um --allow-missing o cubra."""
    if any(fnmatch.fnmatch(path, g) for g in TOLERATED):
        NOTES.append("%s: ausente tolerado / tolerated missing -> %s"
                     % (md, path))
    else:
        errors.append("%s: %s -> %s" % (md, msg, path))


def check_refs(md):
    errors = []
    base = os.path.dirname(md)
    with open(os.path.join(ROOT, md), encoding="utf-8") as fh:
        text = fh.read()
    # logs historicos e TASKs (citam arquivos que ainda serao criados)
    if HISTORICAL in text or md.startswith("docs/tasks/"):
        return []
    # blocos ``` sao exemplos/arvores: fora da checagem
    text = FENCE.sub("", text)
    cands = set()
    for m in TICK.finditer(text):
        cands.add(m.group(1).strip(".,;:"))
    for m in LINK.finditer(text):
        cands.add(("LINK", m.group(1)))
    for c in sorted(cands, key=str):
        if isinstance(c, tuple):
            target = c[1]
            if re.match(r"^[a-z]+:", target):
                continue
            rel = os.path.normpath(os.path.join(base, target)).replace("\\", "/")
            if not exists(rel):
                missing(errors, md, rel, "link quebrado / broken link")
            continue
        c = c.replace("\\", "/").lstrip("./") if not c.startswith("../") else c
        if PLACEHOLDER.search(c) or c.startswith(SKIP_PREFIX) \
                or c in ALLOW_MISSING:
            continue
        if c.startswith("../"):
            rel = os.path.normpath(os.path.join(base, c)).replace("\\", "/")
            if not exists(rel):
                missing(errors, md, rel,
                        "caminho inexistente / missing path")
            continue
        if c.startswith(ROOTS):
            path = c.split(":")[0]
            if not exists(path):
                missing(errors, md, path,
                        "caminho inexistente / missing path")
            continue
        if BARE.match(c):
            pdir = os.path.join(ROOT, "patches")
            dirs = (base,) + BARE_DIRS + tuple(
                "patches/" + k for k in
                (os.listdir(pdir) if os.path.isdir(pdir) else ())
                if os.path.isdir(os.path.join(pdir, k)))
            if not any(exists(os.path.join(d, c).replace("\\", "/"))
                       for d in dirs):
                errors.append("%s: arquivo citado nao existe / cited file "
                              "missing -> %s" % (md, c))
    return errors


def check_pairs(mds):
    errors, warnings = [], []
    en = {p[len("docs/en/"):] for p in mds if p.startswith("docs/en/")}
    pt = {p[len("docs/pt-br/"):] for p in mds if p.startswith("docs/pt-br/")}
    for f in sorted(en - pt):
        errors.append("par faltando / missing pair: docs/pt-br/%s" % f)
    for f in sorted(pt - en):
        errors.append("par faltando / missing pair: docs/en/%s" % f)
    staged = set(git("diff", "--cached", "--name-only").splitlines())
    for f in sorted(en & pt):
        a, b = "docs/en/" + f, "docs/pt-br/" + f
        if (a in staged) != (b in staged):
            warnings.append("so um lado do par esta staged / only one side "
                            "staged: %s" % (a if a in staged else b))
            continue
        ta = git("log", "-1", "--format=%ct", "--", a).strip()
        tb = git("log", "-1", "--format=%ct", "--", b).strip()
        if ta and tb and ta != tb:
            newer = a if int(ta) > int(tb) else b
            warnings.append("par com commits diferentes / pair out of sync "
                            "(mais novo / newer: %s)" % newer)
    return errors, warnings


def check_index(mds):
    idx_path = os.path.join(ROOT, "docs", "INDICE.md")
    if not os.path.isfile(idx_path):
        return ["docs/INDICE.md ausente / missing"]
    with open(idx_path, encoding="utf-8") as fh:
        idx = fh.read()
    errors = []
    for p in mds:
        if not p.startswith("docs/") or p == "docs/INDICE.md" \
                or p.startswith(("docs/tasks/", "docs/archive/")):
            continue
        if os.path.basename(p) not in idx:
            errors.append("docs/INDICE.md nao cita / does not list %s" % p)
    return errors


def main(argv=None):
    ap = argparse.ArgumentParser(description="docs consistency check")
    ap.add_argument("--allow-missing", action="append", default=[],
                    metavar="GLOB", help="tolerate missing paths matching "
                    "GLOB (publish.py only; never in the lab)")
    TOLERATED[:] = ap.parse_args(argv).allow_missing
    mds = tracked_md()
    errors = []
    for md in mds:
        errors += check_refs(md)
    e2, warnings = check_pairs(mds)
    errors += e2 + check_index(mds)
    for n in sorted(set(NOTES)):
        print("NOTA/NOTE:    " + n)
    for w in warnings:
        print("AVISO/WARNING: " + w)
    for e in errors:
        print("ERRO/ERROR:   " + e)
    print("docs_check: %d .md, %d erro(s), %d aviso(s)"
          % (len(mds), len(errors), len(warnings)))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
