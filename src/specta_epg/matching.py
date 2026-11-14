from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path


def load_reviewed_mappings(path: str | Path) -> dict[str, dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schemaVersion") != 1 or not isinstance(payload.get("mappings"), list):
        raise ValueError("Invalid mapping file schema")
    result: dict[str, dict] = {}
    for entry in payload["mappings"]:
        if not isinstance(entry, dict):
            raise ValueError("Each mapping must be an object")
        inventory_id = str(entry.get("inventoryId") or "").strip()
        provider = str(entry.get("provider") or "").strip()
        provider_id = str(entry.get("providerChannelId") or "").strip()
        if not inventory_id or not provider or not provider_id:
            raise ValueError("Mappings require inventoryId, provider and providerChannelId")
        if not entry.get("reviewed", False):
            continue
        if inventory_id in result:
            raise ValueError(f"Duplicate reviewed mapping for inventory ID: {inventory_id}")
        result[inventory_id] = {
            "provider": provider,
            "providerChannelId": provider_id,
        }
    return result


_QUALITY = re.compile(r"\b(hd|fhd|uhd|sd|4k|8k|hevc|50fps|60fps|backup)\b", re.I)


def normalize_channel_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = _QUALITY.sub(" ", value.casefold())
    return re.sub(r"[^a-z0-9]+", "", value)


def write_mapping_suggestions(inventory, provider_channels: list[dict], provider_id: str, output: str | Path) -> dict:
    """Write review-only exact-name suggestions; never auto-approve a mapping."""
    by_name: dict[str, list[dict]] = {}
    for source in provider_channels:
        key = normalize_channel_name(str(source.get("name") or ""))
        if key:
            by_name.setdefault(key, []).append(source)

    rows = []
    counts = {"suggested": 0, "ambiguous": 0, "unmatched": 0}
    for channel in inventory:
        key = normalize_channel_name(channel.name)
        candidates = by_name.get(key, [])
        if len(candidates) == 1:
            status, method = "suggested_review_required", "exact_normalized_name"
        elif len(candidates) > 1:
            status, method = "ambiguous_review_required", "exact_normalized_name_multiple_candidates"
        else:
            status, method = "unmatched", ""
        bucket = "suggested" if len(candidates) == 1 else "ambiguous" if candidates else "unmatched"
        counts[bucket] += 1
        if not candidates:
            rows.append([channel.id, channel.name, provider_id, "", "", method, status, "false"])
        else:
            for candidate in candidates:
                rows.append([
                    channel.id, channel.name, provider_id,
                    str(candidate.get("id") or ""), str(candidate.get("name") or ""),
                    method, status, "false",
                ])

    destination = Path(output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow([
            "inventory_id", "inventory_name", "provider", "provider_channel_id",
            "provider_channel_name", "match_method", "status", "reviewed",
        ])
        writer.writerows(rows)
    return counts
