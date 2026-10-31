#!/usr/bin/env python3
# -*- coding: ascii -*-
"""plan_lint.py - validacao de planos do cache_edit.py (zero tokens, stdlib).

Substitui o "patch-reviewer": roda sozinho ou importado pelo cache_edit.py,
que chama tudo isto ANTES de qualquer escrita (inclusive no --dry-run).

Checagem estatica (lint_plan, so o plano):
  * targets nao vazio; op em json/json_raw/bytes; logical presente;
  * group = GUID de 32 hex; snapshots = lista (e, com cache_dir, existente
    em <cache>/prod - nenhuma casando = erro, algumas = aviso);
  * bytes.file existe e nao e vazio; json.path nao vazio;
  * sem alvos duplicados (logical, snapshot, path/op);
  * Strategy S: logical nao pode ser cache-manifest.json nem prod\\<snap>,
    e o alvo nao pode carregar Path/Id/Size/Checksum/rename;
  * json_raw no BCS gera aviso (troca o arquivo inteiro);
  * multiplayer intocado: o campeonato 1 (Featured Multiplayer, + FTUE 22)
    vive em RacersCupMetaDataV4.json (ANALISE_CARRERA_FM8.md 9.1) - qualquer
    alvo nesse arquivo e erro.

Checagens profundas (chamadas pelo cache_edit.py sobre dados reais):
  * check_bcs_mp: o BCS so tem a carreira (ChampionshipId 500); o conjunto
    de ChampionshipId tem de sair identico (ninguem cria/remove campeonato
    nem injeta o 1 na carreira). Vale para op json e bytes (plaintext).
  * check_mp_untouched: nenhuma entrada alterada pode ser um arquivo de
    multiplayer (MP_LOGICALS).
  * check_strategy_s: manifesto planejado mantem Path/Id/Attributes e a
    quantidade de entradas; so muda Size/Checksum de arquivos realmente
    gravados, e esses batem com len/sha256(base64) dos bytes a gravar.

Uso:
  python _tools\\plan_lint.py --plan patches\\mc58\\plan.json
  python _tools\\plan_lint.py --plan plano.json --cache-dir _work\\cachetest

Codigos de saida: 0 ok, 1 erro, 3 ok com avisos.
"""

import argparse
import base64
import hashlib
import json
import os
import re
import sys
from collections import OrderedDict

OPS = ("json", "json_raw", "bytes")
BCS = "BuildersCupScheduleDataV4.json"
# campeonato 1 (Featured Multiplayer) e FTUE (22) - fora do escopo do mod
MP_LOGICALS = {"RacersCupMetaDataV4.json"}
GUID_RE = re.compile(r"^[0-9A-Fa-f]{32}$")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RETIRED_FILE = os.path.join(ROOT, "patches", "ids_retired.json")
# metadado do plano -> lista em ids_retired.json
META_ID_KEYS = {"series_id": "series", "event_id": "events",
                "cup_id": "cups", "ladder_id": "ladders"}
KNOWN_KEYS = {"logical", "group", "op", "path", "value", "content", "file",
              "snapshots"}
FORBIDDEN_KEYS = {"Path", "Id", "Size", "Checksum", "rename"}


def b64sha(data):
    return base64.b64encode(hashlib.sha256(data).digest()).decode("ascii")


def cache_snapshots(cache_dir):
    prod_dir = os.path.join(cache_dir, "prod")
    if not os.path.isdir(prod_dir):
        return None
    return sorted(n for n in os.listdir(prod_dir)
                  if os.path.isfile(os.path.join(prod_dir, n)))


# --------------------------------------------------------------------------- #
# estatico
# --------------------------------------------------------------------------- #
def lint_plan(plan_path, cache_dir=None):
    """Retorna (erros, avisos) - listas de strings."""
    errors, warnings = [], []
    try:
        with open(plan_path, "r", encoding="utf-8-sig") as fh:
            plan = json.load(fh, object_pairs_hook=OrderedDict)
    except (OSError, ValueError) as exc:
        return ["plano ilegivel: %s" % exc], warnings
    if not isinstance(plan, dict):
        return ["plano nao e objeto JSON"], warnings
    targets = plan.get("targets")
    if not isinstance(targets, list) or not targets:
        return ["'targets' deve ser lista nao vazia"], warnings

    plan_dir = os.path.dirname(os.path.abspath(plan_path))
    snaps_cache = cache_snapshots(cache_dir) if cache_dir else None
    seen = {}
    plan_snaps = set()
    matched_snaps = False

    for idx, t in enumerate(targets):
        tag = "targets[%d]" % idx
        if not isinstance(t, dict):
            errors.append("%s nao e objeto" % tag)
            continue
        logical = t.get("logical")
        op = t.get("op")
        if not logical or not isinstance(logical, str):
            errors.append("%s.logical ausente" % tag)
            continue
        tag = "%s (%s)" % (tag, logical)
        if logical in MP_LOGICALS:
            errors.append("%s: arquivo do multiplayer/campeonato 1 - fora do "
                          "escopo do mod" % tag)
        if op not in OPS:
            errors.append("%s.op=%r invalida" % (tag, op))

        # Strategy S: nada de renomear/recalcular manifesto via plano
        low = logical.replace("/", "\\").lower()
        if low == "cache-manifest.json" or low.startswith("prod\\"):
            errors.append("%s: manifesto/snapshot nao e alvo editavel "
                          "(Strategy S)" % tag)
        bad = sorted(FORBIDDEN_KEYS & set(t.keys()))
        if bad:
            errors.append("%s: chaves proibidas %s (Strategy S: Path/Id "
                          "opacos, Size/Checksum calculados)" % (tag, bad))
        extra = sorted(set(t.keys()) - KNOWN_KEYS - FORBIDDEN_KEYS)
        if extra:
            warnings.append("%s: chaves desconhecidas ignoradas %s"
                            % (tag, extra))

        group = t.get("group")
        if group is not None and (not isinstance(group, str)
                                  or not GUID_RE.match(group)):
            errors.append("%s.group=%r nao e GUID de 32 hex" % (tag, group))

        if op == "json":
            if not isinstance(t.get("path"), str) or not t["path"].strip():
                errors.append("%s.path ausente" % tag)
            if "value" not in t:
                errors.append("%s.value ausente" % tag)
        elif op == "json_raw":
            if not isinstance(t.get("content"), str):
                errors.append("%s.content deve ser string" % tag)
            if logical == BCS:
                warnings.append("%s: json_raw substitui o BCS inteiro" % tag)
        elif op == "bytes":
            f = t.get("file")
            if not f or not isinstance(f, str):
                errors.append("%s.file ausente" % tag)
            else:
                full = f if os.path.isabs(f) else os.path.join(plan_dir, f)
                if not os.path.isfile(full):
                    errors.append("%s.file nao existe: %s" % (tag, full))
                elif os.path.getsize(full) == 0:
                    errors.append("%s.file vazio: %s" % (tag, full))

        snaps = t.get("snapshots")
        if snaps is not None:
            if not isinstance(snaps, list) or not snaps or \
                    not all(isinstance(s, str) and s for s in snaps):
                errors.append("%s.snapshots deve ser lista de nomes" % tag)
                snaps = None
            else:
                plan_snaps.update(snaps)
                if snaps_cache is not None:
                    missing = [s for s in snaps if s not in snaps_cache]
                    if len(missing) < len(snaps):
                        matched_snaps = True
                    for s in missing:
                        warnings.append("%s: snapshot %s ausente no cache"
                                        % (tag, s))
        elif snaps_cache:
            matched_snaps = True

        key_tail = t.get("path") if op == "json" else op
        for s in (snaps or ["*"]):
            key = (logical, s, key_tail)
            if key in seen:
                errors.append("%s duplica targets[%d] (snapshot %s)"
                              % (tag, seen[key], s))
            else:
                seen[key] = idx

    errors.extend(check_retired_ids(plan))

    if snaps_cache is not None and not matched_snaps and not errors:
        errors.append("nenhum alvo casa com as snapshots do cache %s "
                      "(kit de outra snapshot? regenerar)" % snaps_cache)
    return errors, warnings


def check_retired_ids(plan, retired_file=RETIRED_FILE):
    """Erros se os metadados do plano (series_id, event_id...) usam id
    aposentado em patches/ids_retired.json."""
    if not os.path.isfile(retired_file):
        return []
    with open(retired_file, "r", encoding="utf-8-sig") as fh:
        retired = json.load(fh)
    errors = []
    for key, bucket in META_ID_KEYS.items():
        vals = plan.get(key)
        vals = vals if isinstance(vals, list) else [vals]
        for v in vals:
            if isinstance(v, int) and v in retired.get(bucket, []):
                errors.append("%s=%d esta aposentado (patches/ids_retired.json)"
                              " - nunca reutilizar" % (key, v))
    return errors


# --------------------------------------------------------------------------- #
# profundo
# --------------------------------------------------------------------------- #
def _championship_ids(bcs_plain):
    obj = json.loads(bcs_plain.decode("utf-8-sig"))
    return sorted(c.get("ChampionshipId") for c in obj.get("Championships", []))


def check_bcs_mp(plain_old, plain_new, label=""):
    """Erros se o conjunto de campeonatos do BCS mudou entre old e new."""
    try:
        old = _championship_ids(plain_old)
    except ValueError as exc:
        return ["%s: BCS original nao e JSON (%s)" % (label, exc)]
    try:
        new = _championship_ids(plain_new)
    except ValueError as exc:
        return ["%s: BCS novo nao e JSON (%s)" % (label, exc)]
    if old != new:
        return ["%s: campeonatos do BCS mudaram %s -> %s (so a carreira 500 "
                "pode ser editada)" % (label, old, new)]
    return []


def check_mp_untouched(changed_logicals):
    """Erros se alguma entrada alterada pertence ao multiplayer."""
    return ["arquivo do multiplayer/campeonato 1 seria alterado: %s" % n
            for n in sorted(set(changed_logicals) & MP_LOGICALS)]


def check_strategy_s(man_before, man_after, writes):
    """man_before/man_after: Files[] do cache-manifest (antes/planejado).
    writes: {Path do manifesto: bytes que serao gravados}."""
    errors = []
    before = man_before.get("Files", [])
    after = man_after.get("Files", [])
    if len(before) != len(after):
        return ["Strategy S: manifesto mudou de %d para %d entradas"
                % (len(before), len(after))]
    paths = {f["Path"] for f in before}
    for p in writes:
        if p not in paths:
            errors.append("Strategy S: escrita em %s fora do manifesto" % p)
    for b, a in zip(before, after):
        for k in ("Path", "Id", "Attributes"):
            if b.get(k) != a.get(k):
                errors.append("Strategy S: %s mudou em %s" % (k, b.get("Path")))
        data = writes.get(a.get("Path"))
        if data is None:
            if (b.get("Size"), b.get("Checksum")) != \
                    (a.get("Size"), a.get("Checksum")):
                errors.append("Size/Checksum mudou sem escrita em %s"
                              % a.get("Path"))
        else:
            if a.get("Size") != len(data):
                errors.append("Size de %s nao bate com os bytes a gravar"
                              % a.get("Path"))
            if a.get("Checksum") != b64sha(data):
                errors.append("Checksum de %s nao bate com os bytes a gravar"
                              % a.get("Path"))
    return errors


# --------------------------------------------------------------------------- #
def main(argv=None):
    p = argparse.ArgumentParser(prog="plan_lint.py",
                                description="Lint estatico de plan.json.")
    p.add_argument("--plan", required=True)
    p.add_argument("--cache-dir", default=None,
                   help="confere snapshots contra <cache>/prod (opcional)")
    args = p.parse_args(argv)
    errors, warnings = lint_plan(args.plan, args.cache_dir)
    for w in warnings:
        print("AVISO: " + w)
    for e in errors:
        print("ERRO:  " + e)
    print("%s: %d erros, %d avisos"
          % (args.plan, len(errors), len(warnings)))
    if errors:
        return 1
    return 3 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())
