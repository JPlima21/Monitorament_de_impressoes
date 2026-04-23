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
CREATE_RASTREAMENTO_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS rastreamento_diario (
    impressora TEXT PRIMARY KEY,
    data_lista TEXT,
    hora_primeiro_registro TEXT,
    impressoes_inicio INTEGER,
    impressoes_acumuladas INTEGER NOT NULL DEFAULT 0,
    impressoes_dia INTEGER NOT NULL DEFAULT 0,
    registrado_hoje INTEGER NOT NULL DEFAULT 0
)
"""


def _obter_conexao(caminho_banco):
    caminho = Path(caminho_banco)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    return conexao


def inicializar_banco(caminho_banco):
    with _obter_conexao(caminho_banco) as conexao:
        conexao.execute(CREATE_HISTORICO_TABLE_SQL)
        conexao.execute(CREATE_RASTREAMENTO_TABLE_SQL)
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


def carregar_rastreamento_diario(caminho_banco):
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
            FROM rastreamento_diario
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


def salvar_rastreamento_diario(caminho_banco, impressora, rastreamento):
    inicializar_banco(caminho_banco)

    with _obter_conexao(caminho_banco) as conexao:
        conexao.execute(
            """
            INSERT INTO rastreamento_diario (
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
