#!/usr/bin/env python3
# -*- coding: ascii -*-
"""snapshot_cache.py - copia o CmsCache real para um diretorio de teste.

Somente LEITURA do CmsCache. Serve para testar planos/geradores sem tocar no
cache do jogo:
  python _tools\\snapshot_cache.py                  # -> _work\\cachetest
  python _tools\\snapshot_cache.py --dest _work\\outro
  python _tools\\cache_edit.py --dry-run --plan X --cache-dir _work\\cachetest

O destino precisa ficar dentro de _work\\ e e substituido inteiro.
Recusa se o jogo estiver aberto (copia poderia sair inconsistente).
"""

import argparse
import os
import shutil
import sys

import cache_edit


def main(argv=None):
    p = argparse.ArgumentParser(prog="snapshot_cache.py")
    p.add_argument("--dest", default=os.path.join(cache_edit.ROOT, "_work",
                                                   "cachetest"))
    args = p.parse_args(argv)

    src = cache_edit.DEFAULT_CACHE
    dest = os.path.abspath(args.dest)
    work = os.path.join(cache_edit.ROOT, "_work") + os.sep
    if not os.path.normcase(dest).startswith(os.path.normcase(work)):
        print("ERRO: destino deve ficar dentro de %s" % work, file=sys.stderr)
        return 2
    if not os.path.isfile(os.path.join(src, "cache-manifest.json")):
        print("ERRO: CmsCache nao encontrado em %s" % src, file=sys.stderr)
        return 1
    running = cache_edit.forza_processes()
    if running:
        print("ERRO: jogo aberto (%s); feche antes de copiar"
              % ", ".join(running), file=sys.stderr)
        return 1

    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    total = sum(os.path.getsize(os.path.join(dp, f))
                for dp, _, fs in os.walk(dest) for f in fs)
    print("copia: %s -> %s (%d B)" % (src, dest, total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
