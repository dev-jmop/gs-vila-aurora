"""Prova autenticacao MQTT (CONNACK), nao apenas handshake TLS."""
import argparse
import ssl
import threading
import paho.mqtt.client as mqtt


def check(host, mode, timeout=6):
    state = {'connected': False, 'reason': 'sem CONNACK'}
    done = threading.Event()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='probe-mtls-ubs')
    context = ssl.create_default_context(cafile='/certs/ca.crt')
    if mode == 'valid':
        context.load_cert_chain('/certs/client.crt', '/certs/client.key')
    client.tls_set_context(context)

    def on_connect(client, userdata, flags, reason_code, properties):
        state['connected'] = not reason_code.is_failure
        state['reason'] = str(reason_code)
        done.set()

    def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
        if not state['connected']:
            state['reason'] = f'desconectado: {reason_code}'
            done.set()

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    try:
        client.connect(host, 8883, keepalive=10)
        client.loop_start()
        done.wait(timeout)
    except (OSError, ssl.SSLError) as exc:
        state['reason'] = f'{type(exc).__name__}: {exc}'
    finally:
        try:
            client.disconnect()
            client.loop_stop()
        except RuntimeError:
            pass
    return state


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='mqtt-ubs')
    parser.add_argument('--mode', choices=['valid', 'no-cert'], required=True)
    args = parser.parse_args()
    result = check(args.host, args.mode)
    print(result)
    expected = args.mode == 'valid'
    if result['connected'] != expected:
        raise SystemExit('FALHA: resultado diferente do esperado')
    print('PASSOU: autenticacao MQTT conforme esperado')
