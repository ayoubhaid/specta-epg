from __future__ import annotations

import gzip
import json
import xml.etree.ElementTree as ET
from datetime import timezone
from pathlib import Path

from .models import ChannelSchedule


def _xmltv_time(value) -> str:
    return value.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S +0000")


def write_outputs(schedules: list[ChannelSchedule], output_dir: str | Path, generated_at: str) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    root = ET.Element("tv", {
        "generator-info-name": "Specta EPG",
        "generator-info-url": "https://github.com/ayoubhaid/specta-epg",
    })
    json_channels = []
    total_programmes = 0
    mapped_channels = 0

    for schedule in schedules:
        channel = schedule.channel
        element = ET.SubElement(root, "channel", {"id": channel.id})
        for display_name in (channel.name, *channel.aliases):
            ET.SubElement(element, "display-name").text = display_name
        if channel.tvg_id:
            ET.SubElement(element, "display-name").text = channel.tvg_id

        programmes = sorted(schedule.programmes, key=lambda item: item.start)
        if programmes:
            mapped_channels += 1
        total_programmes += len(programmes)
        for programme in programmes:
            p = ET.SubElement(root, "programme", {
                "start": _xmltv_time(programme.start),
                "stop": _xmltv_time(programme.end),
                "channel": channel.id,
            })
            ET.SubElement(p, "title", {"lang": channel.language or "en"}).text = programme.title
            if programme.description:
                ET.SubElement(p, "desc", {"lang": channel.language or "en"}).text = programme.description

        json_channels.append({
            "id": channel.id,
            "name": channel.name,
            "tvgId": channel.tvg_id or None,
            "language": channel.language or None,
            "country": channel.country or None,
            "region": channel.region or None,
            "aliases": list(channel.aliases),
            "programmes": [programme.json_dict() for programme in programmes],
        })

    ET.indent(root)
    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    (output / "guide.xml").write_bytes(xml_bytes)
    with gzip.open(output / "guide.xml.gz", "wb") as compressed:
        compressed.write(xml_bytes)

    json_payload = {
        "schemaVersion": 1,
        "provider": "specta_curated",
        "providerName": "Specta Curated EPG",
        "timezone": "UTC",
        "generatedAt": generated_at,
        "coverage": {
            "channelsInInventory": len(schedules),
            "channelsWithProgrammes": mapped_channels,
            "programmesFound": total_programmes,
        },
        "channels": json_channels,
    }
    (output / "epg.json").write_text(
        json.dumps(json_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return json_payload["coverage"]
