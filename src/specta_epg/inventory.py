from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from .models import InventoryChannel

ROOT_ATTRIBUTES = {"schemaVersion", "generatedAt", "source"}
CHANNEL_ATTRIBUTES = {"id", "name", "tvg-id", "language", "country", "region"}
FORBIDDEN_FIELD_PARTS = (
    "url", "stream", "password", "credential", "token", "username",
    "playlist", "m3u", "authorization", "cookie", "secret", "apikey",
)
SENSITIVE_VALUE = re.compile(
    r"(?:https?|rtmp|rtsp|udp)://|(?:password|token|authorization|cookie)\s*=|\b(?:bearer|basic)\s+",
    re.IGNORECASE,
)


def _check_private_fields(element: ET.Element) -> None:
    for node in element.iter():
        names = [node.tag, *node.attrib.keys()]
        for name in names:
            lowered = name.lower().replace("-", "_")
            if any(part in lowered for part in FORBIDDEN_FIELD_PARTS):
                raise ValueError(f"Inventory must not contain stream or credential field: {name}")
        values = [node.text or "", *node.attrib.values()]
        if any(SENSITIVE_VALUE.search(value) for value in values):
            raise ValueError("Inventory contains a URL or credential-like value")


def load_inventory(path: str | Path) -> list[InventoryChannel]:
    root = ET.parse(path).getroot()
    if root.tag != "channelInventory":
        raise ValueError("Root element must be <channelInventory>")
    if root.get("schemaVersion") != "1":
        raise ValueError("Unsupported channel inventory schemaVersion")
    if set(root.attrib) - ROOT_ATTRIBUTES:
        raise ValueError("Inventory root contains unsupported attributes")
    if any(child.tag != "channel" for child in root):
        raise ValueError("Inventory root may contain only <channel> elements")

    _check_private_fields(root)
    channels: list[InventoryChannel] = []
    seen: set[str] = set()

    for element in root.findall("channel"):
        if set(element.attrib) - CHANNEL_ATTRIBUTES:
            raise ValueError("Channel contains unsupported attributes")
        if any(child.tag != "alias" or child.attrib or len(child) for child in element):
            raise ValueError("Channel may contain only plain-text <alias> elements")
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
