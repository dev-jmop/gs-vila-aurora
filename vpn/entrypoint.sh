#!/bin/sh
set -eu
# Aguarda DNS/UDP do servidor e aplica configuracao WireGuard local.
i=0
until wg-quick up /wg/wg0.conf; do
  i=$((i+1))
  if [ "$i" -ge 20 ]; then echo "ERRO: nao foi possivel iniciar WireGuard" >&2; exit 1; fi
  sleep 2
done
if [ "${WG_ROLE:-}" = "server" ]; then
  # Restringe APIs centrais ao tunel WireGuard (inclusive observabilidade).
  for port in 8080 8081; do
    iptables -I INPUT -p tcp --dport "$port" ! -i wg0 -j REJECT
  done
fi
printf 'WIREGUARD_READY role=%s ip=%s\n' "${WG_ROLE:-edge}" "$(ip -4 -o addr show wg0 | awk '{print $4}')"
exec "$@"
