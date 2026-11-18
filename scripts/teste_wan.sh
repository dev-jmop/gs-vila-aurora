#!/usr/bin/env bash
set -euo pipefail
# O cloud representa a conectividade WAN. Sem derrubar a rede Docker de campo.
DURATION="${1:-60}"
if ! [[ "$DURATION" =~ ^[0-9]+$ ]] || (( DURATION < 1 )); then
  echo "Uso: $0 SEGUNDOS (numero inteiro positivo)" >&2; exit 2
fi
echo "[1] Antes: eventos no servidor central"
curl -fsS http://127.0.0.1:8080/stats; echo
trap 'docker compose start cloud >/dev/null' EXIT
echo "[2] Simulando queda da WAN por $DURATION segundos: docker compose stop cloud"
docker compose stop cloud
echo "[3] Observe os alertas locais durante a falha com: docker compose logs -f edge-ubs"
sleep "$DURATION"
echo '[4] Restaurando conectividade'
docker compose start cloud
trap - EXIT
sleep 12
echo '[5] Eventos sincronizados apos restauracao'
curl -fsS http://127.0.0.1:8080/stats; echo
echo 'Compare os logs e as contagens. Para RT-23 use 1800 segundos e registre evidencias.'
