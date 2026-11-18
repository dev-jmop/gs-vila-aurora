import base64
import hashlib
import hmac
import json
import os
import struct
import time
from pathlib import Path
from werkzeug.security import check_password_hash

ROLES = ('operador', 'tecnico', 'coordenacao', 'auditor')

def totp(secret, at=None):
    at = int(time.time() if at is None else at)
    key = base64.b32decode(secret.upper() + '=' * (-len(secret) % 8))
    digest = hmac.new(key, struct.pack('>Q', at // 30), hashlib.sha1).digest()
    n = digest[-1] & 0x0f
    return f'{(struct.unpack(">I", digest[n:n+4])[0] & 0x7fffffff) % 1000000:06d}'

def verify_totp(secret, code, at=None):
    if not isinstance(code, str) or not (len(code) == 6 and code.isascii() and code.isdigit()):
        return False
    now = int(time.time() if at is None else at)
    return any(hmac.compare_digest(totp(secret, now + delta*30), code) for delta in (-1,0,1))

def load_users(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def authenticate(users, username, password, code, at=None):
    entry = users.get(username)
    if not entry or entry.get('role') not in ROLES:
        return None
    if not check_password_hash(entry['password_hash'], password):
        return None
    if not verify_totp(entry['totp_secret'], code, at):
        return None
    return entry['role']
