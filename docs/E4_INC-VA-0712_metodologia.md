# E4 — INC-VA-0712: metodologia de preservacao e analise

Este incremento cria uma **simulacao forense** de incidente a partir de eventos **sinteticos** gerados na etapa 2E. Nao e admissivel apresenta-la como evidencia de ataque real.

1. Executar `scripts/etapa2e_demo.py` para produzir fontes de dados locais.
2. Verificar o manifesto SHA-256 original antes da coleta.
3. Copiar as quatro fontes para um caso novo sem sobrescrever.
4. Registrar o responsavel, UTC, tamanho e hashes em `03_cadeia_custodia.json`.
5. Reconstruir cronologia UTC em CSV e alertas por regra em JSON.
6. Registrar decisao de resposta sem bloqueios automaticos de alto impacto.
7. Verificar cadeia + manifesto usando `scripts/verify_2f_forensics.py`.

**Limites:** nao inclui imagem forense de disco, memoria, SIEM de producao, autenticidade comprovada por assinatura digital ou autoria de atacante. Hashes mostram integridade comparativa e nao substituem cadeia de custodia legal. O arquivo E4 final pode combinar este metodo e resultados do caso.
