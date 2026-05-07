# Monitoramento de Impressoras

Aplicacao Flask para monitorar impressoras e switches via SNMP, exibir os dados em uma interface web e persistir historico e configuracoes em SQLite.

## Visao geral

O sistema coleta periodicamente dados de equipamentos de rede e disponibiliza essas informacoes em tres camadas:

- dashboard principal com status e metricas das impressoras
- dashboard dedicado para switches
- tela de graficos com leitura diaria, mensal e historico
- tela de configuracoes para cadastrar impressoras e switches sem editar o codigo

Hoje o projeto monitora:

- impressoras: nome, IP, MAC, serie, modelo, asset number, localizacao, uptime, total de impressoes, impressoes do dia, impressoes do mes, copias, scanner, toner e custo estimado
- switches: nome, IP, descricao, localizacao, contato, uptime, MAC, total de interfaces e status da porta principal

## Principais recursos

- monitoramento concorrente com uma thread por equipamento
- consulta SNMP com cache para campos estaveis
- persistencia local em SQLite com WAL habilitado
- historico diario consolidado de impressoes
- rastreamento mensal de impressoes
- cache de dados das impressoras e switches para manter contexto mesmo offline
- cadastro dinamico de impressoras e switches via interface web ou API
- estimativa de custo por impressora com token configuravel
- endpoints JSON para consumo interno e integracao com Power BI

## Arquitetura

### Inicializacao

O ponto de entrada da aplicacao e `main.py`.

Na inicializacao o sistema:

1. carrega configuracoes de ambiente em `config.py`
2. cria e atualiza a estrutura do banco SQLite
3. garante que as configuracoes padrao de impressoras e switches existam no banco
4. instancia os servicos de monitoramento
5. inicia as threads de coleta
6. registra as rotas web e API no Flask

### Servicos principais

- `services/printer_monitor_service.py`
  Responsavel pelo monitoramento das impressoras, calculo das metricas do dia e do mes, cache de dados SNMP e persistencia do historico.
- `services/switch_monitor_service.py`
  Responsavel pelo monitoramento dos switches e cache de dados de rede.
- `services/historico_service.py`
  Centraliza a criacao das tabelas, migracoes leves e operacoes SQLite.
- `services/printer_config_service.py`
  Valida, normaliza e persiste configuracoes de impressoras.
- `services/switch_config_service.py`
  Valida, normaliza e persiste configuracoes de switches.
- `services/snmp_service.py`
  Faz consultas SNMP e formata o MAC address.

### Camada web

- `routes/web_routes.py`
  Rotas HTML.
- `routes/api_routes.py`
  Rotas JSON.
- `templates/`
  Paginas `index.html`, `graficos.html`, `switches.html` e `configuracoes.html`.
- `static/js/`
  Scripts responsaveis por consultar a API e renderizar dashboard, graficos e configuracoes.

## Estrutura do projeto

```text
Monitorament_de_impressoes/
|- main.py
|- config.py
|- requirements.txt
|- README.md
|- COMO_ADICIONAR_IMPRESSORAS.md
|- Dockerfile
|- docker-compose.yml
|- routes/
|  |- api_routes.py
|  \- web_routes.py
|- services/
|  |- historico_service.py
|  |- printer_monitor_service.py
|  |- printer_config_service.py
|  |- snmp_service.py
|  |- switch_config_service.py
|  \- switch_monitor_service.py
|- templates/
|  |- configuracoes.html
|  |- index.html
|  |- graficos.html
|  \- switches.html
|- static/
|  |- style.css
|  |- Epson.JPG
|  |- OKI_CALLCENTER.jpeg
|  \- js/
|     |- configuracoes_abas.js
|     |- configuracoes_impressoras.js
|     |- configuracoes_switches.js
|     |- dashboard.js
|     |- graficos.js
|     \- switch_dashboard.js
\- historico_impressoes.db
```

## Banco de dados

O SQLite e usado para persistir tanto o historico quanto o estado operacional.

Tabelas principais:

- `historico_impressoes`
  Fechamentos diarios e registros de reset de contador.
- `cache_rastreamento_diario`
  Estado diario em andamento por impressora.
- `rastreamento_mensal`
  Estado mensal em andamento por impressora.
- `cache_impressora`
  Ultimos dados estaveis coletados de cada impressora.
- `printer_config`
  Cadastro persistente das impressoras monitoradas.
- `switch_config`
  Cadastro persistente dos switches monitorados.
- `cache_switch`
  Ultimos dados coletados dos switches.

## Calculo de impressoes

### Impressoes do dia

O sistema calcula `impressoes_dia` com base no contador total da impressora.

Regras:

- na primeira leitura do dia, o contador atual vira a base inicial
- durante o dia, o total e calculado pela diferenca entre o contador atual e a base inicial
- ao cruzar o horario configurado em `HISTORICO_FECHAMENTO_DIARIO`, o dia operacional muda
- quando isso acontece, o total consolidado do dia anterior e salvo em `historico_impressoes`
- se o contador da impressora voltar para um valor menor, o sistema trata como reset, salva o acumulado parcial e continua a partir da nova base

### Impressoes do mes

O rastreamento mensal usa a mesma ideia:

- a base reinicia quando muda o mes
- se houver reset do contador no meio do mes, o acumulado anterior e mantido
- o total mensal e recalculado continuamente enquanto a impressora responde

## Variaveis de ambiente

O projeto tenta carregar automaticamente o arquivo `.env` na raiz.

Variaveis principais:

- `FLASK_DEBUG`
- `FLASK_HOST`
- `FLASK_PORT`
- `HISTORICO_DB_FILE`
- `HISTORICO_FECHAMENTO_DIARIO`
- `MONITOR_INTERVAL_SECONDS`
- `STATE_PERSIST_INTERVAL_SECONDS`
- `PRINTER_CACHE_PERSIST_INTERVAL_SECONDS`
- `SNMP_STABLE_REFRESH_INTERVAL_SECONDS`
- `SNMP_DEFAULT_COMMUNITY`
- `IMPRESSORAS_CONFIG_JSON`
- `SWITCHES_CONFIG_JSON`

Exemplo de `.env`:

```env
FLASK_DEBUG=1
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
HISTORICO_DB_FILE=historico_impressoes.db
HISTORICO_FECHAMENTO_DIARIO=08:00
MONITOR_INTERVAL_SECONDS=5
STATE_PERSIST_INTERVAL_SECONDS=60
PRINTER_CACHE_PERSIST_INTERVAL_SECONDS=300
SNMP_STABLE_REFRESH_INTERVAL_SECONDS=300
SNMP_DEFAULT_COMMUNITY=oabce
IMPRESSORAS_CONFIG_JSON=[{"id":"impressora1","ip":"192.168.0.31","community":"oabce","token_valor_centavos":4}]
SWITCHES_CONFIG_JSON=[{"id":"switch1","ip":"192.168.0.10","community":"oabce"}]
```

### Observacoes sobre configuracao

- `IMPRESSORAS_CONFIG_JSON` e `SWITCHES_CONFIG_JSON` sao opcionais
- se essas variaveis nao forem informadas, o sistema usa as configuracoes padrao definidas em `config.py`
- apos o primeiro start, os cadastros ficam persistidos no banco SQLite
- para impressoras, os tokens permitidos hoje sao `4` e `50` centavos

## Como executar localmente

### Requisitos

- Python 3.11
- acesso de rede aos equipamentos monitorados
- SNMP habilitado nos equipamentos

### Passos

1. Crie e ative um ambiente virtual.
2. Instale as dependencias.
3. Copie `.env.example` para `.env` e ajuste os valores necessarios.
4. Execute a aplicacao.

Exemplo no PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python main.py
```

Interface padrao:

```text
http://127.0.0.1:5000/
```

## Como executar com Docker

Build e execucao:

```powershell
docker compose up --build
```

Configuracao atual do container:

- porta exposta: `8080`
- banco persistido em `./data`
- timezone: `America/Sao_Paulo`

Interface no container:

```text
http://127.0.0.1:8080/
```

## Rotas web

- `GET /`
  Dashboard principal das impressoras.
- `GET /graficos`
  Graficos diarios, mensais e historico.
- `GET /impressoras`
  Tela de configuracoes de impressoras e switches.
- `GET /switches`
  Dashboard dedicado para switches.

## Endpoints da API

### Monitoramento geral

- `GET /api`
  Retorna o estado atual das impressoras e, quando habilitado, dos switches.

Exemplo resumido:

```json
{
  "impressoras": {
    "impressora1": {
      "online": true,
      "ip": "192.168.0.31",
      "nome": "OKI XYZ",
      "modelo": "ES4172",
      "total_impressoes": 15234,
      "impressoes_dia": 87,
      "impressoes_mes": 913,
      "token_valor_centavos": 4,
      "token_valor_formatado": "R$ 0,04"
    }
  },
  "switches": {
    "switch1": {
      "online": true,
      "ip": "192.168.0.10",
      "nome": "Switch Core"
    }
  }
}
```

### Impressoras

- `GET /api/impressoras`
  Lista as impressoras cadastradas com resumo de status e custo.
- `POST /api/impressoras`
  Cadastra uma nova impressora.

Payload:

```json
{
  "ip": "192.168.0.50",
  "community": "oabce",
  "id": "impressora17",
  "token_valor_centavos": 4
}
```

Observacoes:

- `id` pode ser omitido; nesse caso o sistema gera o proximo `impressoraN`
- `token_valor_centavos` aceita `4` ou `50`

### Switches

- `GET /api/switches`
  Lista os switches cadastrados.
- `POST /api/switches`
  Cadastra um novo switch.

Payload:

```json
{
  "ip": "192.168.0.10",
  "community": "oabce",
  "id": "switch-core"
}
```

### Historico e integracao

- `GET /api/historico`
  Retorna o historico bruto persistido das impressoes.
- `GET /api/powerbi/impressoras`
  Retorna resumo consolidado das impressoras.
- `GET /api/powerbi/historico`
  Retorna historico em formato tabular, pronto para integracao.

### Debug

- `GET /api/debug/historico`
  Exibe estado interno relevante do rastreamento.
- `GET /api/debug/forcar-historico`
  Forca o salvamento do historico atual das impressoras.

## Fluxo de funcionamento

1. `main.py` cria o app Flask.
2. `config.py` carrega ambiente, OIDs e configuracoes base.
3. `historico_service.py` garante a estrutura do banco.
4. `printer_config_service.py` e `switch_config_service.py` carregam os cadastros ativos.
5. `PrinterMonitorService` e `SwitchMonitorService` iniciam uma thread por equipamento.
6. Cada thread consulta os OIDs SNMP periodicamente.
7. O estado atualizado fica em memoria e parte dele e persistida no SQLite.
8. A interface web consome a API para renderizar cards, tabelas e graficos.

## Cadastro de equipamentos

Voce pode cadastrar equipamentos de tres formas:

- pela interface em `/impressoras`
- pela API `POST /api/impressoras` e `POST /api/switches`
- por variaveis de ambiente no primeiro bootstrap do sistema

Para impressoras, consulte tambem [`COMO_ADICIONAR_IMPRESSORAS.md`](COMO_ADICIONAR_IMPRESSORAS.md).

## Limitacoes atuais

- nao ha autenticacao nas rotas web ou API
- nao existem testes automatizados no repositorio
- os OIDs usados hoje refletem o ambiente atual e podem exigir ajuste para outros fabricantes ou modelos
- o monitoramento depende de conectividade SNMP e das communities corretas

## Melhorias sugeridas

- adicionar autenticacao para as rotas de configuracao
- criar testes automatizados para os servicos
- separar OIDs por fabricante ou perfil de equipamento
- adicionar edicao e remocao de cadastros pela interface
- incluir logs estruturados e healthchecks
