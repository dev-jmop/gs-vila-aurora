"""Publicador de telemetria SINTETICA; nao controla hardware."""
import json
import logging
import os
import random
import time
import uuid

from .edge import SITES, utc_now
from .tls_config import configure_tls

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
LOG = logging.getLogger('sensor')


def synthetic_reading(site):
    kind, base = SITES[site]
    if kind == 'cold_room_temp_c':
        return round(random.choice([5.0, 5.5, 6.0, 8.5, 9.2]), 2)
    if kind == 'water_level_pct':
        return round(max(0, min(100, base + random.randint(-30, 10))), 2)
    if kind == 'flood_sensor':
        return float(random.random() < 0.12)
    return float(random.randint(0, 2))


def build_event(site, reading=None):
    kind, _ = SITES[site]
    return {
        'event_id': str(uuid.uuid4()),
        'site': site,
        'ts_utc': utc_now(),
        'kind': kind,
        'reading': synthetic_reading(site) if reading is None else float(reading),
    }


def main():
    import paho.mqtt.client as mqtt
    site = os.environ['SITE']
    host = os.environ.get('MQTT_HOST', 'localhost')
    interval = max(1.0, float(os.environ.get('PUBLISH_INTERVAL', 5)))
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f'sensor-{site}')
    configure_tls(client)
    client.connect_async(host, int(os.environ.get('MQTT_PORT', 8883)), keepalive=30)
    client.loop_start()
    try:
        while True:
            if client.is_connected():
                event = build_event(site)
                info = client.publish(f'vila/{site}/telemetry', json.dumps(event), qos=1)
                info.wait_for_publish(timeout=10)
                LOG.info('mqtt_publish site=%s event=%s reading=%s rc=%s', site, event['event_id'], event['reading'], info.rc)
            else:
                LOG.warning('mqtt_disconnected site=%s', site)
            time.sleep(interval)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == '__main__':
    main()
