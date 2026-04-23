# Monitoramento de Impressoras

Aplicacao Flask para monitorar impressoras via SNMP, exibir os dados em uma dashboard web e manter um historico local de impressoes em banco SQLite.

## Visao Geral

O sistema faz consultas periodicas nas impressoras configuradas, coleta informacoes como:

- nome da impressora
- IP
- MAC address
- numero de serie
- modelo
- asset number
- contador total de impressoes
- contador de impressoes do dia
- nivel de toner
- status
- uptime
- scanner

Esses dados ficam disponiveis de duas formas:

- interface web em `/`
- API JSON em `/api`

O historico de impressoes do dia e salvo no arquivo `historico_impressoes.db` e pode ser consultado pela rota `/api/historico`.

## Estrutura do Projeto

```text
Monitorament_de_impressoes/
|- app.py
|- config.py
|- historico_impressoes.db
|- routes/
|  |- api.py
|  |- web.py
|  \- __init__.py
|- services/
|  |- historico_service.py
|  |- monitor_service.py
|  |- snmp_service.py
|  \- __init__.py
|- static/
|  |- style.css
|  \- js/
|     \- dashboard.js
|- templates/
|  \- index.html
|- requirements.txt
\- README.md
```

## Papel de Cada Arquivo

### `app.py`

Ponto de entrada da aplicacao.

Responsabilidades:

- cria a instancia do Flask
- instancia o servico principal de monitoramento
- inicia as threads de coleta
- registra as rotas da API e da interface web
- inicia o servidor em modo debug quando executado diretamente

Em resumo, ele monta a aplicacao, mas nao concentra a regra de negocio.

### `config.py`

Arquivo central de configuracao.

Contem:

- caminho do banco de historico
- intervalo entre coletas
- lista de impressoras monitoradas
- OIDs SNMP usados nas consultas

Esse arquivo existe para evitar valores fixos espalhados pelo codigo.

### `services/historico_service.py`

Responsavel pela persistencia do historico em SQLite.

Funcoes principais:

- `inicializar_banco(caminho_banco)`
  - cria a tabela de historico se ela ainda nao existir
- `carregar_historico(caminho_banco)`
  - le o banco SQLite e devolve um dicionario Python
- `salvar_registro_historico(caminho_banco, chave, registro)`
  - grava ou atualiza um registro no banco SQLite

Esse modulo isola a manipulacao de arquivo da logica de monitoramento.

### `services/snmp_service.py`

Responsavel pela comunicacao SNMP.

Funcoes principais:

- `snmp_get(ip, community, oid, version=0, timeout=2)`
  - faz uma consulta SNMP para um OID especifico
  - retorna o valor encontrado ou `None` em caso de erro
- `formatar_mac(mac_raw)`
  - converte o MAC bruto para formato legivel
  - exemplo: `00:25:36:E1:50:3B`

Esse modulo evita que detalhes tecnicos do SNMP fiquem misturados com Flask ou regras do negocio.

### `services/monitor_service.py`

Modulo principal do sistema.

Contem a classe `PrinterMonitorService`, que coordena o monitoramento das impressoras.

Responsabilidades da classe:

- inicializar o estado das impressoras
- controlar o historico em memoria
- calcular as impressoes do dia
- detectar virada de dia
- tratar reset do contador da impressora
- criar uma thread por impressora
- coletar dados via SNMP continuamente
- disponibilizar os dados atualizados para a API

Metodos principais:

- `start()`
  - inicia as threads de monitoramento
- `get_resultado()`
  - devolve o estado atual de todas as impressoras
- `get_historico()`
  - devolve o historico salvo em memoria
- `_calcular_impressoes_dia(...)`
  - calcula o total do dia com suporte a reset de contador
- `_salvar_impressoes_dia(...)`
- registra um fechamento ou reset no banco SQLite
- `_monitorar_impressora(...)`
  - consulta todos os OIDs e monta o dicionario final da impressora
- `_monitor_loop(...)`
  - executa a coleta continuamente com pausa definida em configuracao

### `routes/api.py`

Define os endpoints JSON da aplicacao.

Rotas:

- `/api`
  - retorna os dados atuais das impressoras
- `/api/historico`
  - retorna o historico salvo no banco SQLite

Esse modulo so expõe dados. Ele nao conhece os detalhes de SNMP nem de persistencia.

### `routes/web.py`

Define a rota da interface HTML.

Rota:

- `/`
  - renderiza a pagina principal `index.html`

### `templates/index.html`

Estrutura base da dashboard.

Responsabilidades:

- carregar o CSS
- criar o container principal da pagina
- importar o JavaScript da interface

Ele foi mantido simples para nao misturar HTML com logica de atualizacao da tela.

### `static/js/dashboard.js`

Controla a interface no navegador.

Funcoes principais:

- `criarColunaImpressora(nomeImpressora)`
  - monta dinamicamente o HTML de uma coluna/card
- `atualizarStatus(statusEl, online)`
  - atualiza o texto e a classe visual de status
- `preencherCampos(nomeImpressora, dataImpressora)`
  - preenche os campos da tela com os valores vindos da API
- `inicializarContainer(container, impressoras)`
  - cria os cards das impressoras na primeira carga
- `atualizar()`
  - faz `fetch('/api')`, le o JSON e atualiza a dashboard

O arquivo tambem usa `setInterval(...)` para repetir a atualizacao automaticamente.

## Fluxo de Funcionamento

O fluxo geral da aplicacao e este:

1. `app.py` cria a aplicacao Flask.
2. `PrinterMonitorService` e instanciado.
3. O servico carrega o historico existente de `historico_impressoes.db`.
4. O servico cria o estado inicial das impressoras.
5. O metodo `start()` inicia uma thread para cada impressora configurada.
6. Cada thread executa `_monitor_loop(...)`.
7. O loop consulta os dados SNMP da impressora.
8. O resultado e armazenado em memoria em `resultado_global`.
9. A interface web chama `/api` periodicamente.
10. O JavaScript atualiza os cards na tela com os dados recebidos.

## Calculo de Impressoes do Dia

O calculo de `impressoes_dia` segue esta logica:

- na primeira leitura do dia, o valor atual da impressora vira a base inicial
- as impressoes do dia sao calculadas pela diferenca entre o contador atual e a base inicial
- quando muda o dia, o total anterior e salvo no historico
- se o contador da impressora reiniciar e voltar para um valor menor, o sistema entende isso como reset
- nesse caso, ele acumula o total anterior, salva um registro no historico e continua a contagem a partir do novo valor
- o estado diario em andamento tambem e salvo no banco, para que a aplicacao retome a contagem apos reinicios

Isso evita perder a contagem diaria mesmo quando o equipamento reinicia o contador.

## Endpoints

### `GET /`

Retorna a pagina principal da dashboard.

### `GET /api`

Retorna o estado atual das impressoras em JSON.

Exemplo de estrutura:

```json
{
  "impressoras": {
    "impressora1": {
      "online": true,
      "ip": "192.168.0.39",
      "nome": "OKI",
      "num_serie": "123456",
      "modelo": "Modelo X",
      "asset_number": "ABC123",
      "impressoes": 15234,
      "impressoes_dia": 87,
      "toner": "65%",
      "status": "ready",
      "uptime": "2 Dias / 5 Horas / 12 Minutos",
      "scanner": "ativo",
      "mac": "00:11:22:33:44:55"
    }
  }
}
```

### `GET /api/historico`

Retorna o historico de impressoes salvo no banco SQLite.

## Como Executar

1. Ative o ambiente virtual.
2. Instale as dependencias de `requirements.txt`.
3. Execute:

```powershell
venv\Scripts\python.exe app.py
```

4. Abra no navegador:

```text
http://127.0.0.1:5000/
```

## Como Adicionar uma Nova Impressora

Edite a lista `IMPRESSORAS_CONFIG` em `config.py` e adicione um novo item com:

- `id`
- `ip`
- `community`

Exemplo:

```python
{
    "id": "impressora6",
    "ip": "192.168.0.36",
    "community": "oabce",
}
```

## Observacoes Tecnicas

- o sistema usa threads para monitorar varias impressoras em paralelo
- o acesso ao estado compartilhado e protegido com `threading.Lock()`
- o historico fica em arquivo local SQLite, sem necessidade de servidor externo
- a interface nao consulta SNMP diretamente; ela apenas consome a API Flask

## Melhorias Futuras

- mover configuracoes para variaveis de ambiente ou arquivo externo
- adicionar logs estruturados
- criar testes automatizados
- documentar os OIDs por fabricante/modelo
- permitir cadastro de impressoras pela interface
- adicionar filtros e paginacao no historico via consultas SQL
