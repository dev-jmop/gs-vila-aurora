#!/usr/bin/env python3
"""Gera identidades WireGuard efemeras somente no computador do aluno.
Requer cryptography: python -m venv .venv && .venv/bin/pip install cryptography
"""
import base64
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives import serialization

ROOT = Path(__file__).resolve().parent.parent
DST = ROOT / 'vpn' / 'runtime'
SITES = ['centro', 'escola', 'ubs', 'horta', 'abrigo']

def keypair():
    private = X25519PrivateKey.generate()
    private_raw = private.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
    public_raw = private.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return tuple(base64.b64encode(k).decode('ascii') for k in (private_raw, public_raw))

def main():
    if DST.exists() and list(DST.glob('*.conf')):
        raise SystemExit('Configuracoes existentes em vpn/runtime; nao sobrescrever. Use as chaves atuais.')
    DST.mkdir(parents=True, exist_ok=True, mode=0o700)
    DST.chmod(0o700)
    peers = {'cloud': keypair()}
    peers.update({f'edge-{s}': keypair() for s in SITES})
    hub = '[Interface]\nAddress = 10.77.0.1/24\nListenPort = 51820\nPrivateKey = ' + peers['cloud'][0] + '\n'
    for i, s in enumerate(SITES, 2):
        hub += f'\n[Peer]\n# edge-{s}\nPublicKey = {peers[f"edge-{s}"][1]}\nAllowedIPs = 10.77.0.{i}/32\n'
        edge = f"""[Interface]
Address = 10.77.0.{i}/32
PrivateKey = {peers[f'edge-{s}'][0]}

[Peer]
PublicKey = {peers['cloud'][1]}
Endpoint = cloud:51820
AllowedIPs = 10.77.0.1/32
PersistentKeepalive = 25
"""
        f = DST / f'edge-{s}.conf';f.write_text(edge);f.chmod(0o600)
    f = DST / 'cloud.conf';f.write_text(hub);f.chmod(0o600)
    print('VPN criada: 1 servidor e 5 peers. Chaves privadas nao devem ir ao Git.')

if __name__ == '__main__': main()
