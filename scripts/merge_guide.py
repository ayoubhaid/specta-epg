"""Turn the grabber's raw guide into the final XMLTV for Specta.

usage: merge_guide.py <raw.xml> <mapping.json> <out.xml>
- every channel gets id = provider tvg-id (if the CSV has one) else its sp-xxxx id
- alias ids / duplicate feeds get the same programmes
- all playlist names are added as <display-name> so name-matching works too
"""
import sys, json, gzip
import xml.etree.ElementTree as ET
from copy import deepcopy

raw, mp, out = sys.argv[1:4]
mapping = json.load(open(mp))
import os
try:
    tv = ET.parse(raw).getroot()
except (FileNotFoundError, ET.ParseError) as e:
    print(f"WARNING: no usable raw guide ({e}); writing channels without programmes")
    tv = ET.Element("tv")
progs = {}
for p in tv.findall("programme"):
    progs.setdefault(p.get("channel"), []).append(p)

res = ET.Element("tv", {"generator-info-name": "specta-epg"})
written, with_data = set(), 0
for cid, m in mapping.items():
    if m["status"] == "skipped_vod":
        continue
    src = m.get("feeds_from", cid)
    plist = progs.get(src, [])
    for xid in [m["primary"], *m["aliases"]]:
        if xid in written:
            continue
        written.add(xid)
        ch = ET.SubElement(res, "channel", id=xid)
        for n in m["names"]:
            ET.SubElement(ch, "display-name").text = n
        for p in plist:
            q = deepcopy(p); q.set("channel", xid); res.append(q)
        with_data += bool(plist)
ET.indent(res)
data = ET.tostring(res, encoding="utf-8", xml_declaration=True)
open(out, "wb").write(data)
with gzip.open(out + ".gz", "wb") as g:
    g.write(data)
print(f"{len(written)} channels written, {with_data} with programmes, "
      f"{sum(len(v) for v in progs.values())} raw programmes")
