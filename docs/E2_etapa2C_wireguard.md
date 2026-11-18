# Etapa 2C — VPN WireGuard e segmentação (laboratório)

## Objetivo
RT-06: comunicação borda–nuvem sobre WireGuard; RT-07: redes de campo separadas e acesso restrito ao servidor. A Etapa 2C não abrangia MFA; esse controle foi adicionado posteriormente na Etapa 2D.

## Topologia
Cada sensor e broker participa apenas de `field_<local>` (`internal: true`). Cada borda participa de sua rede de campo e da rede de transporte `wan`. A nuvem participa da `wan`. Um túnel WireGuard `wg0` (hub `10.77.0.1`, peers `.2` a `.6`) é iniciado em cada nó e na nuvem. O aplicativo de borda aponta EXCLUSIVAMENTE a `10.77.0.1:8080`. O servidor bloqueia TCP 8080 via interfaces diferentes de `wg0` com iptables. A API de observabilidade fica publicada em `127.0.0.1:8080` do HOST, redirecionada à porta 8081 do container. Não confundir essa porta de métricas com o canal de ingestão protegido.

## Segurança e limites
Cada peer tem chave privada distinta. A rede de transporte `wan` continua compartilhada como underlay Docker: segmentação lógica é demonstrada nos segmentos de campo; isto **não** é isolamento completo entre nós de borda. ACL de MQTT e mTLS permanecem obrigatórios. Não há MFA ou camada ZTNA nesta etapa. Containers com NET_ADMIN elevam privilégios, apenas aceitáveis em laboratório controlado. A API de métricas na porta 8081 é apenas leitura, mas não tem autenticação e também fica acessível pela rede Docker `wan`; portanto essa rede é considerada confiável **somente no laboratório**. Para produção, proteger métricas por autenticação e firewall dedicado. Não publicar chaves geradas. Recomenda-se reemitir chaves se alguma for copiada em evidências.

## Comandos para evidências
```bash
sudo docker compose -f compose.wireguard.full.yaml ps
sudo docker compose -f compose.wireguard.full.yaml exec cloud wg show
sudo docker compose -f compose.wireguard.full.yaml exec edge-ubs wg show
sudo docker compose -f compose.wireguard.full.yaml exec edge-ubs curl -s http://10.77.0.1:8080/stats
```
A imagem não instala curl; o último comando é opcional e pode ser substituído por Python urllib. A verificação `wg show` deve apresentar `latest handshake` e `transfer` após a aplicação enviar eventos. A prova de não bypass direto precisa ser feita com conexão à `cloud:8080` a partir do edge e observar `Connection refused`/erro (por iptables). A prova de isolamento entre segmentos deve demonstrar que sensor UBS não resolve nem acessa broker de escola (redes distintas). Guarde saídas e carimbo de hora.

## Comandos de auditoria
```bash
sudo docker compose -f compose.wireguard.full.yaml exec edge-ubs python -c 'import urllib.request; print(urllib.request.urlopen("http://10.77.0.1:8080/stats",timeout=4).read().decode())'
sudo docker compose -f compose.wireguard.full.yaml exec edge-ubs python -c 'import urllib.request; urllib.request.urlopen("http://cloud:8080/stats",timeout=4)'
sudo docker compose -f compose.wireguard.full.yaml exec sensor-ubs python -c 'import socket; socket.getaddrinfo("mqtt-escola",8883)'
```
A segunda e terceira operações **devem falhar**. Não é necessário derrubar o túnel para provar isolamento. Para teste de operação degradada, pare a `cloud`, não pare os nós locais.
