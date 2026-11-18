# Etapa 2B: seguranca MQTT com mTLS e CRL

**Requisitos:** RT-04 (identidade unica X.509 por dispositivo) e RT-05 (revogacao e rotacao).

Cada sensor e edge possui par exclusivo de chave/certificado (10 clientes); cada broker tem certificado de servidor com SAN DNS apropriado (5 servidores). A CA do projeto assina todos. Conexoes MQTT TLS 1.2+ na porta 8883. ACL so permite publicar para `sensor-{site}` e ler para `edge-{site}` no topico correspondente.

**Revogacao**: `sudo bash scripts/revoke_cert.sh sensor-ubs`, `sudo docker compose restart mqtt-ubs`. A CRL e checada pelo broker em novas conexoes TLS; reinicie `sensor-ubs` para forcar nova conexao e observar rejeicao. Para restaurar o laboratorio, `sudo bash scripts/rotate_cert.sh sensor-ubs` falhara porque o certificado ja estava revogado; rotacao deve ser feita em identidade ainda valida, ou use `sudo bash scripts/reissue_revoked.sh sensor-ubs` para substituir certificado revogado com novo serial.

**Limites na Etapa 2B (histórico):** WireGuard e MFA ainda não haviam sido integrados; a versão final agrega esses controles em etapas posteriores. O armazenamento de chaves privadas no host exige acesso sudo. A CA nao deve ir ao Git. Este laboratorio nao substitui um HSM ou CA de producao.
