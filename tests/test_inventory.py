import tempfile
import unittest
from pathlib import Path

from specta_epg.inventory import load_inventory


class InventoryTests(unittest.TestCase):
    def _load(self, xml: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.xml"
            path.write_text(xml, encoding="utf-8")
            return load_inventory(path)

    def test_loads_valid_inventory(self):
        channels = self._load(
            '<channelInventory schemaVersion="1"><channel id="a" name="Alpha">'
            '<alias>Alpha HD</alias></channel></channelInventory>'
        )
        self.assertEqual(channels[0].id, "a")
        self.assertEqual(channels[0].aliases, ("Alpha HD",))

    def test_rejects_duplicate_ids(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self._load(
                '<channelInventory schemaVersion="1"><channel id="a" name="A"/>'
                '<channel id="a" name="B"/></channelInventory>'
            )

    def test_rejects_stream_urls(self):
        with self.assertRaisesRegex(ValueError, "stream or credential"):
            self._load(
                '<channelInventory schemaVersion="1"><channel id="a" name="A" stream-url="secret"/>'
                '</channelInventory>'
            )

    def test_rejects_urls_hidden_in_text(self):
        with self.assertRaisesRegex(ValueError, "URL or credential"):
            self._load(
                '<channelInventory schemaVersion="1"><channel id="a" name="A">'
                '<alias>https://private.example/playlist.m3u</alias>'
                '</channel></channelInventory>'
            )

    def test_rejects_unknown_fields(self):
        with self.assertRaisesRegex(ValueError, "unsupported attributes"):
            self._load(
                '<channelInventory schemaVersion="1"><channel id="a" name="A" extra="x"/>'
                '</channelInventory>'
            )


if __name__ == "__main__":
    unittest.main()
