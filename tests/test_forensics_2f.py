import json,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone
from src.security.awareness import simulate
from src.security.detector import detect,write_alerts
from src.security.evidence import create_manifest,verify_manifest
from src.forensics.incident import reconstruct
class Forensics2FTests(unittest.TestCase):
 def create_fixture(self,p):
  simulate(p,datetime(2026,11,18,tzinfo=timezone.utc))
  (p/'security_events.jsonl').write_text(json.dumps({'timestamp':'2026-11-18T10:00:00+00:00','event':'tls_certificate_verify_failed','identity':'sensor-ficticio','simulation':True})+'\n')
  events=[json.loads(x) for x in (p/'security_events.jsonl').read_text().splitlines()]
  write_alerts(detect(events),p/'alerts.jsonl');(p/'detection_summary.json').write_text('{}')
  create_manifest(p)
 def test_case_reconstruction_and_hashes(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'source';p.mkdir();self.create_fixture(p)
   dest=Path(d)/'case';report=reconstruct(p,dest)
   self.assertEqual(report['incident_id'],'INC-VA-0712')
   self.assertGreater(report['event_count'],0)
   self.assertTrue(verify_manifest(dest))
   self.assertTrue(all(a['match'] for a in json.loads((dest/'03_cadeia_custodia.json').read_text())['artifacts']))
 def test_refuse_modified_original(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'source';p.mkdir();self.create_fixture(p)
   (p/'security_events.jsonl').write_text('tampered')
   with self.assertRaises(ValueError):reconstruct(p,Path(d)/'case')
 def test_refuse_case_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'source';p.mkdir();self.create_fixture(p)
   dest=Path(d)/'case';reconstruct(p,dest)
   with self.assertRaises(FileExistsError):reconstruct(p,dest)
