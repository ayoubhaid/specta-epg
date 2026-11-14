import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from specta_epg.models import Programme
from specta_epg.pipeline import build


class FakeAdapter:
    def fetch_programmes(self, provider_channel_id, days):
        start = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)
        return [Programme(
            id="fixture-1",
            channel_id=provider_channel_id,
            title="Fixture programme",
            description="Offline fixture",
            start=start,
            end=start + timedelta(hours=1),
            source="fixture",
        )]


class PipelineTests(unittest.TestCase):
    def _inputs(self, directory, mapping):
        inventory = Path(directory) / "channels.xml"
        inventory.write_text(
            '<channelInventory schemaVersion="1">'
            '<channel id="specta-1" name="Example Channel"/>'
            '</channelInventory>',
            encoding="utf-8",
        )
        mapping_path = Path(directory) / "mapping.json"
        mapping_path.write_text(json.dumps({"schemaVersion": 1, "mappings": mapping}))
        return inventory, mapping_path

    def test_build_creates_curated_feeds_from_reviewed_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            inventory, mapping = self._inputs(directory, [{
                "inventoryId": "specta-1",
                "provider": "fixture",
                "providerChannelId": "source-1",
                "reviewed": True,
            }])
            output = Path(directory) / "public"
            with patch("specta_epg.pipeline.adapters", return_value={"fixture": FakeAdapter()}):
                coverage = build(str(inventory), str(mapping), str(output), days=1)
            self.assertEqual(coverage["programmesFound"], 1)
            self.assertEqual(coverage["unmappedChannels"], 0)
            self.assertTrue((output / "guide.xml").exists())
            self.assertTrue((output / "guide.xml.gz").exists())
            self.assertTrue((output / "epg.json").exists())

    def test_build_refuses_to_publish_without_programmes(self):
        with tempfile.TemporaryDirectory() as directory:
            inventory, mapping = self._inputs(directory, [])
            with patch("specta_epg.pipeline.adapters", return_value={}):
                with self.assertRaisesRegex(RuntimeError, "No programmes"):
                    build(str(inventory), str(mapping), str(Path(directory) / "public"), days=1)


if __name__ == "__main__":
    unittest.main()
