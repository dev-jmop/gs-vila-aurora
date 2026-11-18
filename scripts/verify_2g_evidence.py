#!/usr/bin/env python3
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.security.evidence import verify_manifest
p=Path('evidence/runtime/etapa2g')
if not p.is_dir() or not verify_manifest(p):sys.exit('FALHOU: evidencia da IA ausente ou alterada')
r=json.loads((p/'model_evaluation.json').read_text());d=json.loads((p/'human_review.json').read_text())
assert r['data']=='100% SYNTHETIC HOLDOUT' and r['actions_executed']==0
assert d['approved'] is False and d['executed'] is False
assert sum(r['confusion_matrix'].values())==r['test_benign']+r['test_attack']
print('PASSOU: metricas, revisao humana e manifesto SHA-256 conferem')
