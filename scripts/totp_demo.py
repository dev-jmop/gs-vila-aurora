#!/usr/bin/env python3
"""Somente para laboratorio: exibe TOTP da conta ficticia local."""
import json
import sys
from pathlib import Path
from src.supervision.auth import totp
p=Path(__file__).resolve().parents[1]/'auth/runtime/users.json'
u=sys.argv[1] if len(sys.argv)>1 else 'operador'
d=json.loads(p.read_text())
if u not in d:raise SystemExit('usuario ficticio inexistente')
print(totp(d[u]['totp_secret']))
