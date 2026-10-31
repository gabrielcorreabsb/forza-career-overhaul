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


def add_entry(raw, donor_series, new_series, car_ids):
    """Clones the donor entry as a Whitelist with `car_ids`, bumps ArrayLength.
    Returns the new XML text."""
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
    newlist = '\n        <BlackOrWhitelist>' + ''.join(
        '\n          <CarListEntry\n            val="%d" />' % c
        for c in car_ids) + '\n        </BlackOrWhitelist>'
    block = body.replace('\x00LIST\x00', newlist)
    block = block.replace('SeriesId="%d"' % donor_series,
                          'SeriesId="%d"' % new_series)
    block = block.replace('BlackOrWhitelistType="Blacklist"',
                          'BlackOrWhitelistType="Whitelist"')
    if 'BlackOrWhitelistType="Whitelist"' not in block:
        raise FmError("donor entry is not a Whitelist")

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
