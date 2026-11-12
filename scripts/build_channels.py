"""Match channels in data/channels.csv to iptv-org/epg site grabbers.

usage: build_channels.py <path-to-iptv-org-epg-clone> <out-dir>
Writes: custom.channels.xml (input for the grabber), mapping.json, coverage.csv
"""
import sys, json, glob, difflib, csv
import xml.etree.ElementTree as ET
from collections import defaultdict
import pandas as pd
from common import norm, is_vod, split_ids, COUNTRY

epg_dir, out = sys.argv[1], sys.argv[2]
SITE_PRIORITY = [l.strip() for l in open("data/site_priority.txt") if l.strip() and not l.startswith("#")]
prio = {s: i for i, s in enumerate(SITE_PRIORITY)}
BLOCK = {l.strip() for l in open("data/site_blocklist.txt") if l.strip() and not l.startswith("#")}

by_id, by_name = defaultdict(list), defaultdict(list)
for f in glob.glob(f"{epg_dir}/sites/*/*.channels.xml"):
    try:
        root = ET.parse(f).getroot()
    except ET.ParseError:
        continue
    for c in root.iter("channel"):
        e = dict(site=c.get("site"), site_id=c.get("site_id"), xmltv_id=c.get("xmltv_id") or "",
                 lang=c.get("lang") or "en", name=(c.text or "").strip())
        if not e["site"] or not e["site_id"] or e["site"] in BLOCK:
            continue
        if e["xmltv_id"]:
            by_id[e["xmltv_id"].split("@")[0].lower()].append(e)
        by_name[norm(e["name"])].append(e)
all_names = list(by_name)

def best(entries, cc):
    def key(e):
        suffix = e["xmltv_id"].split("@")[0].rsplit(".", 1)[-1].lower()
        return (0 if cc and suffix == cc else 1, prio.get(e["site"], 999), e["site"])
    return sorted(entries, key=key)[0]

df = pd.read_csv("data/channels.csv")
mapping, rows = {}, []
for r in df.itertuples():
    cc = COUNTRY.get(r.region_code) if isinstance(r.region_code, str) else None
    ids = split_ids(r.epg_ids)
    names = [r.channel_name] + [n.strip() for n in str(r.playlist_names).split(" | ")]
    status, hit, how = "unmatched", None, ""
    if is_vod(r.channel_name):
        status = "skipped_vod"
    else:
        for i in ids:
            if i.lower() in by_id:
                hit, how = best(by_id[i.lower()], cc), "epg_id"; break
        if not hit:
            for n in map(norm, names):
                if n and n in by_name:
                    hit, how = best(by_name[n], cc), "name"; break
        if not hit:
            n = norm(r.channel_name)
            m = difflib.get_close_matches(n, all_names, n=1, cutoff=0.92) if len(n) > 4 else []
            if m:
                hit, how = best(by_name[m[0]], cc), "fuzzy"
        if hit:
            status = "matched"
    primary = ids[0] if ids else r.channel_id
    mapping[r.channel_id] = dict(primary=primary, aliases=ids[1:], names=sorted(set(names)),
                                 status=status, source=hit)
    rows.append([r.channel_id, r.broadcaster, r.channel_name, status, how,
                 hit["site"] if hit else "", hit["site_id"] if hit else ""])

seen, root = {}, ET.Element("channels")
for cid, m in mapping.items():
    s = m["source"]
    if not s:
        continue
    k = (s["site"], s["site_id"])
    if k in seen:
        m["feeds_from"] = seen[k]
        continue
    seen[k] = cid
    el = ET.SubElement(root, "channel", site=s["site"], lang=s["lang"],
                       xmltv_id=cid, site_id=s["site_id"])
    el.text = s["name"] or m["names"][0]
ET.indent(root)
ET.ElementTree(root).write(f"{out}/custom.channels.xml", encoding="utf-8", xml_declaration=True)
json.dump(mapping, open(f"{out}/mapping.json", "w"), ensure_ascii=False)
with open(f"{out}/coverage.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["channel_id", "broadcaster", "channel_name", "status", "how", "site", "site_id"]); w.writerows(rows)
cov = pd.DataFrame(rows, columns=["id", "b", "n", "status", "how", "s", "sid"])
print(cov.status.value_counts().to_string())
print(cov.assign(ok=cov.status == "matched").groupby("b").ok.agg(["sum", "count"]).to_string())
