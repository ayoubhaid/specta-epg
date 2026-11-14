import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from specta_epg.models import ChannelSchedule, InventoryChannel, Programme
from specta_epg.output import write_outputs


class OutputTests(unittest.TestCase):
    def test_writes_xmltv_json_and_gzip(self):
        channel = InventoryChannel("specta-1", "Example", tvg_id="example.tv", aliases=("Example HD",))
        programme = Programme(
            "p1", "provider-1", "News", "Daily news",
            datetime(2026, 1, 1, 10, tzinfo=timezone.utc),
            datetime(2026, 1, 1, 11, tzinfo=timezone.utc),
            "test",
        )
        with tempfile.TemporaryDirectory() as directory:
            coverage = write_outputs(
                [ChannelSchedule(channel, [programme])], directory, "2026-01-01T00:00:00Z"
            )
            root = ET.parse(Path(directory) / "guide.xml").getroot()
            self.assertEqual(root.find("channel").get("id"), "specta-1")
            self.assertEqual(root.find("programme").get("channel"), "specta-1")
            payload = json.loads((Path(directory) / "epg.json").read_text())
            self.assertEqual(payload["channels"][0]["programmes"][0]["title"], "News")
            self.assertTrue((Path(directory) / "guide.xml.gz").exists())
            self.assertEqual(coverage["programmesFound"], 1)


if __name__ == "__main__":
    unittest.main()
