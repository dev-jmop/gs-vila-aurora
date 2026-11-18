# Etapa 2H — RT-12, RT-13, RT-15 e RT-22 (incremento acadêmico)

## Escopo e limitações honestas

- **RT-13**: as quatro categorias obrigatórias estão implementadas como regras para **eventos estruturados**: autenticação VPN fora de CIDR permitido, SQL injection, certificado inválido e comando de atuador fora de perfil/horário. A demonstração usa endereços de documentação (RFC 5737), não tentativas reais de ataque. A detecção VPN exige baseline configurada.
- **RT-15**: os alertas geram **automaticamente casos locais e fila de revisão**; operações como revogar certificados, alterar firewall, derrubar VPN e mudar atuador continuam propostas **não executadas** e exigem pessoa responsável. Isso é um playbook parcial e não uma automação de isolamento real.
- **RT-12**: o coletor lê logs Docker de sensores, brokers, edge, web e nuvem, além de tentar ler journal do host, status NTP, handshakes WireGuard e integridade SQLite. Normaliza as fontes em um banco **local de logs** com deduplicação, saneamento básico e exclusão por retenção de 30 dias a cada coleta. **Não implementa Wazuh** nem sincroniza relógios; agendamento para coleta contínua e integração com SIEM externo permanecem pendentes. A coleta parcial e suas falhas são explicitadas no JSON de saída.
- **RT-22**: o coletor de métricas registra CPU, memória, contadores de banda e verificações de disponibilidade **da janela de amostragem**, e pode ler o intervalo UTC do teste WAN. MTTD/MTTR exigem timestamps reais fornecidos; sem eles ficam `null`. Energia não é medida pelo Docker; só se calcula uma **estimativa** se o operador informar potência média em W, rotulada como estimativa.

## Execução (na pasta raiz do projeto)

```sh
# 1. Cenário sintético: quatro regras + fila de resposta humana
.venv/bin/python scripts/etapa2h_operacoes.py

# 2. Verificar testes automatizados (31 anteriores + 10 novos)
.venv/bin/python -m unittest discover -s tests -q

# 3. Coleta local de logs: apenas leitura; privilegios Docker se necessarios
sudo -v
.venv/bin/python scripts/coletar_logs_2h.py --sudo --minutes 3

# 4. Métricas de borda UBS, cinco amostras (rede VPN ativa)
.venv/bin/python scripts/medir_metricas_2h.py --sudo --samples 5 --interval 2 \
  --wan-evidence evidence/runtime/wan30-20261118-150145
```

Se o runtime não permitir journal do SO ou algum `exec` Docker, os campos `source_checks` indicarão falha. O sucesso da coleta Compose **não valida** todas as fontes automaticamente. O arquivo `evidence/runtime/etapa2h_coleta/siem_local.sqlite3` contém logs de laboratório, permanece fora do Git e pode conter identificadores; não divulgue sem revisão.

As evidências novas ficam em `evidence/runtime/etapa2h*`, ignoradas no Git. Para operações frequentes, agendar a coleta via systemd/cron e demonstrar o envio a um SIEM real; caso contrário, declarar RT-12 parcial. A retenção executa-se apenas quando o coletor roda.

## Regras de detecção e política

| ID | Disparo | Resultado |
|---|---|---|
| VA-RT13-VPN | login VPN fora de CIDR previamente aprovado | alerta e proposta de encerramento de sessão, pendente aprovação |
| VA-RT13-SQLI | evento SQLi estruturado | alerta e proposta de bloqueio de IP, pendente aprovação |
| VA-RT13-CERT | erro de verificação TLS/certificado revogado | alerta e proposta de revogação, pendente aprovação |
| VA-RT13-ACT | comando fora do catálogo, perfil ou janela 06:00–20:00 São Paulo | alerta e proposta de modo seguro, pendente aprovação |

**Não é correto afirmar que o protótipo isolou dispositivos, revogou certificados ou mudou estados físicos por SOAR nessa etapa.** Apenas filas e casos foram criados. O intuito da política é evitar que uma ação ofensiva simulada provoque efeito real.
