import tempfile
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from src.security.awareness import simulate
from src.security.detector import detect, RULES, read_jsonl
from src.security.evidence import create_manifest,verify_manifest

class Security2ETests(unittest.TestCase):
    def test_phishing_only_synthetic_and_expected_counts(self):
        with tempfile.TemporaryDirectory() as d:
            m=simulate(Path(d),datetime(2026,11,18,tzinfo=timezone.utc))
            self.assertEqual((m['simulated_deliveries'],m['simulated_opens'],m['simulated_clicks'],m['simulated_reports']),(12,7,3,4))
            self.assertEqual(m['real_messages_sent'],0)
            self.assertEqual(m['credentials_collected'],0)
    def test_five_detection_rules(self):
        ts=datetime(2026,11,18,tzinfo=timezone.utc)
        e=[]
        for i in range(3):e.append({'timestamp':(ts+timedelta(seconds=i*10)).isoformat(),'event':'login_failed','identity':'demo'})
        for kind in ('tls_certificate_verify_failed','sqli_attempt','mqtt_cross_site_rejected','simulated_click'):
            e.append({'timestamp':(ts+timedelta(seconds=40)).isoformat(),'event':kind,'identity':'demo','source':'phishing_simulation' if kind=='simulated_click' else 'demo'})
        self.assertEqual({a['rule_id'] for a in detect(e)},set(RULES))
        self.assertTrue(all(a['automated_action']=='NONE' for a in detect(e)))
    def test_two_login_fails_do_not_trigger(self):
        ts='2026-11-18T12:00:00+00:00'
        self.assertEqual(detect([{'timestamp':ts,'event':'login_failed','identity':'demo'}]*2),[])
    def test_manifest_detects_tampering(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'evidence.json').write_text('{}')
            create_manifest(p);self.assertTrue(verify_manifest(p))
            (p/'evidence.json').write_text('{"changed":true}')
            self.assertFalse(verify_manifest(p))
    def test_demo_events_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            simulate(Path(d))
            self.assertGreater(len(read_jsonl(Path(d)/'phishing_events.jsonl')),12)
