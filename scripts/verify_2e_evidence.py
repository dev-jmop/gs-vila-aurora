#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.security.evidence import verify_manifest
p=argparse.ArgumentParser();p.add_argument('directory',nargs='?',default='evidence/runtime/etapa2e');args=p.parse_args()
if verify_manifest(args.directory):print('PASSOU: todos os SHA-256 conferem')
else:raise SystemExit('FALHA: evidencias ausentes ou alteradas')
