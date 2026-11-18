# Etapa 2D — Painel com MFA/RBAC e laboratório SQL Injection

## Limites de segurança
- **Painel** `http://127.0.0.1:8090`: acesso apenas pela interface de loopback do host; requer senha e código TOTP; papéis `operador`, `tecnico`, `coordenacao`, `auditor`. Consulta dados sintéticos do volume `cloud_data` somente leitura. Não está liberado para a internet. Em produção seria obrigatório HTTPS, autenticação robusta centralizada e revisão de segurança.
- **SQLi** `http://127.0.0.1:8091`: serviço separado em `sqli_net` em rede Docker separada, sem vínculo explícito com a rede WAN/VPN, PKI ou banco de telemetria. Contém vulnerabilidade **intencional** e dados inventados. Nunca exponha porta 8091 na rede externa nem execute contra alvos reais.
- Não foram integradas ações físicas; não há comandos para bomba/fechadura.

## SQL Injection antes/depois
- Endpoint vulnerável concatena `q` na string SQL e permite contornar o filtro por `name`, por exemplo `' OR 1=1 -- `.
- Endpoint corrigido usa placeholder `?` e valida comprimento/caracteres de controle; mesma entrada maliciosa retorna `count=0`.
- Consultas executadas com `SELECT`; o container do laboratório não tem acesso ao banco da nuvem e executa como usuário sem privilégios. Na avaliação final, confirmar privilégios mínimos também para o banco PostgreSQL caso seja introduzido.
- Mensagens de erro retornam somente `invalid_query`, sem stack trace SQL.

## Evidências a coletar (RT-08 e RT-09)
1. Print do `/vulnerable?q=...` devolvendo três registros e do `/safe?q=...` devolvendo zero.
2. Teste unitário `test_sqli_before_after` passando.
3. Login com senha correta e TOTP; sem código correto não deve entrar.
4. `operador` tentando `/audit` (HTTP 403). `auditor` conseguindo (HTTP 200).
5. `docker compose ... ps`, demonstrando portas `127.0.0.1:8090` e `127.0.0.1:8091`.

## Limitações
- Não há autenticação federada; TOTP é demonstrativo e segredos locais devem ser protegidos.
- A proteção básica de tentativas de login é em memória e local a um processo, suficiente para laboratório, não para produção.
- O servidor de laboratório SQLi intencionalmente inseguro NÃO deve ser publicado, compartilhado ou rodado em redes de terceiros.
- Não há WAF nesta etapa. O WAF é diferencial da rubrica de RT-08 e pode ser acrescentado posteriormente.
- O painel lê SQLite da telemetria central; não substitui o requisito de banco com usuário de privilégios mínimos em produção.
