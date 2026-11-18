"""Configuracao de mTLS obrigatoria no MQTT; proibido fallback plaintext."""
import os
import ssl

def configure_tls(client):
    ca = os.environ.get('MQTT_CA', '/certs/ca.crt')
    cert = os.environ.get('MQTT_CERT', '/certs/client.crt')
    key = os.environ.get('MQTT_KEY', '/certs/client.key')
    client.tls_set(ca_certs=ca, certfile=cert, keyfile=key,
                   cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)
    client.tls_insecure_set(False)
