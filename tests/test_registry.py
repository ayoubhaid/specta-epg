import unittest

from specta_epg.pipeline import adapters


class ProviderRegistryTests(unittest.TestCase):
    def test_enabled_bein_adapter_is_registered(self):
        registry = adapters()
        self.assertIn("bein_mena", registry)
        self.assertEqual(registry["bein_mena"].provider_id, "bein_mena")


if __name__ == "__main__":
    unittest.main()
