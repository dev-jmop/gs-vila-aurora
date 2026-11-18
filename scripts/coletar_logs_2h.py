#!/usr/bin/env python3
"""Coleta de logs local por Docker Compose + host, armazenamento SQLite com retenção.

Não modifica containers, bancos de telemetria, firewall ou certificados.
Não configura Wazuh/NTP; apenas registra seu estado quando consultável.
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.security.siem import LocalSIEM
from src.security.evidence import create_manifest, verify_manifest

PREFIX = re.compile(r'^\s*([\w.-]+?)(?:-\d+)?\s*\|\s*(.*)$')


def run(args, timeout=35):
    try:
        r=subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        return r.returncode, r.stdout, r.stderr[:500]
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127,'',str(exc)[:500]


def category(source, line):
    if source.startswith('mqtt-'):return 'broker'
    if source.startswith('sensor-'):return 'device'
    if source.startswith('edge-'):return 'edge'
    if source == 'cloud':return 'database' if 'stored ' in line else 'web_vpn'
    if source in ('panel','sqli-lab'):return 'web'
    return 'service'


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--minutes',type=int,default=3)
    p.add_argument('--retention-days',type=int,default=30)
    p.add_argument('--output',default='evidence/runtime/etapa2h_coleta')
    p.add_argument('--sudo',action='store_true',help='Usa sudo -n; execute sudo -v antes')
    args=p.parse_args()
    if not 1 <= args.minutes <= 1440: p.error('--minutes precisa estar entre 1 e 1440')
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    docker=['sudo','-n','docker'] if args.sudo else ['docker']
    compose=docker+['compose','-f','compose.wireguard.full.yaml','-f','compose.panel.yaml']
    # logs não contêm segredos por padrão; sanear tokens é uma proteção adicional.
    rc,stdout,err=run(compose+['logs','--no-color','--timestamps','--tail','300',
                               '--since',f'{args.minutes}m'],timeout=60)
    if rc != 0:
        raise SystemExit(f'ERRO docker compose logs: {err or stdout[:500]}')
    batches={}
    for line in stdout.splitlines():
        m=PREFIX.match(line)
        if m:source,message=m.group(1),m.group(2)
        else:source,message='compose_unknown',line
        cat=category(source,message)
        batches.setdefault((source,cat),[]).append(message)
    with LocalSIEM(out/'siem_local.sqlite3') as siem:
        for (source,cat), lines in batches.items():
            siem.ingest(source,cat,lines)

        # Amostra de logs de SO, cuja leitura pode depender de permissões.
        os_rc,os_stdout,os_err=run(['journalctl','--no-pager',
                                    '--since',f'{args.minutes} minutes ago',
                                    '--output','short-iso','-n','100'],timeout=15)
        if os_rc==0:siem.ingest('host-os','operating_system',os_stdout.splitlines())
        # Estado NTP; check apenas, sem modificar configuração do host.
        ntp_rc,ntp_out,ntp_err=run(['timedatectl','show','-p','NTPSynchronized','--value'],timeout=10)
        if ntp_rc==0:siem.ingest('host-ntp','clock',[f'NTPSynchronized={ntp_out.strip()}'])
        # WireGuard. A chamada retorna SOMENTE handshakes/chaves públicas; nenhuma chave privada.
        wg_rc,wg_out,wg_err=run(compose+['exec','-T','cloud','wg','show','wg0','latest-handshakes'],timeout=20)
        if wg_rc==0:
            # Chaves publicas são hasheadas em vez de copiadas para o log central.
            import hashlib
            rows=[]
            for peer in wg_out.splitlines():
                fields=peer.split()
                if len(fields)==2:
                    rows.append('peer_sha256_12='+hashlib.sha256(fields[0].encode()).hexdigest()[:12]+
                                ' last_handshake_unix='+fields[1])
            siem.ingest('cloud-wireguard','vpn',rows)
        # Integridade do banco da nuvem, sem ler/copiar seus eventos originais.
        db_rc,db_out,db_err=run(compose+['exec','-T','cloud','python','-c',
                            "import sqlite3;c=sqlite3.connect('file:/data/cloud.sqlite3?mode=ro',uri=True);print(c.execute('PRAGMA quick_check').fetchone()[0]);c.close()"],timeout=20)
        if db_rc==0:siem.ingest('cloud-db','database_health',['sqlite_quick_check='+db_out.strip()])
        removed=siem.expire(args.retention_days)
        summary=siem.summary()
    summary.update({'collection_at_utc':datetime.now(timezone.utc).isoformat(),
        'retention_days':args.retention_days,'expired_events':removed,
        'source_checks':{'docker_compose':rc==0,'host_os':os_rc==0,
                         'host_ntp':ntp_rc==0,'ntp_synchronized':ntp_out.strip()=='yes' if ntp_rc==0 else None,
                         'wireguard':wg_rc==0,'cloud_db':db_rc==0},
        'limitations':'Coleta pontual em SQLite local; use agendamento para coleta contínua. Ainda NÃO há implantação/ingestão comprovada no Wazuh; NTP somente consultado.'})
    (out/'coleta_resumo.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    create_manifest(out)
    print(json.dumps({'status':'PASSOU','output':str(out),'events':summary['events_total'],
                       'sources':len(summary['sources']),
                       'retention_days':args.retention_days,
                       'source_checks':summary['source_checks'],
                       'sha256_verified':verify_manifest(out)},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
