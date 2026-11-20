#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""encode_intro.py - de um MP4 a um video de introducao FCO_* instalado e indexado.

Um comando faz o fluxo inteiro (D105-D117):
  1. codifica o MP4 em Bink 2 revisao KB2j, uma saida por pasta do install
     (1920x1080 e 3840x2160), com o preset padrao do projeto;
  2. confere o cabecalho (KB2j) de cada saida;
  3. instala os dois arquivos NOVOS (um nome que ja existe e recusado: nunca
     reescreve um video existente) como media\\base\\ui\\videos\\{1080,2160}\\fco_<nome>.bk2
     (mesma logica do bk2_install.py --add);
  4. acrescenta os dois registros ao media\\base\\hash.manifest
     (hash_manifest_edit.py), com o valor de um video vanilla de referencia
     (padrao 3d_carselect_vw, 16:9); um registro que ja existe e mantido.

Preset (D114-D118): video `-c:v bink2video -pix_fmt yuv420p -quant 8`
(`--hq` = quant 6; quanto menor, mais fino e maior); audio, se o MP4 tiver,
`-c:a binkaudio_dct -ac 2 -ar 48000 -quality:a 10` (`--no-audio` tira).
O codificador e um ffmpeg com `bink2video` (MobiPeg, AGPL-3.0): informe o
caminho em --ffmpeg ou em FM_FFMPEG_BK2; o binario nunca entra no repositorio.

Travas: dry-run por padrao (--apply grava); jogo fechado; nome FCO_<letras,
digitos, _>; entrada 16:9; as travas do bk2_install.py e do hash_manifest_edit.py
continuam valendo (cada uma faz o proprio backup).

Uso:
  python _tools\\encode_intro.py --mp4 meu_clipe.mp4 --name FCO_MyIntro --ffmpeg C:\\...\\ffmpeg.exe
  python _tools\\encode_intro.py --mp4-1080 a.mp4 --mp4-2160 b.mp4 --name FCO_MyIntro --apply
  (depois, na spec da rodada: IntroVideoPath FCO_MyIntro.bk2, PlayIntroVideoFullScreen true,
   FirstCarSelectEnabled false, FirstCarSelectCars [])
"""

import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bk2_install as bk  # noqa: E402
import cache_edit as ce  # noqa: E402
import hash_manifest_edit as hm  # noqa: E402

NAME_RE = re.compile(r"^FCO_[A-Za-z0-9_]+$")
QUANT_DEFAULT = 8
QUANT_HQ = 6
OUT = {"1080": (1920, 1080), "2160": (3840, 2160)}


class EnError(Exception):
    pass


def ffprobe_path(ffmpeg):
    d, n = os.path.split(ffmpeg)
    cand = os.path.join(d, n.lower().replace("ffmpeg", "ffprobe"))
    return cand if os.path.isfile(cand) else None


def probe(ffmpeg, mp4):
    fp = ffprobe_path(ffmpeg)
    if not fp:
        raise EnError("ffprobe nao esta ao lado do ffmpeg: %s" % ffmpeg)
    r = subprocess.run([fp, "-v", "error", "-show_entries",
                        "stream=codec_type,width,height,r_frame_rate",
                        "-of", "json", mp4], capture_output=True, text=True)
    if r.returncode:
        raise EnError("ffprobe falhou em %s: %s" % (mp4, r.stderr.strip()))
    info = json.loads(r.stdout).get("streams", [])
    v = [s for s in info if s.get("codec_type") == "video"]
    if not v:
        raise EnError("sem video: %s" % mp4)
    return v[0]["width"], v[0]["height"], any(s.get("codec_type") == "audio" for s in info)


def encode(ffmpeg, mp4, res, quant, audio, out_path):
    w, h = OUT[res]
    cmd = [ffmpeg, "-hide_banner", "-v", "error", "-y", "-i", mp4,
           "-vf", "scale=%d:%d:flags=lanczos" % (w, h),
           "-c:v", "bink2video", "-pix_fmt", "yuv420p", "-quant", str(quant)]
    if audio:
        cmd += ["-c:a", "binkaudio_dct", "-ac", "2", "-ar", "48000", "-quality:a", "10"]
    else:
        cmd += ["-an"]
    cmd += ["-f", "bink2", out_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode or not os.path.isfile(out_path):
        raise EnError("ffmpeg falhou (%s): %s" % (res, r.stderr.strip()[-400:]))
    with open(out_path, "rb") as fh:
        head = fh.read(4)
    if head != b"KB2j":
        raise EnError("%s saiu com cabecalho %r, esperado KB2j" % (out_path, head))


def reference_values(ref):
    with open(hm.manifest_path("base"), "rb") as fh:
        recs = dict(hm.read_records(fh.read()))
    vals = {}
    for res in OUT:
        rel = "ui\\videos\\%s\\%s.bk2" % (res, ref)
        h = hm.path_hash(rel)
        if h not in recs:
            raise EnError("video de referencia fora do indice: %s" % rel)
        vals[res] = recs[h]
    return vals


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--name", required=True, metavar="FCO_NOME")
    p.add_argument("--mp4", help="um MP4 16:9, reduzido/ampliado para as duas saidas")
    p.add_argument("--mp4-1080", help="MP4 para a saida 1920x1080")
    p.add_argument("--mp4-2160", help="MP4 para a saida 3840x2160")
    p.add_argument("--ffmpeg", default=os.environ.get("FM_FFMPEG_BK2"),
                   help="ffmpeg com bink2video (ou FM_FFMPEG_BK2)")
    p.add_argument("--quant", type=int, default=None, help="0 (fino) a 36; padrao %d" % QUANT_DEFAULT)
    p.add_argument("--hq", action="store_true", help="quant %d" % QUANT_HQ)
    p.add_argument("--no-audio", action="store_true")
    p.add_argument("--ref", default="3d_carselect_vw", help="video vanilla de referencia para o valor do indice")
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()
    try:
        if not NAME_RE.match(args.name):
            raise EnError("nome precisa ser FCO_<letras, digitos, _>")
        if not args.ffmpeg or not os.path.isfile(args.ffmpeg):
            raise EnError("informe --ffmpeg (ou FM_FFMPEG_BK2) com um ffmpeg que tenha bink2video")
        src = {"1080": args.mp4_1080 or args.mp4, "2160": args.mp4_2160 or args.mp4}
        if not all(src.values()):
            raise EnError("informe --mp4, ou --mp4-1080 e --mp4-2160")
        quant = args.quant if args.quant is not None else (QUANT_HQ if args.hq else QUANT_DEFAULT)
        if not 0 <= quant <= 36:
            raise EnError("--quant de 0 a 36")
        audio = None
        for res, mp4 in src.items():
            if not os.path.isfile(mp4):
                raise EnError("MP4 inexistente: %s" % mp4)
            w, h, has_a = probe(args.ffmpeg, mp4)
            if abs(w / h - 16 / 9) > 0.02:
                raise EnError("%s nao e 16:9 (%dx%d)" % (mp4, w, h))
            audio = has_a if audio is None else (audio and has_a)
        audio = bool(audio) and not args.no_audio
        for res in OUT:
            if os.path.exists(bk.target(res, args.name)):
                raise EnError("%s ja existe em %s: a ferramenta so cria arquivos novos; use outro nome" % (args.name, res))
        vals = reference_values(args.ref)
        tmp = os.path.join(ce.ROOT, "_work", "encode_intro")
        outs = {res: os.path.join(tmp, "%s_%s.bk2" % (args.name.lower(), res)) for res in OUT}
        print("nome %s | quant %d | audio %s | referencia %s (valores 1080 %d, 2160 %d)" % (
            args.name, quant, "sim" if audio else "nao", args.ref, vals["1080"], vals["2160"]))
        for res in OUT:
            print("  %s: %s -> %s" % (res, src[res], outs[res]))
        if not args.apply:
            print("dry-run: nada codificado nem gravado (use --apply, jogo fechado)")
            return 0
        running = ce.forza_processes()
        if running:
            raise EnError("jogo aberto (%s); feche antes" % ", ".join(running))
        os.makedirs(tmp, exist_ok=True)
        for res in OUT:
            encode(args.ffmpeg, src[res], res, quant, audio, outs[res])
            print("  codificado %s (%d B)" % (res, os.path.getsize(outs[res])))
        # instala: sempre um arquivo NOVO; nunca mexe num video existente
        bk.do_add(argparse.Namespace(add=args.name, from_vanilla=None,
                                     from_file=outs["1080"], from_file_2160=outs["2160"],
                                     apply=True))
        # indexa os que faltam
        have = {h for h, _v in hm.read_records(open(hm.manifest_path("base"), "rb").read())}
        todo = [("ui\\videos\\%s\\%s.bk2" % (res, args.name.lower()), vals[res]) for res in OUT]
        todo = [(r, v) for r, v in todo if hm.path_hash(r) not in have]
        if todo:
            hm.do_add(argparse.Namespace(root="base", add=[r for r, _v in todo],
                                         value=[v for _r, v in todo], apply=True))
        else:
            print("  registros do indice ja existem (mantidos)")
        print("pronto: IntroVideoPath = %s.bk2, PlayIntroVideoFullScreen true, "
              "FirstCarSelectEnabled false, FirstCarSelectCars []" % args.name)
    except (EnError, bk.BkError, hm.HmError) as exc:
        print("ERRO: %s" % exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
