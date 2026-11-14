from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from .models import InventoryChannel

FORBIDDEN_FIELD_PARTS = (
    "url", "stream", "password", "credential", "token", "username",
    "playlist", "m3u", "authorization", "cookie",
)


def _check_private_fields(element: ET.Element) -> None:
    for node in element.iter():
        names = [node.tag, *node.attrib.keys()]
        for name in names:
            lowered = name.lower().replace("-", "_")
            if any(part in lowered for part in FORBIDDEN_FIELD_PARTS):
                raise ValueError(
                    f"Inventory must not contain stream or credential field: {name}"
                )


def load_inventory(path: str | Path) -> list[InventoryChannel]:
    root = ET.parse(path).getroot()
    if root.tag != "channelInventory":
        raise ValueError("Root element must be <channelInventory>")
    if root.get("schemaVersion") != "1":
        raise ValueError("Unsupported channel inventory schemaVersion")

    _check_private_fields(root)
    channels: list[InventoryChannel] = []
    seen: set[str] = set()

    for element in root.findall("channel"):
        channel_id = (element.get("id") or "").strip()
        name = (element.get("name") or "").strip()
        if not channel_id or not name:
            raise ValueError("Every channel requires non-empty id and name")
        if channel_id in seen:
            raise ValueError(f"Duplicate inventory channel id: {channel_id}")
        seen.add(channel_id)
        aliases = tuple(
            (alias.text or "").strip()
            for alias in element.findall("alias")
            if (alias.text or "").strip()
        )
        channels.append(InventoryChannel(
            id=channel_id,
            name=name,
            tvg_id=(element.get("tvg-id") or "").strip(),
            language=(element.get("language") or "").strip(),
            country=(element.get("country") or "").strip(),
            region=(element.get("region") or "").strip(),
            aliases=aliases,
        ))

    if not channels:
        raise ValueError("Inventory contains no channels")
    return channels
