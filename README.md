# Rede Comunitária Vila Aurora

**Global Solution 2026.2 — Resilient Community Infrastructure**
**Curso:** Engenharia da Computação
**Natureza:** protótipo acadêmico com dispositivos, identidades e dados sintéticos

## Visão geral

A Rede Comunitária Vila Aurora demonstra uma infraestrutura distribuída para cinco unidades fictícias: **centro comunitário, escola, UBS, horta e abrigo**. Cada unidade possui um sensor simulado, broker MQTT e serviço de borda. O processamento local continua durante indisponibilidade do servidor central; a borda guarda registros em SQLite e os reconcilia quando a comunicação é restaurada.

O projeto está organizado por módulos de comunicação, segurança, supervisão, experimentos e preservação de evidências. Não foi homologado para operação em infraestrutura real.

## Arquitetura e controles

| Componente | Implementação e finalidade |
|---|---|
| Telemetria distribuída | MQTT com broker e sensor simulados por unidade, isolamento lógico das redes de campo |
| Autonomia local | Regras de alerta no edge e fila persistente SQLite durante interrupções de comunicação |
| Identidade de dispositivos | Certificados X.509 individuais, MQTT com mTLS, ACL, revogação por CRL e reemissão |
| Comunicação borda–central | WireGuard entre cinco peers edge e servidor central; acesso direto à API limitado por firewall |
| Supervisão | Flask com autenticação por senha + TOTP e autorização baseada em papéis (RBAC) |
| Segurança de aplicação | Laboratório SQL Injection com consulta vulnerável e versão corrigida parametrizada, somente com dados sintéticos |
| Conscientização e detecção | Campanha fictícia de phishing offline, exemplos SPF/DKIM/DMARC e cinco regras avaliadas sobre eventos sintéticos |
| Forense | Caso acadêmico INC-VA-0712, linha do tempo, cópias preservadas, manifesto SHA-256 e registro de custódia |
| IA defensiva | Isolation Forest sobre amostras sintéticas; avaliação quantitativa e recomendações sujeitas à revisão humana |
| Monitoramento acadêmico (2H) | Coletor pontual multi-fonte SQLite, quatro regras adicionais, casos com aprovação humana, amostragem de CPU/RAM/rede e probes de disponibilidade; não é Wazuh em produção |

## Resultados observados em 18/11/2026

- **41/41 testes automatizados aprovados** no ambiente de validação informado pelo operador.
- **Falha lógica UBS–Cloud por 1.800 segundos**: 410 eventos pendentes, seguidos de reconciliação (`cloud_reconciled count=410`) e fila local zerada.
- **103.794 eventos** no banco central na verificação informada: 20.762 em cada unidade exceto UBS (20.746).
- **Nenhum `event_id` duplicado** identificado na consulta ao banco central; `PRAGMA integrity_check` retornou `ok`.
- **Etapa 2H — 41/41 testes aprovados**; quatro alertas RT-13, quatro casos abertos, nenhuma ação disruptiva automática.
- **Coleta de logs em laboratório**: 971 eventos de 15 fontes, retenção configurada em 30 dias com expiração executada a cada coleta, sincronização NTP do host reportada como verdadeira, integridade SHA-256 verificada. A coleta é pontual, não um serviço de SIEM contínuo.
- **Métricas RT-22**: cinco probes com 100% de disponibilidade observada nesse intervalo; CPU, memória e tráfego armazenados em `evidence/runtime/etapa2h_metricas/metricas.json`. MTTD/MTTR não calculados sem timestamps de detecção; energia não medida.
- **MFA e RBAC**: login demonstrado e acesso de `operador` a `/audit` negado (403).
- **mTLS**: conexão válida, rejeição sem certificado, revogação e recuperação mediante reemissão demonstradas.
- **WireGuard**: cinco peers com handshake e bloqueio de acesso direto à API após ajuste de firewall.
- **Forense INC-VA-0712**: 32 eventos sintéticos, sete alertas e verificações de integridade aprovadas.
- **IA**: acurácia 86,25%, precisão 80,52%, recall 77,50%, F1 78,98% em conjunto sintético; nenhuma ação automática.

Essas medições se referem ao protótipo. `event_id` sem duplicações e integridade SQLite não provam ausência absoluta de perda de telemetria. O teste WAN simulou interrupção lógica do tráfego VPN, não ruptura física de internet.

## Situação dos requisitos (verificação de 18/11/2026)

O laboratório demonstra o núcleo funcional e a execução relatada de 41 testes, mas **não cumpre integralmente todos os RTs**. Consulte [`docs/MATRIZ_REQUISITOS_AUDITADA.md`](docs/MATRIZ_REQUISITOS_AUDITADA.md): RT-12 (coleta contínua/Wazuh) e RT-15 (resposta operacional) permanecem parciais; RT-13 foi demonstrado com eventos sintéticos estruturados e RT-22 recebeu medições pontuais, mas ambos seguem parciais, além de limitações de DNS, VPN administrativa, isolamento, privacidade e acessibilidade. **Não considerar propostas como recursos implantados.**

A pasta `docs/relatorios/` inclui E1, E3, E4; os hashes forenses individuais e extratos dos logs locais precisam ser anexados a partir da máquina de teste. O enunciado exige declaração de uso de IA e nomes no padrão `GS2026.2_<Turma>_<Grupo>_<ID>.pdf`; confirmar dados e exigência do vídeo na plataforma da disciplina.

## Estrutura do repositório

- `src/`: sensores, edge, nuvem, supervisão, detecção, forense e IA.
- `mqtt/` e `vpn/`: configurações de mensagens e túnel de rede.
- `compose.wireguard.full.yaml` e `compose.panel.yaml`: serviços do laboratório.
- `scripts/`: provisionamento, testes de segurança e geração/verificação das evidências.
- `tests/`: testes automatizados.
- `docs/`: documentação por módulo e relatórios finais E1, E3, E4.
- `dns/example.invalid.zone.txt`: exemplo didático de configuração de domínio.

## Requisitos de execução

Docker Engine com Docker Compose, Python 3 e OpenSSL. A demonstração VPN requer suporte a WireGuard, privilégios de rede (`NET_ADMIN`) e `iptables` nos containers. As dependências Python estão declaradas em `requirements.txt` e `requirements-ai.txt`. A instalação depende da configuração do host e do ambiente de virtualização; não há distribuição específica obrigatória.

### Preparação do laboratório

Os scripts geram identidades e segredos **localmente** e exigem leitura dos comentários antes da execução. Em ambiente novo, a sequência conceitual é:

1. Criar um ambiente virtual Python e instalar `requirements.txt` e `requirements-ai.txt`.
2. Executar `scripts/setup_pki.sh` para estabelecer CA, certificados e ACLs (requer OpenSSL e privilégios adequados).
3. Executar `scripts/setup_wireguard.py` para gerar as configurações privadas da VPN.
4. Executar `scripts/setup_panel_auth.py` para preparar usuários, senhas e TOTP.
5. Subir os serviços usando os arquivos Compose correspondentes e validar o estado com `docker compose ps`.

**Credenciais no primeiro provisionamento:** `scripts/setup_panel_auth.py` grava as credenciais fictícias iniciais em `auth/runtime/credenciais_iniciais.txt` (permissões 0600), sem exibi-las no terminal. Consulte esse arquivo **apenas localmente**, importe as credenciais em um gerenciador seguro, valide login e remova o TXT em seguida. O script não sobrescreve uma configuração existente. Para rotação em ambiente já provisionado, consulte o código de `scripts/rotate_panel_auth.py`; jamais publique ou cole o conteúdo de `auth/runtime` em mensagens.

**Permissões do painel:** `compose.panel.yaml` usa temporariamente o UID 1000 para ler `auth/runtime/*.json` e a chave de sessão (0600). Em outro host, ajuste o UID do container para corresponder ao proprietário dos arquivos, antes de inicializar. Esta é uma limitação do protótipo, não uma configuração portável de produção.

**Atenção:** não execute os scripts de provisionamento novamente em um laboratório com dados persistidos sem avaliar o impacto sobre credenciais, certificados e sessões. Os testes de revogação de certificados alteram identidades e requerem reemissão para restaurar a comunicação.

### Testes automatizados

```sh
python -m unittest discover -s tests -v
```

Os scripts de demonstração geram resultados **sintéticos** e evidências locais:

```sh
python scripts/etapa2e_demo.py
python scripts/verify_2e_evidence.py
python scripts/etapa2f_forense.py
python scripts/verify_2f_forensics.py
python scripts/etapa2g_ia.py
python scripts/verify_2g_evidence.py
```

O teste WAN de 30 minutos (`scripts/teste_wan_30min.sh`) **altera temporariamente regras de firewall** em container de borda. Execute-o somente em um laboratório autorizado e após verificar os nomes dos serviços e o comportamento de restauração.

## Testes complementares e observabilidade (Etapa 2H)

```sh
python scripts/etapa2h_operacoes.py
python scripts/coletar_logs_2h.py --sudo --minutes 3
python scripts/medir_metricas_2h.py --sudo --samples 5 --interval 2 \
  --wan-evidence evidence/runtime/wan30-20261118-150145
```

Executar `sudo -v` antes dos comandos com `--sudo`. Os relatórios numéricos e logs brutos ficam na pasta `evidence/runtime/`, excluída do Git. Os dados abaixo foram obtidos da amostragem local do operador. Os 100% de disponibilidade são referentes a cinco amostras em 13,62 segundos, não uma garantia anual. O edge-ubs apresentou CPU de 0,00% a 0,42% (média 0,154%), uso de memória de 20,19 a 20,99 MiB (média 20,64 MiB) e deltas de rede de aproximadamente 10.000 bytes recebidos e 10.000 bytes transmitidos segundo docker stats.

## Entregáveis

- **E1 — Arquitetura:** `docs/relatorios/E1_Arquitetura_Vila_Aurora.pdf`.
- **E2 — Repositório:** este código, testes e documentação operacional.
- **E3 — Testes de segurança:** `docs/relatorios/E3_Testes_Seguranca_Vila_Aurora.pdf`.
- **E4 — Investigação forense:** `docs/relatorios/E4_Laudo_Forense_INC-VA-0712.pdf`.

## Segurança, privacidade e limites

A campanha de phishing não envia mensagens reais nem coleta credenciais. A IA não executa bloqueios autonomamente. Os exemplos SPF/DKIM/DMARC não implicam implantação de DNS real. O monitoramento inclui coleta pontual multi-fonte e detecção estruturada, não Wazuh ou um SIEM de operação contínua. Quatro casos são abertos automaticamente sem bloquear serviços ou dispositivos. A implementação não substitui uma avaliação de segurança, operação e acessibilidade em produção.

**Nunca versionar** chaves privadas, TOTP, senhas, arquivos `auth/runtime`, `pki/runtime`, `vpn/runtime`, `evidence/runtime` ou bancos locais. Verifique o `.gitignore` e o conteúdo preparado para commit antes de publicar. Dados sensíveis anteriormente expostos devem ser rotacionados antes da entrega.
