"""RT-13: regras acadêmicas sobre eventos JSON estruturados, sem comandos físicos.

Os eventos de demonstração são sintéticos. Os parâmetros de autorização e os
intervalos de horário são fornecidos pelo código (não pelo evento recebido).
"""
from datetime import timedelta, timezone
from ipaddress import ip_address, ip_network
from zoneinfo import ZoneInfo

from .detector import parse_time

POLICY_ACTUATORS = {
    ('horta', 'pump_start'): frozenset({'tecnico', 'coordenacao'}),
    ('escola', 'pump_start'): frozenset({'tecnico', 'coordenacao'}),
    ('ubs', 'cooling_override'): frozenset({'coordenacao'}),
}
# janela ilustrativa em horário local, inicio inclusivo e fim exclusivo
WINDOW_START = 6
WINDOW_END = 20
RULES_REQUIRED = {
    'VA-RT13-VPN': 'Autenticação VPN proveniente de endereço fora da rede autorizada',
    'VA-RT13-SQLI': 'Padrão de tentativa de SQL injection',
    'VA-RT13-CERT': 'Identidade TLS com certificado inválido ou revogado',
    'VA-RT13-ACT': 'Comando de atuador fora de perfil, horário ou catálogo',
}


def _alert(rule, event, reason, severity='high'):
    return {
        'rule_id': rule, 'timestamp': event['timestamp'],
        'identity': str(event.get('identity', 'unknown'))[:100],
        'severity': severity, 'reason': reason,
        'human_approval_required': True,
        'action_executed': False,
        'simulation': bool(event.get('simulation', False)),
    }


def detect_required(events, vpn_allowed_cidrs=(), tz='America/Sao_Paulo'):
    """Inspeciona eventos estruturados com baseline VPN fornecida pelo operador.

    Sem CIDRs configurados, NÃO presume que qualquer IP seja anômalo: a regra
    VPN fica sem base e o relatório deve mostrar essa limitação.
    """
    networks = [ip_network(cidr, strict=False) for cidr in vpn_allowed_cidrs]
    local_tz = ZoneInfo(tz)
    result = []
    for event in sorted(events, key=lambda e: parse_time(e['timestamp'])):
        kind = event.get('event')
        if kind == 'vpn_login_success' and networks:
            try:
                peer = ip_address(event.get('source_ip', ''))
                if not any(peer in net for net in networks):
                    result.append(_alert('VA-RT13-VPN', event, 'source_ip_outside_baseline'))
            except ValueError:
                result.append(_alert('VA-RT13-VPN', event, 'invalid_source_ip'))
        elif kind in ('sqli_attempt', 'sqli_pattern'):
            result.append(_alert('VA-RT13-SQLI', event, 'sqli_pattern_detected'))
        elif kind in ('tls_certificate_verify_failed', 'certificate_revoked', 'certificate_invalid'):
            result.append(_alert('VA-RT13-CERT', event, 'invalid_or_revoked_client_certificate'))
        elif kind == 'actuator_command':
            site = event.get('site')
            command = event.get('command')
            role = event.get('role')
            allowed = POLICY_ACTUATORS.get((site, command))
            local_hour = parse_time(event['timestamp']).astimezone(local_tz).hour
            reasons = []
            if allowed is None:
                reasons.append('command_not_in_policy')
            elif role not in allowed:
                reasons.append('unauthorized_role')
            if not WINDOW_START <= local_hour < WINDOW_END:
                reasons.append('outside_allowed_hours')
            if reasons:
                result.append(_alert('VA-RT13-ACT', event, ','.join(reasons), 'critical'))
    return result
