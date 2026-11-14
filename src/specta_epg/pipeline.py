from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .inventory import load_inventory
from .matching import load_reviewed_mappings, write_mapping_suggestions
from .models import ChannelSchedule
from .output import write_outputs
from .providers.bein_mena import BeinMenaAdapter


ROOT = Path(__file__).resolve().parents[2]
ADAPTER_FACTORIES = {"bein_mena": BeinMenaAdapter}


def adapters() -> dict:
    registry_path = ROOT / "config" / "providers.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    if payload.get("schemaVersion") != 1 or not isinstance(payload.get("providers"), list):
        raise ValueError("Invalid provider registry schema")
    active = {}
    seen = set()
    for provider in payload["providers"]:
        provider_id = str(provider.get("id") or "").strip()
        adapter_id = str(provider.get("adapter") or "").strip()
        if not provider_id or provider_id in seen:
            raise ValueError(f"Missing or duplicate provider ID in registry: {provider_id}")
        seen.add(provider_id)
        if not provider.get("enabled", False):
            continue
        if adapter_id not in ADAPTER_FACTORIES:
            raise ValueError(f"No native adapter is registered for provider: {adapter_id}")
        active[provider_id] = ADAPTER_FACTORIES[adapter_id]()
    return active


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
                raise ValueError(f"Provider is not enabled in the provider registry: {provider_id}")
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
