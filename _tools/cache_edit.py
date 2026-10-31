#!/usr/bin/env python3
# -*- coding: ascii -*-
"""cache_edit.py - editor generico do CmsCache do Forza Motorsport (FM8).

Generaliza `cache_patch_final.py`: em vez de patches hardcoded, aplica um
"plano" JSON externo a qualquer arquivo logico do cache.

Modelo do cache (verificado):
  * <cache>/cache-manifest.json
        container criptografado (asset container: header 32 B = IV+MAC,
        slots de 528 B = 512 dados + 16 MAC). Files[] com Attributes==3 sao
        os blobs (Path = "<bucket>\\<sha256hex>", Size/Checksum do ARQUIVO do
        blob) e Attributes==0 sao as snapshots (Path = "prod\\<snap>",
        Size/Checksum do ARQUIVO da snapshot). O Id (int64) e opaco.
  * <cache>/prod/<snapshot>
        JSON plaintext: {"Version":1,"CmsInstance":{...},"Files":[{"Id","Path",
        "Size","Checksum"}],"ContentGroups":[{"GroupName","FileNames"}]}
        Size/Checksum descrevem o PAYLOAD CIFRADO da entrada (nao o plaintext).
  * <cache>/<bucket>/<SHA256HEX>
        blob = ZIP (todas as entradas method 8/deflate) cujas entradas sao o
        payload cifrado de cada arquivo logico (AES-128-CBC + gzip).

Como o mapeamento grupo->blob e feito: nao se usa o nome do arquivo. Para cada
snapshot, cada blob candidato (que contenha todos os FileNames do grupo) recebe
um score = quantas entradas do ZIP tem sha256 == Checksum de alguma entrada do
prod<snapshot>. Vence o maior score; empates (blobs indistinguiveis pelos
checksums daquela snapshot) sao TODOS editados, para que qualquer um que o jogo
carregue ja esteja correto.

Operacoes do plano ("targets"[i]):
  op="json"      arquivo logico e JSON UTF-8; "path" = caminho com notacao de
                 array (ex.: "Championships[0].ChampionshipCupData[1].X")
                 e "value" = novo valor (substitui no local apontado).
                 Re-serializa com json.dumps(obj, ensure_ascii=False,
                 separators=(",", ":")) preservando a ordem das chaves
                 (object_pairs_hook=OrderedDict; nunca sort_keys).
  op="json_raw"  substitui o arquivo logico inteiro pelo campo "content"
                 (string, codificada em UTF-8).
  op="bytes"     substitui o PAYLOAD CIFRADO pelos bytes do arquivo "file"
                 (caminho absoluto, ou relativo ao diretorio do plano).
                 Util para patches binarios de tamanho fixo (.str UTF-16LE).

Campos opcionais por target:
  "group"      GUID do ContentGroup (omitido: procura o grupo que contem o
               arquivo logico). Se o grupo nao existir no cache (conteudo base
               do install), o alvo e ignorado com aviso.
  "snapshots"  lista de snapshots em que o alvo se aplica (default: todas).

Garantias:
  * backup do CmsCache inteiro em _backup/cache_<YYYYMMDD_HHMMSS> (default ON).
  * --dry-run nao escreve nada no cache nem faz backup.
  * apenas entradas alteradas sao re-criptografadas (oraculo CMS, usando o
    payload cifrado ORIGINAL da MESMA entrada como template) e validadas por
    round-trip; as demais entradas do blob sao copiadas byte-a-byte.
  * o ZIP e reconstruido preservando ordem, date_time, compress_type,
    external_attr, create_system, internal_attr, extra e comment.
  * o blob e gravado no MESMO caminho (mesmo bucket, mesmo nome de arquivo):
    Path e Id do cache-manifest.json sao mantidos, so Size/Checksum mudam.
  * prod/<snapshot> e regravado preservando a formatacao original detectada
    (indent/ensure_ascii/quebra de linha final sao descobertos comparando o raw).
  * cache-manifest.json e regravado por ultimo, re-criptografado com o arquivo
    criptografado original como template.
  * idempotente: se o plaintext ja e o desejado, nada e reescrito.

Travas (valem para qualquer agente/modelo; sem flag de bypass):
  * plan_lint.lint_plan roda antes de tudo (inclusive no --dry-run); as
    checagens profundas (multiplayer/RacersCupMetaDataV4 intocado, BCS so
    com a carreira 500, Strategy S e
    Size/Checksum do manifesto planejado) rodam antes da fase de escrita.
  * escrita no CmsCache real recusa se houver processo "forza*" ativo.
  * escrita exige marcador de --dry-run sem erros, com no maximo
    --dry-run-max-age minutos, para o MESMO plano + payloads .enc + estado
    do cache-manifest.json (_work\\cache_edit\\dryrun\\<chave>.json).
    O marcador e consumido por um apply bem-sucedido.

Uso:
  python _tools\\cache_edit.py --plan plano.json --dry-run
  python _tools\\cache_edit.py --plan plano.json --verify
  python _tools\\cache_edit.py --plan plano.json --cache-dir _work\\cachetest --dry-run

Codigos de saida: 0 ok, 1 erro, 2 uso, 3 ok com avisos (ex.: alvo inexistente).
"""

import argparse
import base64
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from collections import OrderedDict

import plan_lint

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CACHE = os.path.join(
    os.environ.get("LOCALAPPDATA", ""), r"Microsoft.ForzaMotorsport\CmsCache"
)
DEFAULT_CMS_ORACLE = os.path.join(
    ROOT, r"_tools\cmsoracle\bin\Release\net10.0\cmsoracle.exe"
)
DEFAULT_CACHE_ORACLE = os.path.join(
    ROOT, r"_tools\cacheoracle\bin\Release\net10.0\cacheoracle.exe"
)
WORK_ROOT = os.path.join(ROOT, "_work", "cache_edit")
BACKUP_ROOT = os.path.join(ROOT, "_backup")
DRYRUN_DIR = os.path.join(WORK_ROOT, "dryrun")
LEDGER = os.path.join(ROOT, "patches", "ledger.jsonl")
DRYRUN_MAX_AGE_MIN = 30
DRYRUN_MAX_AGE_CAP = 240

BOM = b"\xef\xbb\xbf"
OPS = ("json", "json_raw", "bytes")

# cache de linhas de relatorio; preenchido em runtime
LOG = None


def log(msg=""):
    print(msg, flush=True)
    if LOG is not None:
        LOG.append(msg)


# --------------------------------------------------------------------------- #
# utilitarios
# --------------------------------------------------------------------------- #
def b64sha(data):
    return base64.b64encode(hashlib.sha256(data).digest()).decode("ascii")


def read_bytes(path):
    with open(path, "rb") as fh:
        return fh.read()


def write_bytes(path, data):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp_cachedit"
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, path)


def run(exe, args):
    if not os.path.exists(exe):
        raise RuntimeError("oraculo nao encontrado: %s" % exe)
    proc = subprocess.run([exe] + args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "%s %s falhou rc=%s\n%s\n%s"
            % (os.path.basename(exe), " ".join(args), proc.returncode,
               proc.stdout.strip(), proc.stderr.strip())
        )
    return proc.stdout.strip()


class Oracles:
    """Wrapper dos oraculos .NET (trabalham com arquivos, nao com bytes)."""

    def __init__(self, cms_exe, cache_exe, workdir):
        self.cms = cms_exe
        self.cache = cache_exe
        self.workdir = workdir
        os.makedirs(workdir, exist_ok=True)
        self._seq = 0

    def _tmp(self, suffix):
        self._seq += 1
        return os.path.join(self.workdir, "t%04d%s" % (self._seq, suffix))

    def cms_dec(self, enc_bytes):
        src = self._tmp(".enc")
        dst = self._tmp(".plain")
        write_bytes(src, enc_bytes)
        run(self.cms, ["dec", src, dst])
        return read_bytes(dst)

    def cms_enc(self, plain_bytes, template_bytes):
        src = self._tmp(".plain")
        tmpl = self._tmp(".tmpl")
        dst = self._tmp(".enc")
        write_bytes(src, plain_bytes)
        write_bytes(tmpl, template_bytes)
        run(self.cms, ["enc", src, tmpl, dst])
        return read_bytes(dst)

    def cache_dec(self, enc_path):
        dst = self._tmp(".plain")
        run(self.cache, ["dec", enc_path, dst])
        return read_bytes(dst)

    def cache_enc(self, plain_bytes, template_path):
        src = self._tmp(".plain")
        dst = self._tmp(".enc")
        write_bytes(src, plain_bytes)
        run(self.cache, ["enc", src, template_path, dst])
        return read_bytes(dst)


# --------------------------------------------------------------------------- #
# deteccao de formato JSON (para regravar preservando o original)
# --------------------------------------------------------------------------- #
def detect_json_format(raw, label=""):
    """Descobre a serializacao que reproduz `raw` byte-a-byte.

    Retorna dict(indent, ensure_ascii, trailing, bom) + objeto parseado.
    Se nenhuma combinacao reproduzir o raw, cai para o formato canonico
    minificado (ensure_ascii=False, separators=(",",":")) e avisa.
    """
    bom = raw.startswith(BOM)
    text = raw[len(BOM):].decode("utf-8") if bom else raw.decode("utf-8")
    obj = json.loads(text, object_pairs_hook=OrderedDict)

    candidates = []
    for indent in (None, 2, 4, "\t"):
        for ensure_ascii in (False, True):
            sep = (",", ":") if indent is None else (",", ": ")
            candidates.append((indent, ensure_ascii, sep))
    for indent, ensure_ascii, sep in candidates:
        body = json.dumps(
            obj, ensure_ascii=ensure_ascii, indent=indent, separators=sep
        ).encode("utf-8")
        for trailing in ("", "\n", "\r\n"):
            cand = (BOM if bom else b"") + body + trailing.encode("utf-8")
            if cand == raw:
                return {
                    "indent": indent,
                    "ensure_ascii": ensure_ascii,
                    "trailing": trailing,
                    "bom": bom,
                    "obj": obj,
                    "matched": True,
                }

    if label:
        log("  AVISO: formato JSON de %s nao reproduzido exatamente; "
            "usando minificado canonico." % label)
    return {
        "indent": None,
        "ensure_ascii": False,
        "trailing": "",
        "bom": bom,
        "obj": obj,
        "matched": False,
    }


def dump_json(obj, fmt):
    sep = (",", ":") if fmt["indent"] is None else (",", ": ")
    body = json.dumps(
        obj,
        ensure_ascii=fmt["ensure_ascii"],
        indent=fmt["indent"],
        separators=sep,
    ).encode("utf-8")
    return (BOM if fmt["bom"] else b"") + body + fmt["trailing"].encode("utf-8")


# --------------------------------------------------------------------------- #
# caminho com notacao de array: "a.b[2].c", a["chave.com.pontos"]
# --------------------------------------------------------------------------- #
def parse_path(path):
    if not path or not path.strip():
        raise ValueError("path vazio")
    toks = []
    i, n = 0, len(path)
    while i < n:
        ch = path[i]
        if ch == ".":
            i += 1
            continue
        if ch == "[":
            j = path.find("]", i)
            if j < 0:
                raise ValueError("path %r: '[' sem ']'" % path)
            inner = path[i + 1:j].strip()
            if len(inner) >= 2 and inner[0] == inner[-1] and inner[0] in "\"'":
                body = inner[1:-1]
                toks.append(json.loads(inner) if inner[0] == '"' else body)
            else:
                if not re.match(r"^-?\d+$", inner):
                    raise ValueError("path %r: indice invalido %r" % (path, inner))
                toks.append(int(inner))
            i = j + 1
            continue
        j = i
        while j < n and path[j] not in ".[":
            j += 1
        key = path[i:j].strip()
        if not key:
            raise ValueError("path %r: segmento vazio em %d" % (path, i))
        toks.append(key)
        i = j
    if not toks:
        raise ValueError("path %r nao produziu segmentos" % path)
    return toks


def get_value(obj, toks, path):
    cur = obj
    for depth, tok in enumerate(toks):
        try:
            if isinstance(tok, int):
                if not isinstance(cur, list):
                    raise TypeError("esperava lista em %r" % (toks[:depth],))
                cur = cur[tok]
            else:
                if not isinstance(cur, dict):
                    raise TypeError("esperava objeto em %r" % (toks[:depth],))
                cur = cur[tok]
        except (KeyError, IndexError, TypeError) as exc:
            raise KeyError(
                "path %r: segmento %r nao encontrado (%s)"
                % (path, tok, type(exc).__name__)
            )
    return cur


def set_value(obj, toks, value, path):
    parent = get_value(obj, toks[:-1], path) if len(toks) > 1 else obj
    last = toks[-1]
    if isinstance(last, int):
        if not isinstance(parent, list):
            raise TypeError("path %r: pai nao e lista" % path)
        if last >= len(parent) or last < -len(parent):
            raise IndexError("path %r: indice %d fora da faixa" % (path, last))
        parent[last] = value
    else:
        if not isinstance(parent, dict):
            raise TypeError("path %r: pai nao e objeto" % path)
        if last not in parent:
            raise KeyError("path %r: chave %r nao existe (sem criacao de chave)"
                           % (path, last))
        parent[last] = value


# --------------------------------------------------------------------------- #
# ZIP
# --------------------------------------------------------------------------- #
def rebuild_blob(orig_bytes, replacements):
    """Reconstroi o blob preservando ordem e metadados de cada entrada."""
    zin = zipfile.ZipFile(io.BytesIO(orig_bytes))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as zout:
        for zi in zin.infolist():
            data = replacements.get(zi.filename)
            if data is None:
                data = zin.read(zi.filename)
            ni = zipfile.ZipInfo(zi.filename, date_time=zi.date_time)
            ni.compress_type = zi.compress_type
            ni.external_attr = zi.external_attr
            ni.create_system = zi.create_system
            ni.internal_attr = zi.internal_attr
            ni.extra = zi.extra
            ni.comment = zi.comment
            zout.writestr(ni, data)
    return out.getvalue()


def zip_entries(blob_bytes):
    with zipfile.ZipFile(io.BytesIO(blob_bytes)) as zf:
        return {zi.filename: zf.read(zi.filename) for zi in zf.infolist()}


# --------------------------------------------------------------------------- #
# plano
# --------------------------------------------------------------------------- #
def load_plan(path):
    with open(path, "r", encoding="utf-8-sig") as fh:
        plan = json.load(fh, object_pairs_hook=OrderedDict)
    targets = plan.get("targets")
    if not isinstance(targets, list) or not targets:
        raise SystemExit("plano invalido: 'targets' deve ser uma lista nao vazia")
    plan_dir = os.path.dirname(os.path.abspath(path))
    out = []
    for idx, t in enumerate(targets):
        if not isinstance(t, dict):
            raise SystemExit("plano invalido: targets[%d] nao e objeto" % idx)
        logical = t.get("logical")
        op = t.get("op")
        if not logical or not isinstance(logical, str):
            raise SystemExit("plano invalido: targets[%d].logical ausente" % idx)
        if op not in OPS:
            raise SystemExit(
                "plano invalido: targets[%d].op=%r (suportadas: %s)"
                % (idx, op, ", ".join(OPS))
            )
        item = OrderedDict(t)
        item["_idx"] = idx
        if op == "json":
            if not t.get("path"):
                raise SystemExit("plano invalido: targets[%d].path ausente" % idx)
            if "value" not in t:
                raise SystemExit("plano invalido: targets[%d].value ausente" % idx)
            item["_toks"] = parse_path(t["path"])
        elif op == "json_raw":
            if not isinstance(t.get("content"), str):
                raise SystemExit(
                    "plano invalido: targets[%d].content deve ser string" % idx)
        else:  # bytes
            f = t.get("file")
            if not f:
                raise SystemExit("plano invalido: targets[%d].file ausente" % idx)
            if not os.path.isabs(f):
                f = os.path.join(plan_dir, f)
            if not os.path.exists(f):
                raise SystemExit(
                    "plano invalido: targets[%d].file nao existe: %s" % (idx, f))
            item["_file"] = os.path.abspath(f)
        snaps = t.get("snapshots")
        if snaps is not None and not isinstance(snaps, list):
            raise SystemExit(
                "plano invalido: targets[%d].snapshots deve ser lista" % idx)
        item["_snapshots"] = snaps
        out.append(item)
    return out


# --------------------------------------------------------------------------- #
# mapeamento grupo -> blob
# --------------------------------------------------------------------------- #
def index_blobs(cache_dir, blob_entries):
    idx = OrderedDict()
    for be in blob_entries:
        path = os.path.join(cache_dir, be["Path"])
        data = read_bytes(path)
        entries = zip_entries(data)
        idx[path] = {
            "entry": be,
            "bytes": data,
            "names": list(entries.keys()),
            "sha": {n: b64sha(v) for n, v in entries.items()},
        }
    return idx


def map_groups(prod, blob_index):
    """Retorna {group_guid: (score, [blob paths ordenados])}."""
    prod_files = {f["Path"]: f for f in prod.get("Files", [])}
    all_checksums = {f["Checksum"] for f in prod.get("Files", [])}
    result = OrderedDict()
    for group in prod.get("ContentGroups", []):
        gid = group["GroupName"]
        names = list(group.get("FileNames", []))
        nameset = set(names)
        best = -1
        winners = []
        for path, meta in blob_index.items():
            if not nameset <= set(meta["names"]):
                continue
            score = sum(1 for n in names if meta["sha"].get(n) in all_checksums)
            if score > best:
                best, winners = score, [path]
            elif score == best and score > 0:
                winners.append(path)
        if best > 0:
            result[gid] = (best, sorted(winners))
    return result


def group_for_logical(prod, logical):
    for group in prod.get("ContentGroups", []):
        if logical in group.get("FileNames", []):
            return group["GroupName"]
    return None


# --------------------------------------------------------------------------- #
# aplicacao das operacoes
# --------------------------------------------------------------------------- #
def apply_plain_op(target, plain, label):
    """Aplica op json/json_raw ao plaintext; retorna (novo_plain, mudou, info)."""
    op = target["op"]
    if op == "json_raw":
        new = target["content"].encode("utf-8")
        return new, new != plain, {"op": op}

    # op == "json"
    bom = plain.startswith(BOM)
    text = plain[len(BOM):].decode("utf-8") if bom else plain.decode("utf-8")
    try:
        obj = json.loads(text, object_pairs_hook=OrderedDict)
    except ValueError as exc:
        raise RuntimeError("%s: JSON invalido (%s)" % (label, exc))
    toks = target["_toks"]
    current = get_value(obj, toks, target["path"])
    value = target["value"]
    if current == value:
        return plain, False, {"op": op, "unchanged": True, "before": current}
    set_value(obj, toks, value, target["path"])
    body = json.dumps(
        obj, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    new = (BOM if bom else b"") + body
    # preserva quebra de linha final, se o original tinha
    if plain.endswith(b"\r\n"):
        new += b"\r\n"
    elif plain.endswith(b"\n"):
        new += b"\n"
    return new, True, {"op": op, "before": current, "after": value}


# --------------------------------------------------------------------------- #
# backup / verify / report
# --------------------------------------------------------------------------- #
def make_backup(cache_dir, enabled):
    if not enabled:
        log("backup: desativado (--no-backup)")
        return None
    stamp = time.strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_ROOT, "cache_" + stamp)
    suffix = 1
    while os.path.exists(dst):
        dst = os.path.join(BACKUP_ROOT, "cache_%s_%d" % (stamp, suffix))
        suffix += 1
    os.makedirs(BACKUP_ROOT, exist_ok=True)
    shutil.copytree(cache_dir, dst)
    total = sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, _, fs in os.walk(dst)
        for f in fs
    )
    log("backup do CmsCache: %s (%d B)" % (dst, total))
    return dst


def verify_cache(cache_dir, oracles, expected_plain=None, log_prefix="  "):
    """Re-decripta tudo e confere Size/Checksum. Retorna (ok, n_erros)."""
    expected_plain = expected_plain or {}
    errors = []

    def fail(msg):
        errors.append(msg)
        log(log_prefix + "FALHA: " + msg)

    man_path = os.path.join(cache_dir, "cache-manifest.json")
    try:
        man_plain = oracles.cache_dec(man_path)
        man = json.loads(man_plain.decode("utf-8-sig"),
                         object_pairs_hook=OrderedDict)
    except Exception as exc:  # noqa: BLE001
        fail("cache-manifest.json nao decripta: %s" % exc)
        return False, 1

    blob_entries = {}
    prod_entries = {}
    for f in man.get("Files", []):
        p = f["Path"]
        full = os.path.join(cache_dir, p)
        if not os.path.exists(full):
            fail("arquivo do manifest ausente: %s" % p)
            continue
        data = read_bytes(full)
        if len(data) != f["Size"]:
            fail("tamanho divergente em %s (%d != %d)"
                 % (p, len(data), f["Size"]))
        if b64sha(data) != f["Checksum"]:
            fail("checksum divergente em %s" % p)
        if f.get("Attributes") == 3:
            blob_entries[p] = f
        elif f.get("Attributes") == 0:
            prod_entries[p] = f
    log(log_prefix + "cache-manifest: %d arquivos verificados (%d blobs, "
        "%d snapshots)" % (len(man.get("Files", [])), len(blob_entries),
                           len(prod_entries)))

    # indice de payloads de todos os blobs (nome -> sha b64)
    name_sha = {}
    blobs = OrderedDict()
    for p in blob_entries:
        full = os.path.join(cache_dir, p)
        try:
            data = read_bytes(full)
            entries = zip_entries(data)
        except Exception as exc:  # noqa: BLE001
            fail("blob ilegivel %s: %s" % (p, exc))
            continue
        blobs[os.path.abspath(full)] = entries
        for n, payload in entries.items():
            name_sha.setdefault(n, set()).add(b64sha(payload))

    # round-trip dos plaintexts alterados
    for (blob_path, name), plain in expected_plain.items():
        payload = blobs.get(os.path.abspath(blob_path), {}).get(name)
        if payload is None:
            fail("entrada %s nao encontrada no blob %s apos escrita"
                 % (name, os.path.basename(blob_path)))
            continue
        try:
            back = oracles.cms_dec(payload)
        except Exception as exc:  # noqa: BLE001
            fail("payload de %s nao decripta: %s" % (name, exc))
            continue
        if back != plain:
            fail("round-trip divergente em %s" % name)

    # prod<snapshot>: cada entrada logica deve bater com algum payload do cache
    prod_dir = os.path.join(cache_dir, "prod")
    snaps = sorted(
        n for n in os.listdir(prod_dir)
        if os.path.isfile(os.path.join(prod_dir, n))
    )
    for snap in snaps:
        raw = read_bytes(os.path.join(prod_dir, snap))
        try:
            prod = json.loads(raw.decode("utf-8-sig"),
                              object_pairs_hook=OrderedDict)
        except ValueError as exc:
            fail("prod/%s JSON invalido: %s" % (snap, exc))
            continue
        missing = 0
        bad = 0
        for f in prod.get("Files", []):
            shas = name_sha.get(f["Path"])
            if not shas:
                missing += 1  # conteudo base (vivendo no install)
                continue
            if f["Checksum"] not in shas:
                bad += 1
                if bad <= 5:
                    fail("prod/%s: Checksum de %s nao casa com nenhum payload"
                         % (snap, f["Path"]))
        log(log_prefix + "prod/%s: %d arquivos, %d grupos, %d fora do cache "
            "(base), %d divergentes"
            % (snap, len(prod.get("Files", [])),
               len(prod.get("ContentGroups", [])), missing, bad))
        if bad:
            errors.append("prod/%s com %d divergencias" % (snap, bad))

    ok = not errors
    log(log_prefix + "verificacao: " + ("OK" if ok else "FALHOU (%d erros)"
                                        % len(errors)))
    return ok, len(errors)


# --------------------------------------------------------------------------- #
# travas: processo do jogo e marcador de dry-run
# --------------------------------------------------------------------------- #
def is_live_cache(cache_dir):
    return os.path.normcase(os.path.abspath(cache_dir)) == \
        os.path.normcase(os.path.abspath(DEFAULT_CACHE))


def forza_processes(tasklist_out=None):
    """Nomes de imagem 'forza*' em execucao. Falha fechado se tasklist falhar."""
    if tasklist_out is None:
        proc = subprocess.run(["tasklist", "/FO", "CSV", "/NH"],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError("tasklist falhou (rc=%s); recusando escrever"
                               % proc.returncode)
        tasklist_out = proc.stdout
    found = []
    for line in tasklist_out.splitlines():
        name = line.split(",", 1)[0].strip().strip('"')
        if re.match(r"^forza", name, re.IGNORECASE):
            found.append(name)
    return sorted(set(found))


def dryrun_key(plan_path, targets, cache_dir, man_path):
    """sha256 de plano + payloads 'bytes' + caminho do cache + manifesto."""
    h = hashlib.sha256()
    h.update(read_bytes(plan_path))
    for t in targets:
        if t["op"] == "bytes":
            h.update(t["_file"].encode("utf-8"))
            h.update(read_bytes(t["_file"]))
    h.update(os.path.normcase(cache_dir).encode("utf-8"))
    h.update(read_bytes(man_path))
    return h.hexdigest()


def dryrun_marker(key):
    return os.path.join(DRYRUN_DIR, key + ".json")


def write_dryrun_marker(key, plan_path, cache_dir):
    os.makedirs(DRYRUN_DIR, exist_ok=True)
    with open(dryrun_marker(key), "w", encoding="utf-8") as fh:
        json.dump({"time": time.time(),
                   "when": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "plan": os.path.abspath(plan_path),
                   "cache": cache_dir}, fh, indent=1)


def check_dryrun_marker(key, max_age_min):
    path = dryrun_marker(key)
    if not os.path.isfile(path):
        raise RuntimeError(
            "nenhum --dry-run sem erros encontrado para este plano/payloads/"
            "estado do cache; rode antes: cache_edit.py --dry-run --plan ...")
    with open(path, "r", encoding="utf-8") as fh:
        age = (time.time() - json.load(fh)["time"]) / 60.0
    if age > max_age_min:
        raise RuntimeError("--dry-run de %.0f min atras (> %g min); rode de novo"
                           % (age, max_age_min))
    return age


def append_ledger(plan_path, man_before, man_after, backup_dir, verify_ok,
                  n_changed, ledger=LEDGER):
    """Registra um apply no CmsCache real em patches/ledger.jsonl (versionado)."""
    plan_abs = os.path.abspath(plan_path)
    rel = os.path.relpath(plan_abs, ROOT)
    parts = rel.replace("\\", "/").split("/")
    kit = parts[1] if len(parts) == 3 and parts[0] == "patches" else rel
    try:
        head = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short",
                               "HEAD"], capture_output=True, text=True
                              ).stdout.strip() or None
    except OSError:
        head = None
    entry = OrderedDict([
        ("when", time.strftime("%Y-%m-%d %H:%M:%S")),
        ("kit", kit),
        ("plan", rel.replace("\\", "/")),
        ("plan_sha256", hashlib.sha256(read_bytes(plan_abs)).hexdigest()),
        ("manifest_before", man_before),
        ("manifest_after", man_after),
        ("changed", n_changed),
        ("verify", verify_ok),
        ("backup", os.path.basename(backup_dir) if backup_dir else None),
        ("git_head", head),
    ])
    os.makedirs(os.path.dirname(ledger), exist_ok=True)
    with open(ledger, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def build_parser():
    p = argparse.ArgumentParser(
        prog="cache_edit.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Edita qualquer arquivo logico do CmsCache do Forza "
                    "Motorsport aplicando um plano JSON.",
        epilog="Exemplo de plano:\n"
               "  {\n"
               '    "targets": [\n'
               '      {"logical": "BuildersCupScheduleDataV4.json",\n'
               '       "group": "14571097C5A44CF4154937B60E5F6DDE",\n'
               '       "op": "json",\n'
               '       "path": "Championships[0].ChampionshipCupData[1]'
               '.ChampionshipLadder[0].OrderData",\n'
               '       "value": [570, 571, 572, 553, 601]}\n'
               "    ]\n"
               "  }\n"
               "Ver _tools/cache_edit_plan_example.json.",
    )
    p.add_argument("--plan", required=True, help="plano JSON de edicao")
    p.add_argument("--cache-dir", default=DEFAULT_CACHE,
                   help="diretorio do CmsCache (default: %%LOCALAPPDATA%%\\"
                        "Microsoft.ForzaMotorsport\\CmsCache)")
    p.add_argument("--oracle-cms", default=DEFAULT_CMS_ORACLE,
                   help="cmsoracle.exe (entradas dos blobs)")
    p.add_argument("--oracle-cache", default=DEFAULT_CACHE_ORACLE,
                   help="cacheoracle.exe (cache-manifest.json)")
    p.add_argument("--backup", dest="backup", action="store_true",
                   default=True, help="faz backup do CmsCache (default: ON)")
    p.add_argument("--no-backup", dest="backup", action="store_false",
                   help="nao faz backup (nao recomendado)")
    p.add_argument("--dry-run", action="store_true",
                   help="calcula tudo e relata, sem escrever nada (obrigatorio "
                        "antes de aplicar: grava o marcador)")
    p.add_argument("--dry-run-max-age", type=float, default=DRYRUN_MAX_AGE_MIN,
                   help="idade maxima do --dry-run, em minutos (default %d, "
                        "teto %d)" % (DRYRUN_MAX_AGE_MIN, DRYRUN_MAX_AGE_CAP))
    p.add_argument("--verify", action="store_true",
                   help="verificacao final completa (re-decripta e confere "
                        "Size/Checksum de manifest, blobs, prod e round-trip)")
    p.add_argument("--keep-work", action="store_true",
                   help="mantem o diretorio de trabalho temporario")
    p.add_argument("--report", default=None,
                   help="grava o log da execucao em um arquivo texto")
    return p


def main(argv=None):
    global LOG
    parser = build_parser()
    args = parser.parse_args(argv)
    LOG = []

    cache_dir = os.path.abspath(args.cache_dir)
    man_path = os.path.join(cache_dir, "cache-manifest.json")
    prod_dir = os.path.join(cache_dir, "prod")
    if not os.path.isfile(man_path):
        parser.error("cache-manifest.json nao encontrado em %s" % cache_dir)
    if not os.path.isdir(prod_dir):
        parser.error("diretorio prod\\ nao encontrado em %s" % cache_dir)

    if not 0 < args.dry_run_max_age <= DRYRUN_MAX_AGE_CAP:
        parser.error("--dry-run-max-age deve estar em (0, %d]"
                     % DRYRUN_MAX_AGE_CAP)

    lint_errors, lint_warnings = plan_lint.lint_plan(args.plan, cache_dir)
    for w in lint_warnings:
        log("lint AVISO: " + w)
    if lint_errors:
        for e in lint_errors:
            log("lint ERRO:  " + e)
        raise RuntimeError("plan_lint reprovou o plano (%d erros)"
                           % len(lint_errors))

    targets = load_plan(args.plan)
    dr_key = dryrun_key(args.plan, targets, cache_dir, man_path)
    man_sha_before = b64sha(read_bytes(man_path))
    log("cache:      %s" % cache_dir)
    log("plano:      %s (%d alvos)" % (os.path.abspath(args.plan), len(targets)))
    log("modo:       %s" % ("DRY-RUN (nada sera escrito)" if args.dry_run
                           else "ESCRITA"))
    if not args.dry_run:
        if is_live_cache(cache_dir):
            running = forza_processes()
            if running:
                raise RuntimeError("jogo aberto (%s); feche antes de escrever "
                                   "no CmsCache" % ", ".join(running))
        age = check_dryrun_marker(dr_key, args.dry_run_max_age)
        log("dry-run:    ok (%.1f min atras)" % age)
    log("")

    deep_errors = []

    stamp = time.strftime("%Y%m%d_%H%M%S")
    workdir = os.path.join(WORK_ROOT, "%s_%d" % (stamp, os.getpid()))
    oracles = Oracles(args.oracle_cms, args.oracle_cache, workdir)

    warnings = []

    try:
        # ---------------- fase A: leitura e mapeamento ---------------------- #
        man_plain = oracles.cache_dec(man_path)
        man_fmt = detect_json_format(man_plain, "cache-manifest.json")
        man = man_fmt["obj"]
        blob_entries = [f for f in man.get("Files", [])
                        if f.get("Attributes") == 3]
        prod_manifest = {f["Path"]: f for f in man.get("Files", [])
                         if f.get("Attributes") == 0}
        log("cache-manifest.json: %d entradas (%d blobs, %d snapshots), "
            "plaintext %d B"
            % (len(man.get("Files", [])), len(blob_entries),
               len(prod_manifest), len(man_plain)))

        blob_index = index_blobs(cache_dir, blob_entries)
        log("blobs indexados: %d (%d B)"
            % (len(blob_index),
               sum(len(m["bytes"]) for m in blob_index.values())))

        snapshots = sorted(
            n for n in os.listdir(prod_dir)
            if os.path.isfile(os.path.join(prod_dir, n))
        )
        log("snapshots em prod\\: %d  %s" % (len(snapshots), ", ".join(snapshots)))
        log("")

        snap_state = OrderedDict()
        for snap in snapshots:
            raw = read_bytes(os.path.join(prod_dir, snap))
            fmt = detect_json_format(raw, "prod/" + snap)
            prod = fmt["obj"]
            groups = map_groups(prod, blob_index)
            snap_state[snap] = {
                "raw": raw,
                "fmt": fmt,
                "prod": prod,
                "groups": groups,
            }
            log("snapshot %s: %d arquivos, %d grupos, %d grupos no cache"
                % (snap, len(prod.get("Files", [])),
                   len(prod.get("ContentGroups", [])), len(groups)))
            if not fmt["matched"]:
                warnings.append("prod/%s com formato nao reproduzivel" % snap)

        # ---------------- fase B: calculo das edicoes ---------------------- #
        pending = OrderedDict()      # (blob_path, entry) -> payload novo
        orig_payload = dict()        # (blob_path, entry) -> payload original
        expected_plain = OrderedDict()  # (blob_path, entry) -> plaintext esperado
        applied = []                 # relatorio

        def current_payload(blob_path, name):
            key = (blob_path, name)
            if key in pending:
                return pending[key]
            return blob_index[blob_path]["entries_data"][name]

        # pre-carrega payloads lidos sob demanda (evita reabrir o zip)
        for meta in blob_index.values():
            meta["entries_data"] = zip_entries(meta["bytes"])

        for snap in snapshots:
            st = snap_state[snap]
            prod = st["prod"]
            groups = st["groups"]
            prod_files = {f["Path"]: f for f in prod.get("Files", [])}

            for target in targets:
                if target["_snapshots"] is not None \
                        and snap not in target["_snapshots"]:
                    continue
                logical = target["logical"]
                gid = target.get("group") or group_for_logical(prod, logical)
                tag = "%s / %s" % (snap, logical)
                if not gid:
                    msg = "%s: grupo nao identificado para %s" % (snap, logical)
                    warnings.append(msg)
                    log("  [skip] " + msg)
                    applied.append({"snap": snap, "logical": logical,
                                    "status": "skip", "reason": "sem grupo"})
                    continue
                if gid not in groups:
                    msg = ("%s: grupo %s nao esta no cache (conteudo base do "
                           "install) - alvo ignorado"
                           % (snap, gid[:8]))
                    warnings.append(msg)
                    log("  [skip] " + msg)
                    applied.append({"snap": snap, "logical": logical,
                                    "group": gid, "status": "skip",
                                    "reason": "grupo fora do cache"})
                    continue

                score, blob_paths = groups[gid]
                for blob_path in blob_paths:
                    meta = blob_index[blob_path]
                    if logical not in meta["entries_data"]:
                        msg = "%s: %s nao existe no blob %s" % (
                            snap, logical, os.path.basename(blob_path)[:12])
                        warnings.append(msg)
                        log("  [skip] " + msg)
                        applied.append({"snap": snap, "logical": logical,
                                        "group": gid, "blob": blob_path,
                                        "status": "skip",
                                        "reason": "entrada ausente no blob"})
                        continue

                    key = (blob_path, logical)
                    payload_old = current_payload(blob_path, logical)
                    if key not in orig_payload:
                        orig_payload[key] = payload_old
                    plain_old = oracles.cms_dec(payload_old)

                    if target["op"] == "bytes":
                        payload_new = read_bytes(target["_file"])
                        try:
                            plain_new = oracles.cms_dec(payload_new)
                        except Exception as exc:  # noqa: BLE001
                            raise RuntimeError(
                                "%s: payload de %s nao decripta (%s)"
                                % (tag, target["_file"], exc))
                        info = {"op": "bytes", "file": target["_file"]}
                    else:
                        plain_new, changed, info = apply_plain_op(
                            target, plain_old, tag)
                        if not changed:
                            log("  [=] %s: %s ja esta no valor desejado "
                                "(blob %s)"
                                % (snap, logical,
                                   os.path.basename(blob_path)[:12]))
                            applied.append({"snap": snap, "logical": logical,
                                            "group": gid, "blob": blob_path,
                                            "status": "unchanged"})
                            continue
                        payload_new = oracles.cms_enc(plain_new, payload_old)
                        back = oracles.cms_dec(payload_new)
                        if back != plain_new:
                            raise RuntimeError(
                                "%s: round-trip do oraculo CMS divergiu" % tag)

                    if payload_new == payload_old:
                        log("  [=] %s: %s payload identico (blob %s)"
                            % (snap, logical,
                               os.path.basename(blob_path)[:12]))
                        applied.append({"snap": snap, "logical": logical,
                                        "group": gid, "blob": blob_path,
                                        "status": "unchanged"})
                        continue

                    if logical == plan_lint.BCS:
                        deep_errors.extend(
                            plan_lint.check_bcs_mp(plain_old, plain_new, tag))

                    pending[key] = payload_new
                    expected_plain[key] = plain_new
                    rec = {
                        "snap": snap,
                        "logical": logical,
                        "group": gid,
                        "blob": blob_path,
                        "status": "changed",
                        "payload_before": len(payload_old),
                        "payload_after": len(payload_new),
                        "plain_before": len(plain_old),
                        "plain_after": len(plain_new),
                        "info": info,
                    }
                    applied.append(rec)
                    log("  [+] %s -> blob %s (%s)"
                        % (logical, os.path.basename(blob_path)[:12],
                           os.path.basename(os.path.dirname(blob_path))))
                    log("      payload %d -> %d B | plaintext %d -> %d B"
                        % (len(payload_old), len(payload_new),
                           len(plain_old), len(plain_new)))
                    if target["op"] == "json":
                        log("      %s: %s -> %s"
                            % (target["path"],
                               json.dumps(rec["info"].get("before"),
                                          ensure_ascii=True)[:120],
                               json.dumps(rec["info"].get("after"),
                                          ensure_ascii=True)[:120]))

        # ---------------- fase C: reconstrucao dos blobs ------------------- #
        per_blob = OrderedDict()
        for (blob_path, name), payload in pending.items():
            per_blob.setdefault(blob_path, {})[name] = payload

        new_blobs = OrderedDict()   # blob_path -> (bytes, entry_name -> (old,new))
        for blob_path, repl in per_blob.items():
            meta = blob_index[blob_path]
            old_entries = meta["entries_data"]
            new_bytes = rebuild_blob(meta["bytes"], repl)
            entry_deltas = OrderedDict()
            for name, payload in repl.items():
                old_payload = orig_payload.get((blob_path, name),
                                               old_entries[name])
                entry_deltas[name] = (old_payload, payload)
            new_blobs[blob_path] = (new_bytes, entry_deltas)
            log("")
            log("blob %s" % os.path.basename(blob_path))
            log("  caminho:      %s" % blob_path)
            log("  tamanho:      %d -> %d B" % (len(meta["bytes"]), len(new_bytes)))
            log("  sha256 blob:  %s" % hashlib.sha256(new_bytes).hexdigest().upper())
            log("  entradas:     %d (alteradas: %d)"
                % (len(meta["names"]), len(repl)))

        # ---------------- fase D: atualizacao das snapshots ---------------- #
        # Deriva as mudancas de prod comparando o checksum antigo -> novo de
        # cada entrada alterada. Isso cobre automaticamente os casos em que o
        # mesmo blob e compartilhado por mais de uma snapshot.
        prod_updates = OrderedDict()   # snap -> {logical: (size, checksum)}
        for snap in snapshots:
            prod_updates[snap] = OrderedDict()
        for blob_path, (_new_bytes, deltas) in new_blobs.items():
            for name, (old_payload, new_payload) in deltas.items():
                old_ck = b64sha(old_payload)
                new_ck = b64sha(new_payload)
                if old_ck == new_ck:
                    continue
                for snap in snapshots:
                    st = snap_state[snap]
                    for f in st["prod"].get("Files", []):
                        if f["Path"] == name and f["Checksum"] == old_ck:
                            f["Size"] = len(new_payload)
                            f["Checksum"] = new_ck
                            prod_updates[snap][name] = (len(new_payload), new_ck)

        prod_writes = OrderedDict()    # snap -> bytes
        for snap in snapshots:
            st = snap_state[snap]
            if not prod_updates[snap]:
                continue
            new_raw = dump_json(st["prod"], st["fmt"])
            if new_raw == st["raw"]:
                continue
            prod_writes[snap] = new_raw

        for snap, updates in prod_updates.items():
            if not updates:
                continue
            log("")
            log("prod/%s: %d entradas atualizadas" % (snap, len(updates)))
            for name, (sz, ck) in updates.items():
                log("  %-40s Size=%d Checksum=%s..." % (name, sz, ck[:16]))

        blob_writes = OrderedDict()
        for blob_path, (new_bytes, _d) in new_blobs.items():
            if new_bytes != blob_index[blob_path]["bytes"]:
                blob_writes[blob_path] = new_bytes

        # ---------------- fase D2: manifesto planejado + lint profundo ----- #
        man_before = json.loads(man_plain.decode("utf-8-sig"),
                                object_pairs_hook=OrderedDict)
        manifest_writes = OrderedDict()   # Path do manifesto -> bytes
        for blob_path, new_bytes in blob_writes.items():
            be = blob_index[blob_path]["entry"]
            be["Size"] = len(new_bytes)
            be["Checksum"] = b64sha(new_bytes)
            manifest_writes[be["Path"]] = new_bytes
        for snap, new_raw in prod_writes.items():
            pe = prod_manifest.get("prod\\" + snap) or \
                prod_manifest.get("prod/" + snap)
            if pe is None:
                msg = ("cache-manifest.json sem entrada Attributes=0 para "
                       "prod\\%s" % snap)
                warnings.append(msg)
                log("  AVISO: " + msg)
            else:
                pe["Size"] = len(new_raw)
                pe["Checksum"] = b64sha(new_raw)
                manifest_writes[pe["Path"]] = new_raw
        new_man = dump_json(man, man_fmt) if (blob_writes or prod_writes) \
            else man_plain
        deep_errors.extend(plan_lint.check_mp_untouched(
            name for (_bp, name) in pending))
        deep_errors.extend(plan_lint.check_strategy_s(
            man_before,
            json.loads(new_man.decode("utf-8-sig"),
                       object_pairs_hook=OrderedDict),
            manifest_writes))
        if deep_errors:
            log("")
            for e in deep_errors:
                log("lint ERRO:  " + e)
            raise RuntimeError("lint profundo reprovou o plano (%d erros); "
                               "nada foi escrito" % len(deep_errors))
        log("")
        log("lint profundo: ok (multiplayer intocado, Strategy S, "
            "Size/Checksum)")

        # ---------------- fase E: escrita --------------------------------- #
        if args.dry_run:
            log("")
            log("DRY-RUN: nenhuma escrita realizada.")
            write_dryrun_marker(dr_key, args.plan, cache_dir)
            log("marcador de dry-run gravado (valido por %g min)"
                % args.dry_run_max_age)
        else:
            backup_dir = None
            if blob_writes or prod_writes:
                backup_dir = make_backup(cache_dir, args.backup)
            else:
                log("backup: nao necessario (nada a escrever)")
            if backup_dir:
                log("")
            for blob_path, new_bytes in blob_writes.items():
                write_bytes(blob_path, new_bytes)
            if blob_writes:
                log("blobs gravados: %d" % len(blob_writes))

            for snap, new_raw in prod_writes.items():
                write_bytes(os.path.join(cache_dir, "prod", snap), new_raw)
                log("prod/%s gravado: %d B" % (snap, len(new_raw)))

            if blob_writes or prod_writes:
                if new_man == man_plain:
                    log("cache-manifest.json: sem mudancas, nao reescrito")
                else:
                    enc = oracles.cache_enc(new_man, man_path)
                    write_bytes(man_path, enc)
                    log("cache-manifest.json re-criptografado e gravado: %d B "
                        "(plaintext %d B)" % (len(enc), len(new_man)))
            else:
                log("nada a escrever: cache ja estava no estado desejado")
            try:
                os.remove(dryrun_marker(dr_key))
            except OSError:
                pass

        # ---------------- fase F: verificacao ------------------------------ #
        verify_ok = None
        if args.verify and not args.dry_run:
            log("")
            log("=== VERIFICACAO ===")
            verify_ok, _nerr = verify_cache(cache_dir, oracles,
                                           expected_plain)
            if not verify_ok:
                warnings.append("verificacao final falhou")

        # ---------------- ledger (so CmsCache real com escrita) ------------ #
        if not args.dry_run and (blob_writes or prod_writes) \
                and is_live_cache(cache_dir):
            entry = append_ledger(
                args.plan, man_sha_before, b64sha(read_bytes(man_path)),
                backup_dir, verify_ok,
                len([a for a in applied if a["status"] == "changed"]))
            log("")
            log("ledger: %s (kit %s) - rode `python _tools\\inventory.py` e "
                "commite patches/ledger.jsonl" % (LEDGER, entry["kit"]))

        # ---------------- relatorio ---------------------------------------- #
        log("")
        log("=== RESUMO ===")
        changed = [a for a in applied if a["status"] == "changed"]
        skipped = [a for a in applied if a["status"] == "skip"]
        unchanged = [a for a in applied if a["status"] == "unchanged"]
        log("alvos avaliados: %d  (alterados: %d, ja corretos: %d, ignorados: %d)"
            % (len(applied), len(changed), len(unchanged), len(skipped)))
        for a in applied:
            if a["status"] == "changed":
                log("  %s  %s  blob=%s  payload %d->%d B%s"
                    % (a["snap"], a["logical"],
                       os.path.basename(a["blob"])[:12],
                       a["payload_before"], a["payload_after"],
                       "  [%s]" % a.get("info", {}).get("op", "")))
        log("blobs a gravar: %d | snapshots a gravar: %d"
            % (len(blob_writes), len(prod_writes)))
        if args.dry_run:
            log("modo dry-run: nenhum arquivo do cache foi tocado")
        if warnings:
            log("")
            log("avisos (%d):" % len(warnings))
            for w in warnings:
                log("  - " + w)

        if args.report:
            with open(args.report, "w", encoding="utf-8") as fh:
                fh.write("\n".join(LOG) + "\n")
            print("relatorio: %s" % args.report)

        if args.verify and verify_ok is False:
            return 1
        return 3 if warnings else 0
    finally:
        if not args.keep_work:
            shutil.rmtree(workdir, ignore_errors=True)
        else:
            print("workdir mantido: %s" % workdir)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as exc:  # noqa: BLE001
        print("ERRO: %s" % exc, file=sys.stderr)
        sys.exit(1)
