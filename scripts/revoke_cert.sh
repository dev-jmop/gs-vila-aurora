#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$EUID" -ne 0 ]]; then echo 'Execute com sudo'; exit 1; fi
name="${1:-}"
case "$name" in sensor-centro|sensor-escola|sensor-ubs|sensor-horta|sensor-abrigo|edge-centro|edge-escola|edge-ubs|edge-horta|edge-abrigo) ;; *) echo 'Informe identidade sensor-* ou edge-* valida'; exit 2;; esac
CA="$PWD/pki/runtime/ca"
openssl ca -config "$CA/openssl.cnf" -revoke "$PWD/pki/runtime/clients/$name.crt" -crl_reason keyCompromise >/dev/null
openssl ca -gencrl -config "$CA/openssl.cnf" -out "$CA/crl/ca.crl" >/dev/null 2>&1
chmod 644 "$CA/crl/ca.crl"
echo "Revogado: $name. REINICIE o broker correspondente para carregar a nova CRL: sudo docker compose restart mqtt-${name#*-}"
