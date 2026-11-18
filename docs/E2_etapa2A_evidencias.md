# E2 — Etapa 2A: plano de evidências (registro histórico de testes)

**Status:** plano histórico da Etapa 2A. A execução integrada posterior foi validada no protótipo; os campos "Pendente" abaixo descrevem a etapa inicial e não o estado final da entrega. Consulte E3 para os resultados consolidados.

| Evidência | Comando / ação | Resultado esperado | Resultado real |
|---|---|---|---|
| Containerização | `sudo docker compose ps` | 16 serviços ativos | Pendente |
| MQTT local | `sudo docker compose logs edge-ubs sensor-ubs` | Publicação e recepção da mesma telemetria | Pendente |
| Operação local | `sudo docker compose stop cloud` + `logs edge-ubs` | Alertas continuam durante falha central | Pendente |
| Buffer offline | `docker compose exec edge-ubs python -c ...` (README) | Quantidade pendente aumenta | Pendente |
| Reconciliação | `sudo docker compose start cloud` | Pendências diminuem e `stats` sobe | Pendente |
| Unicidade | teste `test_repeated_cloud_ack_does_not_duplicate` | 1 registro para mesmo `event_id` | Pendente de execução local |
| Segurança | `compose.yaml`, `mqtt/mosquitto.conf` | Sem portas MQTT no host; autenticação ainda pendente | Revisão estática |
| Teste formal RT-23 | link indisponível por 1800 s | Medições e logs com timestamps | Pendente |

**Ressalva:** esta versão não atende ainda mTLS/VPN/segmentação exigidos na rubrica. A simulação de falha central não substitui teste físico de WAN.
