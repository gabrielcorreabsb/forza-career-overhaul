"""
Codec do CMS do Forza Motorsport 8 (FM8).
Formato (confirmado via decompilacao de FH6LocalCrypto.Runtime.dll):
  entry = AES-128-CBC(IV=0x00*16) sobre  [ gzip(plaintext) | padding de zeros ]
  buffer = (len(gzip) // 16 + 1) * 16 bytes
  O trailer CRC32/ISIZE do proprio membro gzip e a ancora de validacao.
"""
import os, re, zlib, gzip, io, struct, hashlib, base64
from Crypto.Cipher import AES

def _load_cms_key():
    """The CMS AES-128 key is NOT stored in this repo. Take it from the Forza
    Mod Tool (see docs/THIRD_PARTY.md) and either export FM_CMS_KEY (32 hex
    chars) or put the hex in _tools/fmtool/cms_key.hex (git-ignored)."""
    hexkey = os.environ.get("FM_CMS_KEY", "").strip()
    if not hexkey:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "fmtool", "cms_key.hex")
        if os.path.isfile(path):
            with open(path, encoding="ascii") as fh:
                hexkey = fh.read().strip()
    try:
        key = bytes.fromhex(hexkey)
    except ValueError:
        key = b""
    if len(key) != 16:
        raise RuntimeError(
            "CMS AES key not found. Set FM_CMS_KEY or create "
            "_tools/fmtool/cms_key.hex (32 hex chars) - see docs/THIRD_PARTY.md")
    return key


CMS_AES_KEY = _load_cms_key()
IV = b"\x00" * 16


def _deobf_strings():
    import glob
    hits = glob.glob(os.path.join(os.path.dirname(__file__), "decomp", "full", "**", "85D8A4AC*.cs"), recursive=True)
    if not hits:
        raise FileNotFoundError("arquivo deobfuscado nao encontrado")
    CS = hits[0]
    txt = open(CS, encoding="utf-8").read()
    m = re.search(r"internal static byte\[\] _4 = new byte\[(\d+)\]\s*\{(.*?)\};", txt, re.S)
    raw = [int(x) for x in re.findall(r"\d+", m.group(2))]
    deob = bytes(b ^ (i & 0xFF) ^ 0xAA for i, b in enumerate(raw))
    segs = {}
    for idx, off, ln in re.findall(r"_6\((\d+),\s*(\d+),\s*(\d+)\)", txt):
        segs[int(idx)] = (int(off), int(ln))
    return {i: deob[o:o + n].decode("utf-8", "replace") for i, (o, n) in sorted(segs.items())}


def cms_decrypt(entry: bytes, key: bytes = CMS_AES_KEY) -> bytes:
    if len(entry) < 32 or len(entry) > 17825792 or len(entry) % 16 != 0:
        raise ValueError("tamanho de entrada CMS invalido: %d" % len(entry))
    plain = AES.new(key, AES.MODE_CBC, IV).decrypt(entry)
    if plain[0:4] != b"\x1f\x8b\x08\x00":
        raise ValueError("prefixo gzip invalido")
    # localiza o fim do membro gzip: o trailer gzip (crc32 + isize) esta no fim
    # do membro; procuramos do fim do buffer, aceitando ate 16 bytes de zeros.
    body = None
    for i in range(0, 17):
        end = len(plain) - i
        if end < 18:
            break
        if i > 0 and plain[end] != 0:
            break
        if plain[end - 8:end - 4] == b"\x00\x00\x00\x00" and i:
            pass
        try:
            data = gzip.decompress(plain[:end])
        except Exception:
            continue
        crc, isize = struct.unpack("<II", plain[end - 8:end])
        if zlib.crc32(data) & 0xFFFFFFFF == crc and len(data) == isize:
            body = data
            break
    if body is None:
        raise ValueError("trailer gzip/CRC/padding invalido")
    return body


def cms_encrypt(plaintext: bytes, key: bytes = CMS_AES_KEY, compresslevel: int = 9) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=compresslevel, mtime=0) as g:
        g.write(plaintext)
    gz = buf.getvalue()
    padded = (len(gz) // 16 + 1) * 16
    out = gz + b"\x00" * (padded - len(gz))
    return AES.new(key, AES.MODE_CBC, IV).encrypt(out)


if __name__ == "__main__":
    import sys
    s = _deobf_strings()
    print("chave CMS (string[37]):", s.get(37))
    src = r"E:\Projetos\ForzaMods\carrer\_extract\cms_14571097"
    for name in ["SeriesFormat.json", "ChampionshipSeriesObjectivesData_1.json", "Overrides.json"]:
        p = os.path.join(src, name)
        if not os.path.exists(p):
            print("faltando", p); continue
        blob = open(p, "rb").read()
        try:
            pt = cms_decrypt(blob)
        except Exception as e:
            print(f"{name}: FALHOU -> {e}")
            continue
        back = cms_encrypt(pt)
        print(f"{name}: {len(blob)}B -> plaintext {len(pt)}B  roundtrip_decrypt_ok={cms_decrypt(back)==pt}  "
              f"bytes_identicos={back==blob}  head={pt[:90]!r}")
