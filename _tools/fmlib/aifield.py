"""AIField_*.xml: read, rewrite and validate (install-only CMS group CFA7698C).

Two document modes exist in vanilla (646 files):
  * AIDrivatarTemplate: PI window + EligibleCars fill NumberOfDrivatars slots.
  * AIDrivatarList: explicit Car per slot, TargetPI="-1".
Both carry a ContentManifest of AI_<car>_<pi> files. The documents are
CRLF text; every function works on blocks and leaves the rest byte-identical.

The root attributes AIDifficulty / AIRubberBandingEnabled and the
BehaviorSettings flags are inherited from the template by default; they can be
rewritten with `rewrite_template(difficulty=..., rubber_banding=...,
behavior=...)`, which touches only those attributes (a document rewritten with
its own values comes back byte-identical).

The XML is not in the CmsCache, so the cipher template is the CURRENT payload
of the entry inside the install zip (see install_edit.py to apply it).
"""

import json
import os
import re
import zipfile

from . import crypto
from .cars import denied_ids, load_cars
from .core import FmError

INSTALL = os.environ.get(
    "FM_INSTALL", r"F:\SteamLibrary\steamapps\common\Forza Motorsport")
GROUP = "CFA7698CDD46663C19F66C30CBE63EBA"
CRLF = "\r\n"

ELIG_HEAD = "  <EligibleCars>" + CRLF
ELIG_TAIL = "  </EligibleCars>" + CRLF
CM_HEAD = "  <ContentManifest>" + CRLF
CM_TAIL = "  </ContentManifest>" + CRLF
FR_HEAD = "    <DrivatarProgressionFrames>" + CRLF
FR_TAIL = "    </DrivatarProgressionFrames>" + CRLF
AI_FILE = re.compile(r"^AI_(\d+)_(\d+)\.xml$")
RBS = re.compile(r"<RaceBehaviorSettings\b[^>]*?/>", re.S)
# key accepted in a `behavior` definition -> attribute of RaceBehaviorSettings
BEHAVIOR_KEYS = {
    "SlowDown": "EnableDifficultySlowDown",
    "CatchUp": "EnableDifficultyCatchUp",
    "Proximity": "EnableDifficultyProximity",
    "PosDifficultySpread": "EnablePosDifficultySpread",
    "SlotCarRaceStart": "EnableSlotCarRaceStart",
}


def zip_path(install=None):
    return os.path.join(install or INSTALL, "media", "pcfamily", "cms",
                        GROUP.lower() + ".zip")


def read_entry(logical, install=None):
    """(encrypted payload, plaintext text, all names in the zip)."""
    with zipfile.ZipFile(zip_path(install)) as zf:
        names = zf.namelist()
        if logical not in names:
            raise FmError("%s not in %s" % (logical, zip_path(install)))
        enc = zf.read(logical)
    return enc, crypto.decrypt(enc).decode("utf-8"), names


def encrypt_for_install(text, current_enc, workdir, tag="aifield"):
    """Encrypts with the entry's current install payload as template."""
    return crypto.encrypt(text.encode("utf-8"), current_enc, workdir, tag)


# ---------------------------------------------------------------- parsing --
def _block(text, head, tail):
    i, j = text.find(head), text.find(tail)
    if i < 0 or j < 0 or j < i:
        raise FmError("AIField: block %r not found" % head.strip())
    return i, j + len(tail)


def mode_of(text):
    m = re.search(r'Type="(AIDrivatar\w+)"', text)
    if not m:
        raise FmError("AIField: no AIDrivatarConfiguration Type")
    return m.group(1)


def parse(text):
    i0, i1 = _block(text, ELIG_HEAD, ELIG_TAIL)
    c0, c1 = _block(text, CM_HEAD, CM_TAIL)
    elig = [int(v) for v in re.findall(r'val="(\d+)"', text[i0:i1])]
    cm = [(int(a), int(b), c, d) for a, b, c, d in re.findall(
        r'<UpgradedPartsFile\s+Car="(\d+)"\s+TargetPI="(-?\d+)"\s+'
        r'File="(AI_\d+_\d+)"\s+Ext="([^"]*)"\s*/>', text[c0:c1])]
    if len(cm) != text[c0:c1].count("<UpgradedPartsFile"):
        raise FmError("AIField: unparsed ContentManifest entries")
    cfg_m = re.search(r"<AIDrivatarConfiguration([^>]*)>", text)
    cfg = dict(re.findall(r'(\w+)="([^"]*)"', cfg_m.group(1))) if cfg_m else {}
    difficulty = re.search(r'AIDifficulty="([^"]*)"', text)
    rubber = re.search(r'AIRubberBandingEnabled="([^"]*)"', text)
    behavior = {}
    for m in RBS.finditer(text):
        attrs = dict(re.findall(r'(\w+)="([^"]*)"', m.group(0)))
        session = attrs.pop("SessionType", None)
        if session:
            behavior[session] = attrs
    drivatars = [int(v) for v in re.findall(
        r'<AIDrivatar\s+PlayerId="\d+"\s+Car="(-?\d+)"', text)]
    f0, f1 = text.find(FR_HEAD), text.find(FR_TAIL)
    frames, frames_span = [], None
    if f0 >= 0 and f1 > f0:
        frames_span = (f0, f1 + len(FR_TAIL))
        frames = [(int(a), int(b), int(c)) for a, b, c in re.findall(
            r'<AIProgressionFrame\s+PlayerPIRelativeToClass="(-?\d+)"\s+'
            r'DrivatarPIAdjustmentLower="(-?\d+)"\s+'
            r'DrivatarPIAdjustmentUpper="(-?\d+)"\s*/>', text[f0:f1])]
        if len(frames) != text[f0:f1].count("<AIProgressionFrame"):
            raise FmError("AIField: unparsed AIProgressionFrame entries")
    return {"mode": mode_of(text), "elig": elig, "cm": cm, "cfg": cfg,
            "drivatars": drivatars, "elig_span": (i0, i1),
            "cm_span": (c0, c1), "frames": frames,
            "frames_span": frames_span,
            "difficulty": difficulty.group(1) if difficulty else None,
            "rubber": rubber.group(1) if rubber else None,
            "behavior": behavior}


# -------------------------------------------------------------- rendering --
def render_elig(cars):
    return ELIG_HEAD + "".join(
        "    <CarListEntry" + CRLF + '      val="%d" />' % c + CRLF
        for c in cars) + ELIG_TAIL


def render_cm(rows):
    return CM_HEAD + "".join(
        "    <UpgradedPartsFile" + CRLF + '      Car="%d"' % c + CRLF
        + '      TargetPI="%d"' % tp + CRLF + '      File="%s"' % f + CRLF
        + '      Ext="%s" />' % e + CRLF for c, tp, f, e in rows) + CM_TAIL


def render_frames(frames):
    """`frames` = [(PlayerPIRelativeToClass, lower, upper), ...]."""
    return FR_HEAD + "".join(
        "      <AIProgressionFrame" + CRLF
        + '        PlayerPIRelativeToClass="%d"' % rel + CRLF
        + '        DrivatarPIAdjustmentLower="%d"' % lo + CRLF
        + '        DrivatarPIAdjustmentUpper="%d" />' % hi + CRLF
        for rel, lo, hi in frames) + FR_TAIL


def render_drivatars(cars, indent, participate=True):
    """AIDrivatar slots; `indent` = spaces before '<AIDrivatar'."""
    p, q = " " * indent, " " * (indent + 2)
    flag = "True" if participate else "False"
    return "".join(
        p + "<AIDrivatar" + CRLF + q + 'PlayerId="0"' + CRLF
        + q + 'Car="%d"' % c + CRLF + q + 'TargetPI="%d"' % (
            -1 if c != -1 else 0) + CRLF
        + q + 'ParticipateInRace="%s" />' % flag + CRLF for c in cars)


def manifest_files(cache, snap=None):
    """Logical paths of a snapshot manifest (the AI_ files live in other CMS
    groups, not in the AIField zip). Defaults to the live snapshot."""
    return list(cache.files(snap or cache.live))


def ai_files(names):
    """{car: sorted [pi]} from logical names (AI_<car>_<pi>.xml)."""
    by_car = {}
    for n in names:
        m = AI_FILE.match(n)
        if m:
            by_car.setdefault(int(m.group(1)), []).append(int(m.group(2)))
    return {k: sorted(v) for k, v in by_car.items()}


def manifest_rows(roster, by_car, window=None):
    """ContentManifest rows. Rule (reproduces all 96 vanilla pairs):
    TargetPI=-1 -> lowest-PI file; window step -> highest-PI file <= step
    (clamped to the lowest). `window`=(min, max, step) or None (list mode,
    one row per distinct car)."""
    rows, seen = [], set()
    for car in roster:
        if car in seen:
            continue
        seen.add(car)
        pis = by_car.get(car)
        if not pis:
            raise FmError("car %d has no AI_<car>_<pi>.xml" % car)
        rows.append((car, -1, "AI_%d_%d" % (car, pis[0]), ".xml"))
        if window:
            steps = list(range(window[0], window[1] + 1, window[2]))
            if (window[1] - window[0]) % window[2]:
                steps.append(window[1])      # vanilla adds a row at an
                                             # off-grid maximum (e.g. 999)
            for tp in steps:
                fp = max([p for p in pis if p <= tp] or [pis[0]])
                rows.append((car, tp, "AI_%d_%d" % (car, fp), ".xml"))
    return rows


def rewrite_template(text, roster, by_car, window=None, drivatars=None,
                     frames=None, difficulty=None, rubber_banding=None,
                     behavior=None):
    """Template-mode document with a new EligibleCars/ContentManifest and,
    optionally, a new PI window, slot count (`drivatars`), progression
    frames (`frames` = [(PlayerPIRelativeToClass, lower, upper), ...]) and the
    metadata the template would otherwise impose: root `difficulty`
    (e.g. "Expert"), root `rubber_banding` (bool) and `behavior`
    ({SessionType: {SlowDown/CatchUp/Proximity/PosDifficultySpread/
    SlotCarRaceStart: bool}}) - see set_behavior. Every argument left as None
    means "keep the template value", so the output is unchanged."""
    st = parse(text)
    if st["mode"] != "AIDrivatarTemplate":
        raise FmError("rewrite_template: document is %s" % st["mode"])
    cfg = st["cfg"]
    win = window or (int(cfg["MinimumPI"]), int(cfg["MaximumPI"]),
                     int(cfg["PIStep"]))
    rows = manifest_rows(roster, by_car, win)
    i0, i1 = st["elig_span"]
    c0, c1 = st["cm_span"]
    if i1 != c0:
        raise FmError("AIField: unexpected gap between the two blocks")
    out = text[:i0] + render_elig(roster) + render_cm(rows) + text[c1:]
    if window:
        for key, val in (("MinimumPI", win[0]), ("MaximumPI", win[1]),
                         ("PIStep", win[2])):
            out = re.sub(r'(%s=")\d+(")' % key, r"\g<1>%d\2" % val, out, 1)
    if drivatars is not None:
        out = _set_slots(out, drivatars)
    if frames is not None:
        span = parse(out)["frames_span"]
        if span is None:
            raise FmError("AIField: no DrivatarProgressionFrames block")
        out = out[:span[0]] + render_frames(frames) + out[span[1]:]
    if difficulty is not None:
        out = _set_attr(out, "AIDifficulty", difficulty)
    if rubber_banding is not None:
        out = _set_attr(out, "AIRubberBandingEnabled",
                        "True" if rubber_banding else "False")
    if behavior is not None:
        out = set_behavior(out, behavior)
    return out


def _set_attr(text, name, value, count=1):
    """Replaces the value of the first `count` `name="..."` occurrences."""
    out, n = re.subn(r'(%s=")[^"]*(")' % name, r"\g<1>%s\2" % value,
                     text, count=count)
    if n != count:
        raise FmError("AIField: attribute %s not found" % name)
    return out


def behavior_span(text, session):
    """(start, end) of the `<RaceBehaviorSettings .../>` of `session`."""
    for m in RBS.finditer(text):
        if re.search(r'SessionType="%s"' % re.escape(session), m.group(0)):
            return m.span()
    raise FmError("AIField: no RaceBehaviorSettings for %r" % session)


def set_behavior(text, behavior):
    """`behavior` = {SessionType: {SlowDown: False, ...}} (keys of
    BEHAVIOR_KEYS). Only the named attributes change; the rest of the document,
    including the other session, stays byte-identical."""
    out = text
    for session, flags in behavior.items():
        if not isinstance(flags, dict) or not flags:
            raise FmError("AIField: behavior[%r] is empty" % session)
        i0, i1 = behavior_span(out, session)
        block = out[i0:i1]
        for key, val in flags.items():
            attr = BEHAVIOR_KEYS.get(key)
            if attr is None:
                raise FmError("AIField: behavior key %r (use %s)"
                              % (key, sorted(BEHAVIOR_KEYS)))
            if not isinstance(val, bool):
                raise FmError("AIField: behavior[%r][%r] must be true/false"
                              % (session, key))
            block, n = re.subn(r'%s="[^"]*"' % attr,
                               '%s="%s"' % (attr, "True" if val else "False"),
                               block, count=1)
            if n != 1:
                raise FmError("AIField: %s has no %s" % (session, attr))
        out = out[:i0] + block + out[i1:]
    return out


def _set_slots(text, n):
    """NumberOfDrivatars + the Car=-1 slot block of a template document."""
    i0 = text.find("  <AIDrivatars>" + CRLF)
    i1 = text.find("  </AIDrivatars>" + CRLF)
    if i0 < 0 or i1 < 0:
        raise FmError("AIField: AIDrivatars block not found")
    head = "  <AIDrivatars>" + CRLF
    slots = render_drivatars([-1] * n, 4, participate=False)
    text = text[:i0 + len(head)] + slots + text[i1:]
    return re.sub(r'(NumberOfDrivatars=")\d+(")', r"\g<1>%d\2" % n, text, 1)


def rewrite_list(text, lineup, by_car, eligible=None):
    """List-mode document: new lineup (23 slots, repeats weight a car) and one
    ContentManifest row per distinct car. EligibleCars is NOT the lineup in
    vanilla (117150001: 7 of its 15 cars), so it is kept unless `eligible`
    is given."""
    st = parse(text)
    if st["mode"] != "AIDrivatarList":
        raise FmError("rewrite_list: document is %s" % st["mode"])
    distinct = list(dict.fromkeys(lineup))
    rows = manifest_rows(distinct, by_car)
    i0 = text.find("  <AIDrivatars>" + CRLF)
    e1 = text.find(ELIG_HEAD)
    if i0 < 0 or e1 < i0:
        raise FmError("AIField: list document layout not recognised")
    head = "  <AIDrivatars>" + CRLF
    c0, c1 = st["cm_span"]
    top = text[:i0 + len(head)] + render_drivatars(lineup, 4) + \
        "  </AIDrivatars>" + CRLF
    mid = render_elig(st["elig"] if eligible is None else eligible) \
        + render_cm(rows)
    rest = text[c1:]
    j0 = rest.find("    <AIDrivatars>" + CRLF)
    j1 = rest.find("    </AIDrivatars>" + CRLF)
    if j0 < 0 or j1 < 0:
        raise FmError("AIField: nested AIDrivatars not found")
    rest = (rest[:j0 + len("    <AIDrivatars>" + CRLF)]
            + render_drivatars(lineup, 6) + rest[j1:])
    return top + mid + rest


# ------------------------------------------------------------- validation --
def validate(roster, by_car, cars=None):
    """Returns (errors, warnings): catalogue, always-on vetoes, AI_ coverage."""
    cars = cars if cars is not None else load_cars()
    cat = {c["id"]: c for c in cars}
    errs, warns = [], []
    for car in dict.fromkeys(roster):
        if car not in cat:
            errs.append("car %d not in the catalogue" % car)
        if car not in by_car:
            errs.append("car %d has no AI_<car>_<pi>.xml" % car)
    veto = sorted(set(roster) & denied_ids())
    if veto:
        errs.append("always-on vetoes: %s" % veto)
    return errs, warns


def coverage(roster, by_car, window):
    """{car: (lowest, [file pi per window step])} for the report."""
    out = {}
    for car in dict.fromkeys(roster):
        pis = by_car.get(car, [])
        if pis:
            used = [max([p for p in pis if p <= tp] or [pis[0]])
                    for tp in range(window[0], window[1] + 1, window[2])]
            out[car] = (pis[0], used)
    return out
