#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.security.evidence import verify_manifest
from src.forensics.incident import sha256
p=argparse.ArgumentParser();p.add_argument('--case',default='evidence/runtime/INC-VA-0712');p.add_argument('--source',default='evidence/runtime/etapa2e');a=p.parse_args()
case=Path(a.case);source=Path(a.source)
if not verify_manifest(case):sys.exit('FALHOU: hash de artefatos derivados alterado')
chain=json.loads((case/'03_cadeia_custodia.json').read_text())
for item in chain['artifacts']:
    preserved=case/'01_originais'/item['filename'];original=source/item['filename']
    if not original.is_file() or sha256(original)!=sha256(preserved) or sha256(preserved)!=item['preserved_sha256']:
        sys.exit('FALHOU: integridade/original divergente: '+item['filename'])
print('PASSOU: cadeia de custodia, originais e manifesto SHA-256 conferem')
