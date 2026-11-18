#!/usr/bin/env python3
import json
import os
import secrets
import base64
from pathlib import Path
from werkzeug.security import generate_password_hash

base = Path(__file__).resolve().parents[1] / "auth" / "runtime"
users_path = base / "users.json"
session_path = base / "session.key"
output = base / "credenciais_novas.txt"

if not users_path.is_file() or not session_path.is_file():
    raise SystemExit("ERRO: configuracao atual nao encontrada.")

users = json.loads(users_path.read_text(encoding="utf-8"))
expected = {"operador", "tecnico", "coordenacao", "auditor"}

if set(users) != expected:
    raise SystemExit("ERRO: usuarios diferentes dos esperados.")

if output.exists():
    raise SystemExit("ERRO: credenciais_novas.txt ja existe. Remova apenas apos guardar as credenciais.")

lines = []
for username, entry in users.items():
    password = secrets.token_urlsafe(24)
    totp_secret = base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")
    entry["password_hash"] = generate_password_hash(password)
    entry["totp_secret"] = totp_secret
    lines.append(f"{username}\nsenha: {password}\nTOTP_secret: {totp_secret}\n")

# Arquivo privado criado antes da substituicao.
fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

def replace_private(path, content):
    temp = path.with_name(path.name + ".new")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(temp, path)

replace_private(users_path, json.dumps(users, indent=2))
replace_private(session_path, secrets.token_urlsafe(48))

print("PASSOU: credenciais e chave de sessao renovadas.")
print("Novas credenciais guardadas em auth/runtime/credenciais_novas.txt")
print("NAO envie esse arquivo para ninguem.")
