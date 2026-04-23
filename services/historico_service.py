import sqlite3
from pathlib import Path


CREATE_HISTORICO_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS historico_impressoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chave TEXT NOT NULL UNIQUE,
    impressora TEXT NOT NULL,
    data TEXT NOT NULL,
    hora_inicio TEXT,
    impressoes_total_dia INTEGER NOT NULL,
    motivo TEXT NOT NULL,
    timestamp_salvo TEXT NOT NULL
)
"""
LEGACY_RASTREAMENTO_DIARIO_TABLE = "rastreamento_diario"
CACHE_RASTREAMENTO_DIARIO_TABLE = "cache_rastreamento_diario"


CREATE_CACHE_RASTREAMENTO_DIARIO_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS cache_rastreamento_diario (
    impressora TEXT PRIMARY KEY,
    data_lista TEXT,
    hora_primeiro_registro TEXT,
    impressoes_inicio INTEGER,
    impressoes_acumuladas INTEGER NOT NULL DEFAULT 0,
    impressoes_dia INTEGER NOT NULL DEFAULT 0,
    registrado_hoje INTEGER NOT NULL DEFAULT 0
)
"""
CREATE_RASTREAMENTO_MENSAL_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS rastreamento_mensal (
    impressora TEXT PRIMARY KEY,
    mes_referencia TEXT,
    impressoes_inicio INTEGER,
    impressoes_acumuladas INTEGER NOT NULL DEFAULT 0,
    impressoes_mes INTEGER NOT NULL DEFAULT 0,
    registrado_mes INTEGER NOT NULL DEFAULT 0
)
"""
CREATE_CACHE_IMPRESSORA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS cache_impressora (
    impressora TEXT PRIMARY KEY,
    ip TEXT,
    nome TEXT,
    num_serie TEXT,
    modelo TEXT,
    asset_number TEXT,
    location TEXT,
    uptime TEXT,
    mac TEXT,
    atualizado_em TEXT NOT NULL
)
"""


def _obter_conexao(caminho_banco):
    caminho = Path(caminho_banco)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    return conexao


def _migrar_cache_rastreamento_diario(conexao):
    tabela_legada = conexao.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (LEGACY_RASTREAMENTO_DIARIO_TABLE,),
    ).fetchone()

    if not tabela_legada:
        return

    conexao.execute(
        f"""
        INSERT OR IGNORE INTO {CACHE_RASTREAMENTO_DIARIO_TABLE} (
            impressora,
            data_lista,
            hora_primeiro_registro,
            impressoes_inicio,
            impressoes_acumuladas,
            impressoes_dia,
            registrado_hoje
        )
        SELECT
            impressora,
            data_lista,
            hora_primeiro_registro,
            impressoes_inicio,
            impressoes_acumuladas,
            impressoes_dia,
            registrado_hoje
        FROM {LEGACY_RASTREAMENTO_DIARIO_TABLE}
        """
    )
    conexao.execute(f"DROP TABLE {LEGACY_RASTREAMENTO_DIARIO_TABLE}")


def inicializar_banco(caminho_banco):
    with _obter_conexao(caminho_banco) as conexao:
        conexao.execute(CREATE_HISTORICO_TABLE_SQL)
        conexao.execute(CREATE_CACHE_RASTREAMENTO_DIARIO_TABLE_SQL)
        conexao.execute(CREATE_RASTREAMENTO_MENSAL_TABLE_SQL)
        conexao.execute(CREATE_CACHE_IMPRESSORA_TABLE_SQL)
        _migrar_cache_rastreamento_diario(conexao)
        conexao.commit()


def carregar_historico(caminho_banco):
    inicializar_banco(caminho_banco)

    with _obter_conexao(caminho_banco) as conexao:
        registros = conexao.execute(
            """
            SELECT
                chave,
                impressora,
                data,
                hora_inicio,
                impressoes_total_dia,
                motivo,
                timestamp_salvo
            FROM historico_impressoes
            ORDER BY timestamp_salvo DESC, id DESC
            """
        ).fetchall()

    return {
        registro["chave"]: {
            "impressora": registro["impressora"],
            "data": registro["data"],
            "hora_inicio": registro["hora_inicio"],
            "impressoes_total_dia": registro["impressoes_total_dia"],
            "motivo": registro["motivo"],
            "timestamp_salvo": registro["timestamp_salvo"],
        }
        for registro in registros
    }


def salvar_registro_historico(caminho_banco, chave, registro):
    inicializar_banco(caminho_banco)

    with _obter_conexao(caminho_banco) as conexao:
        conexao.execute(
            """
            INSERT INTO historico_impressoes (
                chave,
                impressora,
                data,
                hora_inicio,
                impressoes_total_dia,
                motivo,
                timestamp_salvo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(chave) DO UPDATE SET
                impressora = excluded.impressora,
                data = excluded.data,
                hora_inicio = excluded.hora_inicio,
                impressoes_total = excluded.impressoes_total,
                motivo = excluded.motivo,
                timestamp_salvo = excluded.timestamp_salvo
            """,
            (
                chave,
                registro["impressora"],
                registro["data"],
                registro["hora_inicio"],
                int(registro["impressoes_total"]),
                registro["motivo"],
                registro["timestamp_salvo"],
            ),
        )
        conexao.commit()


def carregar_cache_rastreamento_diario(caminho_banco):
    inicializar_banco(caminho_banco)

    with _obter_conexao(caminho_banco) as conexao:
        registros = conexao.execute(
            """
            SELECT
                impressora,
                data_lista,
                hora_primeiro_registro,
                impressoes_inicio,
                impressoes_acumuladas,
                impressoes_dia,
                registrado_hoje
            FROM cache_rastreamento_diario
            """
        ).fetchall()

    return {
        registro["impressora"]: {
            "data_lista": registro["data_lista"],
            "hora_primeiro_registro": registro["hora_primeiro_registro"],
            "impressoes_inicio": registro["impressoes_inicio"],
            "impressoes_acumuladas": registro["impressoes_acumuladas"],
            "impressoes_dia": registro["impressoes_dia"],
            "registrado_hoje": bool(registro["registrado_hoje"]),
        }
        for registro in registros
    }


def carregar_cache_rastreamento_diario_atual(caminho_banco, data_referencia):
    inicializar_banco(caminho_banco)

    with _obter_conexao(caminho_banco) as conexao:
        conexao.execute(
            """
            DELETE FROM cache_rastreamento_diario
            WHERE data_lista IS NOT NULL AND data_lista <> ?
            """,
            (str(data_referencia),),
        )
        registros = conexao.execute(
            """
            SELECT
                impressora,
                data_lista,
                hora_primeiro_registro,
                impressoes_inicio,
                impressoes_acumuladas,
                impressoes_dia,
                registrado_hoje
            FROM cache_rastreamento_diario
            WHERE data_lista = ?
            """,
            (str(data_referencia),),
        ).fetchall()
        conexao.commit()

    return {
        registro["impressora"]: {
            "data_lista": registro["data_lista"],
            "hora_primeiro_registro": registro["hora_primeiro_registro"],
            "impressoes_inicio": registro["impressoes_inicio"],
            "impressoes_acumuladas": registro["impressoes_acumuladas"],
            "impressoes_dia": registro["impressoes_dia"],
            "registrado_hoje": bool(registro["registrado_hoje"]),
        }
        for registro in registros
    }


def salvar_cache_rastreamento_diario(caminho_banco, impressora, rastreamento):
    inicializar_banco(caminho_banco)

    with _obter_conexao(caminho_banco) as conexao:
        conexao.execute(
            """
            INSERT INTO cache_rastreamento_diario (
                impressora,
                data_lista,
                hora_primeiro_registro,
                impressoes_inicio,
                impressoes_acumuladas,
                impressoes_dia,
                registrado_hoje
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(impressora) DO UPDATE SET
                data_lista = excluded.data_lista,
                hora_primeiro_registro = excluded.hora_primeiro_registro,
                impressoes_inicio = excluded.impressoes_inicio,
                impressoes_acumuladas = excluded.impressoes_acumuladas,
                impressoes_dia = excluded.impressoes_dia,
                registrado_hoje = excluded.registrado_hoje
            """,
            (
                impressora,
                rastreamento["data_lista"],
                rastreamento["hora_primeiro_registro"],
                rastreamento["impressoes_inicio"],
                int(rastreamento.get("impressoes_acumuladas", 0) or 0),
                int(rastreamento.get("impressoes_dia", 0) or 0),
                1 if rastreamento.get("registrado_hoje") else 0,
            ),
        )
        conexao.commit()


def carregar_rastreamento_mensal(caminho_banco):
    inicializar_banco(caminho_banco)

    with _obter_conexao(caminho_banco) as conexao:
        registros = conexao.execute(
            """
            SELECT
                impressora,
                mes_referencia,
                impressoes_inicio,
                impressoes_acumuladas,
                impressoes_mes,
                registrado_mes
            FROM rastreamento_mensal
            """
        ).fetchall()

    return {
        registro["impressora"]: {
            "mes_referencia": registro["mes_referencia"],
            "impressoes_inicio": registro["impressoes_inicio"],
            "impressoes_acumuladas": registro["impressoes_acumuladas"],
            "impressoes_mes": registro["impressoes_mes"],
            "registrado_mes": bool(registro["registrado_mes"]),
        }
        for registro in registros
    }


def salvar_rastreamento_mensal(caminho_banco, impressora, rastreamento):
    inicializar_banco(caminho_banco)

    with _obter_conexao(caminho_banco) as conexao:
        conexao.execute(
            """
            INSERT INTO rastreamento_mensal (
                impressora,
                mes_referencia,
                impressoes_inicio,
                impressoes_acumuladas,
                impressoes_mes,
                registrado_mes
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(impressora) DO UPDATE SET
                mes_referencia = excluded.mes_referencia,
                impressoes_inicio = excluded.impressoes_inicio,
                impressoes_acumuladas = excluded.impressoes_acumuladas,
                impressoes_mes = excluded.impressoes_mes,
                registrado_mes = excluded.registrado_mes
            """,
            (
                impressora,
                rastreamento["mes_referencia"],
                rastreamento["impressoes_inicio"],
                int(rastreamento.get("impressoes_acumuladas", 0) or 0),
                int(rastreamento.get("impressoes_mes", 0) or 0),
                1 if rastreamento.get("registrado_mes") else 0,
            ),
        )
        conexao.commit()


def carregar_cache_impressoras(caminho_banco):
    inicializar_banco(caminho_banco)

    with _obter_conexao(caminho_banco) as conexao:
        registros = conexao.execute(
            """
            SELECT
                impressora,
                ip,
                nome,
                num_serie,
                modelo,
                asset_number,
                location,
                uptime,
                mac,
                atualizado_em
            FROM cache_impressora
            """
        ).fetchall()

    return {
        registro["impressora"]: {
            "ip": registro["ip"],
            "nome": registro["nome"],
            "num_serie": registro["num_serie"],
            "modelo": registro["modelo"],
            "asset_number": registro["asset_number"],
            "location": registro["location"],
            "uptime": registro["uptime"],
            "mac": registro["mac"],
            "atualizado_em": registro["atualizado_em"],
        }
        for registro in registros
    }


def salvar_cache_impressora(caminho_banco, impressora, dados_cache):
    inicializar_banco(caminho_banco)

    with _obter_conexao(caminho_banco) as conexao:
        conexao.execute(
            """
            INSERT INTO cache_impressora (
                impressora,
                ip,
                nome,
                num_serie,
                modelo,
                asset_number,
                location,
                uptime,
                mac,
                atualizado_em
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(impressora) DO UPDATE SET
                ip = excluded.ip,
                nome = excluded.nome,
                num_serie = excluded.num_serie,
                modelo = excluded.modelo,
                asset_number = excluded.asset_number,
                location = excluded.location,
                uptime = excluded.uptime,
                mac = excluded.mac,
                atualizado_em = excluded.atualizado_em
            """,
            (
                impressora,
                dados_cache.get("ip"),
                dados_cache.get("nome"),
                dados_cache.get("num_serie"),
                dados_cache.get("modelo"),
                dados_cache.get("asset_number"),
                dados_cache.get("location"),
                dados_cache.get("uptime"),
                dados_cache.get("mac"),
                dados_cache.get("atualizado_em"),
            ),
        )
        conexao.commit()
