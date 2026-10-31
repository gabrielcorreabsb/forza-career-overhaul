"""Restaura o CmsCache a partir de um backup em _backup\\cache_<timestamp>."""
import os
import shutil
import sys
import time

ROOT = r"E:\Projetos\ForzaMods\carrer"
BACKUP_ROOT = os.path.join(ROOT, "_backup")
CACHE = os.path.join(os.environ["LOCALAPPDATA"], "Microsoft.ForzaMotorsport", "CmsCache")


def main():
    if len(sys.argv) > 1:
        src = sys.argv[1]
    else:
        cands = [d for d in os.listdir(BACKUP_ROOT) if d.startswith("cache_")]
        if not cands:
            raise SystemExit("nenhum backup em " + BACKUP_ROOT)
        cands.sort()
        src = os.path.join(BACKUP_ROOT, cands[-1])
    src = os.path.abspath(src)
    if not os.path.isdir(src):
        raise SystemExit("backup inexistente: " + src)

    safety = os.path.join(BACKUP_ROOT, "cache_before_rollback_" + time.strftime("%Y%m%d_%H%M%S"))
    shutil.copytree(CACHE, safety)
    print("copia de seguranca: %s" % safety)

    for name in os.listdir(CACHE):
        p = os.path.join(CACHE, name)
        if os.path.isdir(p):
            shutil.rmtree(p)
        else:
            os.remove(p)
    for name in os.listdir(src):
        s = os.path.join(src, name)
        d = os.path.join(CACHE, name)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
    print("CmsCache restaurado de: %s" % src)


if __name__ == "__main__":
    main()
