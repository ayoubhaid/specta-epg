"""Match provider channels to available iptv-org EPG grabbers.

usage: build_channels.py <path-to-iptv-org-epg-clone> <out-dir>
Writes custom.channels.xml, mapping.json and coverage.csv.
"""
import sys
import json
import glob
import difflib
import csv
import os
import xml.etree.ElementTree as ET
from collections import defaultdict
import pandas as pd
from common import norm, is_vod, split_ids, COUNTRY

epg_dir, out_dir = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)

def read_lines(path):
    with open(path, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.lstrip().startswith("#")]

SITE_PRIORITY = read_lines("data/site_priority.txt")
prio = {site: i for i, site in enumerate(SITE_PRIORITY)}
BLOCK = set(read_lines("data/site_blocklist.txt"))

by_id, by_name = defaultdict(list), defaultdict(list)
for path in glob.glob(os.path.join(epg_dir, "sites", "*", "*.channels.xml")):
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        continue
    for channel in root.iter("channel"):
        item = {
            "site": channel.get("site"),
            "site_id": channel.get("site_id"),
            "xmltv_id": channel.get("xmltv_id") or "",
            "lang": channel.get("lang") or "en",
            "name": (channel.text or "").strip(),
        }
        if not item["site"] or not item["site_id"] or item["site"] in BLOCK:
            continue
        if item["xmltv_id"]:
            by_id[item["xmltv_id"].split("@")[0].lower()].append(item)
        normalized = norm(item["name"])
        if normalized:
            by_name[normalized].append(item)

all_names = list(by_name)
MAX_CANDIDATES = 8

def ranked(entries, country_code):
    def rank(item):
        suffix = item["xmltv_id"].split("@")[0].rsplit(".", 1)[-1].lower()
        return (0 if country_code and suffix == country_code else 1,
                prio.get(item["site"], 999), item["site"], item["site_id"])
    result, seen = [], set()
    for item in sorted(entries, key=rank):
        key = (item["site"], item["site_id"])
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result

df = pd.read_csv("data/channels.csv").fillna("")
mapping, rows = {}, []
for row in df.itertuples(index=False):
    region = getattr(row, "region_code", "")
    country = COUNTRY.get(region) if isinstance(region, str) else None
    ids = split_ids(getattr(row, "epg_ids", ""))
    channel_name = str(getattr(row, "channel_name", "")).strip()
    playlist_names = str(getattr(row, "playlist_names", "")).split(" | ")
    names = [channel_name] + [name.strip() for name in playlist_names if name.strip()]
    status, method, pool = "unmatched", "", []

    if is_vod(channel_name):
        status = "skipped_vod"
    else:
        for external_id in ids:
            matches = by_id.get(external_id.lower(), [])
            if matches:
                pool.extend(ranked(matches, country))
                method = method or "epg_id"
        for name in names:
            normalized = norm(name)
            matches = by_name.get(normalized, []) if normalized else []
            if matches:
                pool.extend(ranked(matches, country))
                method = method or "name"

        if not pool:
            normalized = norm(channel_name)
            close = difflib.get_close_matches(normalized, all_names, n=1, cutoff=0.92) if len(normalized) > 4 else []
            if close:
                pool = ranked(by_name[close[0]], country)
                method = "fuzzy"

        candidates, seen = [], set()
        for item in pool:
            key = (item["site"], item["site_id"])
            if key not in seen:
                seen.add(key)
                candidates.append(item)
            if len(candidates) >= MAX_CANDIDATES:
                break
        pool = candidates
        if pool:
            status = "matched"

    primary = ids[0] if ids else str(getattr(row, "channel_id"))
    mapping[str(getattr(row, "channel_id"))] = {
        "primary": primary,
        "aliases": ids[1:],
        "names": sorted(set(name for name in names if name)),
        "status": status,
        "match_method": method,
        "sources": pool,
        "candidate_sources": [],
    }
    rows.append([
        getattr(row, "channel_id"), getattr(row, "broadcaster"), channel_name,
        status, method,
        " | ".join(f'{item["site"]}:{item["site_id"]}' for item in pool),
        len(pool),
    ])

grab_ids, root = {}, ET.Element("channels")
for channel_id, item in mapping.items():
    item["candidates"] = []
    for source in item.pop("sources"):
        key = (source["site"], source["site_id"])
        if key not in grab_ids:
            grab_id = f"g{len(grab_ids)}"
            grab_ids[key] = grab_id
            element = ET.SubElement(
                root, "channel", site=source["site"], lang=source["lang"],
                xmltv_id=grab_id, site_id=source["site_id"]
            )
            element.text = source["name"] or (item["names"][0] if item["names"] else channel_id)
        item["candidates"].append(grab_ids[key])
        item["candidate_sources"].append({
            "grab_id": grab_ids[key],
            "site": source["site"],
            "site_id": source["site_id"],
            "xmltv_id": source["xmltv_id"],
            "name": source["name"],
            "lang": source["lang"],
        })

ET.indent(root)
ET.ElementTree(root).write(
    os.path.join(out_dir, "custom.channels.xml"),
    encoding="utf-8", xml_declaration=True
)
with open(os.path.join(out_dir, "mapping.json"), "w", encoding="utf-8") as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)

with open(os.path.join(out_dir, "source_manifest.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "grab_id", "site", "site_id", "xmltv_id", "name", "lang"
    ])
    writer.writeheader()
    manifest = {}
    for item in mapping.values():
        for source in item.get("candidate_sources", []):
            manifest[source["grab_id"]] = source
    writer.writerows(manifest[key] for key in sorted(manifest, key=lambda x: int(x[1:])))

with open(os.path.join(out_dir, "coverage.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["channel_id", "broadcaster", "channel_name", "status",
                     "match_method", "sources", "candidate_count"])
    writer.writerows(rows)

coverage = pd.DataFrame(rows, columns=[
    "channel_id", "broadcaster", "channel_name", "status",
    "match_method", "sources", "candidate_count"
])
print("Channel matching:")
print(coverage["status"].value_counts().to_string())
print("\nMatching by broadcaster:")
print(coverage.assign(matched=coverage.status == "matched")
      .groupby("broadcaster").matched.agg(["sum", "count"]).to_string())
print(f"\nUnique grabber channel entries: {len(grab_ids)}")
