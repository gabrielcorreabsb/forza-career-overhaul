#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""swatchbin.py - gerador e validador de texturas .swatchbin (BC7, 1 mip).

Gera um arquivo .swatchbin de `144 + largura * altura` bytes a partir de uma
imagem (PNG/etc.) usando o cabecalho de 144 bytes de uma entrada vanilla do
mesmo tamanho como molde e codificando os pixels em BC7 modo 6 (1 subconjunto,
p-bits individuais por endpoint, 4 bits de indice por texel).

Uso avulso (saida restrita a `_work` ou pasta temporaria):
  python _tools\\swatchbin.py --image poster.png --mold molde.swatchbin ^
      --out _work\\saida.swatchbin [--fit]
"""

import argparse
import io
import os
import struct
import sys
import tempfile

import numpy as np
from PIL import Image

HEADER_SIZE = 144
TEX_OFFSET = 52  # P em docs/reference/SWATCHBIN.md
ENCODING_BC7 = 9
NORMAL_POSTER_SIZE = (424, 660)
HIRES_POSTER_SIZE = (848, 1320)

W4 = np.array([0, 4, 9, 13, 17, 21, 26, 30, 34, 38, 43, 47, 51, 55, 60, 64],
              dtype=np.int32)

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SwatchbinError(Exception):
    pass


def parse_header(buf):
    """Valida o cabecalho de 144 bytes segundo SWATCHBIN.md e devolve metadados."""
    if len(buf) < HEADER_SIZE:
        raise SwatchbinError("cabecalho curto demais: %d B (minimo %d)"
                             % (len(buf), HEADER_SIZE))
    if buf[0:4] != b"burG":
        raise SwatchbinError("magic invalido: %r (esperado b'burG')" % buf[0:4])
    if struct.unpack_from("<BB", buf, 4) != (1, 1):
        raise SwatchbinError("versao do bundle inesperada: %r"
                             % (struct.unpack_from("<BB", buf, 4),))
    blob_count = struct.unpack_from("<I", buf, 16)[0]
    if blob_count != 1:
        raise SwatchbinError("blob count inesperado: %d (esperado 1)"
                             % blob_count)
    if buf[20:24] != b"BCXT":
        raise SwatchbinError("blob tag invalido: %r" % buf[20:24])
    if struct.unpack_from("<BB", buf, 24) != (0, 0):
        raise SwatchbinError("versao do blob inesperada: %r"
                             % (struct.unpack_from("<BB", buf, 24),))
    meta_count = struct.unpack_from("<H", buf, 26)[0]
    if meta_count != 1:
        raise SwatchbinError("metadata count inesperado: %d" % meta_count)
    pixel_offset = struct.unpack_from("<I", buf, 32)[0]
    if pixel_offset != HEADER_SIZE:
        raise SwatchbinError("offset dos pixels inesperado: %d (esperado %d)"
                             % (pixel_offset, HEADER_SIZE))
    if buf[44:48] != b"HCXT":
        raise SwatchbinError("metadata tag invalido: %r" % buf[44:48])

    p = TEX_OFFSET
    width, height, depth = struct.unpack_from("<III", buf, p + 24)
    if width <= 0 or height <= 0 or depth != 1:
        raise SwatchbinError("dimensoes invalidas: %dx%dx%d"
                             % (width, height, depth))
    sp = struct.unpack_from("<H", buf, p + 36)[0]
    slice_count = sp & 0x3FFF
    platform = sp >> 14
    if slice_count != 1 or platform != 0:
        raise SwatchbinError("slice_count=%d platform=%d inesperados"
                             % (slice_count, platform))
    mip_count = buf[p + 38]
    flags = buf[p + 39]
    if mip_count != 1 or flags != 0:
        raise SwatchbinError("mip_count=%d flags=%d inesperados"
                             % (mip_count, flags))
    if buf[p + 40:p + 56] != b"\x00" * 16:
        raise SwatchbinError("transcoding/perfis/dominio nao-zero no cabecalho")

    slice_rel = struct.unpack_from("<I", buf, p + 56)[0]
    if not (0 <= p + slice_rel <= HEADER_SIZE - 8):
        raise SwatchbinError("slice_rel fora do cabecalho: %d" % slice_rel)
    encoding, mip_rel = struct.unpack_from("<II", buf, p + slice_rel)
    if encoding != ENCODING_BC7:
        raise SwatchbinError("encoding %d nao e BC7 (%d)"
                             % (encoding, ENCODING_BC7))
    if not (0 <= p + mip_rel <= HEADER_SIZE - 4):
        raise SwatchbinError("mip_rel fora do cabecalho: %d" % mip_rel)
    mip_size = struct.unpack_from("<I", buf, p + mip_rel)[0]
    if mip_size != width * height:
        raise SwatchbinError("mip_size=%d difere de width*height=%d"
                             % (mip_size, width * height))

    return {
        "width": width,
        "height": height,
        "depth": depth,
        "encoding": encoding,
        "mip_size": mip_size,
        "pixel_offset": pixel_offset,
    }


def validate_mold(mold_bytes, expected_size=None):
    """Valida um .swatchbin completo ou cabecalho de 144 B e devolve (hdr144, (w, h))."""
    meta = parse_header(mold_bytes)
    w, h = meta["width"], meta["height"]
    if len(mold_bytes) not in (HEADER_SIZE, HEADER_SIZE + w * h):
        raise SwatchbinError("tamanho do molde %d B difere de %d ou %d B"
                             % (len(mold_bytes), HEADER_SIZE,
                                HEADER_SIZE + w * h))
    if w % 4 != 0 or h % 4 != 0:
        raise SwatchbinError("dimensoes %dx%d nao sao multiplas de 4 para BC7"
                             % (w, h))
    if expected_size is not None and (w, h) != tuple(expected_size):
        raise SwatchbinError("molde %dx%d difere do tamanho esperado %dx%d"
                             % (w, h, expected_size[0], expected_size[1]))
    return bytes(mold_bytes[:HEADER_SIZE]), (w, h)


def fit_cover_rgba(im, target_w, target_h):
    """Converte para RGBA e ajusta por escala 'cover' + recorte central."""
    im = im.convert("RGBA")
    src_w, src_h = im.size
    if (src_w, src_h) == (target_w, target_h):
        return im
    scale = max(target_w / src_w, target_h / src_h)
    new_w = max(target_w, int(round(src_w * scale)))
    new_h = max(target_h, int(round(src_h * scale)))
    resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return resized.crop((left, top, left + target_w, top + target_h))


def encode_bc7_mode6(rgba):
    """Codifica um array RGBA uint8 (H, W, 4) em blocos BC7 modo 6."""
    if rgba.ndim != 3 or rgba.shape[2] != 4:
        raise SwatchbinError("array RGBA invalido: shape=%r" % (rgba.shape,))
    h, w, _ = rgba.shape
    if w <= 0 or h <= 0 or (w % 4) != 0 or (h % 4) != 0:
        raise SwatchbinError("dimensoes %dx%d invalidas para BC7" % (w, h))

    blocks = (rgba.reshape(h // 4, 4, w // 4, 4, 4)
              .transpose(0, 2, 1, 3, 4)
              .reshape(-1, 16, 4))
    bf = blocks.astype(np.float32)
    bi = blocks.astype(np.int32)
    n_blocks = blocks.shape[0]

    mu = bf.mean(axis=1, keepdims=True)
    centered = bf - mu
    far = np.argmax(np.sum(centered * centered, axis=2), axis=1)
    d = centered[np.arange(n_blocks), far]
    for _ in range(4):
        proj = np.einsum("nij,nj->ni", centered, d)
        dn = np.einsum("ni,nij->nj", proj, centered)
        norm = np.linalg.norm(dn, axis=1, keepdims=True)
        d = np.where(norm > 1e-6, dn / np.maximum(norm, 1e-6), d)
    norm = np.linalg.norm(d, axis=1, keepdims=True)
    d = np.where(norm > 1e-6, d / np.maximum(norm, 1e-6), 0.0)
    proj = np.einsum("nij,nj->ni", centered, d)
    e0_f = np.clip(mu[:, 0, :] + proj.min(axis=1, keepdims=True) * d,
                   0.0, 255.0)
    e1_f = np.clip(mu[:, 0, :] + proj.max(axis=1, keepdims=True) * d,
                   0.0, 255.0)

    best_err = np.full(n_blocks, 1 << 60, dtype=np.int64)
    best_c0 = np.zeros((n_blocks, 4), dtype=np.uint64)
    best_c1 = np.zeros((n_blocks, 4), dtype=np.uint64)
    best_p0 = np.zeros(n_blocks, dtype=np.uint64)
    best_p1 = np.zeros(n_blocks, dtype=np.uint64)
    best_idx = np.zeros((n_blocks, 16), dtype=np.uint64)

    for p0 in (0, 1):
        c0 = np.clip(np.rint((e0_f - p0) * 0.5), 0, 127).astype(np.int32)
        e0 = (c0 << 1) | p0
        for p1 in (0, 1):
            c1 = np.clip(np.rint((e1_f - p1) * 0.5), 0, 127).astype(np.int32)
            e1 = (c1 << 1) | p1
            diff = (e1 - e0).astype(np.float32)
            denom = np.sum(diff * diff, axis=1, keepdims=True)
            t = (np.sum((bf - e0[:, None, :]) * diff[:, None, :], axis=2)
                 / np.maximum(denom, 1e-6))
            idx = np.clip(np.rint(np.clip(t, 0.0, 1.0) * 15.0),
                          0, 15).astype(np.int32)
            w_arr = W4[idx][:, :, None]
            rec = ((64 - w_arr) * e0[:, None, :]
                   + w_arr * e1[:, None, :] + 32) >> 6
            err = np.sum((bi - rec) ** 2, axis=(1, 2), dtype=np.int64)
            better = err < best_err
            if np.any(better):
                best_err[better] = err[better]
                best_c0[better] = c0[better].astype(np.uint64)
                best_c1[better] = c1[better].astype(np.uint64)
                best_p0[better] = p0
                best_p1[better] = p1
                best_idx[better] = idx[better].astype(np.uint64)

    flip = best_idx[:, 0] >= 8
    if np.any(flip):
        best_c0[flip], best_c1[flip] = (best_c1[flip].copy(),
                                        best_c0[flip].copy())
        best_p0[flip], best_p1[flip] = (best_p1[flip].copy(),
                                        best_p0[flip].copy())
        best_idx[flip] = 15 - best_idx[flip]

    lo = (np.uint64(0x40)
          | (best_c0[:, 0] << np.uint64(7))
          | (best_c1[:, 0] << np.uint64(14))
          | (best_c0[:, 1] << np.uint64(21))
          | (best_c1[:, 1] << np.uint64(28))
          | (best_c0[:, 2] << np.uint64(35))
          | (best_c1[:, 2] << np.uint64(42))
          | (best_c0[:, 3] << np.uint64(49))
          | (best_c1[:, 3] << np.uint64(56))
          | (best_p0 << np.uint64(63)))
    hi = best_p1 | ((best_idx[:, 0] & np.uint64(7)) << np.uint64(1))
    for k in range(1, 16):
        hi |= (best_idx[:, k] & np.uint64(15)) << np.uint64(4 * k)

    out = np.empty((n_blocks, 2), dtype="<u8")
    out[:, 0] = lo
    out[:, 1] = hi
    return out.tobytes()


def _open_rgba(image_or_path):
    if isinstance(image_or_path, Image.Image):
        return image_or_path.convert("RGBA")
    if isinstance(image_or_path, (bytes, bytearray, memoryview)):
        with Image.open(io.BytesIO(image_or_path)) as raw:
            return raw.convert("RGBA")
    try:
        with Image.open(image_or_path) as raw:
            return raw.convert("RGBA")
    except OSError as exc:
        raise SwatchbinError("nao foi possivel abrir imagem %r: %s"
                             % (image_or_path, exc)) from None


def make_header(w, h):
    """Cabecalho de 144 B de uma textura BC7 de 1 fatia e 1 mip, no layout de
    docs/reference/SWATCHBIN.md. Nos arquivos de poster e banner do jogo o
    cabecalho so depende de largura e altura (um cabecalho por tamanho); este
    gera o mesmo sem precisar ler um arquivo do jogo (sem o runtime LZX)."""
    if w <= 0 or h <= 0 or w % 4 or h % 4:
        raise SwatchbinError("tamanho %dx%d invalido (multiplo de 4)" % (w, h))
    pix = w * h                                   # BC7: 1 byte por pixel
    b = bytearray(HEADER_SIZE)
    b[0:4] = b"burG"                              # bundle
    struct.pack_into("<BB", b, 4, 1, 1)           # versao 1.1
    struct.pack_into("<II", b, 8, HEADER_SIZE, HEADER_SIZE + pix)
    struct.pack_into("<I", b, 16, 1)              # 1 blob
    b[20:24] = b"BCXT"                            # blob de textura
    struct.pack_into("<HHII", b, 24, 0, 1, 0x2C, HEADER_SIZE)
    struct.pack_into("<II", b, 36, pix, pix)
    b[44:48] = b"HCXT"                            # metadado
    struct.pack_into("<III", b, 48, 0x00080580, 0x38, 0x50)
    p = TEX_OFFSET
    struct.pack_into("<B", b, p + 23, 1)
    struct.pack_into("<III", b, p + 24, w, h, 1)  # largura, altura, profundidade
    struct.pack_into("<HB", b, p + 36, 1, 1)      # 1 fatia, 1 mip
    struct.pack_into("<II", b, p + 56, 0x40, 0x44)  # fatia, mip (de P)
    struct.pack_into("<II", b, p + 64, 9, 0x4C)   # encoding 9 = BC7
    struct.pack_into("<IIIII", b, p + 72, 0xFFFFFFFF, pix, 0, 0xFFFFFFFF, 0)
    return bytes(b)


def build_swatchbin(image_or_path, mold_bytes=None, expected_size=None,
                    fit=False):
    """Gera bytes de .swatchbin (144 + w*h). `mold_bytes`: cabecalho de um
    arquivo do jogo como molde; sem ele, `make_header(expected_size)`."""
    if mold_bytes is None:
        if expected_size is None:
            raise SwatchbinError("sem molde: informe expected_size")
        mold_bytes = make_header(*expected_size)
    hdr144, (w, h) = validate_mold(mold_bytes, expected_size=expected_size)
    im = _open_rgba(image_or_path)
    if im.size != (w, h):
        if not fit:
            raise SwatchbinError(
                "tamanho da imagem %dx%d difere do alvo %dx%d "
                "(use --fit para cobrir e cortar)"
                % (im.size[0], im.size[1], w, h))
        im = fit_cover_rgba(im, w, h)
    payload = encode_bc7_mode6(np.asarray(im, dtype=np.uint8))
    result = hdr144 + payload
    if len(result) != HEADER_SIZE + w * h:
        raise SwatchbinError("tamanho gerado %d B difere de %d B"
                             % (len(result), HEADER_SIZE + w * h))
    return result


def _is_under(path, parent):
    abs_p = os.path.normcase(os.path.abspath(path))
    abs_parent = os.path.normcase(os.path.abspath(parent))
    try:
        return os.path.commonpath([abs_p, abs_parent]) == abs_parent
    except ValueError:
        return False


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="swatchbin.py",
        description="gera .swatchbin BC7 a partir de imagem + molde de 144 B")
    ap.add_argument("--image", required=True, help="imagem de entrada (PNG/etc.)")
    ap.add_argument("--mold", required=True, help="arquivo .swatchbin molde")
    ap.add_argument("--out", required=True, help="arquivo .swatchbin de saida")
    ap.add_argument("--fit", action="store_true",
                    help="redimensiona (cover) e corta ao centro para o alvo")
    args = ap.parse_args(argv)
    try:
        work_root = os.path.join(_ROOT, "_work")
        tmp_root = tempfile.gettempdir()
        if not (_is_under(args.out, work_root) or _is_under(args.out, tmp_root)):
            raise SwatchbinError(
                "saida recusada fora de _work ou temp: %s" % args.out)
        with open(args.mold, "rb") as fh:
            mold = fh.read()
        data = build_swatchbin(args.image, mold, fit=args.fit)
        out_dir = os.path.dirname(os.path.abspath(args.out))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(args.out, "wb") as fh:
            fh.write(data)
        meta = parse_header(data)
        print("OK: %s (%dx%d, %d B)"
              % (args.out, meta["width"], meta["height"], len(data)))
        return 0
    except (SwatchbinError, OSError) as exc:
        print("ERRO: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
