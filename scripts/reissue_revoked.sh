#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$EUID" -ne 0 ]]; then echo 'Execute com sudo'; exit 1; fi
name="${1:-}"
case "$name" in sensor-centro|sensor-escola|sensor-ubs|sensor-horta|sensor-abrigo|edge-centro|edge-escola|edge-ubs|edge-horta|edge-abrigo) ;; *) echo 'Informe identidade valida'; exit 2;; esac
BASE="$PWD/pki/runtime"; CA="$BASE/ca"; DEST="$BASE/clients/$name"
openssl req -new -newkey rsa:2048 -nodes -sha256 -subj "/CN=$name" -keyout "$DEST.key.new" -out "$BASE/$name.csr" >/dev/null 2>&1
openssl ca -batch -config "$CA/openssl.cnf" -extensions client_ext -in "$BASE/$name.csr" -out "$DEST.crt.new" -notext >/dev/null 2>&1
mv "$DEST.key.new" "$DEST.key"; mv "$DEST.crt.new" "$DEST.crt"; rm -f "$BASE/$name.csr"
chmod 600 "$DEST.key"; chmod 644 "$DEST.crt"
echo "Novo certificado para $name emitido, com novo numero de serie. Reinicie broker e cliente."
