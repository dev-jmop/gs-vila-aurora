#!/usr/bin/env python3
"""Gera evidencias sintéticas para conscientizacao e detecções, sem rede."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json
from datetime import datetime,timezone,timedelta
from pathlib import Path
from src.security.awareness import simulate
from src.security.detector import detect, read_jsonl, write_alerts, RULES
from src.security.evidence import create_manifest,verify_manifest


def security_fixture(now):
    events=[]
    def add(offset,kind,who,source='security_demo'):
        events.append({'timestamp':(now+timedelta(seconds=offset)).isoformat(),'event':kind,'identity':who,'source':source,'simulation':True})
    for t in (0,12,31): add(t,'login_failed','operador-ficticio')
    add(45,'tls_certificate_verify_failed','sensor-ubs-ficticio')
    add(50,'sqli_attempt','laboratorio-sqli')
    add(53,'mqtt_cross_site_rejected','sensor-horta-ficticio')
    return events


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--output',default='evidence/runtime/etapa2e',help='Diretorio local ignorado no git')
    args=ap.parse_args()
    out=Path(args.output)
    if out.resolve()==Path.cwd(): raise SystemExit('Escolha subdiretorio especifico para evidencias')
    out.mkdir(parents=True,exist_ok=True)
    now=datetime.now(timezone.utc)
    metrics=simulate(out,now)
    fixture=security_fixture(now)
    with (out/'security_events.jsonl').open('w',encoding='utf-8') as f:
        for e in fixture: f.write(json.dumps(e,sort_keys=True)+'\n')
    all_events=fixture+read_jsonl(out/'phishing_events.jsonl')
    alerts=detect(all_events)
    write_alerts(alerts,out/'alerts.jsonl')
    counts={rule:sum(a['rule_id']==rule for a in alerts) for rule in RULES}
    summary={'mode':'SIMULATION_ONLY', 'generated_at_utc':now.isoformat(), 'security_fixture_events':len(fixture), 'phishing_fixture_events':len(read_jsonl(out/'phishing_events.jsonl')), 'alerts_total':len(alerts), 'alerts_by_rule':counts, 'response_policy':'Sem alteracoes automaticas no firewall, rede ou contas; decisao humana exigida para acoes de alto impacto', 'phishing_metrics':metrics}
    (out/'detection_summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    create_manifest(out)
    assert verify_manifest(out)
    print(json.dumps({'path':str(out),'simulated_deliveries':metrics['simulated_deliveries'],'simulated_clicks':metrics['simulated_clicks'],'alerts_by_rule':counts,'sha256_manifest_verified':True},ensure_ascii=False,indent=2))
    print('AVISO: dados 100% ficticios. Nenhuma mensagem foi enviada, nenhuma acao de bloqueio executada.')

if __name__=='__main__':main()
