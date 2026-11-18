#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
DC=(sudo docker compose -f compose.wireguard.full.yaml -f compose.panel.yaml)
DURATION=1800
OUT="evidence/runtime/wan30-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"

restore() {
  "${DC[@]}" exec -T edge-ubs \
    iptables -D OUTPUT -o wg0 -d 10.77.0.1 -j REJECT \
    2>/dev/null || true
}
trap restore EXIT INT TERM

pending() {
  "${DC[@]}" exec -T edge-ubs python -c \
    "import sqlite3; c=sqlite3.connect('/data/events.sqlite3'); print(c.execute('SELECT COUNT(*) FROM outbox WHERE synced=0').fetchone()[0]); c.close()"
}

echo "=== ANTES ===" | tee "$OUT/resultado.txt"
pending | tee -a "$OUT/resultado.txt"

echo "=== INTERROMPENDO LINK UBS-CLOUD ==="
"${DC[@]}" exec -T edge-ubs \
  iptables -I OUTPUT 1 -o wg0 -d 10.77.0.1 -j REJECT

date -u +'%Y-%m-%dT%H:%M:%SZ' | tee "$OUT/inicio_utc.txt"
sleep "$DURATION"

echo "=== APOS 30 MINUTOS OFFLINE ===" | tee -a "$OUT/resultado.txt"
date -u +'%Y-%m-%dT%H:%M:%SZ' | tee "$OUT/fim_utc.txt"
pending | tee -a "$OUT/resultado.txt"

"${DC[@]}" logs --since=32m edge-ubs sensor-ubs \
  > "$OUT/logs_offline.txt" 2>&1

echo "=== RESTAURANDO LINK ==="
restore
trap - EXIT INT TERM

sleep 30

echo "=== APOS RECONCILIACAO ===" | tee -a "$OUT/resultado.txt"
pending | tee -a "$OUT/resultado.txt"

"${DC[@]}" logs --since=3m edge-ubs \
  > "$OUT/logs_reconciliacao.txt" 2>&1

echo "Evidencias: $OUT"
