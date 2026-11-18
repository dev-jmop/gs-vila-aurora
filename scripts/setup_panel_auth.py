#!/usr/bin/env python3
"""Provisiona usuarios ficticios; segredos SOMENTE em arquivos locais 0600.
Nao reutilizar em producao. Nunca versionar auth/runtime/.
"""
import base64
import json
import os
import secrets
from pathlib import Path
from werkzeug.security import generate_password_hash

base = Path(__file__).resolve().parents[1] / 'auth' / 'runtime'
if base.exists() and any(base.iterdir()):
    raise SystemExit('Auth ja provisionado: nenhum arquivo existente sera sobrescrito.')
base.mkdir(parents=True, exist_ok=True, mode=0o700)
base.chmod(0o700)

users = {}
creds = []
for username, role in (
    ('operador', 'operador'), ('tecnico', 'tecnico'),
    ('coordenacao', 'coordenacao'), ('auditor', 'auditor')
):
    password = secrets.token_urlsafe(24)
    secret = base64.b32encode(secrets.token_bytes(20)).decode().rstrip('=')
    users[username] = {
        'role': role, 'password_hash': generate_password_hash(password),
        'totp_secret': secret,
    }
    creds.append(f'{username}\nsenha: {password}\nTOTP_secret: {secret}\n')

def write_private(filename, content):
    path = base / filename
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        stream.write(content)

write_private('users.json', json.dumps(users, indent=2) + '\n')
write_private('session.key', secrets.token_urlsafe(48) + '\n')
write_private('credenciais_iniciais.txt', '\n'.join(creds))
print('Provisionamento concluido. Nenhum segredo foi mostrado no terminal.')
print('Credenciais iniciais em auth/runtime/credenciais_iniciais.txt (permissoes 0600).')
print('Guarde em gerenciador seguro, valide login e remova o TXT apos uso.')
