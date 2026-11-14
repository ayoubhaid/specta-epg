import json
import tempfile
import unittest
from pathlib import Path

from specta_epg.matching import load_reviewed_mappings, write_mapping_suggestions
from specta_epg.models import InventoryChannel


class MappingTests(unittest.TestCase):
    def test_only_reviewed_mappings_are_loaded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mapping.json"
            path.write_text(json.dumps({
                "schemaVersion": 1,
                "mappings": [
                    {"inventoryId": "a", "provider": "bein_mena", "providerChannelId": "1", "reviewed": True},
                    {"inventoryId": "b", "provider": "bein_mena", "providerChannelId": "2", "reviewed": False},
                    {"inventoryId": "c", "provider": "bein_mena", "providerChannelId": "3", "reviewed": "false"},
                ],
            }))
            result = load_reviewed_mappings(path)
            self.assertIn("a", result)
            self.assertNotIn("b", result)
            self.assertNotIn("c", result)

    def test_suggestions_are_exact_and_never_approved(self):
        inventory = [InventoryChannel("a", "beIN SPORTS 1 HD")]
        catalog = [{"id": "42", "name": "beIN SPORTS 1"}]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "review.csv"
            counts = write_mapping_suggestions(inventory, catalog, "bein_mena", output)
            report = output.read_text(encoding="utf-8")
            self.assertEqual(counts["suggested"], 1)
            self.assertIn("42", report)
            self.assertIn("suggested_review_required", report)
            self.assertIn("false", report)


if __name__ == "__main__":
    unittest.main()
