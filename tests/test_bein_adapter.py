import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from specta_epg.providers.bein_mena import BeinMenaAdapter


class BeinAdapterTests(unittest.TestCase):
    def test_channel_catalog_is_normalized(self):
        adapter = BeinMenaAdapter(delay_ms=0)
        with patch.object(adapter, "_get_json", return_value={
            "rows": [{"id": 123, "name": "  beIN SPORTS 1  "}, {"name": "invalid"}]
        }):
            self.assertEqual(adapter.list_channels(), [
                {"id": "123", "name": "beIN SPORTS 1", "region": "en-mena"}
            ])

    def test_event_rows_become_utc_programmes(self):
        adapter = BeinMenaAdapter(delay_ms=0)
        start = datetime.now(timezone.utc).replace(hour=12, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=2)
        payload = {"rows": [{
            "title": "Live Match",
            "description": "Fixture description",
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
        }]}
        with patch.object(adapter, "_get_json", return_value=payload):
            programmes = adapter.fetch_programmes("source-1", days=1)
        self.assertEqual(len(programmes), 1)
        self.assertEqual(programmes[0].title, "Live Match")
        self.assertEqual(programmes[0].source, "bein_mena")
        self.assertEqual(programmes[0].start.tzinfo, timezone.utc)


if __name__ == "__main__":
    unittest.main()
