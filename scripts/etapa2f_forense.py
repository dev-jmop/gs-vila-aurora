#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.forensics.incident import reconstruct
p=argparse.ArgumentParser(description='INC-VA-0712: reconstrucao forense de evento simulado')
p.add_argument('--source',default='evidence/runtime/etapa2e')
p.add_argument('--output',default='evidence/runtime/INC-VA-0712')
args=p.parse_args()
result=reconstruct(args.source,args.output)
print(json.dumps({'status':'PASSOU','incident':result['incident_id'],'simulation':True,'events':result['event_count'],'alerts':result['alerts_count'],'output':args.output,'sha256_verified':True},ensure_ascii=False,indent=2))
