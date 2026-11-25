#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""swatchbin_edit.py - edita e cria entradas .swatchbin nos seriesposters.zip
(e, com --archive mainmenu, troca o banner do hub Corrida em mainmenu.zip).

Opera SEMPRE sobre o par coerente no mesmo comando:
  - media\\pcfamily\\ui\\textures\\data_bound\\seriesposters.zip        (424x660)
  - media\\pcfamily\\ui\\textures\\hires\\data_bound\\seriesposters.zip  (848x1320)

As entradas vanilla usam compressao 21 (XMem LZX); a leitura vai pelo `m21.py`
e a reescrita segue o molde do `aistatics_edit.py`:
  - entradas intocadas: header local + bytes comprimidos copiados VERBATIM
    (conteudo e comprimido identicos); so o offset no diretorio central muda;
  - entrada editada ou adicionada: gravada com metodo 8 (Deflate);
  - diretorio central e EOCD refeitos (comentario preservado).

Modos:
  1. --replace <nome> --from-entry <outro>: copia os bytes descomprimidos de
     <outro> para <nome> nos dois zips (exige mesmo tamanho em cada zip).
  2. --replace <nome> --image <png> [--image-hires <png>] [--fit]: gera
     .swatchbin BC7 usando o cabecalho de 144 B do proprio <nome> como molde.
  3. --add <nome> --image <png> [--image-hires <png>] [--fit]: anexa uma
     entrada nova no fim dos dois zips usando o cabecalho de uma entrada
     vanilla 424x660 / 848x1320 como molde (recusa nome que ja exista).

Sem `--image-hires`, a mesma imagem de `--image` e usada para normal e hires,
o que exige `--fit` (pois uma unica imagem nao tem 424x660 e 848x1320 ao mesmo
tempo); sem `--fit`, tamanhos divergentes sao recusados.

Travas:
  - exige `--dest-copy <pasta>` ou `--allow-install` (recusa o install real sem
    `--allow-install`, e recusa `--dest-copy` apontando para install, CmsCache,
    _backup, _extract ou graphics);
  - jogo fechado (`ce.forza_processes()`);
  - `--dry-run` recente (30 min) para os mesmos alvos + modo + entrada +
    parametros + shas dos dois zips;
  - estado: recusa se o sha de qualquer um dos dois zips nao for o vanilla nem
    o ultimo arquivo escrito por esta ferramenta;
  - backup: na 1a escrita salva os dois zips originais em
    `swatchbin_vanilla_<ts>\\` + `SHA256.txt`; nas seguintes faz backup
    incremental `swatchbin_<ts>\\`. Com `--dest-copy`, os backups ficam
    isolados em `_work\\swatchbin_edit\\backup\\` (nunca em `_backup\\`).

Uso (sempre em copia com --dest-copy durante o trabalho do executor):
  python _tools\\swatchbin_edit.py --dest-copy _work\\swatch_copy ^
      --replace BC_GermanRivals --from-entry BC_Reward_Showcase_Modern_001 ^
      --dry-run
  python _tools\\swatchbin_edit.py --dest-copy _work\\swatch_copy ^
      --replace BC_GermanRivals --from-entry BC_Reward_Showcase_Modern_001 ^
      --verify
  python _tools\\swatchbin_edit.py --dest-copy _work\\swatch_copy ^
      --replace BC_GermanRivals --image poster_424x660.png ^
      --image-hires poster_848x1320.png --dry-run
  python _tools\\swatchbin_edit.py --dest-copy _work\\swatch_copy ^
      --add FCO_Test_001 --image poster_424x660.png ^
      --image-hires poster_848x1320.png --verify
  python _tools\\swatchbin_edit.py --dest-copy _work\\swatch_copy ^
      --restore _work\\swatchbin_edit\\backup\\swatchbin_vanilla_<ts>

Saida: 0 ok, 1 erro, 3 verify falhou.

Ambiente: FM_INSTALL, XCOMPRESS_DLL (ver m21.py), FM_SWATCHBIN_WORK e
FM_SWATCHBIN_BACKUP_ROOT.
"""

import argparse
import glob
import hashlib
import io
import json
import os
import re
import shutil
import struct
import sys
import time
import zipfile
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cache_edit as ce  # noqa: E402
try:
    import m21  # noqa: E402  (leitor/gravador LZX; so no lab)
except ImportError:          # copia sem m21.py: so Deflate (D102)
    m21 = None
METHOD21 = 21
import swatchbin as sb  # noqa: E402

DEFAULT_INSTALL = os.environ.get(
    "FM_INSTALL", r"F:\SteamLibrary\steamapps\common\Forza Motorsport")
ZIPS_REL = {
    "normal": ("media", "pcfamily", "ui", "textures", "data_bound",
               "seriesposters.zip"),
    "hires": ("media", "pcfamily", "ui", "textures", "hires", "data_bound",
              "seriesposters.zip"),
}
TARGET_DIMS = {
    "normal": sb.NORMAL_POSTER_SIZE,
    "hires": sb.HIRES_POSTER_SIZE,
}
KINDS = ("normal", "hires")

# Arquivos-alvo. `seriesposters` e o padrao (posteres de series). `mainmenu`
# (banner do hub "Corrida", 1300x480 / 2600x960) so aceita trocar no lugar,
# com imagem, as entradas da lista fechada `entries` (nunca outro tile do menu).
ARCHIVES = {
    "seriesposters": {"zip": "seriesposters.zip",
                      "dims": {"normal": sb.NORMAL_POSTER_SIZE,
                               "hires": sb.HIRES_POSTER_SIZE},
                      "entries": None},
    # posteres largos (1296x660 / 2592x1320, ex.: Builders_Cup_Intro); mesmo zip
    # dos posteres normais, entao compartilha estado e backup com ele
    "seriesposters_wide": {"zip": "seriesposters.zip",
                           "dims": {"normal": (1296, 660),
                                    "hires": (2592, 1320)},
                           "entries": None},
    # cartao da ladder (440x140 / 880x280); o seriesposters.zip tem entradas
    # vanilla desse tamanho, usadas como molde
    "seriesposters_ladder": {"zip": "seriesposters.zip",
                             "dims": {"normal": (440, 140),
                                      "hires": (880, 280)},
                             "entries": None},
    "mainmenu": {"zip": "mainmenu.zip",
                 "dims": {"normal": (1300, 480), "hires": (2600, 960)},
                 "entries": ("mm_gorace_builderscup.swatchbin",)},
}
ARCHIVE = "seriesposters"


def set_archive(name):
    """Aponta ZIPS_REL/TARGET_DIMS para o arquivo escolhido (global do modulo)."""
    global ARCHIVE
    if name not in ARCHIVES:
        raise SeError("arquivo desconhecido: %r (use %s)"
                      % (name, ", ".join(ARCHIVES)))
    ARCHIVE = name
    a = ARCHIVES[name]
    ZIPS_REL["normal"] = ("media", "pcfamily", "ui", "textures", "data_bound",
                          a["zip"])
    ZIPS_REL["hires"] = ("media", "pcfamily", "ui", "textures", "hires",
                         "data_bound", a["zip"])
    TARGET_DIMS.update(a["dims"])


def _rel_copy():
    """Caminho de cada zip dentro de uma pasta de backup."""
    return {k: os.path.join(*ZIPS_REL[k][4:]) for k in KINDS}

WORK = os.environ.get("FM_SWATCHBIN_WORK",
                      os.path.join(ce.ROOT, "_work", "swatchbin_edit"))
INSTALL_BACKUP_ROOT = os.environ.get("FM_SWATCHBIN_BACKUP_ROOT", ce.BACKUP_ROOT)
MAX_AGE_MIN = 30
VANILLA_PREFIX = "swatchbin_vanilla_"
INCREMENTAL_PREFIX = "swatchbin_"
METHOD_DEFLATED = 8
DOS_TIME = 0
DOS_DATE = 0x21
ZIP64_EXTRA = 0x0001

NAME_RE = re.compile(r"^[A-Za-z0-9_ -]+$")
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".tga", ".webp", ".dds")


class SeError(Exception):
    pass


# --------------------------------------------------------------------------- #
# utilitarios e caminhos
# --------------------------------------------------------------------------- #
def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    with open(path, "rb") as fh:
        return fh.read()


def put(path, data):
    """Grava `data` em `path` com fallback para destinos que negam DELETE."""
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


def _dryrun_dir():
    return os.path.join(WORK, "dryrun")


def _state_path():
    return os.path.join(WORK, "state.json")


def _backup_root(dest_copy):
    env = os.environ.get("FM_SWATCHBIN_BACKUP_ROOT")
    if env:
        return env
    if dest_copy:
        return os.path.join(WORK, "backup")
    return INSTALL_BACKUP_ROOT


def _same_or_under(path, parent):
    if not path or not parent:
        return False
    a = os.path.normcase(os.path.abspath(path))
    b = os.path.normcase(os.path.abspath(parent))
    try:
        return os.path.commonpath([a, b]) == b
    except ValueError:
        return False


def zip_paths_of(root):
    base = os.path.abspath(root)
    return {k: os.path.join(base, *ZIPS_REL[k]) for k in KINDS}


def _check_dest_copy_safe(dest_copy, install):
    abs_dest = os.path.normcase(os.path.abspath(dest_copy))
    abs_root = os.path.normcase(os.path.abspath(ce.ROOT))
    if abs_dest == abs_root:
        raise SeError("--dest-copy nao pode apontar para a raiz do repo: %s"
                      % dest_copy)
    forbidden = [
        ("install", install),
        ("_backup", ce.BACKUP_ROOT),
        ("CmsCache", getattr(ce, "CACHE_DIR", None)),
        ("_extract", os.path.join(ce.ROOT, "_extract")),
        ("graphics", os.path.join(ce.ROOT, "graphics")),
    ]
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        forbidden.append(("CmsCache", os.path.join(
            local_app, "Microsoft.ForzaMotorsport", "CmsCache")))
    for label, parent in forbidden:
        if _same_or_under(dest_copy, parent):
            raise SeError("--dest-copy recusado dentro de %s: %s"
                          % (label, dest_copy))


def prepare_targets(args):
    """Valida --dest-copy / --allow-install e copia do install se necessario."""
    if not args.dest_copy and not args.allow_install:
        raise SeError("operacao no install real recusada sem --allow-install; "
                      "use --dest-copy <pasta>")
    if args.dest_copy and args.allow_install:
        raise SeError("informe --dest-copy ou --allow-install, nao os dois")
    if args.dest_copy:
        _check_dest_copy_safe(args.dest_copy, args.install)
        root = os.path.abspath(args.dest_copy)
        targets = zip_paths_of(root)
        sources = zip_paths_of(args.install)
        for kind in KINDS:
            dst = targets[kind]
            if not os.path.isfile(dst):
                src = sources[kind]
                if not os.path.isfile(src):
                    raise SeError("%s %s nao encontrado no "
                                  "install: %s"
                                  % (kind, ZIPS_REL[kind][-1], src))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                print("copia (%s): %s -> %s" % (kind, src, dst))
    else:
        root = os.path.abspath(args.install)
        targets = zip_paths_of(root)
        for kind in KINDS:
            if not os.path.isfile(targets[kind]):
                raise SeError("%s %s nao encontrado: %s"
                              % (kind, ZIPS_REL[kind][-1],
                                 targets[kind]))
    return root, targets


def normalize_entry_name(raw):
    """Mapeia nome do BCS ou de entrada para `<stem>.swatchbin` em minusculas."""
    if not raw or not isinstance(raw, str):
        raise SeError("nome de entrada vazio")
    if "/" in raw or "\\" in raw or ".." in raw:
        raise SeError("nome de entrada invalido (use so o nome, sem caminho): "
                      "%r" % raw)
    if raw != raw.strip():
        raise SeError("nome de entrada com espacos nas pontas: %r" % raw)
    low = raw.lower()
    for ext in IMAGE_EXTS:
        if low.endswith(ext):
            raise SeError("nome de entrada %r parece caminho de imagem "
                          "(informe o nome da entrada sem %s)" % (raw, ext))
    stem = raw[:-len(".swatchbin")] if low.endswith(".swatchbin") else raw
    if not stem or stem != stem.strip() or not NAME_RE.fullmatch(stem):
        raise SeError("nome de entrada invalido: %r" % raw)
    return stem.lower() + ".swatchbin"


# --------------------------------------------------------------------------- #
# leitura das entradas (metodo 21 via m21.py; 0/8 via zipfile)
# --------------------------------------------------------------------------- #
def _find_m21_dll():
    if m21 is None:
        return None
    dll = m21.find_dll()
    if dll:
        return dll
    git_file = os.path.join(ce.ROOT, ".git")
    if os.path.isfile(git_file):
        try:
            with open(git_file, encoding="utf-8") as fh:
                line = fh.read().strip()
            if line.lower().startswith("gitdir:"):
                gitdir = line.split(":", 1)[1].strip()
                if not os.path.isabs(gitdir):
                    gitdir = os.path.abspath(os.path.join(ce.ROOT, gitdir))
                cur = gitdir
                for _ in range(5):
                    cand = os.path.join(cur, "_external", "ForzaTechStudio",
                                        "Native", "xcompress64.dll")
                    if os.path.isfile(cand):
                        return cand
                    parent = os.path.dirname(cur)
                    if parent == cur:
                        break
                    cur = parent
        except OSError:
            pass
    return None


class _NoLzx:
    available = False
    reason = "m21.py ausente (copia sem o runtime LZX); use codec deflate"


def _m21_reader():
    if m21 is None:
        return _NoLzx()
    return m21.Method21Reader(_find_m21_dll())


class _EntryReader:
    def __init__(self):
        self._reader = _m21_reader()
        self._session = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        if self._session is not None:
            self._session.close()
            self._session = None

    def read(self, zip_path, info):
        if info.compress_type == METHOD21:
            if not self._reader.available:
                raise SeError("leitura metodo 21 indisponivel: %s (ver "
                              "docs/project/THIRD_PARTY.md)"
                              % self._reader.reason)
            if self._session is None:
                self._session = m21.Method21Session(reader=self._reader)
            try:
                return self._session.read(zip_path, info)
            except m21.Method21Unavailable as exc:
                raise SeError("leitura metodo 21 indisponivel: %s" % exc) \
                    from None
            except m21.Method21Error:
                try:
                    return m21.read_isolated(zip_path, info,
                                             reader=self._reader)
                except m21.Method21Unavailable as exc:
                    raise SeError("leitura metodo 21 indisponivel: %s" % exc) \
                        from None
                except m21.Method21Error as exc:
                    raise SeError("%s: %s" % (info.filename, exc)) from None
        if info.compress_type in (0, METHOD_DEFLATED):
            try:
                with zipfile.ZipFile(zip_path) as zf:
                    return zf.read(info.filename)
            except zipfile.BadZipFile as exc:
                raise SeError("zip invalido: %s" % exc) from None
        raise SeError("%s: metodo de compressao %d nao suportado"
                      % (info.filename, info.compress_type))


def list_infos(zip_bytes):
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            return zf.infolist(), zf.comment
    except zipfile.BadZipFile as exc:
        raise SeError("zip invalido: %s" % exc) from None


def info_map(infos):
    out = {}
    for info in infos:
        if info.filename in out:
            raise SeError("%s aparece duplicado no zip" % info.filename)
        out[info.filename] = info
    return out


# --------------------------------------------------------------------------- #
# zip: reescrita por splice cru (entradas intocadas verbatim)
# --------------------------------------------------------------------------- #
ALIGN = 4096


def deflate(data):
    co = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    return co.compress(data) + co.flush()


def _local_bounds(buf, info):
    n, e = struct.unpack("<HH", buf[info.header_offset + 26:
                                    info.header_offset + 30])
    start = info.header_offset + 30 + n + e
    return start, start + info.compress_size


def raw_slices(buf):
    """{nome: bytes comprimidos crus} na ordem do diretorio central."""
    out = {}
    infos, _comment = list_infos(buf)
    for info in infos:
        start, end = _local_bounds(buf, info)
        if end > len(buf):
            raise SeError("%s: entrada truncada" % info.filename)
        out[info.filename] = buf[start:end]
    return out


def _check_zip_layout(buf, infos):
    with zipfile.ZipFile(io.BytesIO(buf)) as zf:
        comment_len = len(zf.comment)
    eocd = len(buf) - 22 - comment_len
    if eocd < 0 or buf[eocd:eocd + 4] != b"PK\x05\x06":
        raise SeError("EOCD nao encontrado no fim do zip")
    (_disk, _cd_disk, _n_disk, n_total, cd_size, cd_off,
     _clen) = struct.unpack("<HHHHIIH", buf[eocd + 4:eocd + 22])
    if 0xFFFF in (n_total,) or 0xFFFFFFFF in (cd_size, cd_off):
        raise SeError("zip64 nao suportado")
    if n_total != len(infos):
        raise SeError("EOCD declara %d entradas e o diretorio tem %d"
                      % (n_total, len(infos)))
    for info in infos:
        if info.flag_bits & 0x08:
            raise SeError("%s: data descriptor (flag 0x08) nao suportado"
                          % info.filename)
        if 0xFFFFFFFF in (info.header_offset, info.compress_size,
                          info.file_size):
            raise SeError("%s: campos zip64 nao suportados" % info.filename)
        pos = 0
        while pos + 4 <= len(info.extra):
            fid, fsz = struct.unpack("<HH", info.extra[pos:pos + 4])
            if fid == ZIP64_EXTRA:
                raise SeError("%s: campo extra zip64 nao suportado"
                              % info.filename)
            pos += 4 + fsz
    return eocd, cd_off, cd_size


def _slot_end(infos, info, cd_off):
    """Fim da vaga de `info`: inicio da proxima entrada (por offset) ou o
    diretorio central."""
    later = [i.header_offset for i in infos
             if i.header_offset > info.header_offset]
    return min(later) if later else cd_off


def rebuild_zip_inplace(buf, edit_name, raw, method, crc, usize):
    """Troca o conteudo de `edit_name` NO LUGAR: mesmo tamanho de arquivo e
    todos os offsets iguais (as texturas de UI ficam alinhadas a 4096 B; um
    zip com offsets deslocados fez o jogo travar em 18/11/2026). `raw` e o
    payload ja comprimido do `method`; o que sobra da vaga vira zeros. Recusa
    se `raw` nao couber na vaga."""
    infos, _comment = list_infos(buf)
    names = [i.filename for i in infos]
    if edit_name not in names:
        raise SeError("%s nao existe no zip" % edit_name)
    if len(set(names)) != len(names):
        raise SeError("entradas duplicadas no zip")
    eocd, cd_off, _cd_size = _check_zip_layout(buf, infos)
    info = next(i for i in infos if i.filename == edit_name)
    start, _end = _local_bounds(buf, info)
    slot_end = _slot_end(infos, info, cd_off)
    if start + len(raw) > slot_end:
        raise SeError("%s: o conteudo novo (%d B comprimidos) nao cabe na "
                      "vaga (%d B); trocar no lugar exige que caiba"
                      % (edit_name, len(raw), slot_end - start))
    out = bytearray(buf)
    flags = info.flag_bits & ~0x0006 if method == METHOD_DEFLATED \
        else info.flag_bits
    struct.pack_into("<H", out, info.header_offset + 6, flags)
    struct.pack_into("<H", out, info.header_offset + 8, method)
    struct.pack_into("<I", out, info.header_offset + 14, crc)
    struct.pack_into("<I", out, info.header_offset + 18, len(raw))
    struct.pack_into("<I", out, info.header_offset + 22, usize)
    out[start:slot_end] = bytes(raw) + b"\x00" * (slot_end - start - len(raw))
    pos = cd_off
    for i in infos:
        if buf[pos:pos + 4] != b"PK\x01\x02":
            raise SeError("registro do diretorio central invalido")
        n, e, c = struct.unpack("<HHH", buf[pos + 28:pos + 34])
        if i.filename == edit_name:
            struct.pack_into("<H", out, pos + 8, flags)
            struct.pack_into("<H", out, pos + 10, method)
            struct.pack_into("<I", out, pos + 16, crc)
            struct.pack_into("<I", out, pos + 20, len(raw))
            struct.pack_into("<I", out, pos + 24, usize)
        pos += 46 + n + e + c
    return bytes(out)


def check_inplace(old, new, edit_name, raw, method, crc, usize):
    """Prova: mesmo tamanho, mesmos offsets, so a vaga de `edit_name` mudou."""
    errs = []
    if len(old) != len(new):
        errs.append("tamanho do arquivo mudou (%d -> %d)"
                    % (len(old), len(new)))
        return errs
    a_infos, a_comment = list_infos(old)
    b_infos, b_comment = list_infos(new)
    if [(i.filename, i.header_offset) for i in a_infos] != \
            [(i.filename, i.header_offset) for i in b_infos]:
        errs.append("nomes/offsets do diretorio central mudaram")
        return errs
    if a_comment != b_comment:
        errs.append("comentario do zip mudou")
    _eocd, cd_off, _sz = _check_zip_layout(old, a_infos)
    edit = next(i for i in a_infos if i.filename == edit_name)
    s0 = edit.header_offset
    e0 = _slot_end(a_infos, edit, cd_off)
    if old[:s0] != new[:s0]:
        errs.append("bytes antes da vaga de %s mudaram" % edit_name)
    if old[e0:cd_off] != new[e0:cd_off]:
        errs.append("bytes depois da vaga de %s mudaram" % edit_name)
    ni = next(i for i in b_infos if i.filename == edit_name)
    if ni.compress_type != method:
        errs.append("%s: metodo %d != %d" % (edit_name, ni.compress_type,
                                             method))
    if ni.CRC != crc or ni.file_size != usize or ni.compress_size != len(raw):
        errs.append("%s: CRC/tamanhos do diretorio central nao conferem"
                    % edit_name)
    start, end = _local_bounds(new, ni)
    if new[start:end] != raw:
        errs.append("%s: payload gravado difere do esperado" % edit_name)
    if any(new[end:e0]):
        errs.append("%s: sobra da vaga nao e zero" % edit_name)
    cd_a, cd_b = old[cd_off:], new[cd_off:]
    if len(cd_a) != len(cd_b):
        errs.append("diretorio central mudou de tamanho")
    return errs


def append_entry(buf, name, data, packed=None, method=METHOD_DEFLATED):
    """Zip novo com `name` anexada no FIM (offset alinhado a 4096); demais
    entradas verbatim. `packed`/`method`: payload ja comprimido (LZX, 21);
    sem eles, Deflate."""
    infos, _comment = list_infos(buf)
    names = [i.filename for i in infos]
    if name in names:
        raise SeError("%s ja existe no zip; use --replace para substituir"
                      % name)
    if len(set(names)) != len(names):
        raise SeError("entradas duplicadas no zip")
    eocd, cd_off, cd_size = _check_zip_layout(buf, infos)

    if packed is None:
        packed, method = deflate(data), METHOD_DEFLATED
    crc = zlib.crc32(data) & 0xFFFFFFFF
    fname = name.encode("utf-8")

    # molde: versoes do 1o registro vanilla; o extra 0x1123 (4 bytes) do
    # diretorio central guarda o offset dos dados da entrada em todas as
    # entradas vanilla de textura: a nova ganha o seu
    first = min(infos, key=lambda i: i.header_offset) if infos else None
    ver_made, ver_need = (struct.unpack("<HH", buf[cd_off + 4:cd_off + 8])
                          if infos else (20, 20))
    loc_need = (struct.unpack("<H", buf[first.header_offset + 4:
                                        first.header_offset + 6])[0]
                if first else 20)
    data_extra = bool(first) and first.extra[:4] == b"\x23\x11\x04\x00"

    out = bytearray(buf[:cd_off])
    out += b"\x00" * (-len(out) % ALIGN)      # entradas vanilla: offset % 4096 == 0
    new_off = len(out)
    out += struct.pack("<IHHHHHIIIHH", 0x04034B50, loc_need, 0, method,
                       DOS_TIME, DOS_DATE, crc, len(packed), len(data),
                       len(fname), 0)
    out += fname + packed
    data_off = new_off + 30 + len(fname)
    if cd_off % ALIGN == 0:                   # diretorio central alinhado
        out += b"\x00" * (-len(out) % ALIGN)

    cd_start = len(out)
    pos = cd_off
    for info in infos:
        if buf[pos:pos + 4] != b"PK\x01\x02":
            raise SeError("registro do diretorio central invalido")
        n, e, c = struct.unpack("<HHH", buf[pos + 28:pos + 34])
        rec = bytearray(buf[pos:pos + 46 + n + e + c])
        struct.pack_into("<I", rec, 42, info.header_offset)
        out += rec
        pos += len(rec)
    if pos != cd_off + cd_size:
        raise SeError("tamanho do diretorio central nao confere")
    extra = struct.pack("<HHI", 0x1123, 4, data_off) if data_extra else b""
    out += struct.pack("<IHHHHHHIIIHHHHHII", 0x02014B50, ver_made, ver_need,
                       0, method, DOS_TIME, DOS_DATE, crc, len(packed),
                       len(data), len(fname), len(extra), 0, 0, 0, 0, new_off)
    out += fname + extra
    new_cd_size = len(out) - cd_start

    tail = bytearray(buf[eocd:])
    struct.pack_into("<HH", tail, 8, len(infos) + 1, len(infos) + 1)
    struct.pack_into("<II", tail, 12, new_cd_size, cd_start)
    out += tail
    return bytes(out)


def check_append(old, new, name, data, packed=None, method=METHOD_DEFLATED):
    """Prova que as entradas antigas ficaram iguais e a nova le de volta."""
    errs = []
    a, b = raw_slices(old), raw_slices(new)
    if packed is not None and b.get(name) != packed:
        errs.append("%s: payload LZX gravado difere do esperado" % name)
    if list(b) != list(a) + [name]:
        errs.append("entradas nao sao as originais + %s no fim" % name)
    for old_name in a:
        if b.get(old_name) != a[old_name]:
            errs.append("%s: bytes comprimidos mudaram" % old_name)
    try:
        if zipfile.ZipFile(io.BytesIO(new)).getinfo(name).header_offset \
                % ALIGN:
            errs.append("%s: entrada nova nao esta alinhada a %d" % (name,
                                                                    ALIGN))
        with zipfile.ZipFile(io.BytesIO(old)) as zf:
            old_comment = zf.comment
        with zipfile.ZipFile(io.BytesIO(new)) as zf:
            info = zf.getinfo(name)
            if info.compress_type != method:
                errs.append("%s: metodo %d != %d"
                            % (name, info.compress_type, method))
            if info.CRC != zlib.crc32(data) & 0xFFFFFFFF:
                errs.append("%s: CRC do diretorio central nao confere" % name)
            if method == METHOD_DEFLATED and zf.read(name) != data:
                errs.append("%s: entrada nova nao volta aos bytes esperados"
                            % name)
            if zf.comment != old_comment:
                errs.append("comentario do zip mudou")
    except (zipfile.BadZipFile, KeyError, NotImplementedError) as exc:
        errs.append("zip novo ilegivel: %s" % exc)
    return errs


# --------------------------------------------------------------------------- #
# backup / estado por raiz alvo
# --------------------------------------------------------------------------- #
def _target_key(root):
    key = os.path.normcase(os.path.abspath(root))
    zname = ARCHIVES[ARCHIVE]["zip"]
    return key if zname == "seriesposters.zip" else "%s::%s" % (key, zname)


def load_state():
    path = _state_path()
    if not os.path.isfile(path):
        return {"targets": {}}
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict) or "targets" not in data:
            return {"targets": {}}
        return data
    except (OSError, ValueError):
        return {"targets": {}}


def save_state(state):
    os.makedirs(WORK, exist_ok=True)
    with open(_state_path(), "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=1)


def _parse_sha_file(path):
    target = None
    hashes = {}
    for line in read(path).decode("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("target:"):
            target = line.split(":", 1)[1].strip()
        elif line.startswith("normal:") or line.startswith("hires:"):
            kind, rest = line.split(":", 1)
            hashes[kind] = rest.strip().split()[0].lower()
    return target, hashes


def backup_dirs(broot, prefix):
    return sorted(d for d in glob.glob(os.path.join(broot, prefix + "*"))
                  if os.path.isdir(d))


def vanilla_dir(broot, target_root=None):
    want_key = _target_key(target_root) if target_root else None
    for d in backup_dirs(broot, VANILLA_PREFIX):
        sha_file = os.path.join(d, "SHA256.txt")
        if not os.path.isfile(sha_file):
            continue
        if want_key is None:
            return d
        tkey, _hashes = _parse_sha_file(sha_file)
        if tkey is None or tkey == want_key:
            return d
    return None


def vanilla_shas(target_state, broot, target_root):
    vid = target_state.get("vanilla_sha256")
    if isinstance(vid, dict) and set(vid) == set(KINDS):
        return vid
    vdir = vanilla_dir(broot, target_root)
    if vdir:
        _tkey, hashes = _parse_sha_file(os.path.join(vdir, "SHA256.txt"))
        if set(hashes) == set(KINDS):
            return hashes
    return None


def make_backup(broot, target_root, targets, old_zips):
    """Vanilla na 1a escrita do alvo (nunca sobrescrito); incremental depois."""
    vanilla = vanilla_dir(broot, target_root)
    prefix = INCREMENTAL_PREFIX if vanilla else VANILLA_PREFIX
    stamp = time.strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(broot, prefix + stamp)
    n = 1
    while os.path.exists(dst):
        dst = os.path.join(broot, "%s%s_%d" % (prefix, stamp, n))
        n += 1
    os.makedirs(dst)

    rel_copy = _rel_copy()
    digests = {}
    lines = ["target: %s" % _target_key(target_root)]
    for kind in KINDS:
        copy_path = os.path.join(dst, rel_copy[kind])
        os.makedirs(os.path.dirname(copy_path), exist_ok=True)
        shutil.copy2(targets[kind], copy_path)
        dig = sha256(old_zips[kind])
        if sha256(read(copy_path)) != dig:
            raise SeError("backup divergente em %s; nada escrito" % dst)
        digests[kind] = dig
        lines.append("%s: %s  %s"
                     % (kind, dig, rel_copy[kind].replace("\\", "/")))
    with open(os.path.join(dst, "SHA256.txt"), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    return dst, digests


def require_closed():
    running = ce.forza_processes()
    if running:
        raise SeError("jogo aberto (%s); feche antes" % ", ".join(running))


# --------------------------------------------------------------------------- #
# plano (dry-run e apply compartilham)
# --------------------------------------------------------------------------- #
def _check_targets_state(args):
    root, targets = prepare_targets(args)
    old_zips = {k: read(targets[k]) for k in KINDS}
    current = {k: sha256(old_zips[k]) for k in KINDS}
    broot = _backup_root(args.dest_copy)
    state = load_state()
    tkey = _target_key(root)
    tstate = state["targets"].get(tkey, {})
    vid = vanilla_shas(tstate, broot, root)
    last = tstate.get("last_written_sha256")
    for kind in KINDS:
        allowed = set()
        if vid and kind in vid:
            allowed.add(vid[kind])
        if isinstance(last, dict) and kind in last:
            allowed.add(last[kind])
        if allowed and current[kind] not in allowed:
            raise SeError(
                "%s %s nao e o vanilla nem o ultimo arquivo "
                "escrito por esta ferramenta (sha %s...); nada feito"
                % (kind, ZIPS_REL[kind][-1], current[kind][:12]))
    return root, targets, old_zips, current, vid, state, broot


def _find_poster_mold(zip_path, infos, target_dim):
    want_size = sb.HEADER_SIZE + target_dim[0] * target_dim[1]
    candidates = [i for i in infos if i.file_size == want_size]
    if not candidates:
        raise SeError("nenhuma entrada %dx%d (%d B) em %s para servir de molde"
                      % (target_dim[0], target_dim[1], want_size, zip_path))
    with _EntryReader() as reader:
        for info in candidates:
            raw = reader.read(zip_path, info)
            try:
                sb.validate_mold(raw, expected_size=target_dim)
                return info.filename, raw
            except sb.SwatchbinError:
                continue
    raise SeError("nenhum molde valido %dx%d encontrado em %s"
                  % (target_dim[0], target_dim[1], zip_path))


def _image_sha(path):
    if not os.path.isfile(path):
        raise SeError("imagem nao encontrada: %s" % path)
    return sha256(read(path))


# --------------------------------------------------------------------------- #
# manifesto: todas as entradas FCO_* de uma vez (base da release)
# --------------------------------------------------------------------------- #
OWN_PREFIX = "fco_"


def remove_entry(buf, name):
    """Tira `name` do diretorio central SEM mover nada: a vaga vira zeros e
    as demais entradas ficam nos mesmos offsets (offsets deslocados travam o
    jogo, D99)."""
    infos, _comment = list_infos(buf)
    eocd, cd_off, cd_size = _check_zip_layout(buf, infos)
    info = next((i for i in infos if i.filename == name), None)
    if info is None:
        raise SeError("%s nao existe no zip" % name)
    end = _slot_end(infos, info, cd_off)
    out = bytearray(buf[:cd_off])
    out[info.header_offset:end] = b"\x00" * (end - info.header_offset)
    pos = cd_off
    for i in infos:
        n, e, c = struct.unpack("<HHH", buf[pos + 28:pos + 34])
        rec = buf[pos:pos + 46 + n + e + c]
        if i.filename != name:
            out += rec
        pos += 46 + n + e + c
    if pos != cd_off + cd_size:
        raise SeError("tamanho do diretorio central nao confere")
    tail = bytearray(buf[eocd:])
    struct.pack_into("<HH", tail, 8, len(infos) - 1, len(infos) - 1)
    struct.pack_into("<II", tail, 12, len(out) - cd_off, cd_off)
    return bytes(out + tail)


def load_manifest(path):
    path = os.path.abspath(path)
    try:
        with open(path, encoding="utf-8-sig") as fh:
            m = json.load(fh)
    except (OSError, ValueError) as exc:
        raise SeError("manifesto ilegivel: %s" % exc) from None
    if not isinstance(m, dict) or set(m) - {"_doc", "codec", "add", "remove"}:
        raise SeError("manifesto: chaves aceitas: codec, add, remove")
    codec = m.get("codec", "deflate")
    if codec not in ("deflate", "lzx"):
        raise SeError("manifesto: codec deve ser deflate ou lzx")
    base = os.path.dirname(path)
    adds, seen = [], set()
    for k, it in enumerate(m.get("add", [])):
        if not isinstance(it, dict) or set(it) - {"name", "image",
                                                  "image_hires"} \
                or "name" not in it or "image" not in it:
            raise SeError("manifesto add[%d]: precisa de name, image "
                          "(e image_hires opcional)" % k)
        name = normalize_entry_name(it["name"])
        if not name.startswith(OWN_PREFIX):
            raise SeError("manifesto add[%d]: so entradas %s* (nunca vanilla)"
                          % (k, OWN_PREFIX.upper()))
        if name in seen:
            raise SeError("manifesto: %s repetida" % name)
        seen.add(name)
        img = os.path.join(base, it["image"])
        adds.append((name, img, os.path.join(base, it.get("image_hires",
                                                             it["image"]))))
    removes = []
    for k, raw in enumerate(m.get("remove", [])):
        name = normalize_entry_name(raw)
        if not name.startswith(OWN_PREFIX):
            raise SeError("manifesto remove[%d]: so entradas %s* (nunca "
                          "vanilla)" % (k, OWN_PREFIX.upper()))
        if name in seen:
            raise SeError("manifesto: %s em add e remove" % name)
        removes.append(name)
    if not adds and not removes:
        raise SeError("manifesto vazio")
    return {"path": path, "sha": sha256(read(path)), "codec": codec,
            "add": adds, "remove": removes}


def plan_manifest(args):
    root, targets, old_zips, current, vid, state, broot = (
        _check_targets_state(args))
    man = load_manifest(args.manifest)
    lzx = man["codec"] == "lzx"
    enc = _m21_reader() if lzx else None
    if lzx and not enc.available:
        raise SeError("codec lzx sem o DLL: %s" % enc.reason)
    new_zips, new_shas, actions, want_entries = {}, {}, {}, {}
    with _EntryReader() as reader:
        for kind in KINDS:
            buf = old_zips[kind]
            acts = []
            want = {}
            for name in man["remove"]:
                if name in info_map(list_infos(buf)[0]):
                    buf = remove_entry(buf, name)
                    acts.append("remove " + name)
                else:
                    acts.append("ja ausente " + name)
            # cabecalho gerado (igual ao das vanilla do mesmo tamanho): o
            # manifesto nao le arquivo do jogo, entao nao precisa do LZX
            mold_name, mold = "gerado", sb.make_header(*TARGET_DIMS[kind])
            for name, img_n, img_h in man["add"]:
                img = img_n if kind == "normal" else img_h
                try:
                    data = sb.build_swatchbin(img, mold,
                                              expected_size=TARGET_DIMS[kind])
                except sb.SwatchbinError as exc:
                    raise SeError("%s %s: %s" % (kind, name, exc)) from None
                want[name] = data
                imap = info_map(list_infos(buf)[0])
                if name in imap:
                    # entradas que ficam nao mudam de lugar: le do arquivo
                    cur = reader.read(targets[kind], imap[name])
                    if cur == data:
                        acts.append("ja igual " + name)
                        continue
                    raise SeError("%s ja existe em %s com outro conteudo; "
                                  "ponha-a em remove e rode de novo, ou mude "
                                  "o nome" % (name, kind))
                packed = enc.compress(data) if lzx else None
                method = METHOD21 if lzx else METHOD_DEFLATED
                buf = append_entry(buf, name, data, packed, method)
                acts.append("add %s (%s)" % (name, "lzx" if lzx else
                                             "deflate"))
            new_zips[kind] = buf
            new_shas[kind] = sha256(buf)
            actions[kind] = acts
            want_entries[kind] = want
    if all(new_shas[k] == current[k] for k in KINDS):
        raise SeError("nada a fazer: o manifesto ja esta aplicado")
    return {
        "target_root": root, "targets": targets, "backup_root": broot,
        "mode": "manifest", "entry": os.path.basename(man["path"]),
        "old_zips": old_zips, "new_zips": new_zips, "old_shas": current,
        "new_shas": new_shas, "vanilla_shas": vid, "state": state,
        "extra": {"manifest_sha": man["sha"], "codec": man["codec"],
                  "actions": actions, "remove": man["remove"],
                  "want": want_entries, "mold": mold_name},
    }


def verify_manifest(r):
    errs = []
    if not vanilla_dir(r["backup_root"], r["target_root"]):
        raise SeError("sem backup vanilla; --verify precisa dele")
    for kind in KINDS:
        new_zip = read(r["targets"][kind])
        if sha256(new_zip) != r["new_shas"][kind]:
            errs.append("%s: sha256 gravado difere do plano" % kind)
        old_infos = list_infos(r["old_zips"][kind])[0]
        infos = list_infos(new_zip)[0]
        imap = info_map(infos)
        a, b = raw_slices(r["old_zips"][kind]), raw_slices(new_zip)
        for i in old_infos:
            if i.filename in r["extra"]["remove"]:
                if i.filename in imap:
                    errs.append("%s: %s nao foi removida" % (kind, i.filename))
                continue
            if imap.get(i.filename) is None or \
                    imap[i.filename].header_offset != i.header_offset or \
                    a[i.filename] != b[i.filename]:
                errs.append("%s: %s mudou de lugar ou de bytes"
                            % (kind, i.filename))
        if any(i.header_offset % ALIGN for i in infos):
            errs.append("%s: entrada fora da grade de %d" % (kind, ALIGN))
        with _EntryReader() as reader:
            for name, data in r["extra"]["want"][kind].items():
                info = imap.get(name)
                if info is None:
                    errs.append("%s: %s ausente" % (kind, name))
                    continue
                fid = info.extra[:4]
                if fid != b"\x23\x11\x04\x00" or struct.unpack(
                        "<I", info.extra[4:8])[0] != _local_bounds(
                            new_zip, info)[0]:
                    errs.append("%s: %s sem o extra 0x1123 correto"
                                % (kind, name))
                if reader.read(r["targets"][kind], info) != data:
                    errs.append("%s: %s nao le de volta igual" % (kind, name))
    return errs


def plan(args):
    if getattr(args, "manifest", None):
        return plan_manifest(args)
    root, targets, old_zips, current, vid, state, broot = (
        _check_targets_state(args))
    infos = {}
    imap = {}
    for kind in KINDS:
        infs, _comment = list_infos(old_zips[kind])
        infos[kind] = infs
        imap[kind] = info_map(infs)

    if args.replace:
        mode = "replace_from" if args.from_entry else "replace_image"
        entry = normalize_entry_name(args.replace)
        missing = [k for k in KINDS if entry not in imap[k]]
        if missing:
            raise SeError("%s ausente em %s" % (entry, ", ".join(missing)))
    else:
        mode = "add_image"
        entry = normalize_entry_name(args.add)
        present = [k for k in KINDS if entry in imap[k]]
        if present:
            raise SeError("%s ja existe em %s; use --replace para substituir"
                          % (entry, ", ".join(present)))

    new_entries = {}
    old_entries = {}
    mold_names = {}
    dims = {}
    extra_param = {}

    if mode == "replace_from":
        src_entry = normalize_entry_name(args.from_entry)
        if src_entry == entry:
            raise SeError("--replace e --from-entry apontam para a mesma "
                          "entrada: %s" % entry)
        missing_src = [k for k in KINDS if src_entry not in imap[k]]
        if missing_src:
            raise SeError("origem %s ausente em %s"
                          % (src_entry, ", ".join(missing_src)))
        with _EntryReader() as reader:
            for kind in KINDS:
                old_b = reader.read(targets[kind], imap[kind][entry])
                src_b = reader.read(targets[kind], imap[kind][src_entry])
                try:
                    _h0, dim_t = sb.validate_mold(old_b)
                    _h1, dim_s = sb.validate_mold(src_b, expected_size=dim_t)
                except sb.SwatchbinError as exc:
                    raise SeError("%s (%s): %s" % (kind, entry, exc)) from None
                if dim_t != TARGET_DIMS[kind]:
                    raise SeError("%s (%s): dimensao %dx%d difere de %dx%d"
                                  % (kind, entry, dim_t[0], dim_t[1],
                                     TARGET_DIMS[kind][0],
                                     TARGET_DIMS[kind][1]))
                old_entries[kind] = old_b
                new_entries[kind] = src_b
                dims[kind] = dim_t
        if dims["hires"] != (dims["normal"][0] * 2, dims["normal"][1] * 2):
            raise SeError("dimensoes normal/hires incoerentes: %r vs %r"
                          % (dims["normal"], dims["hires"]))
        if all(new_entries[k] == old_entries[k] for k in KINDS):
            raise SeError("nada a fazer: %s ja tem o conteudo de %s nos dois "
                          "zips" % (entry, src_entry))
        extra_param = {"from_entry": src_entry}
    else:
        img_paths = {
            "normal": os.path.abspath(args.image),
            "hires": os.path.abspath(args.image_hires or args.image),
        }
        img_shas = {k: _image_sha(img_paths[k]) for k in KINDS}
        with _EntryReader() as reader:
            for kind in KINDS:
                if mode == "replace_image":
                    mold_bytes = reader.read(targets[kind], imap[kind][entry])
                    mold_names[kind] = entry
                    old_entries[kind] = mold_bytes
                else:
                    mname, mold_bytes = _find_poster_mold(
                        targets[kind], infos[kind], TARGET_DIMS[kind])
                    mold_names[kind] = mname
                try:
                    new_b = sb.build_swatchbin(
                        img_paths[kind], mold_bytes,
                        expected_size=TARGET_DIMS[kind], fit=args.fit)
                except sb.SwatchbinError as exc:
                    raise SeError("%s: %s" % (kind, exc)) from None
                new_entries[kind] = new_b
                dims[kind] = TARGET_DIMS[kind]
        extra_param = {
            "fit": bool(args.fit),
            "image_shas": img_shas,
            "image_paths": img_paths,
            "molds": mold_names,
            "codec": args.codec,
        }

    new_zips = {}
    new_shas = {}
    new_methods = {k: METHOD_DEFLATED for k in KINDS}
    lzx = mode != "replace_from" and args.codec == "lzx"
    enc = _m21_reader() if lzx else None
    if lzx and not enc.available:
        raise SeError("--codec lzx sem o DLL: %s" % enc.reason)
    for kind in KINDS:
        if mode == "add_image":
            packed = (enc.compress(new_entries[kind]) if lzx else None)
            method = METHOD21 if lzx else METHOD_DEFLATED
            new_z = append_entry(old_zips[kind], entry, new_entries[kind],
                                 packed, method)
            errs = check_append(old_zips[kind], new_z, entry,
                                new_entries[kind], packed, method)
            new_methods[kind] = method
        else:
            data = new_entries[kind]
            if mode == "replace_from":
                # payload ja comprimido da origem, copiado como esta (sem
                # recomprimir): so o conteudo da vaga muda
                src_info = imap[kind][src_entry]
                raw = raw_slices(old_zips[kind])[src_entry]
                method, crc, usize = (src_info.compress_type, src_info.CRC,
                                      src_info.file_size)
            else:
                raw = enc.compress(data) if lzx else deflate(data)
                method, crc, usize = (METHOD21 if lzx else METHOD_DEFLATED,
                                      zlib.crc32(data) & 0xFFFFFFFF,
                                      len(data))
            new_z = rebuild_zip_inplace(old_zips[kind], entry, raw, method,
                                        crc, usize)
            errs = check_inplace(old_zips[kind], new_z, entry, raw, method,
                                 crc, usize)
            new_methods[kind] = method
        if errs:
            raise SeError("reescrita do zip %s falhou: %s"
                          % (kind, "; ".join(errs)))
        new_zips[kind] = new_z
        new_shas[kind] = sha256(new_z)

    return {
        "target_root": root,
        "targets": targets,
        "backup_root": broot,
        "mode": mode,
        "entry": entry,
        "old_zips": old_zips,
        "new_zips": new_zips,
        "old_shas": current,
        "new_shas": new_shas,
        "old_entries": old_entries,
        "new_entries": new_entries,
        "dims": dims,
        "new_methods": new_methods,
        "entry_counts": {k: len(infos[k]) for k in KINDS},
        "vanilla_shas": vid,
        "state": state,
        "extra": extra_param,
    }


def dryrun_key(r):
    h = hashlib.sha256()
    for kind in KINDS:
        h.update(os.path.normcase(os.path.abspath(
            r["targets"][kind])).encode("utf-8"))
        h.update(r["old_shas"][kind].encode("ascii"))
    h.update(("%s:%s;" % (r["mode"], r["entry"])).encode("utf-8"))
    if r["mode"] == "manifest":
        h.update(r["extra"]["manifest_sha"].encode("ascii"))
        for kind in KINDS:
            h.update(r["new_shas"][kind].encode("ascii"))
    elif r["mode"] == "replace_from":
        h.update(r["extra"]["from_entry"].encode("utf-8"))
    else:
        h.update(b"fit=1;" if r["extra"]["fit"] else b"fit=0;")
        h.update(("codec=%s;" % r["extra"].get("codec")).encode("ascii"))
        for kind in KINDS:
            h.update(r["extra"]["image_shas"][kind].encode("ascii"))
    return h.hexdigest()


def report(r):
    if r["mode"] == "manifest":
        print("modo:       manifesto %s (codec %s, molde %s)"
              % (r["entry"], r["extra"]["codec"], r["extra"]["mold"]))
        for kind in KINDS:
            print("[%s] alvo:  %s" % (kind, r["targets"][kind]))
            print("[%s] sha:   %s -> %s"
                  % (kind, r["old_shas"][kind], r["new_shas"][kind]))
            print("[%s] bytes: %d -> %d B | entradas: %d -> %d"
                  % (kind, len(r["old_zips"][kind]), len(r["new_zips"][kind]),
                     len(list_infos(r["old_zips"][kind])[0]),
                     len(list_infos(r["new_zips"][kind])[0])))
            for a in r["extra"]["actions"][kind]:
                print("[%s]   %s" % (kind, a))
        return
    print("modo:       %s" % r["mode"])
    print("entrada:    %s" % r["entry"])
    if r["mode"] == "replace_from":
        print("origem:     %s" % r["extra"]["from_entry"])
    else:
        print("fit:        %s" % ("sim" if r["extra"]["fit"] else "nao"))
    for kind in KINDS:
        n_before = r["entry_counts"][kind]
        n_after = n_before + (1 if r["mode"] == "add_image" else 0)
        w, h = r["dims"][kind]
        print("[%s] alvo:  %s" % (kind, r["targets"][kind]))
        print("[%s] sha:   %s -> %s"
              % (kind, r["old_shas"][kind], r["new_shas"][kind]))
        print("[%s] bytes: %d -> %d B | entradas: %d -> %d | dim: %dx%d (%d B)"
              % (kind, len(r["old_zips"][kind]), len(r["new_zips"][kind]),
                 n_before, n_after, w, h, len(r["new_entries"][kind])))


# --------------------------------------------------------------------------- #
# verify
# --------------------------------------------------------------------------- #
def verify(r):
    """Confere os dois zips gravados contra o plano e exige backup vanilla."""
    if r["mode"] == "manifest":
        return verify_manifest(r)
    errs = []
    if not vanilla_dir(r["backup_root"], r["target_root"]):
        raise SeError("sem backup vanilla; --verify precisa dele")
    dims_got = {}
    for kind in KINDS:
        new_zip = read(r["targets"][kind])
        if sha256(new_zip) != r["new_shas"][kind]:
            errs.append("%s: sha256 gravado difere do plano" % kind)
        va, vb = raw_slices(r["old_zips"][kind]), raw_slices(new_zip)
        entry = r["entry"]
        if r["mode"] == "add_image":
            if list(vb) != list(va) + [entry]:
                errs.append("%s: entradas nao sao as de antes + %s no fim"
                            % (kind, entry))
            for n in va:
                if vb.get(n) != va[n]:
                    errs.append("%s: bytes comprimidos de %s mudaram"
                                % (kind, n))
        else:
            if list(vb) != list(va):
                errs.append("%s: lista/ordem de entradas mudou" % kind)
            for n in va:
                if n != entry and vb.get(n) != va[n]:
                    errs.append("%s: bytes comprimidos de %s mudaram"
                                % (kind, n))
            if len(new_zip) != len(r["old_zips"][kind]):
                errs.append("%s: tamanho do zip mudou (trocar no lugar nao "
                            "pode mover nada)" % kind)
            if [i.header_offset for i in list_infos(new_zip)[0]] != \
                    [i.header_offset for i in list_infos(
                        r["old_zips"][kind])[0]]:
                errs.append("%s: offsets das entradas mudaram" % kind)
        want_method = r["new_methods"][kind]
        try:
            with zipfile.ZipFile(io.BytesIO(r["old_zips"][kind])) as zf_old:
                old_comment = zf_old.comment
            with zipfile.ZipFile(io.BytesIO(new_zip)) as zf:
                info = zf.getinfo(entry)
                if info.compress_type != want_method:
                    errs.append("%s: %s metodo %d != %d"
                                % (kind, entry, info.compress_type,
                                   want_method))
                with _EntryReader() as reader:
                    got = reader.read(r["targets"][kind], info)
                want = r["new_entries"][kind]
                if got != want:
                    errs.append("%s: %s bytes diferem do esperado"
                                % (kind, entry))
                if info.CRC != (zlib.crc32(want) & 0xFFFFFFFF):
                    errs.append("%s: %s CRC do diretorio central nao confere"
                                % (kind, entry))
                if zf.comment != old_comment:
                    errs.append("%s: comentario do zip mudou" % kind)
                _hdr, dims_got[kind] = sb.validate_mold(
                    got, expected_size=TARGET_DIMS[kind])
        except (zipfile.BadZipFile, KeyError, NotImplementedError,
                sb.SwatchbinError) as exc:
            errs.append("%s: falha ao validar %s: %s" % (kind, entry, exc))
    if set(dims_got) == set(KINDS):
        nw, nh = dims_got["normal"]
        if dims_got["hires"] != (nw * 2, nh * 2):
            errs.append("dimensoes normal/hires incoerentes no verify: %r vs %r"
                        % (dims_got["normal"], dims_got["hires"]))
    return errs


# --------------------------------------------------------------------------- #
# restore
# --------------------------------------------------------------------------- #
def restore(src, args):
    src = os.path.abspath(src)
    sha_file = os.path.join(src, "SHA256.txt")
    rel_copy = _rel_copy()
    if not os.path.isfile(sha_file):
        raise SeError("%s: sem SHA256.txt" % src)
    _tkey, want = _parse_sha_file(sha_file)
    if set(want) != set(KINDS):
        raise SeError("%s: SHA256.txt incompleto" % src)
    backup_data = {}
    for kind in KINDS:
        zcopy = os.path.join(src, rel_copy[kind])
        if not os.path.isfile(zcopy):
            raise SeError("%s: sem %s" % (src, rel_copy[kind]))
        raw = read(zcopy)
        if sha256(raw) != want[kind]:
            raise SeError("backup %s corrompido (sha nao confere); nada feito"
                          % kind)
        backup_data[kind] = raw

    require_closed()
    root, targets = prepare_targets(args)
    old_data = {k: read(targets[k]) for k in KINDS}
    before = {k: sha256(old_data[k]) for k in KINDS}
    wrote_normal = False
    try:
        put(targets["normal"], backup_data["normal"])
        wrote_normal = True
        put(targets["hires"], backup_data["hires"])
    except OSError:
        if wrote_normal:
            put(targets["normal"], old_data["normal"])
        raise
    after = {k: sha256(read(targets[k])) for k in KINDS}
    for kind in KINDS:
        print("restaurado (%s): %s" % (kind, targets[kind]))
        print("  sha256 antes:  %s" % before[kind])
        print("  sha256 depois: %s" % after[kind])
        if after[kind] != want[kind]:
            print("FALHA: hash restaurado (%s) nao confere" % kind)
            return 3
    state = load_state()
    tkey = _target_key(root)
    prev_t = state["targets"].get(tkey, {})
    vid = prev_t.get("vanilla_sha256") or dict(want)
    state["targets"][tkey] = {
        "vanilla_sha256": vid,
        "last_written_sha256": after,
    }
    save_state(state)
    print("OK: originais restaurados (hashes conferem)")
    return 0


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def _validate_cli(ap, args):
    if args.restore:
        if any([args.replace, args.add, args.from_entry, args.image,
                args.image_hires, args.fit, args.dry_run, args.verify]):
            ap.error("--restore nao combina com flags de edicao/dry-run/verify")
        return
    if ARCHIVES[args.archive]["entries"] is not None:
        if args.manifest or args.add:
            ap.error("--archive %s so aceita --replace (nunca --add/--manifest)"
                     % args.archive)
        allowed = ARCHIVES[args.archive]["entries"]
        if args.replace and normalize_entry_name(args.replace) not in allowed:
            ap.error("--archive %s: entradas permitidas: %s"
                     % (args.archive, ", ".join(allowed)))
        if args.from_entry:
            ap.error("--archive %s so aceita --image" % args.archive)
    if args.manifest:
        if any([args.replace, args.add, args.from_entry, args.image,
                args.image_hires, args.fit]):
            ap.error("--manifest nao combina com --replace/--add/--image")
        return
    if bool(args.replace) == bool(args.add):
        ap.error("informe exatamente um entre --replace <nome> e --add <nome>")
    if args.replace:
        if bool(args.from_entry) == bool(args.image):
            ap.error("com --replace, informe exatamente um entre --from-entry "
                     "e --image")
        if args.from_entry and (args.image_hires or args.fit):
            ap.error("--image-hires e --fit so valem com --image")
    if args.add:
        if args.from_entry:
            ap.error("--from-entry so vale com --replace")
        if not args.image:
            ap.error("com --add, informe --image <png>")


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="swatchbin_edit.py",
        description="substitui ou adiciona entradas .swatchbin nos dois "
                    "seriesposters.zip (normal e hires)")
    ap.add_argument("--install", default=DEFAULT_INSTALL,
                    help="raiz do install (padrao: FM_INSTALL)")
    ap.add_argument("--dest-copy", metavar="PASTA",
                    help="opera numa copia em <PASTA>/media/pcfamily/ui/"
                         "textures/...")
    ap.add_argument("--allow-install", action="store_true",
                    help="habilita escrita no install real (nao use em copia)")
    ap.add_argument("--archive", choices=tuple(ARCHIVES),
                    default="seriesposters",
                    help="zip alvo (padrao seriesposters; mainmenu = banner do "
                         "hub Corrida, so --replace mm_gorace_builderscup "
                         "--image; seriesposters_wide = posteres largos "
                         "1296x660 / 2592x1320, ex. --add FCO_Intro_Series)")
    ap.add_argument("--replace", metavar="NOME",
                    help="substitui entrada existente nos dois zips")
    ap.add_argument("--add", metavar="NOME",
                    help="adiciona entrada nova no fim dos dois zips")
    ap.add_argument("--from-entry", metavar="OUTRO",
                    help="com --replace: copia os bytes de outra entrada")
    ap.add_argument("--image", metavar="PNG",
                    help="imagem de entrada para gerar o .swatchbin BC7")
    ap.add_argument("--image-hires", metavar="PNG",
                    help="imagem hires opcional (848x1320); sem ela usa "
                         "--image nos dois")
    ap.add_argument("--codec", choices=("lzx", "deflate"), default="deflate",
                    help="compressao da imagem nova (--image): deflate = "
                         "metodo 8, so Python, aceito pelo jogo no formato "
                         "vanilla (D102; padrao); lzx = metodo 21 como as "
                         "vanilla (exige m21.py e o DLL)")
    ap.add_argument("--fit", action="store_true",
                    help="redimensiona (cover) e corta ao centro quando a "
                         "imagem diferir do alvo")
    ap.add_argument("--manifest", metavar="JSON",
                    help="aplica um manifesto {codec, add:[{name, image, "
                         "image_hires}], remove:[nomes]} de entradas FCO_* "
                         "numa escrita so; idempotente; remover nao move nada")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--restore", metavar="BACKUP_DIR")
    args = ap.parse_args(argv)
    set_archive(args.archive)
    _validate_cli(ap, args)
    try:
        if args.restore:
            return restore(args.restore, args)
        r = plan(args)
        report(r)
        ddir = _dryrun_dir()
        marker = os.path.join(ddir, dryrun_key(r) + ".json")
        if args.dry_run:
            os.makedirs(ddir, exist_ok=True)
            with open(marker, "w", encoding="utf-8") as fh:
                json.dump({
                    "time": time.time(),
                    "target_root": r["target_root"],
                    "mode": r["mode"],
                    "entry": r["entry"],
                    "old_shas": r["old_shas"],
                }, fh)
            print("\nDRY-RUN: nada escrito (marcador valido por %d min)"
                  % MAX_AGE_MIN)
            return 0
        require_closed()
        if not os.path.isfile(marker):
            raise SeError("sem --dry-run para este alvo/modo/estado; rode "
                          "--dry-run antes")
        with open(marker, encoding="utf-8") as fh:
            age = (time.time() - json.load(fh)["time"]) / 60
        if age > MAX_AGE_MIN:
            raise SeError("--dry-run de %.0f min atras; rode de novo" % age)
        bk, digests = make_backup(r["backup_root"], r["target_root"],
                                  r["targets"], r["old_zips"])
        print("\nbackup: %s" % bk)
        print("  sha normal: %s" % digests["normal"])
        print("  sha hires:  %s" % digests["hires"])
        wrote_normal = False
        try:
            put(r["targets"]["normal"], r["new_zips"]["normal"])
            wrote_normal = True
            put(r["targets"]["hires"], r["new_zips"]["hires"])
        except OSError:
            if wrote_normal:
                put(r["targets"]["normal"], r["old_zips"]["normal"])
            raise
        for kind in KINDS:
            if sha256(read(r["targets"][kind])) != r["new_shas"][kind]:
                print("FALHA: zip %s gravado nao confere. Restaurar: python "
                      "_tools\\swatchbin_edit.py --restore %s" % (kind, bk))
                return 3
        state = r["state"]
        tkey = _target_key(r["target_root"])
        vid = r["vanilla_shas"] or digests
        state["targets"][tkey] = {
            "vanilla_sha256": vid,
            "last_written_sha256": dict(r["new_shas"]),
        }
        save_state(state)
        os.remove(marker)
        errs = verify(r) if args.verify else []
        if errs:
            for e in errs:
                print("FALHA: " + e)
            print("Reverter: python _tools\\swatchbin_edit.py --restore " + bk)
            return 3
        print("OK" + (" (verificado)" if args.verify else ""))
        return 0
    except (SeError, OSError, RuntimeError) as exc:
        print("ERRO: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
