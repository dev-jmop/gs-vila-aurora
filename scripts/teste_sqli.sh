#!/usr/bin/env bash
set -euo pipefail
python - <<'INTERNAL_PY'
import json
import urllib.parse
import urllib.request
payload="' OR 1=1 -- "
for endpoint in ('vulnerable','safe'):
    url='http://127.0.0.1:8091/'+endpoint+'?'+urllib.parse.urlencode({'q':payload})
    with urllib.request.urlopen(url,timeout=5) as r:
        data=json.load(r)
    print(endpoint,data)
    expected=3 if endpoint=='vulnerable' else 0
    if data['count']!=expected:raise SystemExit('FALHA: resultado inesperado')
print('PASSOU: vulnerabilidade demonstrada e reteste corrigido.')
INTERNAL_PY
