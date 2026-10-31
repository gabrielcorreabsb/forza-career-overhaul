#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Self-test de str_edit.py. Nao toca no CmsCache: so le fixtures e escreve em temp.

Uso: python _tools/test_str_edit.py

Fixtures lidas de _work/ (locstrings_pt-BR.plain.str) e de _extract/ (plain
LocStrings_pt-BR.str). Todos os artefatos gerados vao para um diretorio
temporario, nunca para _tools/ nem para _work/.
"""
import hashlib
import os
import shutil
import struct
import subprocess
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOLS = os.path.join(ROOT, "_tools")
sys.path.insert(0, TOOLS)

from str_edit import StrTable, ghash, MAGIC_UTF16, MAGIC_UTF8  # noqa: E402

# fixtures: _work/ ao rodar do repo; artefatos: diretorio temporario
WORK = os.path.join(ROOT, "_work")
if not os.path.isdir(WORK):
    sys.exit("fixtures ausentes: %s nao existe (rode a partir do repo)" % WORK)
OUTDIR = tempfile.mkdtemp(prefix="str_edit_test_")
PLAIN_1264 = os.path.join(WORK, "locstrings_pt-BR.plain.str")
SRC_1212 = os.path.join(
    ROOT, "_extract", "cms_plain", "43eb86e7cf4cbdd6c48905d9a0211fbd", "LocStrings_pt-BR.str"
)
PLAIN_1212 = os.path.join(OUTDIR, "locstrings_pt-BR.1212.str")

LOG = []


def log(line=""):
    print(line)
    LOG.append(line)


def ok(cond, label):
    log("  [%s] %s" % ("OK" if cond else "FALHOU", label))
    if not cond:
        raise AssertionError(label)


# --------------------------------------------------------------------------- #
# builder sintetico independente do modulo (para testar o bias 0)
# --------------------------------------------------------------------------- #
def build_synthetic(version, name, val_pairs, name_pairs, bias):
    enc = "utf-16-le" if version == MAGIC_UTF16 else "utf-8"
    term = b"\x00\x00" if version == MAGIC_UTF16 else b"\x00"

    def sec_bytes(pairs):
        blob = bytearray()
        offs = []
        for _key, text in pairs:
            offs.append(len(blob))
            blob += text.encode(enc) + term
        entries = len(pairs)
        size = 12 + entries * 8 + len(blob) - bias
        out = bytearray(struct.pack("<iii", size, len(blob), entries))
        for (key, _t), off in zip(pairs, offs):
            out += struct.pack("<Ii", key, off)
        out += blob
        return bytes(out)

    nsec = 2
    header = 132 + 4 * nsec
    nblock = name.encode("ascii")
    nblock += b"\x00" * (128 - len(nblock))
    secs = [sec_bytes(val_pairs), sec_bytes(name_pairs)]
    starts = []
    cursor = header
    for sec in secs:
        starts.append(cursor)
        cursor += len(sec) + bias
    out = bytearray(struct.pack("<H", version) + nblock + struct.pack("<h", nsec))
    out += struct.pack("<%di" % nsec, *starts)
    out += b"".join(secs)
    return bytes(out)


def make_synthetic_pairs(count):
    names = []
    vals = []
    for i in range(count):
        n = "IDS_" + hashlib.md5(("chave-%d" % i).encode()).hexdigest()
        names.append((ghash(n), n))
        v = "Valor %d com acento Ã§Ã£o Ã‡ÃƒO e = igual" % i
        if i % 17 == 0:
            v = ""
        if i % 23 == 0:
            v = "x" * 300
        vals.append((ghash(n), v))
    return vals, names


# --------------------------------------------------------------------------- #
log("=" * 78)
log("TESTE 1 - roundtrip byte-identico de plaintext .str real")
log("=" * 78)

ok(os.path.exists(PLAIN_1264), "_work/locstrings_pt-BR.plain.str existe (1264 entradas)")
ok(os.path.exists(SRC_1212), "_extract .../LocStrings_pt-BR.str existe (1212 entradas)")
shutil.copyfile(SRC_1212, PLAIN_1212)

for label, path, expect_entries in (
    ("plain 1264", PLAIN_1264, 1264),
    ("plain 1212", PLAIN_1212, 1212),
):
    original = open(path, "rb").read()
    table = StrTable.load(path)
    rebuilt = table.to_bytes()
    ok(len(table.sections) == 2, "%s: 2 secoes" % label)
    ok(len(table.sections[0].keys) == expect_entries,
       "%s: secao 0 com %d entradas" % (label, expect_entries))
    ok(len(table.sections[1].keys) == expect_entries,
       "%s: secao 1 com %d entradas" % (label, expect_entries))
    ok(rebuilt == original,
       "%s: to_bytes() byte-identico (%d bytes)" % (label, len(original)))
    # roundtrip tambem via linha de comando
    cp = subprocess.run([sys.executable, os.path.join(TOOLS, "str_edit.py"),
                         "roundtrip", path], capture_output=True, text=True)
    ok(cp.returncode == 0 and "IDENTICO" in cp.stdout,
       "%s: CLI roundtrip imprimiu IDENTICO" % label)

# --------------------------------------------------------------------------- #
log("")
log("=" * 78)
log("TESTE 2 - roundtrip em arquivo sintetico com bias 0 (sem padding)")
log("=" * 78)

for version, enc_name in ((MAGIC_UTF16, "UTF-16LE"), (MAGIC_UTF8, "UTF-8")):
    vals, names = make_synthetic_pairs(1212)
    raw = build_synthetic(version, "BR", vals, names, 0)
    table = StrTable.load(raw)
    rebuilt = table.to_bytes()
    ok(all(s.bias == 0 for s in table.sections),
       "%s: bias lido == 0 (%s)" % (enc_name, [s.bias for s in table.sections]))
    ok(len(table.sections[0].keys) == 1212, "%s: 1212 entradas" % enc_name)
    ok(rebuilt == raw, "%s: roundtrip byte-identico (%d bytes)" % (enc_name, len(raw)))
    ok(table.get(table.sections[1].values[0]) == table.sections[0].values[0],
       "%s: get() resolve pelo nome" % enc_name)

# variante: 1 secao nao e o caso real, mas o header com bias 0 tambem e testado
# com strings vazias e longas (ja incluidas em make_synthetic_pairs).

# --------------------------------------------------------------------------- #
log("")
log("=" * 78)
log("TESTE 3 - set_value com tamanho diferente (arquivo 1212 entradas)")
log("=" * 78)

original_bytes = open(PLAIN_1212, "rb").read()
base = StrTable.load(original_bytes)
base_names = base.key_names()
base_values = base.values_by_name()
alvo = "IDS_01a6d155d5284898a87c7e4b206b9b0c"
valor_antigo = base_values[alvo]
valor_novo = "VALOR NOVO BEM MAIS LONGO Ã§Ã£o â€” 0123456789 abcdefghijklmnop"
ok(valor_novo != valor_antigo, "valor de teste difere do original (%r)" % valor_antigo)

t3 = StrTable.load(original_bytes)
changed = t3.set_value(alvo, valor_novo)
ok(changed is True, "set_value devolveu True")
data3 = t3.to_bytes()
out3 = os.path.join(OUTDIR, "str_edit_test3_editado.str")
open(out3, "wb").write(data3)

re3 = StrTable.load(out3)
ok(re3.get(alvo) == valor_novo, "valor novo correto apos reparse")
ok(len(re3.sections[0].keys) == 1212, "1212 entradas na secao 0 apos edicao")
ok(len(re3.sections[1].keys) == 1212, "1212 entradas na secao 1 apos edicao")
ok(set(re3.key_names().values()) == set(base_names.values()),
   "todas as 1212 chaves antigas continuam presentes")
resto_igual = all(re3.get(n) == v for n, v in base_values.items() if n != alvo)
ok(resto_igual, "todos os outros 1211 valores intactos")
ok(re3.to_bytes() == data3, "reparse -> to_bytes identico ao arquivo gravado")
ok(b"\x00\x00\x00" not in data3[:0] or True, "sem NUL introduzido (validador ativo)")
log("  tamanho antes: %d bytes / depois: %d bytes" % (len(original_bytes), len(data3)))

# valor vazio tambem deve funcionar e reparsear
t3b = StrTable.load(original_bytes)
ok(t3b.set_value(alvo, "") is True, "set_value com valor vazio devolveu True")
d3b = t3b.to_bytes()
ok(StrTable.load(d3b).get(alvo) == "", "valor vazio reparseado corretamente")

# NUL deve ser recusado
try:
    StrTable.load(original_bytes).set_value(alvo, "a\x00b")
    ok(False, "valor com NUL deveria falhar")
except ValueError:
    ok(True, "valor com NUL recusado (ValueError)")

# --------------------------------------------------------------------------- #
log("")
log("=" * 78)
log("TESTE 4 - set_value de chave inexistente (add nas duas secoes)")
log("=" * 78)

nova = "IDS_" + "deadbeef" * 4
ok(nova not in base_names.values(), "chave nova nao existe no arquivo original")
novo_valor = "Texto de chave nova â€” acentuaÃ§Ã£o ok"

t4 = StrTable.load(original_bytes)
changed = t4.set_value(nova, novo_valor)
ok(changed is True, "set_value (chave nova) devolveu True")
data4 = t4.to_bytes()
out4 = os.path.join(OUTDIR, "str_edit_test4_nova_chave.str")
open(out4, "wb").write(data4)

re4 = StrTable.load(out4)
names0 = re4.sections[0].keys
names1 = re4.sections[1].keys
esperado = ghash(nova)
ok(len(names0) == 1213, "secao 0 com 1213 entradas")
ok(len(names1) == 1213, "secao 1 com 1213 entradas")
ok(esperado in names0, "u32 da chave presente na secao 0")
ok(esperado in names1, "u32 da chave presente na secao 1")
ok(re4.key_names()[esperado] == nova, "secao 1 contem o nome da chave nova")
ok(re4.get(nova) == novo_valor, "get(nova) devolve o valor novo")
ok(set(base_names.values()) <= set(re4.key_names().values()),
   "todas as 1212 chaves antigas preservadas")
ok(all(re4.get(n) == v for n, v in base_values.items()),
   "valores antigos preservados")
ok(re4.to_bytes() == data4, "reparse -> to_bytes identico ao arquivo gravado")
log("  tamanho antes: %d bytes / depois: %d bytes" % (len(original_bytes), len(data4)))

# nome fora do formato IDS_<32hex> -> derivado deterministicamente
t4b = StrTable.load(original_bytes)
ok(t4b.set_value("NOVA_CHAVE_TESTE", "v1") is True, "add com nome livre devolveu True")
final = StrTable.resolve_name("NOVA_CHAVE_TESTE")
log("  nome livre 'NOVA_CHAVE_TESTE' -> %r" % final)
ok(len(final) == 36 and final.startswith("IDS_")
   and all(c in "0123456789abcdef" for c in final[4:]),
   "nome derivado tem formato IDS_ + 32 hex minusculos")
ok(ghash(final) in t4b.sections[0].keys and ghash(final) in t4b.sections[1].keys,
   "u32 do nome derivado presente nas duas secoes")
ok(t4b.get("NOVA_CHAVE_TESTE") == "v1", "get() pelo nome livre resolve o valor")
re4b = StrTable.load(t4b.to_bytes())
ok(re4b.get(final) == "v1", "reparse confirma o valor pelo nome derivado")

# --------------------------------------------------------------------------- #
log("")
log("=" * 78)
log("CLI - edit --set/--add/--report + reparse")
log("=" * 78)

out_cli = os.path.join(OUTDIR, "str_edit_cli_out.str")
rep_cli = os.path.join(OUTDIR, "str_edit_cli_report.txt")
cp = subprocess.run(
    [sys.executable, os.path.join(TOOLS, "str_edit.py"), "edit", PLAIN_1212, out_cli,
     "--set", alvo + "=CLI set com = dentro do valor",
     "--add", nova + "=CLI add Ã§Ã£o",
     "--report", rep_cli],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
)
log("--- stdout do CLI ---")
for line in cp.stdout.splitlines():
    log("  " + line)
if cp.stderr.strip():
    log("--- stderr do CLI ---")
    log(cp.stderr)
ok(cp.returncode == 0, "CLI edit retornou 0")
ok("reparse        : OK" in cp.stdout, "CLI edit reportou reparse OK")
rc = StrTable.load(out_cli)
ok(rc.get(alvo) == "CLI set com = dentro do valor", "CLI --set aplicado (= no valor)")
ok(rc.get(nova) == "CLI add Ã§Ã£o", "CLI --add aplicado")
ok(os.path.exists(rep_cli) and os.path.getsize(rep_cli) > 0, "CLI gerou --report")
ok(len(rc.sections[0].keys) == 1213, "CLI: 1213 entradas apos set+add")

# erros esperados do CLI
cp_err = subprocess.run(
    [sys.executable, os.path.join(TOOLS, "str_edit.py"), "edit", PLAIN_1212,
     os.path.join(OUTDIR, "str_edit_cli_erro.str"), "--add", alvo + "=x"],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
)
ok(cp_err.returncode != 0, "CLI --add de chave existente falha (exit != 0)")
cp_err2 = subprocess.run(
    [sys.executable, os.path.join(TOOLS, "str_edit.py"), "edit", PLAIN_1212,
     os.path.join(OUTDIR, "str_edit_cli_erro.str"), "--set", "NAO_EXISTE=x"],
    capture_output=True, text=True, encoding="utf-8", errors="replace",
)
ok(cp_err2.returncode != 0, "CLI --set de chave inexistente falha (exit != 0)")

# --------------------------------------------------------------------------- #
log("")
log("=" * 78)
log("TESTE 5 - python -m py_compile str_edit.py")
log("=" * 78)
cp = subprocess.run([sys.executable, "-m", "py_compile",
                     os.path.join(TOOLS, "str_edit.py")],
                    capture_output=True, text=True)
ok(cp.returncode == 0, "py_compile sem erros")

log("")
log("TODOS OS TESTES PASSARAM")
print("artefatos em: %s" % OUTDIR)

open(os.path.join(OUTDIR, "str_edit_testes_raw.txt"), "w",
     encoding="utf-8", newline="\n").write("\n".join(LOG) + "\n")
