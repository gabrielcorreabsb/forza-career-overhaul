#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_swatchbin_edit.py - autoteste 100% sintetico de swatchbin e swatchbin_edit.

Nao le nem escreve nenhum arquivo do jogo: constroi moldes .swatchbin e pares
de seriesposters.zip sinteticos (incluindo entradas em metodo 8, uma entrada
intocada em metodo 21 com bytes opacos, padding entre entradas e campo extra
0x1123 no diretorio central) numa pasta temporaria isolada.
"""

import contextlib
import io
import json
import os
import shutil
import struct
import sys
import tempfile
import zipfile
import zlib

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swatchbin as sb  # noqa: E402
import swatchbin_edit as se  # noqa: E402


def expect(cond, label):
    print(("  ok: " if cond else "  FALHOU: ") + label)
    if not cond:
        shutil.rmtree(os.environ.get("_SE_TEST_ROOT", ""), ignore_errors=True)
        sys.exit(1)


def run(*args):
    args = list(args)
    # os zips sinteticos sao lidos com zipfile: imagem em Deflate, salvo
    # quando o teste pede --codec lzx de proposito
    if "--image" in args and "--codec" not in args:
        args += ["--codec", "deflate"]
    return se.main(args)


def capture(*args):
    buf = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
        code = run(*args)
    return code, buf.getvalue() + err.getvalue()


def make_synthetic_header(w, h):
    """Cabecalho .swatchbin de 144 B sintetico conforme docs/reference/SWATCHBIN.md."""
    buf = bytearray(sb.HEADER_SIZE)
    buf[0:4] = b"burG"
    struct.pack_into("<BB", buf, 4, 1, 1)
    struct.pack_into("<I", buf, 16, 1)
    buf[20:24] = b"BCXT"
    struct.pack_into("<BB", buf, 24, 0, 0)
    struct.pack_into("<H", buf, 26, 1)
    struct.pack_into("<I", buf, 32, sb.HEADER_SIZE)
    buf[44:48] = b"HCXT"
    p = sb.TEX_OFFSET
    struct.pack_into("<III", buf, p + 24, w, h, 1)
    struct.pack_into("<H", buf, p + 36, 1)  # slice=1, platform=0
    buf[p + 38] = 1  # mip_count=1
    buf[p + 39] = 0  # flags=0
    slice_rel = 64
    mip_rel = 76
    struct.pack_into("<I", buf, p + 56, slice_rel)
    struct.pack_into("<II", buf, p + slice_rel, sb.ENCODING_BC7, mip_rel)
    struct.pack_into("<I", buf, p + mip_rel, w * h)
    return bytes(buf)


def make_synthetic_mold(w, h, fill_byte=0):
    return make_synthetic_header(w, h) + (bytes([fill_byte]) * (w * h))


def decode_bc7_mode6_ref(bc7_bytes, w, h):
    """Decodificador BC7 modo 6 proprio do teste (independente do encoder)."""
    expect(len(bc7_bytes) == w * h and w % 4 == 0 and h % 4 == 0,
           "tamanho do buffer BC7 valido (%dx%d)" % (w, h))
    n_blocks = (w // 4) * (h // 4)
    raw = np.frombuffer(bc7_bytes, dtype="<u8").reshape(n_blocks, 2)
    lo = raw[:, 0]
    hi = raw[:, 1]
    if not np.all((lo & np.uint64(0x7F)) == np.uint64(0x40)):
        raise ValueError("bloco fora do modo 6 encontrado")

    def bits_lo(shift):
        return ((lo >> np.uint64(shift)) & np.uint64(0x7F)).astype(np.int32)

    r0, r1 = bits_lo(7), bits_lo(14)
    g0, g1 = bits_lo(21), bits_lo(28)
    b0, b1 = bits_lo(35), bits_lo(42)
    a0, a1 = bits_lo(49), bits_lo(56)
    p0 = ((lo >> np.uint64(63)) & np.uint64(1)).astype(np.int32)
    p1 = (hi & np.uint64(1)).astype(np.int32)

    c0 = np.stack([r0, g0, b0, a0], axis=1)
    c1 = np.stack([r1, g1, b1, a1], axis=1)
    e0 = (c0 << 1) | p0[:, None]
    e1 = (c1 << 1) | p1[:, None]

    idx = np.empty((n_blocks, 16), dtype=np.int32)
    idx[:, 0] = ((hi >> np.uint64(1)) & np.uint64(0x7)).astype(np.int32)
    for k in range(1, 16):
        idx[:, k] = ((hi >> np.uint64(4 * k)) & np.uint64(0xF)).astype(np.int32)

    w_arr = sb.W4[idx][:, :, None]
    rec = (((64 - w_arr) * e0[:, None, :]
            + w_arr * e1[:, None, :] + 32) >> 6).astype(np.uint8)
    return (rec.reshape(h // 4, w // 4, 4, 4, 4)
            .transpose(0, 2, 1, 3, 4)
            .reshape(h, w, 4))


def make_test_rgba(w, h, seed=0):
    """Imagem RGBA sintetica deterministica (degrade + retangulos + alfa)."""
    xs = np.linspace(10, 240, w, dtype=np.float32)[None, :]
    ys = np.linspace(20, 230, h, dtype=np.float32)[:, None]
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[:, :, 0] = np.clip(xs + (seed * 37) % 50, 0, 255).astype(np.uint8)
    arr[:, :, 1] = np.clip(ys, 0, 255).astype(np.uint8)
    arr[:, :, 2] = np.clip(255.0 - 0.5 * xs - 0.3 * ys, 0, 255).astype(np.uint8)
    arr[:, :, 3] = 255
    # Retangulo interno com outra cor e alfa 220
    y0, y1 = h // 4, (h * 3) // 4
    x0, x1 = w // 4, (w * 3) // 4
    arr[y0:y1, x0:x1, 0] = 210
    arr[y0:y1, x0:x1, 1] = 80
    arr[y0:y1, x0:x1, 2] = 40
    arr[y0:y1, x0:x1, 3] = 220
    return arr


def make_synthetic_zip(entries, comment=b"FCO_SYNTH"):
    """Constroi um zip sintetico com padding entre entradas e extra 0x1123 no CD.

    `entries`: lista de tuplas `(name, method, raw_or_uncompressed_bytes, usize, crc)`
    Se `method == 8`, `raw_or_uncompressed_bytes` e comprimido via deflate; se
    `method == 21`, os bytes ja sao o payload comprimido opaco e `usize`/`crc`
    sao gravados nos headers.
    """
    out = bytearray()
    cd_records = []
    for idx, item in enumerate(entries):
        name, method, payload, usize, crc = item
        # como o vanilla: toda entrada comeca em offset multiplo de 4096
        out += b"\x00" * (-len(out) % 4096)
        hdr_off = len(out)
        fname = name.encode("utf-8")
        if method == se.METHOD_DEFLATED:
            packed = se.deflate(payload)
            usize = len(payload)
            crc = zlib.crc32(payload) & 0xFFFFFFFF
        else:
            packed = payload
        out += struct.pack("<IHHHHHIIIHH", 0x04034B50, 20, 0, method,
                           se.DOS_TIME, se.DOS_DATE, crc, len(packed), usize,
                           len(fname), 0)
        data_off = len(out) + len(fname)
        out += fname + packed
        # folga na vaga (o vanilla tambem deixa espaco depois de cada entrada)
        out += b"\x00" * (-(len(out) + len(packed) // 4) % 4096
                          + len(packed) // 4)

        extra_cd = struct.pack("<HHI", 0x1123, 4, data_off)
        cd = struct.pack("<IHHHHHHIIIHHHHHII", 0x02014B50, 20, 20, 0, method,
                         se.DOS_TIME, se.DOS_DATE, crc, len(packed), usize,
                         len(fname), len(extra_cd), 0, 0, 0, 0, hdr_off)
        cd_records.append(cd + fname + extra_cd)

    cd_start = len(out)
    for rec in cd_records:
        out += rec
    cd_size = len(out) - cd_start
    out += struct.pack("<IHHHHIIH", 0x06054B50, 0, 0, len(entries),
                       len(entries), cd_size, cd_start, len(comment))
    out += comment
    return bytes(out)


def unit_swatchbin():
    print("unidade do gerador (swatchbin.py, dados 100% sinteticos):")
    for w, h in (sb.NORMAL_POSTER_SIZE, sb.HIRES_POSTER_SIZE):
        mold = make_synthetic_mold(w, h, fill_byte=0xAA)
        rgba = make_test_rgba(w, h, seed=w)
        im = Image.fromarray(rgba, "RGBA")
        out = sb.build_swatchbin(im, mold, expected_size=(w, h))
        expect(len(out) == sb.HEADER_SIZE + w * h,
               "%dx%d: tamanho = 144 + w*h (%d B)" % (w, h, len(out)))
        expect(out[:sb.HEADER_SIZE] == mold[:sb.HEADER_SIZE],
               "%dx%d: cabecalho de 144 B igual ao molde byte a byte" % (w, h))
        expect(out[sb.HEADER_SIZE:] != mold[sb.HEADER_SIZE:],
               "%dx%d: payload de pixels foi substituido" % (w, h))

        dec_ref = decode_bc7_mode6_ref(out[sb.HEADER_SIZE:], w, h)
        dec_pil = np.array(Image.frombytes(
            "RGBA", (w, h), out[sb.HEADER_SIZE:], "bcn", 7))
        expect(np.array_equal(dec_ref, dec_pil),
               "%dx%d: decoder proprio do teste == decoder nativo PIL bcn"
               % (w, h))
        rmse = float(np.sqrt(np.mean(
            (rgba.astype(np.float32) - dec_ref.astype(np.float32)) ** 2)))
        expect(rmse < 2.5,
               "%dx%d: ida e volta BC7 dentro da tolerancia (RMSE=%.3f)"
               % (w, h, rmse))

    # Bloco anti-correlacionado (duas cores opostas no mesmo bloco 4x4)
    anti = np.zeros((4, 4, 4), dtype=np.uint8)
    anti[:2, :, :] = (220, 30, 40, 255)
    anti[2:, :, :] = (20, 230, 240, 200)
    bc7_anti = sb.encode_bc7_mode6(anti)
    dec_anti = decode_bc7_mode6_ref(bc7_anti, 4, 4)
    expect(int(np.max(np.abs(anti.astype(int) - dec_anti.astype(int)))) <= 2,
           "bloco 4x4 anti-correlacionado codifica sem degenerescencia")

    # Recusa de imagem com tamanho errado sem --fit
    mold_n = make_synthetic_mold(*sb.NORMAL_POSTER_SIZE)
    bad_im = Image.fromarray(make_test_rgba(300, 300), "RGBA")
    try:
        sb.build_swatchbin(bad_im, mold_n,
                           expected_size=sb.NORMAL_POSTER_SIZE, fit=False)
        expect(False, "imagem de tamanho diferente recusada sem --fit")
    except sb.SwatchbinError:
        expect(True, "imagem de tamanho diferente recusada sem --fit")

    # Com --fit (cobrir e cortar)
    fitted = sb.build_swatchbin(bad_im, mold_n,
                                expected_size=sb.NORMAL_POSTER_SIZE, fit=True)
    expect(len(fitted) == sb.HEADER_SIZE + 424 * 660
           and fitted[:sb.HEADER_SIZE] == mold_n[:sb.HEADER_SIZE],
           "--fit ajusta e gera arquivo 424x660 valido")

    # Recusa de moldes invalidos
    bad_magic = bytearray(mold_n[:sb.HEADER_SIZE])
    bad_magic[0:4] = b"XXXX"
    try:
        sb.validate_mold(bytes(bad_magic))
        expect(False, "molde com magic invalido recusado")
    except sb.SwatchbinError:
        expect(True, "molde com magic invalido recusado")

    bad_enc = bytearray(mold_n[:sb.HEADER_SIZE])
    struct.pack_into("<I", bad_enc, sb.TEX_OFFSET + 64, 7)
    try:
        sb.validate_mold(bytes(bad_enc))
        expect(False, "molde com encoding != 9 recusado")
    except sb.SwatchbinError:
        expect(True, "molde com encoding != 9 recusado")

    try:
        sb.validate_mold(b"burGshort")
        expect(False, "molde truncado recusado")
    except sb.SwatchbinError:
        expect(True, "molde truncado recusado")


def build_synthetic_pair(copy_root):
    """Cria os dois seriesposters.zip sinteticos em `copy_root`."""
    wn, hn = sb.NORMAL_POSTER_SIZE
    wh, hh = sb.HIRES_POSTER_SIZE
    mold_n = make_synthetic_mold(wn, hn)
    mold_h = make_synthetic_mold(wh, hh)

    ger_n = sb.build_swatchbin(
        Image.fromarray(make_test_rgba(wn, hn, seed=1), "RGBA"), mold_n)
    ger_h = sb.build_swatchbin(
        Image.fromarray(make_test_rgba(wh, hh, seed=1), "RGBA"), mold_h)
    rew_n = sb.build_swatchbin(
        Image.fromarray(make_test_rgba(wn, hn, seed=2), "RGBA"), mold_n)
    rew_h = sb.build_swatchbin(
        Image.fromarray(make_test_rgba(wh, hh, seed=2), "RGBA"), mold_h)
    only_n = sb.build_swatchbin(
        Image.fromarray(make_test_rgba(wn, hn, seed=3), "RGBA"), mold_n)
    only_h = sb.build_swatchbin(
        Image.fromarray(make_test_rgba(wh, hh, seed=4), "RGBA"), mold_h)

    opaque_m21_n = b"\x5a\xa5\x11\xee" * 64
    opaque_m21_h = b"\x3c\xc3\x77\x88" * 96

    zip_n = make_synthetic_zip([
        ("bc_germanrivals.swatchbin", se.METHOD_DEFLATED, ger_n, 0, 0),
        ("untouched_m21.swatchbin", 21, opaque_m21_n, 512, 0x12345678),
        ("bc_reward_showcase_modern_001.swatchbin",
         se.METHOD_DEFLATED, rew_n, 0, 0),
        ("only_normal_poster.swatchbin", se.METHOD_DEFLATED, only_n, 0, 0),
    ])
    zip_h = make_synthetic_zip([
        ("bc_germanrivals.swatchbin", se.METHOD_DEFLATED, ger_h, 0, 0),
        ("untouched_m21.swatchbin", 21, opaque_m21_h, 512, 0x87654321),
        ("bc_reward_showcase_modern_001.swatchbin",
         se.METHOD_DEFLATED, rew_h, 0, 0),
        ("only_hires_poster.swatchbin", se.METHOD_DEFLATED, only_h, 0, 0),
    ])

    targets = se.zip_paths_of(copy_root)
    for kind, data in (("normal", zip_n), ("hires", zip_h)):
        os.makedirs(os.path.dirname(targets[kind]), exist_ok=True)
        se.put(targets[kind], data)
    return targets, {"normal": zip_n, "hires": zip_h}, {
        "ger_n": ger_n, "ger_h": ger_h, "rew_n": rew_n, "rew_h": rew_h,
    }


def mainmenu_tests(root, img_dir):
    """--archive mainmenu: so troca builderscup, no lugar, com imagem."""
    print("--archive mainmenu (banner do hub Corrida):")
    mm_root = os.path.join(root, "_work", "mm_copy")
    dims = {"normal": (1300, 480), "hires": (2600, 960)}
    zips = {}
    for kind in se.KINDS:
        w, h = dims[kind]
        mold = make_synthetic_mold(w, h)
        ents = []
        for i, name in enumerate(("mm_gorace_builderscup.swatchbin",
                                  "mm_gorace_rivals.swatchbin")):
            raw = sb.build_swatchbin(
                Image.fromarray(make_test_rgba(w, h, seed=40 + i), "RGBA"),
                mold)
            ents.append((name, se.METHOD_DEFLATED, raw, 0, 0))
        zips[kind] = make_synthetic_zip(ents)
    se.set_archive("mainmenu")
    paths = se.zip_paths_of(mm_root)
    se.set_archive("seriesposters")
    for kind in se.KINDS:
        expect(os.path.basename(paths[kind]) == "mainmenu.zip",
               "%s: alvo e mainmenu.zip" % kind)
        os.makedirs(os.path.dirname(paths[kind]), exist_ok=True)
        se.put(paths[kind], zips[kind])
    before = {k: se.sha256(zips[k]) for k in se.KINDS}
    img_n = os.path.join(img_dir, "mm_1300x480.png")
    img_h = os.path.join(img_dir, "mm_2600x960.png")
    Image.fromarray(make_test_rgba(1300, 480, seed=50), "RGBA").save(img_n)
    Image.fromarray(make_test_rgba(2600, 960, seed=51), "RGBA").save(img_h)
    base = ("--archive", "mainmenu", "--dest-copy", mm_root)
    def refused(*a):
        try:
            return capture(*a)[0] != 0
        except SystemExit:      # ap.error
            return True

    expect(refused(*(base + ("--replace", "mm_gorace_rivals", "--image",
                             img_n, "--image-hires", img_h, "--dry-run"))),
           "outro tile do menu (rivals) recusado")
    expect(refused(*(base + ("--add", "fco_x", "--image", img_n,
                             "--dry-run"))),
           "--add recusado com --archive mainmenu")
    args = base + ("--replace", "mm_gorace_builderscup", "--image", img_n,
                   "--image-hires", img_h)
    expect(run(*(args + ("--dry-run",))) == 0, "dry-run builderscup")
    expect(run(*(args + ("--verify",))) == 0, "apply + verify builderscup")
    for kind in se.KINDS:
        new = se.read(paths[kind])
        a, b = se.raw_slices(zips[kind]), se.raw_slices(new)
        expect(len(new) == len(zips[kind]) and list(a) == list(b),
               "%s: zip do mesmo tamanho e mesma lista" % kind)
        expect(a["mm_gorace_rivals.swatchbin"] ==
               b["mm_gorace_rivals.swatchbin"],
               "%s: rivals intacto byte a byte" % kind)
        expect(a["mm_gorace_builderscup.swatchbin"] !=
               b["mm_gorace_builderscup.swatchbin"],
               "%s: builderscup trocado" % kind)
    van = se.backup_dirs(se._backup_root(mm_root), se.VANILLA_PREFIX)
    expect(len(van) >= 1 and os.path.isfile(
        os.path.join(van[-1], "data_bound", "mainmenu.zip")) and
        os.path.isfile(os.path.join(van[-1], "hires", "data_bound",
                                    "mainmenu.zip")),
        "backup vanilla guarda os dois mainmenu.zip")
    expect(run("--archive", "mainmenu", "--dest-copy", mm_root,
               "--restore", van[-1]) == 0, "--restore do mainmenu")
    expect(all(se.sha256(se.read(paths[k])) == before[k] for k in se.KINDS),
           "restore devolve os shas vanilla do mainmenu")


def main():
    unit_swatchbin()

    root = tempfile.mkdtemp(prefix="swatchbin_test_")
    os.environ["_SE_TEST_ROOT"] = root
    se.WORK = os.path.join(root, "_work", "swatchbin_edit")
    se.INSTALL_BACKUP_ROOT = os.path.join(root, "_backup_install")
    fake_install = os.path.join(root, "fake_install")
    os.makedirs(fake_install, exist_ok=True)
    se.DEFAULT_INSTALL = fake_install
    se.ce.forza_processes = lambda tasklist_out=None: []

    copy_root = os.path.join(root, "_work", "swatch_copy")
    targets, orig_zips, payloads = build_synthetic_pair(copy_root)
    orig_shas = {k: se.sha256(orig_zips[k]) for k in se.KINDS}

    img_dir = os.path.join(root, "_work", "imgs")
    os.makedirs(img_dir, exist_ok=True)
    img_n_path = os.path.join(img_dir, "own_424x660.png")
    img_h_path = os.path.join(img_dir, "own_848x1320.png")
    img_sq_path = os.path.join(img_dir, "own_600x600.png")
    rgba_n = make_test_rgba(424, 660, seed=10)
    rgba_h = make_test_rgba(848, 1320, seed=20)
    Image.fromarray(rgba_n, "RGBA").save(img_n_path)
    Image.fromarray(rgba_h, "RGBA").save(img_h_path)
    Image.fromarray(make_test_rgba(600, 600, seed=30), "RGBA").save(img_sq_path)

    print("travas de destino e pre-condicoes:")
    expect(run("--install", fake_install, "--replace", "BC_GermanRivals",
               "--from-entry", "BC_Reward_Showcase_Modern_001",
               "--dry-run") == 1,
           "operacao sem --dest-copy e sem --allow-install recusada")
    expect(run("--install", fake_install, "--dest-copy", fake_install,
               "--replace", "BC_GermanRivals",
               "--from-entry", "BC_Reward_Showcase_Modern_001",
               "--dry-run") == 1,
           "--dest-copy apontando para o install recusado")
    expect(run("--dest-copy", copy_root, "--allow-install",
               "--replace", "BC_GermanRivals",
               "--from-entry", "BC_Reward_Showcase_Modern_001",
               "--dry-run") == 1,
           "--dest-copy + --allow-install juntos recusados")

    print("degrau 1 (--replace --from-entry):")
    args_d1 = ("--dest-copy", copy_root, "--replace", "BC_GermanRivals",
               "--from-entry", "BC_Reward_Showcase_Modern_001")
    expect(run(*(args_d1 + ("--verify",))) == 1,
           "apply sem --dry-run recusado")
    expect(all(se.sha256(se.read(targets[k])) == orig_shas[k]
               for k in se.KINDS), "zips intactos apos recusa")
    expect(run(*(args_d1 + ("--dry-run",))) == 0, "dry-run degrau 1")
    expect(all(se.sha256(se.read(targets[k])) == orig_shas[k]
               for k in se.KINDS), "dry-run nao escreve nos zips")

    se.ce.forza_processes = lambda tasklist_out=None: ["ForzaMotorsport.exe"]
    expect(run(*(args_d1 + ("--verify",))) == 1,
           "apply com jogo aberto recusado")
    se.ce.forza_processes = lambda tasklist_out=None: []

    expect(run(*(args_d1 + ("--verify",))) == 0,
           "apply + verify degrau 1")
    expect(not os.path.exists(se.INSTALL_BACKUP_ROOT),
           "nenhum byte escrito em _backup do install durante --dest-copy")

    for kind, want_rew in (("normal", payloads["rew_n"]),
                           ("hires", payloads["rew_h"])):
        edited = se.read(targets[kind])
        expect(se.sha256(edited) != orig_shas[kind],
               "%s: zip mudou apos degrau 1" % kind)
        a, b = se.raw_slices(orig_zips[kind]), se.raw_slices(edited)
        same = [n for n in a if n != "bc_germanrivals.swatchbin"]
        expect(list(a) == list(b) and all(a[n] == b[n] for n in same),
               "%s: %d entradas intocadas (incl. metodo 21) byte a byte iguais"
               % (kind, len(same)))
        with zipfile.ZipFile(targets[kind]) as zf:
            expect(zf.read("bc_germanrivals.swatchbin") == want_rew,
                   "%s: bc_germanrivals recebeu os bytes de reward_showcase"
                   % kind)
            expect(zf.comment == b"FCO_SYNTH",
                   "%s: comentario do zip preservado" % kind)

    for kind in se.KINDS:
        edited = se.read(targets[kind])
        offs_a = [i.header_offset for i in se.list_infos(orig_zips[kind])[0]]
        offs_b = [i.header_offset for i in se.list_infos(edited)[0]]
        expect(len(edited) == len(orig_zips[kind]),
               "%s: tamanho do zip igual (trocar no lugar)" % kind)
        expect(offs_a == offs_b and all(o % 4096 == 0 for o in offs_b),
               "%s: todos os offsets iguais e alinhados a 4096" % kind)
    big = se.raw_slices(orig_zips["normal"])["bc_germanrivals.swatchbin"]
    try:
        se.rebuild_zip_inplace(orig_zips["normal"],
                               "untouched_m21.swatchbin", big * 4, 8, 0, 0)
        expect(False, "conteudo maior que a vaga recusado")
    except se.SeError:
        expect(True, "conteudo maior que a vaga recusado (nao move nada)")

    expect(run(*(args_d1 + ("--verify",))) == 1,
           "segundo apply sem novo dry-run recusado")
    expect(run(*(args_d1 + ("--dry-run",))) == 1,
           "repetir mesmo from-entry quando ja igual recusado (nada a fazer)")

    print("degrau 2 (--replace --image):")
    expect(run("--dest-copy", copy_root, "--replace", "BC_GermanRivals",
               "--image", img_n_path, "--dry-run") == 1,
           "--image unica 424x660 sem --image-hires e sem --fit recusada")
    expect(run("--dest-copy", copy_root, "--replace", "BC_GermanRivals",
               "--image", img_sq_path, "--dry-run") == 1,
           "--image 600x600 sem --fit recusada")

    args_d2 = ("--dest-copy", copy_root, "--replace", "BC_GermanRivals",
               "--image", img_n_path, "--image-hires", img_h_path)
    expect(run(*(args_d2 + ("--dry-run",))) == 0, "dry-run degrau 2")
    expect(run(*(args_d2 + ("--verify",))) == 0, "apply + verify degrau 2")

    for kind, src_rgba, dim in (("normal", rgba_n, (424, 660)),
                                ("hires", rgba_h, (848, 1320))):
        edited = se.read(targets[kind])
        a, b = se.raw_slices(orig_zips[kind]), se.raw_slices(edited)
        same = [n for n in a if n != "bc_germanrivals.swatchbin"]
        expect(all(a[n] == b[n] for n in same),
               "%s: entradas intocadas seguem verbatim no degrau 2" % kind)
        with zipfile.ZipFile(targets[kind]) as zf:
            got = zf.read("bc_germanrivals.swatchbin")
        expect(len(got) == sb.HEADER_SIZE + dim[0] * dim[1],
               "%s: tamanho 144 + w*h (%d B)" % (kind, len(got)))
        dec = decode_bc7_mode6_ref(got[sb.HEADER_SIZE:], dim[0], dim[1])
        rmse = float(np.sqrt(np.mean(
            (src_rgba.astype(np.float32) - dec.astype(np.float32)) ** 2)))
        expect(rmse < 2.5,
               "%s: imagem decodificada do zip bate com a original (RMSE=%.3f)"
               % (kind, rmse))

    if se._m21_reader().available:
        args_lzx = args_d2 + ("--codec", "lzx")
        expect(run(*(args_lzx + ("--dry-run",))) == 0, "dry-run degrau 2 LZX")
        expect(run(*(args_lzx + ("--verify",))) == 0,
               "apply + verify degrau 2 LZX (metodo 21, no lugar)")
        for kind in se.KINDS:
            edited = se.read(targets[kind])
            info = se.info_map(se.list_infos(edited)[0])[
                "bc_germanrivals.swatchbin"]
            expect(info.compress_type == 21 and
                   len(edited) == len(orig_zips[kind]),
                   "%s: entrada em metodo 21, tamanho do zip igual" % kind)
            with se._EntryReader() as rd:
                got = rd.read(targets[kind], info)
            expect(len(got) == sb.HEADER_SIZE + (424 * 660 if kind == "normal"
                                                 else 848 * 1320),
                   "%s: LZX le de volta com 144 + w*h bytes" % kind)
    else:
        print("  (sem DLL: teste LZX pulado)")

    # Teste tambem de --replace --image unica com --fit
    args_fit = ("--dest-copy", copy_root, "--replace", "BC_GermanRivals",
                "--image", img_sq_path, "--fit")
    expect(run(*(args_fit + ("--dry-run",))) == 0, "dry-run degrau 2 com --fit")
    expect(run(*(args_fit + ("--verify",))) == 0,
           "apply + verify degrau 2 com --fit")

    print("degrau 3 (--add --image):")
    args_d3 = ("--dest-copy", copy_root, "--add", "FCO_Test_001",
               "--image", img_n_path, "--image-hires", img_h_path)
    expect(run(*(args_d3 + ("--dry-run",))) == 0, "dry-run degrau 3")
    expect(run(*(args_d3 + ("--verify",))) == 0, "apply + verify degrau 3")

    for kind, dim in (("normal", (424, 660)), ("hires", (848, 1320))):
        edited = se.read(targets[kind])
        a, b = se.raw_slices(orig_zips[kind]), se.raw_slices(edited)
        expect(list(b) == list(a) + ["fco_test_001.swatchbin"],
               "%s: fco_test_001.swatchbin anexada no fim" % kind)
        for n in a:
            if n != "bc_germanrivals.swatchbin":
                expect(b[n] == a[n],
                       "%s: %s intocada preserva bytes comprimidos" % (kind, n))
        with zipfile.ZipFile(targets[kind]) as zf:
            ni = zf.getinfo("fco_test_001.swatchbin")
            fid, fsz, doff = struct.unpack("<HHI", ni.extra[:8])
            expect(fid == 0x1123 and fsz == 4 and doff == ni.header_offset
                   + 30 + len(ni.filename.encode()) and
                   ni.header_offset % 4096 == 0 and zf.start_dir % 4096 == 0,
                   "%s: entrada nova alinhada, extra 0x1123 com o offset dos "
                   "dados, diretorio central alinhado" % kind)
            got = zf.read("fco_test_001.swatchbin")
            expect(len(got) == sb.HEADER_SIZE + dim[0] * dim[1],
                   "%s: fco_test_001 tem 144 + w*h bytes" % kind)
            expect(zf.comment == b"FCO_SYNTH",
                   "%s: comentario do zip preservado no --add" % kind)

    for wh in ((424, 660), (848, 1320), (380, 100), (760, 200)):
        hdr = sb.make_header(*wh)
        expect(len(hdr) == sb.HEADER_SIZE and
               sb.validate_mold(hdr, expected_size=wh)[1] == wh,
               "cabecalho gerado %dx%d valido (sem arquivo do jogo)" % wh)

    print("manifesto (lote de entradas + remocao):")
    man = os.path.join(copy_root, "posters.json")
    with open(man, "w", encoding="utf-8") as fh:
        json.dump({"codec": "deflate",
                   "add": [{"name": "FCO_Batch_A", "image": img_n_path,
                            "image_hires": img_h_path},
                           {"name": "FCO_Batch_B", "image": img_n_path,
                            "image_hires": img_h_path}]}, fh)
    expect(run("--dest-copy", copy_root, "--manifest", man, "--dry-run") == 0,
           "dry-run do manifesto (2 entradas)")
    expect(run("--dest-copy", copy_root, "--manifest", man, "--verify") == 0,
           "apply + verify do manifesto (2 entradas)")
    expect(run("--dest-copy", copy_root, "--manifest", man, "--dry-run") == 1,
           "manifesto ja aplicado: nada a fazer")
    with open(man, "w", encoding="utf-8") as fh:
        json.dump({"codec": "deflate",
                   "add": [{"name": "FCO_Batch_B", "image": img_n_path,
                            "image_hires": img_h_path}],
                   "remove": ["FCO_Batch_A"]}, fh)
    before = {k: se.read(targets[k]) for k in se.KINDS}
    expect(run("--dest-copy", copy_root, "--manifest", man, "--dry-run") == 0,
           "dry-run da remocao (B ja igual, A sai)")
    expect(run("--dest-copy", copy_root, "--manifest", man, "--verify") == 0,
           "apply + verify da remocao")
    for kind in se.KINDS:
        now = se.read(targets[kind])
        old_i = se.info_map(se.list_infos(before[kind])[0])
        new_i = se.info_map(se.list_infos(now)[0])
        expect("fco_batch_a.swatchbin" not in new_i and
               "fco_batch_b.swatchbin" in new_i and
               se.list_infos(now)[0] and
               zipfile.ZipFile(io.BytesIO(now)).start_dir ==
               zipfile.ZipFile(io.BytesIO(before[kind])).start_dir,
               "%s: A removida, B fica, diretorio central no mesmo lugar"
               % kind)
        expect(all(new_i[n].header_offset == old_i[n].header_offset
                   for n in old_i if n != "fco_batch_a.swatchbin"),
               "%s: entradas que ficam nao mudam de lugar" % kind)
        expect(all(i.header_offset % 4096 == 0 for i in new_i.values()),
               "%s: tudo na grade de 4096" % kind)
    with open(man, "w", encoding="utf-8") as fh:
        json.dump({"remove": ["BC_GermanRivals"]}, fh)
    expect(run("--dest-copy", copy_root, "--manifest", man, "--dry-run") == 1,
           "manifesto recusa remover entrada vanilla")

    print("recusas (nomes, par normal/hires, estado, dry-run, backup):")
    expect(run(*(args_d3 + ("--dry-run",))) == 1,
           "--add de nome que ja existe recusado")
    expect(run("--dest-copy", copy_root, "--replace", "Nao_Existe_999",
               "--from-entry", "BC_Reward_Showcase_Modern_001",
               "--dry-run") == 1,
           "--replace de nome inexistente recusado")
    expect(run("--dest-copy", copy_root, "--replace", "BC_GermanRivals",
               "--from-entry", "Nao_Existe_999",
               "--dry-run") == 1,
           "--from-entry inexistente recusado")
    expect(run("--dest-copy", copy_root, "--replace", "only_normal_poster",
               "--from-entry", "BC_Reward_Showcase_Modern_001",
               "--dry-run") == 1,
           "--replace de entrada sem par em hires recusado")
    expect(run("--dest-copy", copy_root, "--replace", "BC_GermanRivals",
               "--from-entry", "only_hires_poster",
               "--dry-run") == 1,
           "--from-entry sem par em normal recusado")
    expect(run("--dest-copy", copy_root, "--add", "only_normal_poster",
               "--image", img_n_path, "--image-hires", img_h_path,
               "--dry-run") == 1,
           "--add de nome que ja existe em um dos zips recusado")
    for bad_name in ("sub/dir", "../escape", "poster.png", ""):
        try:
            se.normalize_entry_name(bad_name)
            expect(False, "nome invalido %r recusado" % bad_name)
        except se.SeError:
            expect(True, "nome invalido %r recusado" % bad_name)

    # Dry-run expirado (> 30 min)
    expect(run("--dest-copy", copy_root, "--add", "FCO_Test_002",
               "--image", img_n_path, "--image-hires", img_h_path,
               "--dry-run") == 0, "dry-run para testar expiracao")
    for fn in os.listdir(se._dryrun_dir()):
        p = os.path.join(se._dryrun_dir(), fn)
        data = json.loads(open(p, encoding="utf-8").read())
        data["time"] -= 45 * 60
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
    expect(run("--dest-copy", copy_root, "--add", "FCO_Test_002",
               "--image", img_n_path, "--image-hires", img_h_path,
               "--verify") == 1, "dry-run expirado recusado")

    # Imagem alterada apos --dry-run recusada
    expect(run("--dest-copy", copy_root, "--add", "FCO_Test_002",
               "--image", img_n_path, "--image-hires", img_h_path,
               "--dry-run") == 0, "dry-run antes de alterar imagem")
    Image.fromarray(make_test_rgba(424, 660, seed=99), "RGBA").save(img_n_path)
    expect(run("--dest-copy", copy_root, "--add", "FCO_Test_002",
               "--image", img_n_path, "--image-hires", img_h_path,
               "--verify") == 1,
           "apply com imagem alterada apos --dry-run recusado")
    Image.fromarray(rgba_n, "RGBA").save(img_n_path)

    # Trava de estado (adulterar so 1 dos 2 zips)
    saved_hires = se.read(targets["hires"])
    tampered = bytearray(saved_hires)
    tampered[-25] ^= 0xFF
    se.put(targets["hires"], bytes(tampered))
    expect(run(*(args_d1 + ("--dry-run",))) == 1,
           "zip hires adulterado fora do vanilla/ultimo escrito recusado")
    se.put(targets["hires"], saved_hires)

    # Verify sem backup vanilla recusado
    class DummyArgs:
        install = fake_install
        dest_copy = copy_root
        allow_install = False
        replace = "BC_GermanRivals"
        add = None
        from_entry = "BC_Reward_Showcase_Modern_001"
        image = None
        image_hires = None
        fit = False

    r_plan = se.plan(DummyArgs())
    r_plan["backup_root"] = os.path.join(root, "_work", "sem_vanilla")
    try:
        se.verify(r_plan)
        expect(False, "verify sem backup vanilla recusado")
    except se.SeError as exc:
        expect("sem backup vanilla" in str(exc),
               "verify sem backup vanilla recusado")

    print("restore e conferencia do backup vanilla:")
    broot = se._backup_root(copy_root)
    van_backups = se.backup_dirs(broot, se.VANILLA_PREFIX)
    inc_backups = se.backup_dirs(broot, se.INCREMENTAL_PREFIX)
    expect(len(van_backups) == 1,
           "exatamente 1 backup vanilla criado (%s)"
           % os.path.basename(van_backups[0]))
    expect(len(inc_backups) >= 3,
           "backups incrementais criados nas escritas seguintes (%d)"
           % len(inc_backups))

    expect(run("--dest-copy", copy_root, "--restore", van_backups[0]) == 0,
           "--restore do backup vanilla")
    for kind in se.KINDS:
        restored = se.read(targets[kind])
        expect(se.sha256(restored) == orig_shas[kind],
               "%s: restore devolve o sha256 vanilla exato" % kind)
        expect("fco_test_001.swatchbin" not in se.raw_slices(restored),
               "%s: entrada adicionada sumiu apos restore" % kind)
    expect(run("--dest-copy", copy_root, "--restore", van_backups[0]) == 0,
           "--restore repetido e idempotente")
    expect(all(se.sha256(se.read(targets[k])) == orig_shas[k]
               for k in se.KINDS),
           "shas continuam identicos ao vanilla apos 2o restore")

    mainmenu_tests(root, img_dir)

    shutil.rmtree(root, ignore_errors=True)
    os.environ.pop("_SE_TEST_ROOT", None)
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
