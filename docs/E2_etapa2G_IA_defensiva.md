# Etapa 2G — IA defensiva sem LLM

## Objetivo

Demonstracao offline de deteccao de anomalias com Isolation Forest. Os dados sao inteiramente sinteticos; **nao demonstram a precisao em rede real**. Nao ha acesso a APIs externas ou treinamento em dados pessoais.

## Desenho do experimento

- Conjunto de treino: 600 janelas benignas sinteticas.
- Teste independente: 160 janelas benignas e 80 ataques sinteticos; distribuicoes reprodutiveis por seed 712.
- Entradas: contagens em cinco minutos de falhas de login, falhas TLS, rejeicoes entre sites, tentativas SQLi e taxa de eventos por minuto.
- Modelo: IsolationForest com 150 arvores, semente fixa. Calibracao de limiar baseada apenas nos scores do treinamento benigno (percentil 8).
- Metricas: TN, FP, FN, TP, acuracia, precisao, recall, F1. Interpretar a classe 1 como anomalia.
- Decisao: apenas recomendacao; `human_review.json` inicia como nao aprovado e nao executado.

## Execucao

```bash
.venv/bin/pip install -r requirements-ai.txt
.venv/bin/python scripts/etapa2g_ia.py
.venv/bin/python scripts/verify_2g_evidence.py
.venv/bin/python -m unittest discover -s tests -v
```

## Limites e ameacas

Nao utilizar em producao sem telemetria autorizada, anonimizacao, rotulagem representativa, avaliacao por janela temporal, testes de drift, validacao de vieses e processo humano documentado. O modelo nao realiza bloqueio de IP, alteracao de ACL ou revogacao. Nao utiliza prompt, LLM ou embeddings, evitando riscos de prompt injection e vazamento por servicos de inferencia externa. Registros e credenciais do projeto ficam fora do pipeline de treinamento.
