from __future__ import annotations

import json
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
