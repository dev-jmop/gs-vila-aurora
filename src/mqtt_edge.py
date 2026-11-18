"""Borda: consome MQTT local, aplica regra local, guarda SQLite e reenvia para a nuvem.

Sem dependencia da nuvem para alarmar. Transporte para central ainda sem VPN/TLS,
apropriado SOMENTE para laboratorio Docker isolado (etapa 2A).
"""
import json
from contextlib import closing
import logging
import os
import sqlite3
import time
import urllib.error
import urllib.request
from pathlib import Path

from .edge import SITES, control, initialize
from .tls_config import configure_tls

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
LOG = logging.getLogger('edge')


def save_event(conn, event, expected_site):
    """Valida payload de laboratorio e grava uma vez, sem perder alerta local."""
    if not isinstance(event, dict) or event.get('site') != expected_site:
        raise ValueError('site invalido')
    kind, _ = SITES[expected_site]
    if event.get('kind') != kind:
        raise ValueError('tipo de leitura invalido')
    event_id = event['event_id']
    if not isinstance(event_id, str) or len(event_id) > 80 or not event_id:
        raise ValueError('identificador invalido')
    reading = float(event['reading'])
    if not (-1000 <= reading <= 1000):
        raise ValueError('leitura fora do limite de laboratorio')
    alert = control(expected_site, kind, reading)
    row = (event_id, expected_site, str(event['ts_utc']), kind, reading, alert)
    conn.execute('''INSERT OR IGNORE INTO outbox
        (event_id,site,ts_utc,kind,reading,alert) VALUES (?,?,?,?,?,?)''', row)
    conn.commit()
    return alert


def send_one(url, event, timeout=2):
    request = urllib.request.Request(url, data=json.dumps(event).encode(),
                                     headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        if resp.status != 200:
            raise RuntimeError(f'cloud HTTP {resp.status}')
        return json.load(resp)


def sync_once(conn, sender):
    """ACK por evento: se o envio falha, permanece pendente para nova tentativa."""
    rows = conn.execute('''SELECT event_id,site,ts_utc,kind,reading,alert
                            FROM outbox WHERE synced=0 ORDER BY ts_utc,event_id''').fetchall()
    sent = 0
    for event_id, site, ts_utc, kind, reading, alert in rows:
        event = dict(event_id=event_id, site=site, ts_utc=ts_utc,
                     kind=kind, reading=reading, alert=alert)
        try:
            ack = sender(event)
            if ack.get('event_id') != event_id:
                raise ValueError('ACK incorreto')
        except (OSError, ValueError, RuntimeError, urllib.error.URLError) as exc:
            LOG.warning('cloud_unavailable pending=%s error=%s', len(rows)-sent, exc)
            break
        conn.execute('UPDATE outbox SET synced=1 WHERE event_id=?', (event_id,))
        conn.commit()
        sent += 1
    return sent


def main():
    import paho.mqtt.client as mqtt
    site = os.environ['SITE']
    if site not in SITES:
        raise ValueError('SITE desconhecido')
    path = Path(os.environ.get('DB_PATH', '/data/events.sqlite3'))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = initialize(path)
    url = os.environ.get('CENTRAL_URL', 'http://cloud:8080/events')

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            client.subscribe(f'vila/{site}/telemetry', qos=1)
            LOG.info('mqtt_subscribed site=%s', site)
        else:
            LOG.warning('mqtt_connect_failed site=%s code=%s', site, reason_code)

    def on_message(client, userdata, message):
        try:
            event = json.loads(message.payload)
            # Paho executa callbacks em outra thread. Cada callback abre sua propria
            # conexao SQLite; a conexao de sincronizacao fica na thread principal.
            with closing(initialize(path)) as message_db:
                alert = save_event(message_db, event, site)
            LOG.info('LOCAL_EVENT site=%s event=%s reading=%s alert=%s',
                     site, event['event_id'], event['reading'], alert)
        except (ValueError, KeyError, TypeError, sqlite3.Error) as exc:
            LOG.warning('invalid_message site=%s error=%s', site, exc)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                         client_id=f'edge-{site}', clean_session=False)
    client.on_connect = on_connect
    client.on_message = on_message
    configure_tls(client)
    client.connect_async(os.environ.get('MQTT_HOST', f'mqtt-{site}'),
                         int(os.environ.get('MQTT_PORT', 8883)), keepalive=30)
    client.loop_start()
    try:
        while True:
            sent = sync_once(db, lambda event: send_one(url, event))
            if sent:
                LOG.info('cloud_reconciled site=%s count=%s', site, sent)
            time.sleep(max(1.0, float(os.environ.get('SYNC_INTERVAL', 3))))
    finally:
        client.loop_stop()
        client.disconnect()
        db.close()


if __name__ == '__main__':
    main()
