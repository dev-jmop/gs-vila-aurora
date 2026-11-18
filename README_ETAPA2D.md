# Etapa 2D — Painel Flask + SQL Injection (antes/depois)

Este pacote preserva a Etapa 2C e inclui a correção persistente validada em ambiente de laboratório em `vpn/entrypoint.sh`: bloqueio 8080/8081 fora de wg0.

**Não apague seus volumes Docker nem as pastas `pki/runtime` e `vpn/runtime`.** O ZIP não contém segredos e não os substitui.

## Instalação

```bash
cd diretorio-do-projeto
unzip -o GS_Vila_Aurora_Etapa2D_Painel_SQLi.zip
cd vila-aurora-etapa2
python -m venv .venv
.venv/bin/pip install 'Flask>=3.1,<4'
.venv/bin/python scripts/setup_panel_auth.py
sudo docker compose -f compose.wireguard.full.yaml -f compose.panel.yaml config --quiet
sudo docker compose -f compose.wireguard.full.yaml -f compose.panel.yaml up -d --build
```

Anote as senhas fictícias geradas. O script cria o arquivo `auth/runtime/users.json` e a chave de sessão local. Não compartilhe as credenciais. Se já estiverem provisionadas, não sobrescreva.

## Validar

Painel `http://127.0.0.1:8090` (somente localhost). Gerar código TOTP fictício:

```bash
.venv/bin/python scripts/totp_demo.py operador
```

A conta `operador` pode consultar o dashboard, mas recebe HTTP 403 em `/audit`. A conta `auditor` acessa `/audit`.

Laboratório intencionalmente vulnerável:

```bash
bash scripts/teste_sqli.sh
.venv/bin/python -m unittest discover -s tests -v
```

Conferir os serviços:

```bash
sudo docker compose -f compose.wireguard.full.yaml -f compose.panel.yaml ps
sudo docker compose -f compose.wireguard.full.yaml -f compose.panel.yaml logs --tail=30 panel sqli-lab
```

O container `sqli-lab` contém uma falha **deliberada**, acessível apenas no notebook via `127.0.0.1:8091`, com rede interna separada, sem VPN, certificados ou volume de telemetria. Nunca exponha a porta na internet. O painel também é restrito a localhost; em produção seriam necessários HTTPS, rate limit distribuído e controles adicionais.

Consulte `docs/E2_etapa2D_painel_sqli.md` para detalhes, evidências e limitações.
