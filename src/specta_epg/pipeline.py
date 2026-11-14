from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .inventory import load_inventory
from .matching import load_reviewed_mappings, write_mapping_suggestions
from .models import ChannelSchedule
from .output import write_outputs
from .providers.bein_mena import BeinMenaAdapter


def adapters() -> dict:
    return {"bein_mena": BeinMenaAdapter()}


def discover(provider_id: str) -> list[dict]:
    registry = adapters()
    if provider_id not in registry:
        raise ValueError(f"Unknown or disabled provider: {provider_id}")
    return registry[provider_id].list_channels()


def suggest_mappings(inventory_path: str, provider_id: str, output_path: str) -> dict:
    inventory = load_inventory(inventory_path)
    catalog = discover(provider_id)
    return write_mapping_suggestions(inventory, catalog, provider_id, output_path)


def build(inventory_path: str, mapping_path: str, output_dir: str, days: int = 5) -> dict:
    channels = load_inventory(inventory_path)
    mappings = load_reviewed_mappings(mapping_path)
    providers = adapters()
    schedules: list[ChannelSchedule] = []
    unknown_inventory_ids = sorted(set(mappings) - {channel.id for channel in channels})
    if unknown_inventory_ids:
        raise ValueError("Mappings reference unknown inventory IDs: " + ", ".join(unknown_inventory_ids))

    for channel in channels:
        schedule = ChannelSchedule(channel=channel)
        mapping = mappings.get(channel.id)
        if mapping:
            provider_id = mapping["provider"]
            if provider_id not in providers:
                raise ValueError(f"Provider adapter is not implemented: {provider_id}")
            schedule.programmes = providers[provider_id].fetch_programmes(
                mapping["providerChannelId"], days
            )
        schedules.append(schedule)

    total = sum(len(item.programmes) for item in schedules)
    if total == 0:
        raise RuntimeError("No programmes collected; refusing to publish an empty guide")
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    coverage = write_outputs(schedules, output_dir, generated_at)
    coverage["unmappedChannels"] = sum(
        1 for channel in channels if channel.id not in mappings
    )
    Path(output_dir, "coverage.json").write_text(
        json.dumps(coverage, indent=2) + "\n", encoding="utf-8"
    )
    return coverage
