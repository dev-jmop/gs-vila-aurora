#!/usr/bin/env python3
"""Cenario sintético RT-13/RT-15, sem acao real em rede ou atuadores."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.security.required_rules import detect_required, RULES_REQUIRED
from src.security.soar import process_alerts
from src.security.evidence import create_manifest, verify_manifest


def scenario():
    # IPs reservados para documentação RFC 5737, sem alvo externo.
    return [
        {'timestamp':'2026-11-18T14:00:00+00:00','event':'vpn_login_success',
         'identity':'tecnico-ficticio','source_ip':'203.0.113.42','simulation':True},
        {'timestamp':'2026-11-18T14:00:08+00:00','event':'sqli_attempt',
         'identity':'sqli-lab-ficticio','simulation':True},
        {'timestamp':'2026-11-18T14:00:11+00:00','event':'tls_certificate_verify_failed',
         'identity':'sensor-revogado-ficticio','simulation':True},
        {'timestamp':'2026-11-18T14:00:19+00:00','event':'actuator_command',
         'identity':'voluntario-ficticio','site':'horta','role':'operador',
         'command':'pump_start','simulation':True},
        {'timestamp':'2026-11-18T15:00:00+00:00','event':'vpn_login_success',
         'identity':'tecnico-autorizado-ficticio','source_ip':'198.51.100.9','simulation':True},
        {'timestamp':'2026-11-18T15:00:10+00:00','event':'actuator_command',
         'identity':'tecnico-autorizado-ficticio','site':'horta','role':'tecnico',
         'command':'pump_start','simulation':True},
    ]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',default='evidence/runtime/etapa2h')
    args=parser.parse_args()
    out=Path(args.out)
    out.mkdir(parents=True,exist_ok=True)
    events=scenario()
    alerts=detect_required(events,vpn_allowed_cidrs=['198.51.100.0/24'])
    with (out/'eventos_sinteticos.jsonl').open('w',encoding='utf-8') as f:
        for e in events:f.write(json.dumps(e,sort_keys=True,ensure_ascii=False)+'\n')
    with (out/'alertas_rt13.jsonl').open('w',encoding='utf-8') as f:
        for e in alerts:f.write(json.dumps(e,sort_keys=True,ensure_ascii=False)+'\n')
    action_summary=process_alerts(alerts,out)
    summary={
        'mode':'SYNTHETIC_LAB_ONLY', 'expected_required_rule_ids':sorted(RULES_REQUIRED),
        'triggered_rule_ids':sorted({a['rule_id'] for a in alerts}),
        'alerts_total':len(alerts),'soar':action_summary,
        'limitations': 'Detecção em eventos estruturados sintéticos e abertura automática de casos locais; sem integração com sessão VPN real, broker, firewall, Wazuh ou atuador físico.'
    }
    (out/'resumo.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    create_manifest(out)
    assert verify_manifest(out)
    assert set(summary['triggered_rule_ids'])==set(RULES_REQUIRED)
    print(json.dumps({'status':'PASSOU','alerts':len(alerts),
                      'rules':summary['triggered_rule_ids'],
                      'cases':action_summary['cases_created'],
                      'disruptive_actions_executed':0,
                      'sha256_verified':True,
                      'output':str(out)},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
