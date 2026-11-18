#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$EUID" -ne 0 ]]; then echo 'Execute com sudo'; exit 1; fi
name="${1:-}"
case "$name" in sensor-centro|sensor-escola|sensor-ubs|sensor-horta|sensor-abrigo|edge-centro|edge-escola|edge-ubs|edge-horta|edge-abrigo) ;; *) echo 'Informe identidade sensor-* ou edge-* valida'; exit 2;; esac
BASE="$PWD/pki/runtime"; CA="$BASE/ca"; DEST="$BASE/clients/$name"
# Primeiro revoga o certificado antigo. Falha se ja revogado.
openssl ca -config "$CA/openssl.cnf" -revoke "$DEST.crt" -crl_reason superseded >/dev/null
openssl req -new -newkey rsa:2048 -nodes -sha256 -subj "/CN=$name" \
  -keyout "$DEST.key.new" -out "$BASE/$name.csr" >/dev/null 2>&1
openssl ca -batch -config "$CA/openssl.cnf" -extensions client_ext \
  -in "$BASE/$name.csr" -out "$DEST.crt.new" -notext >/dev/null 2>&1
mv "$DEST.key.new" "$DEST.key"; mv "$DEST.crt.new" "$DEST.crt"; rm -f "$BASE/$name.csr"
chmod 600 "$DEST.key"; chmod 644 "$DEST.crt"
openssl ca -gencrl -config "$CA/openssl.cnf" -out "$CA/crl/ca.crl" >/dev/null 2>&1
chmod 644 "$CA/crl/ca.crl"
echo "Rotacionado $name. Reinicie broker e cliente: sudo docker compose restart mqtt-${name#*-} $name"
