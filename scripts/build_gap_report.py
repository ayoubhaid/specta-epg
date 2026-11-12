"""Build a focused EPG gap report for English-speaking sports markets.

Inputs: provider channel inventory plus matching and post-scrape coverage reports.
Output: priority_gaps.csv, ordered by missing programme data and target market.
"""
import csv
import os
import sys

channels_path, match_path, channel_coverage_path, output_path = sys.argv[1:5]
TARGET_REGIONS = {"US", "UK", "CA", "AU", "NZ"}

def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

channels = {row["channel_id"]: row for row in read_csv(channels_path)}
matches = {row["channel_id"]: row for row in read_csv(match_path)}
post = {row["provider_channel_id"]: row for row in read_csv(channel_coverage_path)}

region_order = {"US": 0, "UK": 1, "CA": 2, "AU": 3, "NZ": 4}
status_order = {"unmatched": 0, "matched_no_programmes": 1, "covered": 2, "skipped_vod": 3}
rows = []
for channel_id, channel in channels.items():
    region = channel.get("region_code", "")
    if region not in TARGET_REGIONS:
        continue
    match = matches.get(channel_id, {})
    coverage = post.get(channel_id, {})
    match_status = match.get("status", "missing_match_record")
    selected_count = int(coverage.get("selected_programmes") or 0)
    if match_status == "skipped_vod":
        gap_status = "skipped_vod"
    elif match_status != "matched":
        gap_status = "unmatched"
    elif selected_count == 0:
        gap_status = "matched_no_programmes"
    else:
        gap_status = "covered"
    rows.append({
        "region_code": region,
        "gap_status": gap_status,
        "channel_id": channel_id,
        "broadcaster": channel.get("broadcaster", ""),
        "channel_name": channel.get("channel_name", ""),
        "epg_ids": channel.get("epg_ids", ""),
        "has_epg_id": channel.get("has_epg_id", ""),
        "playlist_names": channel.get("playlist_names", ""),
        "playlist_groups": channel.get("playlist_groups", ""),
        "match_method": match.get("match_method", ""),
        "candidate_count": match.get("candidate_count", "0"),
        "selected_source": coverage.get("selected_source", ""),
        "selected_programmes": selected_count,
        "all_candidate_programmes": coverage.get("all_candidate_programmes", ""),
    })

rows.sort(key=lambda r: (
    status_order.get(r["gap_status"], 9),
    region_order.get(r["region_code"], 9),
    r["broadcaster"].lower(),
    r["channel_name"].lower(),
))
os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
fields = list(rows[0]) if rows else [
    "region_code", "gap_status", "channel_id", "broadcaster", "channel_name",
    "epg_ids", "has_epg_id", "playlist_names", "playlist_groups", "match_method",
    "candidate_count", "selected_source", "selected_programmes", "all_candidate_programmes"
]
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

from collections import Counter
counts = Counter((r["region_code"], r["gap_status"]) for r in rows)
print(f"English-market channel rows: {len(rows)}")
for region in ["US", "UK", "CA", "AU", "NZ"]:
    parts = [f"{status}={counts[(region, status)]}" for status in
             ["covered", "unmatched", "matched_no_programmes", "skipped_vod"]]
    print(f"{region}: " + ", ".join(parts))
