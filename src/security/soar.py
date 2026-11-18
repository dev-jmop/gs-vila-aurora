"""RT-15: playbook defensivo acadêmico com operação local de baixo risco.

Não altera firewall, certificados, VPN ou atuadores. Ações de impacto
requerem aprovação humana e execução manual fora deste módulo.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

# Respostas de baixo risco aplicadas: registrar caso e enfileirar notificação.
# Mudanças na rede/identidades não são feitas sem aprovação explícita.
HIGH_IMPACT_ACTIONS = {
    'revoke_certificate', 'isolate_device', 'terminate_vpn_session',
    'block_network_ip', 'set_actuator_safe_mode',
}


def decide(alert):
    rule = alert['rule_id']
    if rule == 'VA-RT13-CERT':
        proposed = 'revoke_certificate'
    elif rule == 'VA-RT13-VPN':
        proposed = 'terminate_vpn_session'
    elif rule == 'VA-RT13-ACT':
        proposed = 'set_actuator_safe_mode'
    elif rule == 'VA-RT13-SQLI':
        proposed = 'block_network_ip'
    else:
        proposed = 'investigate'
    return {
        'timestamp': alert['timestamp'],
        'rule_id': rule,
        'identity': alert.get('identity', 'unknown'),
        'suggested_action': proposed,
        'status': 'AWAITING_HUMAN_APPROVAL' if proposed in HIGH_IMPACT_ACTIONS else 'TRIAGE_ONLY',
        'executed': False,
    }


def process_alerts(alerts, outdir, at=None):
    """Automatiza abertura de caso e fila de avisos; nunca ações disruptivas.

    O arquivo JSONL é o fluxo de trabalho reproduzível. A integração com
    notificações externas e execução de firewall permanecem pendentes.
    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    received = (at or datetime.now(timezone.utc)).isoformat()
    cases = []
    queue = []
    for index, alert in enumerate(alerts, 1):
        case = decide(alert)
        case['case_id'] = f'VA-CASE-{index:04d}'
        case['received_at_utc'] = received
        cases.append(case)
        queue.append({
            'case_id': case['case_id'], 'channel': 'local_operator_queue',
            'severity': alert.get('severity', 'unknown'),
            'status': 'PENDING_REVIEW',
            'message': f"Revisar {case['rule_id']} para {case['identity']}",
        })
    for filename, rows in (('soar_cases.jsonl', cases), ('operator_queue.jsonl', queue)):
        with (outdir / filename).open('w', encoding='utf-8') as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
    return {'cases_created': len(cases), 'notifications_queued': len(queue),
            'disruptive_actions_executed': 0, 'human_gate_enforced': True}
