"""Dotted-path edits on the career JSON (round specs).

A round variation declares **only what changes** (`FeatureRace.Laps`,
`NumberOfRequiredLaps`, ...). A path that does not exist is an error: the
generator must never create a field by accident. The variation declares
`"create": true` when the field really is new.

Also holds `diff`, used by the regression test to prove that a generated
series differs from its base only in the declared paths.
"""

from .core import FmError


def split_path(dotted):
    if not isinstance(dotted, str) or not dotted.strip():
        raise FmError("field path must be a non-empty string")
    parts = dotted.split(".")
    if any(not p for p in parts):
        raise FmError("field path %r has an empty segment" % dotted)
    return parts


def get_path(obj, dotted):
    """Value at `dotted`; raises FmError when the path is missing."""
    cur = obj
    done = []
    for part in split_path(dotted):
        done.append(part)
        if not isinstance(cur, dict) or part not in cur:
            raise FmError("field path %r does not exist (at %r)"
                          % (dotted, ".".join(done)))
        cur = cur[part]
    return cur


def set_path(obj, dotted, value, create=False):
    """Writes `value` at `dotted`. Missing path raises unless `create`."""
    parts = split_path(dotted)
    cur = obj
    done = []
    for part in parts[:-1]:
        done.append(part)
        if not isinstance(cur, dict):
            raise FmError("field path %r: %r is not an object"
                          % (dotted, ".".join(done[:-1])))
        if part not in cur:
            if not create:
                raise FmError("field path %r: %r does not exist (declare "
                              "\"create\": true to add it)"
                              % (dotted, ".".join(done)))
            cur[part] = {}
        elif not isinstance(cur[part], dict):
            raise FmError("field path %r: %r is not an object (type %s)"
                          % (dotted, ".".join(done),
                             type(cur[part]).__name__))
        cur = cur[part]
    last = parts[-1]
    if not isinstance(cur, dict):
        raise FmError("field path %r: parent is not an object" % dotted)
    if last not in cur and not create:
        raise FmError("field path %r does not exist (declare \"create\": true "
                      "to add it)" % dotted)
    cur[last] = value
    return value


def diff(old, new, path=""):
    """[(path, old, new)] for every leaf/list/dict that differs."""
    out = []
    if isinstance(old, dict) and isinstance(new, dict):
        for key in sorted(set(old) | set(new)):
            sub = "%s.%s" % (path, key) if path else str(key)
            if key not in old:
                out.append((sub, "<missing>", new[key]))
            elif key not in new:
                out.append((sub, old[key], "<missing>"))
            else:
                out.extend(diff(old[key], new[key], sub))
    elif isinstance(old, list) and isinstance(new, list):
        if len(old) != len(new):
            out.append((path, old, new))
        else:
            for i, (a, b) in enumerate(zip(old, new)):
                out.extend(diff(a, b, "%s[%d]" % (path, i)))
    elif old != new:
        out.append((path, old, new))
    return out
