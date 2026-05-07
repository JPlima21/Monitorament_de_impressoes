# Como adicionar impressoras

O projeto nao depende mais de editar HTML ou listas fixas no codigo para crescer. Hoje uma nova impressora pode ser cadastrada pela interface, pela API ou, no primeiro bootstrap, pelo arquivo `.env`.

## Metodo recomendado: interface web

Use a tela de configuracoes:

```text
http://127.0.0.1:5000/impressoras
```

Se estiver rodando com Docker:

```text
http://127.0.0.1:8080/impressoras
```

Na aba `Impressoras`, preencha:

- `IP`
- `Community SNMP`
- `Identificador interno`
  Opcional. Se ficar em branco, o sistema cria automaticamente algo como `impressora17`.
- `Token por impressao`
  Valores permitidos hoje:
  - `R$ 0,04`
  - `R$ 0,50`

Depois de salvar:

- a configuracao e gravada no SQLite
- o monitoramento da nova impressora comeca sem reiniciar a interface
- uma nova thread e criada para o equipamento
- a dashboard passa a exibir a impressora assim que houver dados

## Metodo por API

Tambem e possivel cadastrar via `POST /api/impressoras`.

Exemplo:

```http
POST /api/impressoras
Content-Type: application/json

{
  "ip": "192.168.0.50",
  "community": "oabce",
  "id": "impressora17",
  "token_valor_centavos": 4
}
```

Regras:

- `ip` e obrigatorio
- `community` e obrigatoria
- `id` e opcional
- `token_valor_centavos` aceita apenas `4` ou `50`
- nao pode haver outro cadastro com o mesmo `id` ou o mesmo `ip`

## Metodo por arquivo `.env`

Esse caminho e util para bootstrap inicial ou provisionamento automatizado.

Exemplo:

```env
IMPRESSORAS_CONFIG_JSON=[
  {"id":"impressora1","ip":"192.168.0.31","community":"oabce","token_valor_centavos":4},
  {"id":"impressora2","ip":"192.168.0.32","community":"oabce","token_valor_centavos":50}
]
```

Observacoes importantes:

- o `.env` e lido durante a inicializacao da aplicacao
- essas configuracoes servem como base inicial
- depois disso, os cadastros ficam persistidos na tabela `printer_config`
- se o banco ja tiver impressoras cadastradas com o mesmo `id` ou `ip`, o sistema nao duplica

## Campos da impressora

### `id`

Identificador interno usado pela aplicacao.

Exemplos:

- `impressora1`
- `impressora17`
- `colorida-financeiro`

### `ip`

Endereco IP acessivel pelo servidor onde a aplicacao esta rodando.

### `community`

Community SNMP configurada no equipamento.

Exemplos comuns:

- `public`
- `oabce`

### `token_valor_centavos`

Valor unitario usado para estimar custo diario e mensal.

Valores aceitos hoje:

- `4`
- `50`

## O que o sistema faz automaticamente

Ao adicionar uma impressora, o sistema:

1. valida o cadastro
2. persiste a configuracao no banco
3. cria a estrutura interna de cache e rastreamento
4. inicia a thread de monitoramento
5. consulta os OIDs SNMP periodicamente
6. atualiza dashboard, tela de configuracoes e endpoints da API

## Nao e mais necessario

Com a versao atual, voce nao precisa mais:

- editar `main.py` para cadastrar impressoras
- alterar HTML para criar mais colunas
- mexer manualmente no JavaScript para exibir novos equipamentos

A interface monta os cards dinamicamente com base no que a API retorna.

## Quando a impressora aparece como offline

Se o cadastro funcionar mas a impressora permanecer offline, revise:

- conectividade de rede entre a aplicacao e o IP informado
- community SNMP
- SNMP habilitado no equipamento
- compatibilidade dos OIDs usados com o modelo monitorado

## Arquivos relacionados

- `main.py`
- `config.py`
- `routes/api_routes.py`
- `services/printer_config_service.py`
- `services/printer_monitor_service.py`
- `templates/configuracoes.html`
- `static/js/configuracoes_impressoras.js`
