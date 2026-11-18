import sqlite3
import threading
from contextlib import closing
import tempfile
import unittest
from pathlib import Path
from src.edge import initialize, pending
from src.mqtt_edge import save_event, sync_once
from src.mqtt_sensor import build_event
from src.cloud import accept_event, SCHEMA


class MqttPipelineTests(unittest.TestCase):
    def test_save_alert_to_local_database(self):
        with tempfile.TemporaryDirectory() as folder, initialize(Path(folder) / 'edge.db') as db:
            e = build_event('ubs', 9)
            alert = save_event(db, e, 'ubs')
            self.assertIn('ALERTA LOCAL', alert)
            self.assertEqual(len(pending(db)), 1)
            save_event(db, e, 'ubs')
            self.assertEqual(len(pending(db)), 1)

    def test_callback_thread_uses_own_sqlite_connection(self):
        with tempfile.TemporaryDirectory() as folder:
            db_path = Path(folder) / 'edge.db'
            with closing(initialize(db_path)) as sync_db:
                failures = []
                def mqtt_callback_thread():
                    try:
                        with closing(initialize(db_path)) as message_db:
                            save_event(message_db, build_event('ubs', 9), 'ubs')
                    except Exception as exc:
                        failures.append(exc)
                thread = threading.Thread(target=mqtt_callback_thread)
                thread.start()
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())
                self.assertFalse(failures, failures)
                self.assertEqual(len(pending(sync_db)), 1)

    def test_reject_cross_site_event(self):
        with tempfile.TemporaryDirectory() as folder, initialize(Path(folder) / 'edge.db') as db:
            with self.assertRaises(ValueError):
                save_event(db, build_event('escola', 25), 'ubs')

    def test_stays_pending_while_cloud_offline_then_reconciles(self):
        with tempfile.TemporaryDirectory() as folder, initialize(Path(folder) / 'edge.db') as edge, sqlite3.connect(':memory:') as cloud:
            cloud.execute(SCHEMA)
            e = build_event('ubs', 9)
            save_event(edge, e, 'ubs')
            def unavailable(event):
                raise OSError('WAN offline')
            self.assertEqual(sync_once(edge, unavailable), 0)
            self.assertEqual(len(pending(edge)), 1)
            self.assertEqual(sync_once(edge, lambda event: accept_event(cloud, event)), 1)
            self.assertEqual(len(pending(edge)), 0)
            self.assertEqual(cloud.execute('SELECT COUNT(*) FROM events').fetchone()[0], 1)

    def test_repeated_cloud_ack_does_not_duplicate(self):
        with sqlite3.connect(':memory:') as cloud:
            cloud.execute(SCHEMA)
            e = build_event('abrigo', 1)
            e['alert'] = 'simulado'
            accept_event(cloud, e)
            accept_event(cloud, e)
            self.assertEqual(cloud.execute('SELECT COUNT(*) FROM events').fetchone()[0], 1)


if __name__ == '__main__':
    unittest.main()
