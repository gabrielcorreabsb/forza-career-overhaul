"""Kit writer: patches/<kit>/ = plan.json + <SHORT>.<snap>.enc + NOTA.md.

Only `bytes` targets, one per (logical, snapshot), each encrypted with the
current payload of the SAME entry as template. Applying is cache_edit.py's job.
"""

import collections
import json
import os

from . import crypto
from .core import PATCHES, WORK, FmError

SHORT = {
    "BuildersCupScheduleDataV4.json": "BCS",
    "BCSeriesSelectableCars.xml": "CAR",
    "BCEventOverrides.json": "OVR",
    "LocStrings_pt-BR.str": "STR",
    "GlobalChallengeConfiguration.json": "GCC",
    "ChallengeGroupData.json": "CGD",
    "ChallengeHub.json": "CHUB",
}

NOTA_TEMPLATE = """# {kit} - {title}

Gerado por `{generator}`{spec_line}. Snapshots: {snaps}.

## Escopo
{scope}

## Requer
{requires}

## Aplicar (jogo FECHADO)
```powershell
python _tools\\plan_lint.py --plan patches\\{kit}\\plan.json
python _tools\\cache_edit.py --dry-run --plan patches\\{kit}\\plan.json
python _tools\\cache_edit.py --plan patches\\{kit}\\plan.json --verify
python _tools\\inventory.py
```

## Verificar
- `cache_verify.py` com 0 erros; `docs/inventario/ESTADO.md` mostra `{kit}` = live.
- Teste in-game: aparece -> abre -> entra -> conclui -> premio.

## Rollback
`python _tools\\rollback_cache.py` (backup automatico do apply).
"""


class Kit:
    def __init__(self, name, cache, out_dir=None):
        self.name = name
        self.cache = cache
        self.dir = os.path.abspath(out_dir or os.path.join(PATCHES, name))
        self.work = os.path.join(WORK, "kit_" + name)
        self.targets = []
        self.plains = collections.OrderedDict()   # (logical, snap) -> plain

    def add(self, snap, logical, plain):
        """Encrypts `plain` for (logical, snap) and registers the target."""
        if (logical, snap) in self.plains:
            raise FmError("kit %s: %s/%s added twice" % (self.name, logical, snap))
        group = self.cache.group_of(snap, logical)
        if group is None:
            raise FmError("%s: %s has no ContentGroup" % (snap, logical))
        template = self.cache.payload(snap, logical)
        short = SHORT.get(logical, logical.split(".")[0])
        fname = "%s.%s.enc" % (short, snap)
        enc = crypto.encrypt(plain, template, self.work,
                             tag="%s.%s" % (short, snap))
        os.makedirs(self.dir, exist_ok=True)
        with open(os.path.join(self.dir, fname), "wb") as fh:
            fh.write(enc)
        self.plains[(logical, snap)] = plain
        self.targets.append(collections.OrderedDict([
            ("logical", logical), ("group", group), ("op", "bytes"),
            ("file", fname), ("snapshots", [snap])]))
        return enc

    def write_plan(self, note, meta=None):
        plan = collections.OrderedDict([("note", note)])
        for k, v in (meta or {}).items():
            plan[k] = v
        plan["targets"] = self.targets
        path = os.path.join(self.dir, "plan.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(plan, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        return path

    def write_nota(self, title, generator, scope, requires="-", spec=None,
                   overwrite=False):
        path = os.path.join(self.dir, "NOTA.md")
        if os.path.exists(path) and not overwrite:
            return path
        txt = NOTA_TEMPLATE.format(
            kit=self.name, title=title, generator=generator,
            spec_line=(" a partir de `%s`" % spec) if spec else "",
            snaps=", ".join(sorted({t["snapshots"][0] for t in self.targets})),
            scope=scope, requires=requires)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(txt)
        return path

    def reread(self):
        """Decrypts every written .enc and checks it equals the registered
        plaintext (catches a stale/partial kit dir)."""
        for t in self.targets:
            with open(os.path.join(self.dir, t["file"]), "rb") as fh:
                got = crypto.decrypt(fh.read())
            if got != self.plains[(t["logical"], t["snapshots"][0])]:
                raise FmError("kit %s: %s does not decrypt to the expected "
                              "plaintext" % (self.name, t["file"]))
