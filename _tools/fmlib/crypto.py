"""CMS payload codec. Encryption goes through cmsoracle with the CURRENT
encrypted payload as template (keeps gzip settings, Strategy S)."""

import os
import subprocess
import sys

from .core import ORACLE, TOOLS, FmError

sys.path.insert(0, TOOLS)
from cms_crypto import cms_decrypt  # noqa: E402


def decrypt(enc):
    return cms_decrypt(enc)


def encrypt(plain, template, workdir, tag="payload"):
    """Encrypts `plain` with cmsoracle and checks the round-trip."""
    if not os.path.exists(ORACLE):
        raise FmError("cmsoracle.exe not found: %s (dotnet build "
                      "_tools\\cmsoracle\\cmsoracle.csproj -c Release)" % ORACLE)
    os.makedirs(workdir, exist_ok=True)
    src = os.path.join(workdir, tag + ".plain")
    tpl = os.path.join(workdir, tag + ".tpl")
    dst = os.path.join(workdir, tag + ".enc")
    with open(src, "wb") as fh:
        fh.write(plain)
    with open(tpl, "wb") as fh:
        fh.write(template)
    r = subprocess.run([ORACLE, "enc", src, tpl, dst],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise FmError("cmsoracle enc failed (%s): %s" % (tag, r.stderr.strip()))
    with open(dst, "rb") as fh:
        enc = fh.read()
    for p in (src, tpl, dst):
        os.remove(p)
    if cms_decrypt(enc) != plain:
        raise FmError("cmsoracle round-trip diverged (%s)" % tag)
    return enc
