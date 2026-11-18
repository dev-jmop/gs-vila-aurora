"""Teste de handshake SSL sem side effects; nao envia comandos a atuadores."""
import argparse
import socket
import ssl

def probe(host, port, cafile, certfile=None, keyfile=None):
    context = ssl.create_default_context(cafile=cafile)
    if certfile:
        context.load_cert_chain(certfile, keyfile)
    with socket.create_connection((host, port), timeout=8) as sock:
        with context.wrap_socket(sock, server_hostname=host) as tls:
            tls.sendall(b'\x10\x00')  # CONNECT MQTT malformado; TLS ja negociado
            try:
                tls.recv(2)
            except (ConnectionResetError, TimeoutError, ssl.SSLError):
                pass
            return tls.version()

if __name__ == '__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--host', default='mqtt-ubs')
    a.add_argument('--mode', choices=['valid','no-cert'], default='valid')
    args=a.parse_args()
    try:
        version=probe(args.host,8883,'/certs/ca.crt',
            '/certs/client.crt' if args.mode=='valid' else None,
            '/certs/client.key' if args.mode=='valid' else None)
        print('TLS established:', version)
    except Exception as exc:
        print('TLS rejected:',type(exc).__name__,str(exc))
