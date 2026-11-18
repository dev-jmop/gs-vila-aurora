#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ "$EUID" -ne 0 ]]; then echo "Execute com sudo: sudo bash scripts/setup_pki.sh"; exit 1; fi
umask 077
BASE="$PWD/pki/runtime"; CA="$BASE/ca"
if [[ -e "$CA/private/ca.key" ]]; then echo "PKI ja existe. Para rotacao, use scripts/rotate_cert.sh"; exit 1; fi
mkdir -p "$CA"/{private,certs,crl,newcerts} "$BASE"/{clients,servers}
touch "$CA/index.txt"
echo 1000 > "$CA/serial"
echo 1000 > "$CA/crlnumber"
cat > "$CA/openssl.cnf" <<EOF
[ ca ]
default_ca = CA_default
[ CA_default ]
dir = $CA
certificate = \$dir/certs/ca.crt
private_key = \$dir/private/ca.key
database = \$dir/index.txt
new_certs_dir = \$dir/newcerts
serial = \$dir/serial
crlnumber = \$dir/crlnumber
crl = \$dir/crl/ca.crl
default_md = sha256
default_days = 365
policy = policy_any
unique_subject = no
default_crl_days = 30
copy_extensions = none
[ policy_any ]
commonName = supplied
[ server_ext ]
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = DNS:localhost
[ client_ext ]
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature
extendedKeyUsage = clientAuth
EOF
openssl req -x509 -newkey rsa:3072 -nodes -sha256 -days 3650 \
 -subj '/CN=Vila Aurora Lab Root CA' \
 -addext 'basicConstraints=critical,CA:TRUE' \
 -addext 'keyUsage=critical,keyCertSign,cRLSign' \
 -keyout "$CA/private/ca.key" -out "$CA/certs/ca.crt" >/dev/null 2>&1
issue() {
 local role="$1" name="$2" dest="$3" ext="$4" san="${5:-}"
 openssl req -new -newkey rsa:2048 -nodes -sha256 \
   -subj "/CN=$name" -keyout "$dest.key" -out "$BASE/$name.csr" >/dev/null 2>&1
 if [[ "$role" == server ]]; then
   printf '[ server_ext ]\nbasicConstraints=CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\nsubjectAltName=%s\n' "$san" > "$BASE/server_ext.cnf"
   openssl ca -batch -config "$CA/openssl.cnf" -extfile "$BASE/server_ext.cnf" -extensions server_ext \
     -in "$BASE/$name.csr" -out "$dest.crt" -notext >/dev/null 2>&1
   rm -f "$BASE/server_ext.cnf"
 else
   openssl ca -batch -config "$CA/openssl.cnf" -extensions "$ext" \
     -in "$BASE/$name.csr" -out "$dest.crt" -notext >/dev/null 2>&1
 fi
 rm -f "$BASE/$name.csr"
 chmod 600 "$dest.key"
 chmod 644 "$dest.crt"
 if [[ "$role" == server ]]; then chown 1883:1883 "$dest.key"; fi
}
for site in centro escola ubs horta abrigo; do
 issue server "mqtt-$site" "$BASE/servers/mqtt-$site" server_ext "DNS:mqtt-$site"
 issue client "sensor-$site" "$BASE/clients/sensor-$site" client_ext
 issue client "edge-$site" "$BASE/clients/edge-$site" client_ext
done
openssl ca -gencrl -config "$CA/openssl.cnf" -out "$CA/crl/ca.crl" >/dev/null 2>&1
chmod 644 "$CA/certs/ca.crt" "$CA/crl/ca.crl"
# Necessario para que mosquitto (UID 1883) leia arquivos montados em /certs.
chmod 755 "$BASE" "$BASE/servers" "$CA" "$CA/certs" "$CA/crl" "$BASE/clients"
echo 'PKI criada: 5 servidores + 10 clientes, sem chaves privadas no Git.'
