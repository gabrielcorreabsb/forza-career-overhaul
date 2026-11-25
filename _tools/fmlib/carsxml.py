"""BCSeriesSelectableCars.xml: one CarSelectCarRestrictions entry per series.

Without the entry the game throws (0xe06d7363) when the series is clicked
(F3_TEMPLATE 1.6). Text-level edit to keep the original bytes elsewhere.
"""

import re

from .core import FmError

LOGICAL = "BCSeriesSelectableCars.xml"


def block_re(series_id):
    return re.compile(r'<CarSelectCarRestrictions\s+SeriesId="%d">.*?'
                      r'</CarSelectCarRestrictions>' % series_id, re.S)


def series_ids(raw):
    return [int(v) for v in re.findall(r'SeriesId="(\d+)"', raw)]


CLASS_IDS = {"E": 0, "D": 1, "C": 2, "B": 3, "A": 4, "S": 5, "R": 6, "X": 8}


def add_entry(raw, donor_series, new_series, car_ids, list_type="Whitelist",
              class_id=None, severity=None, ranges=None, ownership=None,
              spec_division=None):
    """Clones the donor entry with `car_ids`, bumps ArrayLength. Default: a
    Whitelist (donor class/severity kept). list_type="Blacklist" mirrors a
    SelectableCars Blocklist; an empty Blacklist drops the list element and
    self-closes CarRestrictions, as the 15 vanilla ones do. class_id (letter
    in CLASS_IDS) and severity ("None"/"Strict") overwrite the donor's.
    spec_division (int 0-255) overwrites CarRestrictions@SeriesSpecDivisionId
    (the gamedb SeriesSpecDivisions id; 0 = off, as in every career entry).
    Returns the new XML text."""
    if list_type not in ("Whitelist", "Blacklist"):
        raise FmError("list_type must be Whitelist or Blacklist")
    if not car_ids and list_type == "Whitelist":
        raise FmError("an empty Whitelist is not a vanilla shape")
    if new_series in series_ids(raw):
        raise FmError("XML already has SeriesId=%d" % new_series)
    m = block_re(donor_series).search(raw)
    if m is None:
        raise FmError("XML has no donor entry SeriesId=%d" % donor_series)
    donor = m.group(0)
    body = re.sub(r'\n        <BlackOrWhitelist>.*?\n        </BlackOrWhitelist>',
                  '\x00LIST\x00', donor, flags=re.S)
    if body == donor:
        raise FmError("donor entry without a recognizable <BlackOrWhitelist>")
    if car_ids:
        newlist = '\n        <BlackOrWhitelist>' + ''.join(
            '\n          <CarListEntry\n            val="%d" />' % c
            for c in car_ids) + '\n        </BlackOrWhitelist>'
    else:
        newlist = ''
    block = body.replace('\x00LIST\x00', newlist)
    if not car_ids:
        # vanilla empty blacklist: CarRestrictions self-closes, no children
        block = re.sub(r'(BlackOrWhitelistType="\w+")>\s*</CarRestrictions>',
                       r'\1 />', block)
    block = block.replace('SeriesId="%d"' % donor_series,
                          'SeriesId="%d"' % new_series)
    block = re.sub(r'BlackOrWhitelistType="\w+"',
                   'BlackOrWhitelistType="%s"' % list_type, block)
    if class_id is not None:
        if class_id not in CLASS_IDS:
            raise FmError("class %r not in %s" % (class_id, sorted(CLASS_IDS)))
        block = re.sub(r'CarClassId="\d+"',
                       'CarClassId="%d"' % CLASS_IDS[class_id], block, count=1)
    if severity is not None:
        if severity not in ("None", "Strict"):
            raise FmError("severity must be None or Strict")
        block = re.sub(r'SeverityType="\w+"',
                       'SeverityType="%s"' % severity, block, count=1)
    if ownership is not None:
        if not isinstance(ownership, str) or not re.fullmatch(r"[A-Za-z]{1,24}", ownership):
            raise FmError("ownership must be a word of 1-24 letters")
        if re.search(r'Ownership="[^"]*"', block) is None:
            raise FmError("donor entry has no attribute Ownership")
        block = re.sub(r'Ownership="[^"]*"', 'Ownership="%s"' % ownership,
                       block, count=1)
    if spec_division is not None:
        if (isinstance(spec_division, bool) or not isinstance(spec_division, int)
                or not 0 <= spec_division <= 255):
            raise FmError("spec_division must be an integer 0-255")
        if re.search(r'SeriesSpecDivisionId="\d+"', block) is None:
            raise FmError("donor entry has no attribute SeriesSpecDivisionId")
        block = re.sub(r'SeriesSpecDivisionId="\d+"',
                       'SeriesSpecDivisionId="%d"' % spec_division, block,
                       count=1)
    if ranges is not None:
        if not isinstance(ranges, dict) or not ranges:
            raise FmError("ranges must be a non-empty object")
        for key, val in ranges.items():
            if isinstance(val, bool) or not isinstance(val, (int, float)):
                raise FmError("range %r must be numeric" % key)
            text = str(int(val)) if float(val).is_integer() else str(val)
            pat = re.compile(re.escape(key) + r'="[^"]*"')
            if pat.search(block) is None:
                raise FmError("donor entry has no attribute %s" % key)
            block = pat.sub('%s="%s"' % (key, text), block, count=1)

    n_before = len(series_ids(raw))
    mlen = re.search(r'ArrayLength="(\d+)"', raw)
    if mlen is None or int(mlen.group(1)) != n_before:
        raise FmError("ArrayLength(%s) != entries(%d)"
                      % (mlen.group(1) if mlen else "?", n_before))
    anchor = '\r\n  </CarSelectCarRestrictionsArray>'
    closing = anchor + '\r\n</CarSelectCollection>'
    if anchor in raw:
        new_raw = raw.replace(anchor, '\r\n    ' + block + anchor)
    elif raw.endswith('</CarSelectCarRestrictions>'):
        # defeito herdado (mc5x): XML sem as 2 tags de fechamento - restaura
        new_raw = raw + '\r\n    ' + block + closing
    else:
        raise FmError("unexpected XML ending %r" % raw[-60:])
    new_raw = new_raw.replace('ArrayLength="%d"' % n_before,
                              'ArrayLength="%d"' % (n_before + 1), 1)

    if len(series_ids(new_raw)) != n_before + 1:
        raise FmError("entries after insert != %d" % (n_before + 1))
    mnew = block_re(new_series).search(new_raw)
    vals = [int(v) for v in re.findall(r'val="(\d+)"', mnew.group(0))]
    if vals != list(car_ids):
        raise FmError("new entry car list mismatch")
    return new_raw
