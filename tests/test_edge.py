import sqlite3
import tempfile
import unittest
from pathlib import Path
from src.edge import SITES, control, initialize, pending, produce, reconcile


class EdgeTests(unittest.TestCase):
    def test_each_site_operates_independently_offline(self):
        with tempfile.TemporaryDirectory() as folder:
            for site in SITES:
                with initialize(Path(folder) / (site + '.db')) as db:
                    event = produce(db, site)
                    self.assertEqual(event['site'], site)
                    self.assertEqual(len(pending(db)), 1)

    def test_local_alert_without_cloud(self):
        with tempfile.TemporaryDirectory() as folder:
            with initialize(Path(folder) / 'ubs.db') as db:
                self.assertIn('ALERTA LOCAL', produce(db, 'ubs', 9)['alert'])
                self.assertEqual(len(pending(db)), 1)

    def test_reconnection_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            with initialize(Path(folder) / 'edge.db') as edge, sqlite3.connect(':memory:') as cloud:
                produce(edge, 'abrigo', 1)
                produce(edge, 'abrigo', 0)
                self.assertEqual(reconcile(edge, cloud), 2)
                self.assertEqual(reconcile(edge, cloud), 0)
                self.assertEqual(cloud.execute('SELECT COUNT(*) FROM events').fetchone()[0], 2)
                self.assertEqual(len(pending(edge)), 0)

    def test_low_water_blocks_simulated_pump(self):
        self.assertIn('bloquear', control('escola','water_level_pct',5))
        self.assertIsNone(control('escola','water_level_pct',55))


if __name__ == '__main__':
    unittest.main()
