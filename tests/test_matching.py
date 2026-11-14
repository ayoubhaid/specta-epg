import json
import tempfile
import unittest
from pathlib import Path

from specta_epg.matching import load_reviewed_mappings


class MappingTests(unittest.TestCase):
    def test_only_reviewed_mappings_are_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mapping.json"
            path.write_text(json.dumps({
                "schemaVersion": 1,
                "mappings": [
                    {"inventoryId": "a", "provider": "bein_mena", "providerChannelId": "1", "reviewed": True},
                    {"inventoryId": "b", "provider": "bein_mena", "providerChannelId": "2", "reviewed": False},
                ],
            }))
            result = load_reviewed_mappings(path)
            self.assertIn("a", result)
            self.assertNotIn("b", result)


if __name__ == "__main__":
    unittest.main()
