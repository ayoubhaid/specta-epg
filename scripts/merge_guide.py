"""Merge raw grabber XMLTV into provider channel IDs with best-source selection.

usage: merge_guide.py <raw.xml> <mapping.json> <out.xml>
Writes out.xml, out.xml.gz, channel_coverage.csv and source_coverage.csv.
"""
import sys
import json
import gzip
import csv
import os
import xml.etree.ElementTree as ET
from copy import deepcopy
from collections import defaultdict

raw_path, mapping_path, output_path = sys.argv[1:4]
with open(mapping_path, encoding="utf-8") as f:
    mapping = json.load(f)

try:
    raw_tv = ET.parse(raw_path).getroot()
except (FileNotFoundError, ET.ParseError, OSError) as exc:
    print(f"WARNING: no usable raw guide ({exc}); writing channels without programmes")
    raw_tv = ET.Element("tv")

programmes_by_channel = defaultdict(list)
for programme in raw_tv.findall("programme"):
    source_channel = programme.get("channel")
    if source_channel:
        programmes_by_channel[source_channel].append(programme)

source_stats = defaultdict(lambda: {"programmes": 0, "channels": 0})
for source_id, programmes in programmes_by_channel.items():
    source_stats[source_id]["programmes"] = len(programmes)

result = ET.Element("tv", {"generator-info-name": "specta-epg"})
written_ids = set()
channel_rows, source_rows = [], []
channels_with_programmes = 0
total_programmes = 0

for provider_id, item in mapping.items():
    if item.get("status") == "skipped_vod":
        continue

    candidates = item.get("candidates", [])
    candidate_counts = [(source_id, len(programmes_by_channel.get(source_id, [])))
                        for source_id in candidates]
    # Pick the candidate with the most programmes; keep mapping order as tie-breaker.
    selected_id, selected_count = max(candidate_counts, key=lambda pair: pair[1], default=(None, 0))
    selected_programmes = programmes_by_channel.get(selected_id, []) if selected_id else []
    if selected_count:
        channels_with_programmes += 1

    unique_names = item.get("names", [])
    output_ids = [item.get("primary", provider_id), *item.get("aliases", [])]
    for output_id in output_ids:
        if output_id in written_ids:
            continue
        written_ids.add(output_id)
        channel = ET.SubElement(result, "channel", id=output_id)
        for name in unique_names:
            ET.SubElement(channel, "display-name").text = name
        for programme in selected_programmes:
            cloned = deepcopy(programme)
            cloned.set("channel", output_id)
            result.append(cloned)
        total_programmes += len(selected_programmes)

    channel_rows.append([
        provider_id, item.get("primary", provider_id), unique_names[0] if unique_names else "",
        item.get("status", "unmatched"), item.get("match_method", ""),
        len(candidates), selected_id or "", selected_count,
        " | ".join(f"{source_id}:{count}" for source_id, count in candidate_counts),
    ])

    for source_id, count in candidate_counts:
        source_stats[source_id]["channels"] += 1
        source_rows.append([provider_id, source_id, count, source_id == selected_id])

os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
ET.indent(result)
xml_data = ET.tostring(result, encoding="utf-8", xml_declaration=True)
with open(output_path, "wb") as f:
    f.write(xml_data)
with gzip.open(output_path + ".gz", "wb") as f:
    f.write(xml_data)

channel_report = os.path.join(os.path.dirname(output_path), "channel_coverage.csv")
with open(channel_report, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["provider_channel_id", "xmltv_id", "channel_name", "match_status",
                     "match_method", "candidate_count", "selected_source",
                     "selected_programmes", "all_candidate_programmes"])
    writer.writerows(channel_rows)

source_report = os.path.join(os.path.dirname(output_path), "source_coverage.csv")
with open(source_report, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["provider_channel_id", "grabber_source_id", "programme_count", "selected"])
    writer.writerows(source_rows)

print(f"{len(written_ids)} output channel IDs written")
print(f"{channels_with_programmes} provider channels have programmes")
print(f"{total_programmes} programmes written")
print(f"{sum(len(values) for values in programmes_by_channel.values())} raw programmes")
