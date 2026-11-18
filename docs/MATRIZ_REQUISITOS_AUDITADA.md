# Conferência do enunciado FIAP GS 2026.2 — versão real recebida em 18/11/2026

**Origem:** inspeção do arquivo `vila-aurora-para-auditoria.tar.gz` e comparação com o enunciado de 11 páginas; também considerados resultados apresentados pelo operador em conversa. O arquivo enviado **não contém** os logs brutos dos testes, chaves ou o estado `.git` do computador. A ausência desses arquivos no pacote não significa que não existam na máquina.

## Matriz requisito a requisito

| ID | Avaliação | Evidência ou pendência |
|---|---|---|
| RT-01 | Demonstrado no protótipo | cinco sensores, brokers, edges e central em Compose |
| RT-02 | Demonstrado | lógica local, SQLite e store-and-forward; teste WAN |
| RT-03 | Demonstrado como modo degradado | edge autônomo; não há redundância física efetiva |
| RT-04 | Demonstrado em MQTT | certificados individuais X.509, mTLS e ACL; sem HTTPS mTLS na API |
| RT-05 | Demonstrado | scripts CRL/revogação/reemissão; validação relatada |
| RT-06 | Parcial | VPN entre máquinas, mas sem MFA de operador **na VPN administrativa** |
| RT-07 | Parcial | field networks, ACL MQTT, firewall; faltam testes matriz IoT/operador/admin e vínculo de peer a site na API |
| RT-08 | Parcial | demonstração SQLi vulnerável/corrigido; SQLite não implementa usuários GRANT/minimum privilege no DB |
| RT-09 | Demonstrado | TOTP, quatro papéis e HTTP 403 verificado |
| RT-10 | Parcial | domínio `.invalid`, DMARC/SPF exemplo, DKIM placeholder inválido |
| RT-11 | Demonstrado apenas como simulação offline | 12 contas fictícias e métricas predefinidas; não ocorreu campanha real |
| RT-12 | **Parcial — Etapa 2H** | coleta pontual de 971 eventos em 15 fontes, NTP sincronizado verificado, SQLite local e expiração por retenção de 30 dias a cada coleta; falta coleta contínua agendada e integração SIEM/Wazuh |
| RT-13 | **Parcial — simulação coberta** | quatro regras adicionais (VPN anômala, SQLi, certificado, atuador fora de perfil/horário) produziram 4 alertas em eventos estruturados sintéticos; faltam ingestão operacional/ataque de validação real |
| RT-14 | Parcial | SHA-256, custódia e timeline sintética; não há reprodução integral do INC-VA-0712 nem hashes reais incorporados no PDF |
| RT-15 | **Parcial — casos automáticos** | geração automatizada de 4 casos e fila de aprovação humana, zero ações disruptivas; não há isolamento/revogação/alteração de dispositivo automatizados demonstrados |
| RT-16 | Demonstrado com dataset sintético | Isolation Forest, matriz TN=145 FP=15 FN=18 TP=62; não extrapolar para produção |
| RT-17 | Não se aplica condicionalmente | nenhuma solução LLM foi integrada ao protótipo |
| RT-18 | Parcial/documental | riscos de phishing por IA/voz clonada e verificação fora de banda discutidos; falta simulação operacional completa |
| RT-19 | Parcial | só dados fictícios; faltam RIPD simplificado completo, política operacional de retenção e pseudonimização mensurável |
| RT-20 | Parcial | orçamento anual ilustrativo e plano de manutenção; ainda não cotado/validado |
| RT-21 | Parcial | português, labels e foco visual; falta evidência de auditoria de contraste/teclado WCAG 2.1 AA |
| RT-22 | **Parcial — amostragem concluída** | 5 probes saudáveis (100% da amostra), CPU 0,00–0,42% (média 0,154%), RAM 20,19–20,99 MiB (média 20,64 MiB), rede +10 kB RX/TX em 13,62 s e WAN de 1.800 s; MTTD/MTTR sem timestamps e energia não medida; amostra não prova SLA |
| RT-23 | Demonstrado em laboratório | corte lógico UBS–Cloud 1800s, fila 0→410→0, alertas locais e sincronização |

## E1 a E4

- **E1**: três PDFs presentes no arquivo atual; E1 original tem duas páginas e não possui diagrama gráfico. A versão corrigida do pacote acrescenta um desenho fiel e declaração de IA.
- **E2**: README e Compose presentes. `setup_panel_auth.py` da versão enviada não permitia recuperar senha inicial; corrigido neste pacote. UID de painel fixo `1000:1000` permanece limitado a hosts com arquivos 0600 do mesmo dono.
- **E3**: PDF atual resume testes, mas não contém capturas de evidências brutas/anexos, teste de isolamento completo ou coleta SIEM. Não afirmar o contrário.
- **E4**: PDF atual tem metodologia e limitações, mas não os SHA-256 e timestamps concretos da máquina do operador. Para laudo verificável, incorporar os anexos reais anonimizados.

## Outros requisitos formais

- A página 9 exige a seção **Uso de IA**; a declaração foi acrescentada à documentação e à nova página do E1.
- Os nomes PDF ainda exigem turma, grupo e ID: `GS2026.2_<Turma>_<Grupo>_<E1|E3|E4>.pdf`.
- O repositório deve estar público ou acessível ao professor; não publicar credenciais.
- O enunciado menciona **vídeo** na rubrica e link na seção de entrega; verificar o tempo exigido na plataforma.
- Há diferenças internas no edital: primeira página individual/duplas/trios vs página 9 até cinco integrantes; verificar orientação oficial.

## Falhas reais adicionais do pacote

1. `src/cloud.py`: o POST da API só valida dados do payload, não vincula `site` ao IP/peer WireGuard; um peer autorizado pode tentar enviar telemetria de outro site.
2. `src/cloud.py`: comentário da primeira linha ainda descreve API "sem autenticacao; proxima etapa: VPN", apesar da VPN existir.
3. `src/mqtt_edge.py` e `src/edge.py`: docstrings de etapas antigas podem sugerir ausência de MQTT/VPN na versão final.
4. `docs/E2_etapa2A_evidencias.md`: diversas células ainda aparecem como "Pendente" por ser plano histórico, apesar dos testes já terem sido executados; risco de confusão.
5. `.gitignore` da versão enviada tinha várias duplicações; corrigido neste pacote.
6. `scripts/setup_panel_auth.py` gerava senhas sem mostrar nem armazenar plaintext em lugar recuperável; corrigido para `auth/runtime/credenciais_iniciais.txt` protegido 0600 **apenas em novos ambientes**, sem alterar configurações existentes.
7. Não é possível auditar o histórico Git real, pois `.git` foi intencionalmente excluído do TAR; conferir localmente antes de publicar.

## Ordem de ação antes do primeiro commit definitivo

1. Aplicar as correções deste pacote; verificar diagrama/README e executar a suíte completa no computador do projeto.
2. Validar RT-12/13/15/22 ou explicitá-los como limitações nos PDFs. Para melhor nota, priorizar implementação e evidências reais dos quatro itens.
3. Enriquecer E3 e E4 com capturas/manifestos com hashes reais gerados localmente, e dados de isolamento.
4. Preencher os identificadores da equipe/turma, ajustar nomenclatura e preparar eventual vídeo.
5. Executar scanner de segredos e auditoria `git status`, `git log`, `git remote -v`; somente então limpar histórico local e criar commit final.

**Não publicar o repositório como se 100% dos 23 RTs estivessem concluídos.**

## Atualização confirmada da Etapa 2H — resultado do operador em 18/11/2026

- 41 testes Python em 1,789 s: `OK` (avisos de conexões SQLite abertas permanecem).
- Detecção sintética: 4 alertas, regras `VA-RT13-ACT`, `VA-RT13-CERT`, `VA-RT13-SQLI`, `VA-RT13-VPN`; 4 casos, 0 ações disruptivas e SHA-256 verificado.
- Coleta pontual: 971 eventos, 15 fontes, NTP sincronizado, verificações Docker/SO/WireGuard/SQLite positivas, 30 dias de retenção em política de expiração por coleta, manifesto SHA-256 verificado.
- Disponibilidade observada: cinco probes, 100% dessa janela, teste WAN 1.800 s vinculado; energia não medida; MTTD/MTTR ausentes sem carimbos confiáveis. Arquivos `evidence/runtime/etapa2h_*` são locais e não foram compartilhados integralmente.
- **Os resultados não implicam Wazuh implantado, cron configurado, automação de bloqueio, disponibilidade anual de 100% ou conformidade integral dos 23 requisitos.**
