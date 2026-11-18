# Etapa 2E — Phishing etico e regras de deteccao

## Escopo e integridade

Tudo offline, sem email/SMS real, contas 100% ficticias, sem coleta de senhas, sem vinculo com pessoas. Os numeros gerados pela simulacao nao representam taxas de comportamento de participantes. Scripts usam apenas bibliotecas da linguagem Python. Artefatos em `evidence/runtime/etapa2e/` (ignorado no Git) e manifest SHA-256, que garante deteccao de alteracao acidental, nao autenticidade criptografica assinada ou cadeia de custodia completa.

## Como executar

```bash
PYTHONPATH=. .venv/bin/python scripts/etapa2e_demo.py
PYTHONPATH=. .venv/bin/python scripts/verify_2e_evidence.py
.venv/bin/python -m unittest discover -s tests -v
```

## Cenario simulado

12 personagens ficticios recebem evento de entrega; 7 eventos de abertura; 3 cliques; 4 relatos ao time de seguranca. Numeros fixos/deterministicos para repetir experimento; nao sao metricas empiricas.

### Medidas educativas

Mensagem modelo (NAO enviada): 'Atualizacao de cadastro da Vila Aurora — exercicio. Nunca informe sua senha, senha temporaria ou codigo MFA em links. Em caso de suspeita reporte ao canal interno ficticio.' Discussoes: pressao de urgencia, dominio parecido, anexos, links encurtados e audio clonado por IA. Para suposta ligacao de coordenador, confirmar em canal independente, nunca fornecer OTP, exigir callback previamente cadastrado. Nao foi sintetizada voz real nem coletada biometria.

## SPF/DKIM/DMARC

Arquivo `dns/example.invalid.zone.txt` contem exemplos de SPF `-all`, DMARC `p=reject` e DKIM com placeholder — **nao e uma implementacao em dominio real**, nao comprova DKIM funcional ou entregabilidade. Para producao: dominio controlado, chave publica DKIM valida, logs do provedor, testes de alinhamento SPF/DKIM, relay de envio autorizado.

## Monitoramento e correlacao (cinco regras)

- VA-DET-01: 3 falhas de login por identidade em 5 min.
- VA-DET-02: falha de verificacao de certificado TLS (possivel revogacao, nao prova especifica por si so).
- VA-DET-03: tentativa de SQLi no lab.
- VA-DET-04: MQTT rejeitado por site divergente.
- VA-DET-05: clique simulado no exercicio.

Os cinco detectores analisam eventos JSONL gerados pelo laboratorio, nao trafego automaticamente coletado de toda a infraestrutura. Esses alertas sao uma demonstracao do mecanismo de deteccao, nao evidencias de ataque real ou de um SIEM em producao. A resposta e apenas **recomendacao**. Nenhum bloqueio automatico ou alteracao de rede; eventos de alto risco exigem aprovacao humana.

## Evidencias e limites

- `phishing_events.jsonl` / `phishing_metrics.json` / `phishing_metrics.csv`: campanha simulada, taxas e identidades imaginarias.
- `security_events.jsonl`: eventos de ataque/defesa simulados.
- `alerts.jsonl` / `detection_summary.json`: correlacao, severidade, resposta proposta.
- `sha256_manifest.json`: hash de cada evidencia gerada. Validar com `scripts/verify_2e_evidence.py`.

**Pendente:** coletor real de logs centralizados, sincronizacao NTP verificavel, SIEM persistente, testes reais de falso positivo e tempo de deteccao, SPF/DKIM/DMARC de dominio sob controle, protocolo de incidente forense INC-VA-0712.
