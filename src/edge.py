"""Protótipo etapa 1: regras locais e fila durável, sem MQTT/mTLS ainda.

A operação deste script demonstra apenas RT-01/RT-02 de forma parcial.
Todos os dados e atuadores são fictícios.
"""
import argparse
import json
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

SITES = {
    'centro': ('access_attempts', 0),
    'escola': ('water_level_pct', 45),
    'ubs': ('cold_room_temp_c', 7.1),
    'horta': ('water_level_pct', 18),
    'abrigo': ('flood_sensor', 0),
}


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')


def initialize(path):
    conn = sqlite3.connect(path)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('''CREATE TABLE IF NOT EXISTS outbox (
        event_id TEXT PRIMARY KEY, site TEXT NOT NULL, ts_utc TEXT NOT NULL,
        kind TEXT NOT NULL, reading REAL NOT NULL, alert TEXT, synced INTEGER NOT NULL DEFAULT 0
    )''')
    conn.commit()
    return conn


def control(site, kind, reading):
    """Valores *ilustrativos de laboratório*, não parâmetros operacionais reais."""
    if site == 'ubs' and kind == 'cold_room_temp_c' and reading > 7:
        return 'ALERTA LOCAL: temperatura acima do limite SIMULADO'
    if site in ('escola', 'horta') and kind == 'water_level_pct' and reading < 20:
        return 'ALERTA LOCAL: nível baixo; bloquear acionamento SIMULADO da bomba'
    if site == 'abrigo' and kind == 'flood_sensor' and reading >= 1:
        return 'ALERTA LOCAL: possível alagamento'
    return None


def produce(conn, site, reading=None):
    if site not in SITES:
        raise ValueError('Espaço desconhecido')
    kind, default = SITES[site]
    val = float(default if reading is None else reading)
    alert = control(site, kind, val)
    data = dict(event_id=str(uuid.uuid4()), site=site, ts_utc=utc_now(), kind=kind,
                reading=val, alert=alert)
    conn.execute('''INSERT INTO outbox(event_id,site,ts_utc,kind,reading,alert)
                    VALUES(:event_id,:site,:ts_utc,:kind,:reading,:alert)''', data)
    conn.commit()
    return data


def pending(conn):
    return [dict(zip(('event_id','site','ts_utc','kind','reading','alert'), row))
            for row in conn.execute('''SELECT event_id,site,ts_utc,kind,reading,alert
                                      FROM outbox WHERE synced=0 ORDER BY ts_utc,event_id''')]


def reconcile(conn, central):
    """Simula WAN restaurada: cópia idempotente para banco central local."""
    central.execute('''CREATE TABLE IF NOT EXISTS events (
        event_id TEXT PRIMARY KEY, site TEXT, ts_utc TEXT, kind TEXT, reading REAL, alert TEXT
    )''')
    synced = 0
    for e in pending(conn):
        central.execute('''INSERT OR IGNORE INTO events VALUES (?,?,?,?,?,?)''',
                        (e['event_id'],e['site'],e['ts_utc'],e['kind'],e['reading'],e['alert']))
        central.commit()  # confirmação de persistência antes do ACK
        conn.execute('UPDATE outbox SET synced=1 WHERE event_id=?', (e['event_id'],))
        conn.commit()
        synced += 1
    return synced


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--site', choices=SITES, required=True)
    parser.add_argument('--db-dir', default='runtime')
    parser.add_argument('--reading', type=float)
    parser.add_argument('--offline', action='store_true', help='não sincronizar com servidor central')
    args = parser.parse_args()
    d = Path(args.db_dir)
    d.mkdir(parents=True, exist_ok=True)
    with initialize(d / (args.site + '.sqlite3')) as edge:
        event = produce(edge, args.site, args.reading)
        print(json.dumps({'evento':event, 'pendentes':len(pending(edge))}, ensure_ascii=False))
        if not args.offline:
            with sqlite3.connect(d / 'cloud.sqlite3') as cloud:
                print(json.dumps({'sincronizados':reconcile(edge, cloud), 'pendentes':len(pending(edge))}))


if __name__ == '__main__':
    main()
