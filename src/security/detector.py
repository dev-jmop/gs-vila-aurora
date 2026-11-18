"""Deterministic defensive detection and response planning. Never changes firewall automatically."""
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

RULES={
    'VA-DET-01': '3+ falhas de login por identidade em 5 minutos',
    'VA-DET-02': 'falha TLS de verificacao de certificado (possivel revogacao)',
    'VA-DET-03': 'tentativa de SQL injection no laboratorio',
    'VA-DET-04': 'evento MQTT indicando origem de site divergente',
    'VA-DET-05': 'clique simulado em exercicio de phishing'
}


def parse_time(value):
    dt=datetime.fromisoformat(value.replace('Z','+00:00'))
    if dt.tzinfo is None: raise ValueError('timestamp must have timezone')
    return dt.astimezone(timezone.utc)


def detect(events):
    alerts=[]
    login_fails=defaultdict(list)
    ordered=sorted(events,key=lambda e:parse_time(e['timestamp']))
    for event in ordered:
        kind=event.get('event')
        identity=str(event.get('identity','unknown'))[:100]
        ts=event['timestamp']
        if kind=='login_failed':
            moment=parse_time(ts)
            attempts=login_fails[identity]
            attempts[:]=[t for t in attempts if moment-t <= timedelta(minutes=5)]
            attempts.append(moment)
            if len(attempts)==3:
                alerts.append(_alert('VA-DET-01',ts,identity,'medium','Revisar origem e conta. Bloqueio requer validacao do operador.'))
        elif kind=='tls_certificate_verify_failed':
            alerts.append(_alert('VA-DET-02',ts,identity,'high','Isolar identidade suspeita após aprovação humana; coletar CRL e logs.'))
        elif kind=='sqli_attempt':
            alerts.append(_alert('VA-DET-03',ts,identity,'high','Registrar tentativa; manter laboratorio isolado; nao executar retaliacao.'))
        elif kind=='mqtt_cross_site_rejected':
            alerts.append(_alert('VA-DET-04',ts,identity,'high','Verificar ACL MQTT e certificado do dispositivo.'))
        elif kind=='simulated_click' and event.get('source')=='phishing_simulation':
            alerts.append(_alert('VA-DET-05',ts,identity,'low','Notificar treinamento ficticio; sem acao em contas reais.'))
    return alerts


def _alert(rule, ts, identity, severity, action):
    return {'rule_id':rule, 'timestamp':ts, 'identity':identity,
            'severity':severity, 'description':RULES[rule],
            'suggested_action':action, 'automated_action':'NONE',
            'human_approval_required': severity in ('medium','high')}


def read_jsonl(path):
    events=[]
    with Path(path).open(encoding='utf-8') as f:
        for i,line in enumerate(f,1):
            if not line.strip():continue
            e=json.loads(line)
            if not isinstance(e,dict) or not isinstance(e.get('timestamp'),str):
                raise ValueError(f'{path}:{i} invalid event')
            events.append(e)
    return events


def write_alerts(alerts,path):
    with Path(path).open('w',encoding='utf-8') as f:
        for a in alerts: f.write(json.dumps(a,ensure_ascii=False,sort_keys=True)+'\n')
