# Evidência complementar da Etapa 2H — 18/11/2026

**Escopo:** laboratório acadêmico da Rede Comunitária Vila Aurora. Os resultados foram apresentados pelo responsável por meio do terminal, não por arquivos brutos enviados ao repositório. Os manifestos permanecem no ambiente local.

| Comando | Resultado observado | Limitação |
|---|---|---|
| `unittest discover -s tests -q` | 41 testes, OK | avisos `ResourceWarning` de SQLite |
| `etapa2h_operacoes.py` | 4 alertas, 4 casos, 0 ações disruptivas, SHA-256 validado | eventos estruturados sintéticos |
| `coletar_logs_2h.py` | 971 eventos, 15 fontes, NTP sincronizado, seis verificações positivas, retenção de 30 dias, SHA-256 validado | coleta pontual, não Wazuh e não serviço agendado |
| `medir_metricas_2h.py` | 5 probes em 13,62 s, 100% disponíveis, CPU média 0,154%, memória média 20,64 MiB, RX +10.000 bytes e TX +10.000 bytes, 1.800 s WAN, SHA-256 OK | não é SLA; MTTD, MTTR e energia não medidos |

**Arquivos locais:** `evidence/runtime/etapa2h/`, `evidence/runtime/etapa2h_coleta/`, `evidence/runtime/etapa2h_metricas/`; as pastas ficam excluídas do Git devido a possíveis identificadores e logs. Uma apresentação ao avaliador pode demonstrar as verificações e os manifestos localmente, sem publicar segredos.

**Série informada:** CPU: `[0.01, 0.01, 0.0, 0.42, 0.33]`%; memória: `[21170749.44, 21873295.36, 21233664.0, 22009610.24, 21915238.4]` bytes. CPU média: **0,154%**; memória média: **20,64 MiB** (faixa 20,19 a 20,99 MiB). Os deltas de rede em `docker stats` foram **10.000 bytes de RX e 10.000 bytes de TX**, sujeitos a arredondamento. MTTD, MTTR e energia permaneceram `null`; não foi registrada potência medida.
