import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from src.security.required_rules import detect_required, RULES_REQUIRED
from src.security.soar import process_alerts
from src.security.siem import LocalSIEM, clean_line
from src.security.evidence import create_manifest,verify_manifest
from scripts.medir_metricas_2h import number_with_unit, parse_stats, time_metrics

NOW='2026-11-18T14:00:00Z'

class RequiredRulesTests(unittest.TestCase):
    def test_four_mandatory_categories(self):
        ev=[
            {'timestamp':NOW,'event':'vpn_login_success','identity':'t','source_ip':'203.0.113.42'},
            {'timestamp':NOW,'event':'sqli_attempt','identity':'web'},
            {'timestamp':NOW,'event':'tls_certificate_verify_failed','identity':'sensor'},
            {'timestamp':NOW,'event':'actuator_command','identity':'x','role':'operador','site':'horta','command':'pump_start'},
        ]
        alerts=detect_required(ev,vpn_allowed_cidrs=['198.51.100.0/24'])
        self.assertEqual({a['rule_id'] for a in alerts},set(RULES_REQUIRED))
        self.assertTrue(all(not a['action_executed'] for a in alerts))
    def test_vpn_without_known_baseline_does_not_claim_anomaly(self):
        e={'timestamp':NOW,'event':'vpn_login_success','identity':'demo','source_ip':'203.0.113.2'}
        self.assertEqual(detect_required([e]),[])
    def test_authorized_actuator_in_daytime_does_not_alert(self):
        e={'timestamp':'2026-11-18T15:00:00Z','event':'actuator_command',
           'site':'horta','command':'pump_start','role':'tecnico','identity':'tester'}
        self.assertEqual(detect_required([e]),[])
    def test_actuator_outside_hours_alerts_even_valid_role(self):
        e={'timestamp':'2026-11-18T03:00:00Z','event':'actuator_command',
           'site':'horta','command':'pump_start','role':'tecnico'}
        self.assertEqual(detect_required([e])[0]['reason'],'outside_allowed_hours')
    def test_soar_keeps_high_impact_changes_manual(self):
        e={'rule_id':'VA-RT13-CERT','timestamp':NOW,'identity':'sensor','severity':'high'}
        with tempfile.TemporaryDirectory() as d:
            result=process_alerts([e],d)
            self.assertEqual(result['cases_created'],1)
            self.assertEqual(result['disruptive_actions_executed'],0)
            self.assertIn('AWAITING_HUMAN_APPROVAL',(Path(d)/'soar_cases.jsonl').read_text())

class LocalSIEMTests(unittest.TestCase):
    def test_retention_dedup_redaction(self):
        with tempfile.TemporaryDirectory() as d:
            with LocalSIEM(Path(d)/'logs.sqlite3') as db:
                old=datetime(2026,10,1,tzinfo=timezone.utc)
                now=datetime(2026,11,18,tzinfo=timezone.utc)
                self.assertEqual(db.ingest('cloud','web',['password=SECRET'],old),1)
                self.assertEqual(db.ingest('cloud','web',['password=SECRET'],now),0)
                self.assertIn('[REDACTED]',db.conn.execute('select message from logs').fetchone()[0])
                self.assertEqual(db.expire(30,now),1)
                self.assertEqual(db.summary()['events_total'],0)
    def test_different_sources_have_independent_event_ids(self):
        with tempfile.TemporaryDirectory() as d:
            with LocalSIEM(Path(d)/'db.sqlite3') as db:
                db.ingest('broker','broker',['same message'])
                db.ingest('edge','edge',['same message'])
                self.assertEqual(db.summary()['events_total'],2)
    def test_manifest_of_lab_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'evidence.json').write_text('{}')
            create_manifest(d)
            self.assertTrue(verify_manifest(d))

class MetricsTests(unittest.TestCase):
    def test_unit_conversion_and_docker_stats(self):
        self.assertEqual(number_with_unit('2MiB'),2097152)
        s=parse_stats('{"CPUPerc":"2.50%","MemUsage":"50MiB / 2GiB","NetIO":"2kB / 4kB"}')
        self.assertEqual(s['memory_bytes'],50*1024*1024)
        self.assertEqual(s['network_rx_bytes_total'],2000)
    def test_metric_timestamps_are_validated(self):
        times=time_metrics('2026-11-18T14:00:00Z','2026-11-18T14:00:10Z','2026-11-18T14:00:30Z')
        self.assertEqual(times['mttd_seconds_observed'],10)
        self.assertEqual(times['mttr_seconds_observed'],20)
        with self.assertRaises(ValueError):
            time_metrics('2026-11-18T14:00:30Z','2026-11-18T14:00:20Z','2026-11-18T14:00:40Z')

if __name__=='__main__':unittest.main()
