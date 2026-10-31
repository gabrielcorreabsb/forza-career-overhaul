#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""str_edit.py - parser/rewriter de string tables `.str` do Forza Motorsport 8.

Formato (versao "v4" = UTF-16LE, "v8" = UTF-8), decodificado:

    offset 0      u16 version      0x400 = UTF-16LE | 0x800 = UTF-8
    offset 2      nome ASCII (locale, ex. "BR") + zeros ate o offset 128
    offset 130    i16 numSecoes
    offset 132    i32 start[sec]   (headerSize = 132 + 4*numSecoes)

    cada secao (start = S):
      S+0    i32 size
      S+4    i32 stringBytes
      S+8    i32 entries
      S+12   entries pares (u32 key, i32 offset relativo ao blob de strings)
      S+12+entries*8   blob de strings (stringBytes bytes), NUL-terminated

Secao 0 = VALORES localizados, secao 1 = NOMES das chaves ("IDS_<32 hex>").
As duas secoes possuem o mesmo conjunto de chaves de indice (u32 = ghash(nome)).

Notas de layout:
  * `size = 12 + entries*8 + stringBytes - bias`, onde
    `bias = (S + 12 + entries*8 + stringBytes) - S - size`.
    Nos arquivos reais o bias e 0 (secoes justapostas) ou 12 (padding de
    alinhamento). O bias original de cada secao e preservado na reconstrucao.
  * a secao seguinte comeca em `S + size + bias`.
  * a ordem fisica das strings no blob e irrelevante (o jogo usa o offset);
    `rebuild()` grava na ordem dos pares e recalcula os offsets.

Uso:
    python str_edit.py info      <arquivo.str>
    python str_edit.py roundtrip <arquivo.str>
    python str_edit.py edit      <in> <out> [--set NOME=VALOR]... [--add NOME=VALOR]...
                                 [--report <arquivo.txt>]
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import struct
import sys

__all__ = ["StrTable", "Section", "ghash", "MAGIC_UTF16", "MAGIC_UTF8"]

MAGIC_UTF16 = 0x400
MAGIC_UTF8 = 0x800
HEADER_BASE = 132          # bytes antes da tabela de starts
NAME_OFFSET = 2
NAME_SIZE = 128            # bytes 2..130
VERSION_LEN = 2

_IDS_RE = re.compile(r"IDS_[0-9a-f]{32}\Z")
_IDS_RE_ANY = re.compile(r"IDS_[0-9A-Fa-f]{32}\Z")


# --------------------------------------------------------------------------- #
# hash de chave (confirmado 1212/1212 no LocStrings_pt-BR.str)
# --------------------------------------------------------------------------- #
def ghash(text):
    """Hash u32 usado pelo jogo: xor do code point + rotl 7."""
    if not isinstance(text, str):
        raise TypeError("ghash espera str")
    v = 0xFFFFFFFF
    for ch in text:
        v ^= ord(ch)
        v = ((v << 7) | (v >> 25)) & 0xFFFFFFFF
    return v


def _read_source(path_or_bytes):
    if isinstance(path_or_bytes, (bytes, bytearray, memoryview)):
        return bytes(path_or_bytes)
    if hasattr(path_or_bytes, "read"):
        data = path_or_bytes.read()
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("stream deve estar em modo binario")
        return bytes(data)
    with open(os.fspath(path_or_bytes), "rb") as fh:
        return fh.read()


class Section:
    """Uma secao individual da string table."""

    __slots__ = ("keys", "offsets", "values", "strings", "bias")

    def __init__(self, keys=None, offsets=None, values=None, strings=b"", bias=12):
        self.keys = list(keys or [])
        self.offsets = list(offsets or [])
        self.values = list(values or [])
        self.strings = bytes(strings or b"")
        self.bias = int(bias)

    @property
    def entries(self):
        return len(self.keys)

    def __len__(self):
        return len(self.keys)

    def __repr__(self):
        return "<Section entries=%d stringBytes=%d bias=%d>" % (
            len(self.keys), len(self.strings), self.bias,
        )


class StrTable:
    """String table `.str` do Forza Motorsport 8."""

    def __init__(self, version=MAGIC_UTF16, name="", sections=None, name_block=None):
        if version not in (MAGIC_UTF16, MAGIC_UTF8):
            raise ValueError("version nao suportada: 0x%X" % int(version))
        self.version = int(version)
        self.name = str(name)
        if name_block is None:
            raw = self.name.encode("ascii")
            if len(raw) > NAME_SIZE - 1:
                raise ValueError("nome ASCII maior que %d bytes" % (NAME_SIZE - 1))
            name_block = raw + b"\x00" * (NAME_SIZE - len(raw))
        name_block = bytes(name_block)
        if len(name_block) != NAME_SIZE:
            raise ValueError("name_block deve ter %d bytes" % NAME_SIZE)
        self.name_block = name_block
        self.sections = list(sections or [])

    # ---------------- leitura / escrita ---------------- #

    @property
    def is_utf16(self):
        return self.version == MAGIC_UTF16

    @property
    def encoding(self):
        return "utf-16-le" if self.is_utf16 else "utf-8"

    @property
    def terminator(self):
        return b"\x00\x00" if self.is_utf16 else b"\x00"

    # ---------------- helpers de string ---------------- #

    def _decode_at(self, blob, offset):
        term = self.terminator
        step = len(term)
        n = len(blob)
        if offset < 0 or offset > n:
            raise ValueError("offset de string fora do blob: %d (blob=%d)" % (offset, n))
        if offset == n:
            # string vazia colada no fim (sem terminador fisico)
            return ""
        end = -1
        e = offset
        while e + step <= n:
            if blob[e:e + step] == term:
                end = e
                break
            e += step
        if end < 0:
            end = n  # sem terminador: usa o resto do blob
        raw = blob[offset:end]
        return raw.decode(self.encoding, errors="surrogatepass")

    def _encode_value(self, value):
        if not isinstance(value, str):
            raise TypeError("valor deve ser str, recebido %r" % type(value))
        if "\x00" in value:
            raise ValueError("valor nao pode conter NUL: %r" % value)
        try:
            return value.encode(self.encoding)
        except UnicodeEncodeError:
            # surrogates isolados: preserva byte a byte no roundtrip
            return value.encode(self.encoding, errors="surrogatepass")

    # ---------------- load ---------------- #

    @classmethod
    def load(cls, path_or_bytes):
        """Le de um caminho, stream binario ou bytes."""
        data = _read_source(path_or_bytes)
        if len(data) < HEADER_BASE:
            raise ValueError("arquivo curto demais (%d bytes)" % len(data))

        version = struct.unpack_from("<H", data, 0)[0]
        if version not in (MAGIC_UTF16, MAGIC_UTF8):
            raise ValueError("version desconhecida: 0x%X" % version)

        name_block = bytes(data[NAME_OFFSET:NAME_OFFSET + NAME_SIZE])
        name = name_block.split(b"\x00", 1)[0].decode("ascii", "replace")

        num_sections = struct.unpack_from("<h", data, 130)[0]
        if num_sections <= 0:
            raise ValueError("numSecoes invalido: %d" % num_sections)
        header_size = HEADER_BASE + 4 * num_sections
        if len(data) < header_size:
            raise ValueError("header truncado (%d < %d)" % (len(data), header_size))

        starts = list(struct.unpack_from("<%di" % num_sections, data, HEADER_BASE))
        table = cls(version=version, name=name, sections=[], name_block=name_block)

        for idx, start in enumerate(starts):
            if start < 0 or start + 12 > len(data):
                raise ValueError("secao %d: start invalido %d" % (idx, start))
            size, string_bytes, entries = struct.unpack_from("<iii", data, start)
            if entries < 0 or string_bytes < 0:
                raise ValueError(
                    "secao %d: entries/stringBytes negativos (%d/%d)"
                    % (idx, entries, string_bytes)
                )
            data_start = start + 12 + entries * 8
            if data_start + string_bytes > len(data):
                raise ValueError(
                    "secao %d: blob excede o arquivo (%d > %d)"
                    % (idx, data_start + string_bytes, len(data))
                )
            blob = bytes(data[data_start:data_start + string_bytes])

            keys, offsets, values = [], [], []
            for i in range(entries):
                key, off = struct.unpack_from("<Ii", data, start + 12 + i * 8)
                if table.is_utf16 and (off & 1):
                    raise ValueError(
                        "secao %d entrada %d: offset impar em UTF-16 (%d)"
                        % (idx, i, off)
                    )
                if off < 0 or off > string_bytes:
                    raise ValueError(
                        "secao %d entrada %d: offset fora do blob (%d > %d)"
                        % (idx, i, off, string_bytes)
                    )
                keys.append(key)
                offsets.append(off)
                values.append(table._decode_at(blob, off))

            bias = (data_start + string_bytes) - start - size
            if bias < 0:
                raise ValueError("secao %d: bias negativo (%d)" % (idx, bias))
            table.sections.append(Section(keys, offsets, values, blob, bias))

        return table

    # ---------------- API de consulta ---------------- #

    def key_names(self):
        """key (u32) -> nome da chave (IDS_...), vindo da secao 1."""
        if len(self.sections) < 2:
            return {}
        sec = self.sections[1]
        return {k: v for k, v in zip(sec.keys, sec.values)}

    def values_by_name(self):
        """nome da chave -> valor localizado (secao 0)."""
        if len(self.sections) < 2:
            return {}
        values = self.sections[0]
        by_key = {}
        for k, v in zip(values.keys, values.values):
            by_key.setdefault(k, v)
        out = {}
        for k, name in zip(self.sections[1].keys, self.sections[1].values):
            if k in by_key:
                out[name] = by_key[k]
        return out

    def get(self, name):
        """Valor da chave `name`, ou None."""
        if not isinstance(name, str):
            return None
        if len(self.sections) < 2:
            return None
        key = ghash(self.resolve_name(name))
        names = self.key_names()
        if key not in names:
            return None
        values = self.sections[0]
        for k, v in zip(values.keys, values.values):
            if k == key:
                return v
        return None

    # ---------------- alteracao ---------------- #

    @staticmethod
    def resolve_name(name):
        """Normaliza para o formato exigido 'IDS_' + 32 hex minusculos.

        Nomes ja no formato IDS_<32 hex> sao mantidos (maiusculas -> minusculas);
        qualquer outro nome vira IDS_ + sha256(nome)[:32] (deterministico).
        """
        if not isinstance(name, str) or not name:
            raise ValueError("nome de chave invalido: %r" % (name,))
        if _IDS_RE.fullmatch(name):
            return name
        if _IDS_RE_ANY.fullmatch(name):
            return name.lower()
        digest = hashlib.sha256(name.encode("utf-8")).hexdigest()[:32]
        return "IDS_" + digest

    def set_value(self, name, value):
        """Define o valor de `name`. Se a chave nao existe, cria nas 2 secoes.

        Devolve True se algo mudou.
        """
        if not isinstance(name, str) or not name:
            raise ValueError("nome de chave invalido: %r" % (name,))
        if not isinstance(value, str):
            raise TypeError("valor deve ser str")
        if "\x00" in value:
            raise ValueError("valor nao pode conter NUL")
        if len(self.sections) < 2:
            raise ValueError("tabela precisa de 2 secoes (valores + nomes)")

        final = self.resolve_name(name)
        key = ghash(final)
        sec_vals, sec_names = self.sections[0], self.sections[1]

        try:
            i_val = sec_vals.keys.index(key)
        except ValueError:
            i_val = -1
        try:
            i_name = sec_names.keys.index(key)
        except ValueError:
            i_name = -1

        changed = False
        if i_val >= 0:
            if sec_vals.values[i_val] != value:
                sec_vals.values[i_val] = value
                changed = True
        else:
            sec_vals.keys.append(key)
            sec_vals.offsets.append(-1)  # rebuild recalcula
            sec_vals.values.append(value)
            changed = True

        if i_name >= 0:
            if sec_names.values[i_name] != final:
                sec_names.values[i_name] = final
                changed = True
        else:
            sec_names.keys.append(key)
            sec_names.offsets.append(-1)  # rebuild recalcula
            sec_names.values.append(final)
            changed = True

        return changed

    # ---------------- serializacao ---------------- #

    def rebuild(self):
        """Reconstroi o arquivo inteiro (recalcula offsets, stringBytes, size)."""
        num_sections = len(self.sections)
        if num_sections <= 0:
            raise ValueError("tabela sem secoes")
        term = self.terminator

        header_size = HEADER_BASE + 4 * num_sections
        starts = []
        payloads = []
        cursor = header_size

        for idx, sec in enumerate(self.sections):
            if len(sec.keys) != len(sec.values):
                raise ValueError(
                    "secao %d: %d chaves para %d valores"
                    % (idx, len(sec.keys), len(sec.values))
                )
            starts.append(cursor)
            blob = bytearray()
            offsets = []
            for value in sec.values:
                offsets.append(len(blob))
                blob += self._encode_value(value)
                blob += term
            sec.offsets = offsets
            sec.strings = bytes(blob)
            size = 12 + len(sec.keys) * 8 + len(blob) - sec.bias
            if size < 12:
                raise ValueError("secao %d: size invalido (%d)" % (idx, size))
            payloads.append((sec, size, len(blob), len(sec.keys)))
            cursor += size + sec.bias

        out = bytearray()
        out += struct.pack("<H", self.version)
        out += self.name_block
        out += struct.pack("<h", num_sections)
        out += struct.pack("<%di" % num_sections, *starts)
        if len(out) != header_size:
            raise AssertionError("header reconstruido com tamanho errado")

        for sec, size, string_bytes, entries in payloads:
            out += struct.pack("<iii", size, string_bytes, entries)
            for key, off in zip(sec.keys, sec.offsets):
                out += struct.pack("<Ii", key & 0xFFFFFFFF, off)
            out += sec.strings

        return bytes(out)

    def to_bytes(self):
        return self.rebuild()


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _split_assignment(text, flag):
    if "=" not in text:
        raise SystemExit("erro: %s espera NOME=VALOR, recebido %r" % (flag, text))
    name, value = text.split("=", 1)
    name = name.strip()
    if not name:
        raise SystemExit("erro: %s com nome vazio (%r)" % (flag, text))
    return name, value


def _fmt_value(value, limit=72):
    if value is None:
        return "<None>"
    shown = value
    if len(shown) > limit:
        shown = shown[:limit] + "..."
    return repr(shown)


def cmd_info(args):
    table = StrTable.load(args.path)
    print("arquivo    : %s" % args.path)
    print("tamanho    : %d bytes" % os.path.getsize(args.path))
    print("version    : 0x%X (%s)" % (table.version, table.encoding))
    print("name       : %r" % table.name)
    print("secoes     : %d" % len(table.sections))
    for idx, sec in enumerate(table.sections):
        print(
            "  secao %d : entries=%d stringBytes=%d size=%d bias=%d"
            % (idx, len(sec.keys), len(sec.strings),
              12 + len(sec.keys) * 8 + len(sec.strings) - sec.bias, sec.bias)
        )
    print("padrao chaves IDS_<32hex> (secao 1): %s"
          % ("sim" if all(_IDS_RE.fullmatch(v) for v in
                          table.sections[1].values) else "nao"))

    names = table.key_names()
    print("amostra de 5 pares chave->valor:")
    shown = 0
    for key, value in zip(table.sections[0].keys, table.sections[0].values):
        print("  %s  (u32=0x%08X) -> %s"
              % (names.get(key, "<sem nome>"), key, _fmt_value(value)))
        shown += 1
        if shown >= 5:
            break
    return 0


def cmd_roundtrip(args):
    with open(args.path, "rb") as fh:
        original = fh.read()
    table = StrTable.load(original)
    rebuilt = table.to_bytes()
    print("arquivo    : %s" % args.path)
    print("original   : %d bytes" % len(original))
    print("reconstruido: %d bytes" % len(rebuilt))
    if rebuilt == original:
        print("resultado  : IDENTICO (byte a byte)")
        return 0
    first = None
    for i, (a, b) in enumerate(zip(original, rebuilt)):
        if a != b:
            first = i
            break
    if first is None:
        first = min(len(original), len(rebuilt))
    print("resultado  : DIFERENTE")
    print("primeira divergencia no offset: %d" % first)
    lo = max(0, first - 8)
    print("  original    [%d:%d] = %s" % (lo, first + 8, original[lo:first + 8].hex()))
    print("  reconstruido[%d:%d] = %s" % (lo, first + 8, rebuilt[lo:first + 8].hex()))
    return 1


def cmd_edit(args):
    with open(args.inp, "rb") as fh:
        original = fh.read()
    table = StrTable.load(original)

    before_entries = sum(len(s.keys) for s in table.sections)
    before_size = len(original)

    sets = [_split_assignment(x, "--set") for x in (args.set or [])]
    adds = [_split_assignment(x, "--add") for x in (args.add or [])]

    # validacao antes de alterar qualquer coisa
    for name, _value in sets:
        if table.get(name) is None:
            raise SystemExit("erro: --set de chave inexistente: %r "
                             "(use --add para criar)" % name)
    for name, _value in adds:
        if table.get(name) is not None:
            raise SystemExit("erro: --add de chave ja existente: %r "
                             "(use --set para substituir)" % name)
    seen = {}
    for flag, items in (("--set", sets), ("--add", adds)):
        for name, _value in items:
            final = StrTable.resolve_name(name)
            if final in seen:
                raise SystemExit("erro: chave %r repetida em %s e %s"
                                 % (final, seen[final], flag))
            seen[final] = flag

    report = []
    for name, value in sets:
        old = table.get(name)
        changed = table.set_value(name, value)
        final = StrTable.resolve_name(name)
        report.append({
            "kind": "set", "name": final, "key": ghash(final),
            "old": old, "new": value, "changed": changed,
        })
        print("set  %s : %s -> %s"
              % (final, _fmt_value(old), _fmt_value(value)))

    for name, value in adds:
        final = StrTable.resolve_name(name)
        changed = table.set_value(name, value)
        report.append({
            "kind": "add", "name": final, "key": ghash(final),
            "old": None, "new": value, "changed": changed,
        })
        print("add  %s : %s (u32=0x%08X)" % (final, _fmt_value(value), ghash(final)))

    data = table.to_bytes()
    with open(args.out, "wb") as fh:
        fh.write(data)

    after_entries = sum(len(s.keys) for s in table.sections)
    print("entradas antes : %d" % before_entries)
    print("entradas depois: %d" % after_entries)
    print("tamanho antes  : %d bytes" % before_size)
    print("tamanho depois : %d bytes" % len(data))

    # reparse do arquivo gravado
    with open(args.out, "rb") as fh:
        written = fh.read()
    check = StrTable.load(written)
    problems = []
    if check.version != table.version:
        problems.append("version mudou")
    if check.name != table.name:
        problems.append("nome mudou")
    if len(check.sections) != len(table.sections):
        problems.append("numero de secoes mudou")
    if check.to_bytes() != written:
        problems.append("reparse->to_bytes nao e identico ao arquivo gravado")
    for section_idx, (a, b) in enumerate(zip(table.sections, check.sections)):
        if a.keys != b.keys:
            problems.append("secao %d: chaves diferem apos reparse" % section_idx)
    for item in report:
        got = check.get(item["name"])
        if got != item["new"]:
            problems.append("chave %s: valor %r apos reparse (esperado %r)"
                            % (item["name"], got, item["new"]))
    # todas as chaves antigas presentes
    old_names = set(table.key_names().values())
    new_names = set(check.key_names().values())
    missing = old_names - new_names
    if missing:
        problems.append("chaves perdidas: %s" % sorted(missing)[:5])

    if problems:
        print("reparse        : FALHOU")
        for p in problems:
            print("  - %s" % p)
        status = "FALHOU"
    else:
        print("reparse        : OK (%d secoes, %d entradas na secao 0, %d na secao 1)"
              % (len(check.sections), len(check.sections[0].keys),
                 len(check.sections[1].keys)))
        status = "OK"

    if args.report:
        lines = []
        lines.append("# str_edit report")
        lines.append("entrada: %s" % args.inp)
        lines.append("saida  : %s" % args.out)
        lines.append("version: 0x%X (%s)" % (table.version, table.encoding))
        lines.append("name   : %r" % table.name)
        lines.append("entradas antes : %d" % before_entries)
        lines.append("entradas depois: %d" % after_entries)
        lines.append("tamanho antes  : %d" % before_size)
        lines.append("tamanho depois : %d" % len(data))
        lines.append("")
        for item in report:
            lines.append("[%s] %s  (u32=0x%08X)" % (item["kind"], item["name"], item["key"]))
            lines.append("  valor anterior: %s" % _fmt_value(item["old"], 200))
            lines.append("  valor novo    : %s" % _fmt_value(item["new"], 200))
            lines.append("  alterou       : %s" % ("sim" if item["changed"] else "nao"))
        lines.append("")
        lines.append("reparse: %s" % status)
        for p in problems:
            lines.append("  problema: %s" % p)
        lines.append("")
        with open(args.report, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines))
        print("relatorio      : %s" % args.report)

    return 0 if not problems else 1


def build_parser():
    parser = argparse.ArgumentParser(
        prog="str_edit.py",
        description="Parser/rewriter de string tables .str do Forza Motorsport 8.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_info = sub.add_parser("info", help="mostra o cabecalho/secoes e amostra de pares")
    p_info.add_argument("path", help="arquivo .str")
    p_info.set_defaults(func=cmd_info)

    p_rt = sub.add_parser("roundtrip", help="parse -> to_bytes e compara com o original")
    p_rt.add_argument("path", help="arquivo .str")
    p_rt.set_defaults(func=cmd_roundtrip)

    p_edit = sub.add_parser("edit", help="edita valores e/ou cria chaves")
    p_edit.add_argument("inp", help="arquivo .str de entrada")
    p_edit.add_argument("out", help="arquivo .str de saida")
    p_edit.add_argument("--set", action="append", default=[], metavar="NOME=VALOR",
                        help="substitui o valor de uma chave existente")
    p_edit.add_argument("--add", action="append", default=[], metavar="NOME=VALOR",
                        help="adiciona uma chave nova (erro se ja existir)")
    p_edit.add_argument("--report", metavar="ARQUIVO.TXT",
                        help="grava um relatorio das alteracoes")
    p_edit.set_defaults(func=cmd_edit)
    return parser


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
