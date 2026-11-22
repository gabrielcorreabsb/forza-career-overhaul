"""FCO base profile (specs/fco_base/): documented JSON.

JSON has no comments, so every field `X` of a profile file carries a sibling
`X_doc` (what it does, the evidence, why this value). Builders call
`strip_docs` to drop the `*_doc` keys; with `require=True` a field without its
`_doc` is a refusal, so nothing enters the profile unexplained.
"""

import json
import os

from .core import FmError, ROOT

PROFILE_DIR = os.path.join(ROOT, "specs", "fco_base")
DOC = "_doc"


def strip_docs(obj, require=False, label="profile"):
    """Copy of obj without *_doc keys (recursive into objects and lists)."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k.endswith(DOC):
                if k != DOC and k[:-len(DOC)] not in obj:
                    raise FmError("%s: '%s' documents a missing field"
                                  % (label, k))
                continue
            if require and (k + DOC) not in obj:
                raise FmError("%s: field '%s' has no '%s%s' (every profile "
                              "value needs its reason)" % (label, k, k, DOC))
            out[k] = strip_docs(v, require, "%s.%s" % (label, k))
        return out
    if isinstance(obj, list):
        return [strip_docs(v, require, "%s[%d]" % (label, i))
                for i, v in enumerate(obj)]
    return obj


def load(name, base=None):
    """Loads specs/<base>/<name>.json with every field documented."""
    folder = os.path.join(ROOT, "specs", base) if base else PROFILE_DIR
    path = os.path.join(folder, name + ".json")
    if not os.path.isfile(path):
        raise FmError("profile file not found: %s" % path)
    with open(path, encoding="utf-8-sig") as fh:
        raw = json.load(fh)
    return strip_docs(raw, require=True, label="%s/%s" % (
        os.path.basename(folder), name))
