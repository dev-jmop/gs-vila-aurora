# Etapa 2F: investigacao forense simulada INC-VA-0712

```bash
cd vila-aurora-etapa2
.venv/bin/python scripts/etapa2e_demo.py
.venv/bin/python scripts/verify_2e_evidence.py
.venv/bin/python scripts/etapa2f_forense.py
.venv/bin/python scripts/verify_2f_forensics.py
.venv/bin/python -m unittest discover -s tests -v
```

Os artefatos estao em `evidence/runtime/INC-VA-0712/`: originais preservados, linha do tempo, cadeia de custodia, relatorio E4 e manifesto SHA-256. Nunca execute a geracao novamente no mesmo diretorio sem arquivar o caso anterior. Nao ha dependencia de Docker e os dados sao 100% sinteticos.
