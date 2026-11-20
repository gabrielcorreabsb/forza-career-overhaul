#!/usr/bin/env python3
"""apply_kit.py - apply small graphics kits to loose XML files of the FM8 install.

Lab copy (20/11/2026). Differences from the first version kept in the sibling graphics
folder: it no longer writes lab/_extract (the only vanilla reference is
graphics/_vanilla, filled on the first edit of each file), and kits live in
graphics_kits/render. State and originals still live in the graphics folder (outside git).

A kit is graphics_kits/render/<id>.json:

  {"id": "V1", "description": "...",
   "edits": [{"file": "pcfamily/renderscenarios/ultra/race.xml",
              "key": "DXRRoughReflectionsFullRange", "attr": "value",
              "value": "1", "occurrence": 1, "insert_after": "DXRCarLODBias"}]}

Edits are textual: bytes outside the edited attribute stay identical, comments
are ignored when locating a key and duplicate keys are addressed by occurrence.
"insert_after" is only used when the key does not exist in the file yet.
In the options file, "option" + "option_value" select where the Property lives:
  {"file": "base/gametunablesettings/userconfigoptions.xml",
   "option": "IDS_ShadowQuality_Label", "option_value": "IDS_Ultra",
   "key": "PSSMShadowsResolution", "attr": "Resolution_Level1", "value": "4096x4096"}

The first time a file is touched its original goes to graphics/_vanilla/media/.
Applied kits are recorded in graphics/_state/.
Usage:
  python _tools/graphics/apply_kit.py --dry-run V1
  python _tools/graphics/apply_kit.py --apply V1
  python _tools/graphics/apply_kit.py --restore V1      (undo one kit, keep the others)
  python _tools/graphics/apply_kit.py --restore-all     (back to the originals)
  python _tools/graphics/apply_kit.py --status
  python _tools/graphics/apply_kit.py --self-test
"""

import argparse
import difflib
import hashlib
import json
import os
import re
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

LAB = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# the graphics folder (originals, state) lives OUTSIDE git, next to the lab
GRAPHICS = os.environ.get("FM_GRAPHICS", os.path.join(os.path.dirname(LAB), "graphics"))
# kits: FM_GRAPHICS_KITS overrides the folder (a clone without our kits can point it at its own)
KITS = os.environ.get("FM_GRAPHICS_KITS", os.path.join(LAB, "graphics_kits", "render"))
GAME = os.environ.get("FM_INSTALL",
                      r"F:\SteamLibrary\steamapps\common\Forza Motorsport")
EXE_NAME = "forza_steamworks_release_final.exe"
MAX_DRYRUN_AGE_S = 30 * 60
ALLOWED = (
    re.compile(r"^pcfamily/renderscenarios/ultra/[a-z0-9-]+\.xml$"),
    re.compile(r"^pcfamily/tracks/[a-z0-9]+/tracksettings\.xml$"),
    re.compile(r"^base/tracks/basetracksettings\.xml$"),
    re.compile(r"^base/gametunablesettings/userconfigoptions\.xml$"),
)
KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
VALUE_RE = re.compile(r'^[A-Za-z0-9_.+ x-]*$')


class KitError(Exception):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    with open(path, "rb") as f:
        return f.read()


def write_atomic(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp_apply_kit"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def write_in_place(path, data):
    """For game files: users may write them but not delete or rename over them."""
    with open(path, "wb") as f:
        f.write(data)


def mask_comments(text):
    return re.sub(r"<!--.*?-->", lambda m: " " * len(m.group(0)), text, flags=re.S)


def find_option_property(masked, edit):
    """Locate <Property id=key> inside one <Value> of one <Option>."""
    where = "%s: %s/%s" % (edit["file"], edit["option"], edit.get("option_value"))
    option = re.search(r'<Option\s[^>]*\bname="%s"[^>]*>' % re.escape(edit["option"]),
                       masked)
    if not option:
        raise KitError("%s: option not found" % where)
    option_end = masked.find("</Option>", option.end())
    value = re.compile(r'<Value\s[^>]*\bname="%s"[^>]*>'
                       % re.escape(edit.get("option_value", ""))).search(
                           masked, option.end(), option_end)
    if not value:
        raise KitError("%s: value not found" % where)
    value_end = masked.find("</Value>", value.end())
    pattern = re.compile(r'<Property\s[^>]*\bid="%s"[^>]*>' % re.escape(edit["key"]))
    tags = list(pattern.finditer(masked, value.end(), value_end))
    if not tags:
        raise KitError("%s: property %s not found" % (where, edit["key"]))
    return tags


def apply_edit(data, edit):
    """Return data with one edit applied. Raises KitError if it cannot apply."""
    if b"\0" in data:
        raise KitError("%s: not a single-byte text file" % edit["file"])
    text = data.decode("latin-1")
    masked = mask_comments(text)
    key, attr, value = edit["key"], edit.get("attr", "value"), edit["value"]
    occurrence = edit.get("occurrence", 1)
    if "option" in edit:
        tags = find_option_property(masked, edit)
    else:
        pattern = re.compile(r"<%s(?=[\s/>])[^>]*>" % re.escape(key))
        tags = list(pattern.finditer(masked))
    if tags:
        if occurrence < 1 or occurrence > len(tags):
            raise KitError("%s: %s occurrence %d not found (%d present)"
                           % (edit["file"], key, occurrence, len(tags)))
        tag = tags[occurrence - 1]
        found = re.search(r'\b%s\s*=\s*"([^"]*)"' % re.escape(attr), tag.group(0))
        if not found:
            raise KitError("%s: %s has no attribute %s" % (edit["file"], key, attr))
        if found.group(1) == value:
            raise KitError("%s: %s already has %s=%s; the edit changes nothing"
                           % (edit["file"], key, attr, value))
        start = tag.start() + found.start(1)
        end = tag.start() + found.end(1)
        return (text[:start] + value + text[end:]).encode("latin-1")

    anchor_key = edit.get("insert_after")
    if not anchor_key:
        raise KitError("%s: %s not found and the edit has no insert_after"
                       % (edit["file"], key))
    anchor_re = re.compile(r"<%s(?=[\s/>])[^>]*>" % re.escape(anchor_key))
    anchor = anchor_re.search(masked)
    if not anchor:
        raise KitError("%s: anchor %s not found" % (edit["file"], anchor_key))
    line_start = text.rfind("\n", 0, anchor.start()) + 1
    indent = re.match(r"[ \t]*", text[line_start:]).group(0)
    eol = "\r\n" if "\r\n" in text else "\n"
    line_end = text.find("\n", anchor.end())
    if line_end < 0:
        raise KitError("%s: anchor %s has no line end" % (edit["file"], anchor_key))
    new = '%s<%s %s="%s"/>%s' % (indent, key, attr, value, eol)
    at = line_end + 1
    return (text[:at] + new + text[at:]).encode("latin-1")


def validate_kit(kit):
    if not isinstance(kit.get("edits"), list) or not kit["edits"]:
        raise KitError("kit has no edits")
    if not re.match(r"^[A-Za-z0-9_-]+$", str(kit.get("id", ""))):
        raise KitError("invalid kit id")
    for edit in kit["edits"]:
        rel = edit.get("file", "")
        if not any(rule.match(rel) for rule in ALLOWED):
            raise KitError("path outside the allowed graphics files: %r" % rel)
        if not KEY_RE.match(edit.get("key", "")):
            raise KitError("invalid key: %r" % edit.get("key"))
        if not KEY_RE.match(edit.get("attr", "value")):
            raise KitError("invalid attribute: %r" % edit.get("attr"))
        if edit.get("insert_after") and not KEY_RE.match(edit["insert_after"]):
            raise KitError("invalid anchor: %r" % edit["insert_after"])
        if "option" in edit and not (KEY_RE.match(edit["option"])
                                     and KEY_RE.match(edit.get("option_value", ""))):
            raise KitError("invalid option locator: %r" % edit)
        if not VALUE_RE.match(str(edit.get("value", "!"))):
            raise KitError("invalid value: %r" % edit.get("value"))


def parses(data):
    try:
        ET.fromstring(data)
        return True
    except ET.ParseError:
        return False


def check_xml(rel, data, original=None):
    """Refuse XML broken by an edit; files that never parsed are not blamed."""
    if original is not None and not parses(original):
        return
    if not parses(data):
        raise KitError("%s: invalid XML after the edit" % rel)


class Env:
    def __init__(self, game, graphics, kits_dir=None, processes=None):
        self.game = game
        self.install = os.path.join(game, "media")
        self.vanilla = os.path.join(graphics, "_vanilla", "media")
        self.state_dir = os.path.join(graphics, "_state")
        self.kits_dir = kits_dir or KITS
        self.state_file = os.path.join(self.state_dir, "applied.json")
        self.log_file = os.path.join(self.state_dir, "log.jsonl")
        self.processes = processes or self._real_processes

    @staticmethod
    def _real_processes():
        sys.path.insert(0, os.path.join(LAB, "_tools"))
        import cache_edit  # noqa: E402  (fails closed if tasklist fails)
        return cache_edit.forza_processes()

    def path(self, root, rel):
        return os.path.join(root, *rel.split("/"))

    def load_kit(self, kit_id):
        path = os.path.join(self.kits_dir, kit_id + ".json")
        if not os.path.exists(path):
            raise KitError("kit not found: %s" % path)
        raw = read(path)
        kit = json.loads(raw.decode("utf-8"))
        validate_kit(kit)
        if kit["id"] != kit_id:
            raise KitError("kit id %s does not match its file name" % kit["id"])
        return kit, raw

    def applied(self):
        if not os.path.exists(self.state_file):
            return []
        return json.loads(read(self.state_file).decode("utf-8"))

    def save_applied(self, applied):
        data = json.dumps(applied, indent=2, ensure_ascii=False).encode("utf-8")
        write_atomic(self.state_file, data)

    def log(self, action, kit_id, files):
        os.makedirs(self.state_dir, exist_ok=True)
        row = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "action": action,
               "kit": kit_id, "files": files}
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def require_closed(self):
        running = self.processes()
        if running:
            raise KitError("close the game first; running: %s" % ", ".join(running))

    def expected(self, rel, applied):
        """Content a file should have now, from its original plus applied kits."""
        original = self.path(self.vanilla, rel)
        if not os.path.exists(original):
            return None
        data = read(original)
        for entry in applied:
            for edit in entry["edits"]:
                if edit["file"] == rel:
                    data = apply_edit(data, edit)
        return data

    def current(self, rel, applied):
        """Read the install file and refuse any divergence from the recorded
        state (original from _vanilla plus the applied kits)."""
        target = self.path(self.install, rel)
        if not os.path.exists(target):
            raise KitError("file not found: %s" % target)
        data = read(target)
        want = self.expected(rel, applied)
        if want is not None and want != data:
            raise KitError("%s: differs from the recorded state; a game update or "
                           "another edit changed it" % rel)
        return data

    def plan(self, kit, applied):
        if any(entry["id"] == kit["id"] for entry in applied):
            raise KitError("kit %s is already applied" % kit["id"])
        before, after = {}, {}
        for edit in kit["edits"]:
            rel = edit["file"]
            if rel not in before:
                before[rel] = self.current(rel, applied)
                after[rel] = before[rel]
            after[rel] = apply_edit(after[rel], edit)
        for rel, data in after.items():
            check_xml(rel, data, before[rel])
        return before, after

    def check_exe(self, kit):
        exe = read(os.path.join(self.game, EXE_NAME))
        for edit in kit["edits"]:
            if edit["key"].encode("ascii") not in exe:
                raise KitError("key %s is not in the game executable; it would "
                               "probably be ignored" % edit["key"])

    def dryrun_key(self, raw, before):
        h = hashlib.sha256(raw)
        for rel in sorted(before):
            h.update(rel.encode("utf-8"))
            h.update(before[rel])
        return h.hexdigest()

    def marker(self, kit_id):
        return os.path.join(self.state_dir, "dryrun_%s.json" % kit_id)

    def dry_run(self, kit_id, out=print):
        kit, raw = self.load_kit(kit_id)
        self.check_exe(kit)
        before, after = self.plan(kit, self.applied())
        for rel in sorted(before):
            if not os.path.exists(self.path(self.vanilla, rel)):
                out("  NOTE %s: first edit, so this install file becomes the vanilla snapshot; "
                    "it must be unmodified (run Steam verify files if unsure)" % rel)
        changed = 0
        for rel in sorted(before):
            old = before[rel].decode("latin-1").splitlines()
            new = after[rel].decode("latin-1").splitlines()
            for line in difflib.unified_diff(old, new, rel, rel, lineterm="", n=0):
                out(line)
                if line[:1] in "+-" and line[:3] not in ("+++", "---"):
                    changed += 1
            out("  %s  %s -> %s" % (rel, sha(before[rel])[:16], sha(after[rel])[:16]))
        data = json.dumps({"key": self.dryrun_key(raw, before),
                           "time": time.time()}).encode("utf-8")
        write_atomic(self.marker(kit_id), data)
        out("DRY-RUN OK: %s, %d file(s), %d changed line(s). Nothing was written "
            "to the game." % (kit_id, len(before), changed))

    def write_both(self, contents):
        """Write the install files; on failure put everything back. (The name is
        historical: the tool no longer writes lab/_extract.)"""
        previous = {}
        try:
            for rel, data in contents.items():
                path = self.path(self.install, rel)
                previous[path] = read(path)
                write_in_place(path, data)
                if sha(read(path)) != sha(data):
                    raise KitError("hash mismatch after writing %s" % path)
        except (OSError, KitError) as e:
            failed = []
            for path, data in previous.items():
                try:
                    write_in_place(path, data)
                    if read(path) != data:
                        failed.append(path)
                except OSError:
                    failed.append(path)
            if failed:
                raise KitError("write failed (%s) and these files could NOT be "
                               "restored: %s" % (e, ", ".join(failed)))
            raise KitError("write failed, previous files restored: %s" % e)

    def apply(self, kit_id, out=print):
        self.require_closed()
        kit, raw = self.load_kit(kit_id)
        applied = self.applied()
        before, after = self.plan(kit, applied)
        marker = self.marker(kit_id)
        if not os.path.exists(marker):
            raise KitError("run --dry-run %s first" % kit_id)
        info = json.loads(read(marker).decode("utf-8"))
        if time.time() - info["time"] > MAX_DRYRUN_AGE_S:
            raise KitError("dry-run is older than 30 minutes; run it again")
        if info["key"] != self.dryrun_key(raw, before):
            raise KitError("kit or files changed since the dry-run; run it again")
        for rel, data in before.items():
            original = self.path(self.vanilla, rel)
            if not os.path.exists(original):
                write_atomic(original, data)
        self.write_both(after)
        applied.append({"id": kit_id, "description": kit.get("description", ""),
                        "edits": kit["edits"],
                        "applied_at": time.strftime("%Y-%m-%d %H:%M:%S")})
        self.save_applied(applied)
        os.remove(marker)
        self.log("apply", kit_id, {r: sha(d) for r, d in after.items()})
        out("APPLIED %s: %s" % (kit_id, ", ".join(sorted(after))))

    def restore(self, kit_id=None, out=print):
        self.require_closed()
        applied = self.applied()
        if kit_id is None:
            removed, remaining = applied, []
        else:
            removed = [e for e in applied if e["id"] == kit_id]
            remaining = [e for e in applied if e["id"] != kit_id]
            if not removed:
                raise KitError("kit %s is not applied" % kit_id)
        files = sorted({ed["file"] for entry in removed for ed in entry["edits"]})
        contents = {}
        for rel in files:
            self.current(rel, applied)
            contents[rel] = self.expected(rel, remaining)
            if contents[rel] is None:
                raise KitError("%s: original missing from _vanilla" % rel)
        self.write_both(contents)
        self.save_applied(remaining)
        self.log("restore", kit_id or "ALL", {r: sha(d) for r, d in contents.items()})
        out("RESTORED %s: %s" % (kit_id or "all kits", ", ".join(files) or "nothing"))

    def status(self, out=print):
        applied = self.applied()
        out("Applied kits: %s" % (", ".join(e["id"] for e in applied) or "none"))
        files = sorted({ed["file"] for entry in applied for ed in entry["edits"]})
        for rel in files:
            try:
                self.current(rel, applied)
                out("  ok        %s" % rel)
            except KitError as e:
                out("  PROBLEM   %s" % e)


def self_test():
    rel = "pcfamily/renderscenarios/ultra/race.xml"
    xml = ('<DynamicRenderSettings>\r\n'
           '  <!-- <SSRQuality Active="9"/> -->\r\n'
           '  <SSRQuality Active="1" />\r\n'
           '  <Twice value ="1"/>\r\n'
           '  <Twice value="2"/>\r\n'
           '  <Anchor value="0"/>\r\n'
           '</DynamicRenderSettings>\r\n').encode("latin-1")
    results = []

    def check(name, condition):
        results.append(bool(condition))
        print("%s %s" % ("ok  " if condition else "FAIL", name))

    def refused(name, func):
        try:
            func()
            check(name, False)
        except KitError:
            check(name, True)

    with tempfile.TemporaryDirectory(prefix="apply_kit_test_") as tmp:
        game = os.path.join(tmp, "game")
        graphics = os.path.join(tmp, "graphics")
        running = []
        env = Env(game, graphics, os.path.join(tmp, "kits"), processes=lambda: list(running))
        os.makedirs(env.kits_dir)
        write_atomic(env.path(env.install, rel), xml)
        write_atomic(os.path.join(game, EXE_NAME),
                     b"SSRQuality Twice NewKey Anchor")
        quiet = lambda *_: None

        def kit(kit_id, *edits):
            for edit in edits:
                edit.setdefault("file", rel)
            write_atomic(os.path.join(env.kits_dir, kit_id + ".json"),
                         json.dumps({"id": kit_id, "edits": list(edits)}).encode())

        kit("A", {"key": "Twice", "value": "7", "occurrence": 2})
        kit("B", {"key": "NewKey", "value": "1", "insert_after": "Anchor"})
        kit("C", {"key": "SSRQuality", "attr": "Active", "value": "0"})
        write_atomic(os.path.join(env.kits_dir, "OUT.json"),
                     json.dumps({"id": "OUT", "edits": [
                         {"file": "pcfamily/cms/x.xml", "key": "A", "value": "1"}
                     ]}).encode())
        kit("MISS", {"key": "Nope", "value": "1"})
        kit("SAME", {"key": "Anchor", "value": "0"})

        refused("refuses apply without dry-run", lambda: env.apply("A", quiet))
        refused("refuses a path outside the list", lambda: env.dry_run("OUT", quiet))
        refused("refuses a missing key", lambda: env.dry_run("MISS", quiet))
        refused("refuses an edit that changes nothing", lambda: env.dry_run("SAME", quiet))

        kit("BADEXE", {"key": "NotInExe", "value": "1", "insert_after": "Anchor"})
        refused("refuses a key missing from the exe", lambda: env.dry_run("BADEXE", quiet))

        env.dry_run("A", quiet)
        check("dry-run writes nothing to the game", read(env.path(env.install, rel)) == xml)
        running.append("forza_steamworks_release_final.exe")
        refused("refuses apply with the game open", lambda: env.apply("A", quiet))
        running.clear()

        write_atomic(env.path(env.install, rel), xml + b" ")
        write_atomic(env.path(env.vanilla, rel), xml)
        refused("refuses when the install differs from the recorded state", lambda: env.apply("A", quiet))
        write_atomic(env.path(env.install, rel), xml)
        os.remove(env.path(env.vanilla, rel))

        env.apply("A", quiet)
        now = read(env.path(env.install, rel))
        check("edits only the requested duplicate",
              b'<Twice value ="1"/>' in now and b'<Twice value="7"/>' in now)
        check("only the value bytes changed", now == xml.replace(b'value="2"', b'value="7"'))
        check("original saved in _vanilla", read(env.path(env.vanilla, rel)) == xml)
        refused("refuses applying a kit twice", lambda: env.dry_run("A", quiet))

        env.dry_run("B", quiet)
        env.apply("B", quiet)
        check("inserts with same indent and CRLF",
              b'  <Anchor value="0"/>\r\n  <NewKey value="1"/>\r\n'
              in read(env.path(env.install, rel)))
        env.dry_run("C", quiet)
        env.apply("C", quiet)
        now = read(env.path(env.install, rel))
        check("ignores keys inside comments",
              b'<!-- <SSRQuality Active="9"/> -->' in now
              and b'<SSRQuality Active="0" />' in now)

        write_atomic(env.path(env.install, rel), now + b" ")
        refused("detects a file changed outside the tool", lambda: env.restore("B", quiet))
        write_atomic(env.path(env.install, rel), now)

        env.restore("B", quiet)
        now = read(env.path(env.install, rel))
        check("restoring a middle kit keeps the others",
              b"NewKey" not in now and b'<Twice value="7"/>' in now
              and b'Active="0"' in now)
        env.restore(None, quiet)
        check("restore-all returns the original bytes",
              read(env.path(env.install, rel)) == xml)
        check("no kit left applied", env.applied() == [])

        env.dry_run("A", quiet)
        marker = json.loads(read(env.marker("A")).decode())
        marker["time"] -= MAX_DRYRUN_AGE_S + 1
        write_atomic(env.marker("A"), json.dumps(marker).encode())
        refused("refuses a stale dry-run", lambda: env.apply("A", quiet))

        opt_rel = "base/gametunablesettings/userconfigoptions.xml"
        opt_xml = ('<UserConfig><Options>\n'
                   '<Option name="IDS_A_Label" id="1">\n'
                   '<Value name="IDS_High" id="2"><Property id="P" value="1"/></Value>\n'
                   '<Value name="IDS_Ultra" id="3"><Property id="P" value="2"/></Value>\n'
                   '</Option>\n'
                   '<Option name="IDS_B_Label" id="2">\n'
                   '<Value name="IDS_Ultra" id="3"><Property id="P" value="3"/></Value>\n'
                   '</Option>\n'
                   '</Options></UserConfig>\n').encode("latin-1")
        write_atomic(env.path(env.install, opt_rel), opt_xml)
        write_atomic(os.path.join(game, EXE_NAME), b"SSRQuality Twice NewKey Anchor P")
        kit("OPT", {"file": opt_rel, "option": "IDS_A_Label",
                    "option_value": "IDS_Ultra", "key": "P", "value": "9"})
        env.dry_run("OPT", quiet)
        env.apply("OPT", quiet)
        check("edits only the chosen option value",
              read(env.path(env.install, opt_rel))
              == opt_xml.replace(b'<Property id="P" value="2"/>',
                                 b'<Property id="P" value="9"/>'))
        kit("OPTBAD", {"file": opt_rel, "option": "IDS_A_Label",
                       "option_value": "IDS_Nope", "key": "P", "value": "1"})
        refused("refuses a missing option value", lambda: env.dry_run("OPTBAD", quiet))
        env.restore("OPT", quiet)
        check("restores the option file", read(env.path(env.install, opt_rel)) == opt_xml)

        real_write = write_in_place
        calls = []

        def failing_write(path, data):
            calls.append(path)
            if len(calls) == 2:
                raise OSError("simulated lock")
            real_write(path, data)

        env.dry_run("OPT", quiet)
        globals()["write_in_place"] = failing_write
        try:
            refused("reports a failed write", lambda: env.write_both(
                {rel: xml + b" ", opt_rel: opt_xml + b" "}))
        finally:
            globals()["write_in_place"] = real_write
        check("a failed write leaves the files as they were",
              read(env.path(env.install, opt_rel)) == opt_xml
              and read(env.path(env.install, rel)) == xml)

    print("SELF-TEST: %d checks, %d failed" % (len(results), results.count(False)))
    return 0 if all(results) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", metavar="KIT")
    group.add_argument("--apply", metavar="KIT")
    group.add_argument("--restore", metavar="KIT")
    group.add_argument("--restore-all", action="store_true")
    group.add_argument("--status", action="store_true")
    group.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    env = Env(GAME, GRAPHICS)
    try:
        if args.dry_run:
            env.dry_run(args.dry_run)
        elif args.apply:
            env.apply(args.apply)
        elif args.restore:
            env.restore(args.restore)
        elif args.restore_all:
            env.restore()
        else:
            env.status()
    except (KitError, RuntimeError, OSError, ValueError) as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
