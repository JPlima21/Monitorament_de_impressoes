import json
from pathlib import Path


def carregar_historico(caminho_arquivo):
    caminho = Path(caminho_arquivo)

    if not caminho.exists():
        return {}

    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (json.JSONDecodeError, OSError):
        return {}


def salvar_historico(caminho_arquivo, historico):
    caminho = Path(caminho_arquivo)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    with caminho.open("w", encoding="utf-8") as arquivo:
        json.dump(historico, arquivo, ensure_ascii=False, indent=2)
