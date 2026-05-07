import os
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def _load_local_env():
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            continue

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]

        os.environ.setdefault(key, value)


def _get_int_env(name, default):
    value = os.getenv(name, str(default)).strip()
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"A variavel {name} precisa ser um numero inteiro valido.") from exc


def _get_bool_env(name, default):
    value = os.getenv(name, "1" if default else "0").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _get_path_env(name, default):
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default

    path = Path(raw_value)
    if path.is_absolute():
        return path
    return BASE_DIR / path


def _normalizar_token_valor_centavos(valor, default=4):
    if valor is None or str(valor).strip() == "":
        return default

    texto = str(valor).strip().replace("R$", "").replace(" ", "")
    texto = texto.replace(",", ".")

    try:
        if "." in texto:
            return round(float(texto) * 100)
        return int(texto)
    except ValueError as exc:
        raise ValueError("O token da impressora precisa ser informado em centavos ou em reais.") from exc


def _build_default_printers(default_community):
    return [
        {"id": "impressora1", "ip": "192.168.0.31", "community": default_community, "token_valor_centavos": 4},
        {"id": "impressora2", "ip": "192.168.0.32", "community": default_community, "token_valor_centavos": 4},
        {"id": "impressora3", "ip": "192.168.0.33", "community": default_community, "token_valor_centavos": 4},
        {"id": "impressora4", "ip": "192.168.0.34", "community": default_community, "token_valor_centavos": 4},
        {"id": "impressora5", "ip": "192.168.0.35", "community": default_community, "token_valor_centavos": 4},
        {"id": "impressora6", "ip": "192.168.0.36", "community": default_community, "token_valor_centavos": 4},
        {"id": "impressora7", "ip": "192.168.0.37", "community": default_community, "token_valor_centavos": 4},
        {"id": "impressora8", "ip": "192.168.0.38", "community": default_community, "token_valor_centavos": 4},
        {"id": "impressora9", "ip": "192.168.0.39", "community": default_community, "token_valor_centavos": 4},
        {"id": "impressora10", "ip": "192.168.0.40", "community": default_community, "token_valor_centavos": 4},
        {"id": "impressora11", "ip": "192.168.0.41", "community": default_community, "token_valor_centavos": 4},
        {"id": "impressora12", "ip": "10.10.20.5", "community": default_community, "token_valor_centavos": 4},
        {"id": "impressora13", "ip": "10.10.20.6", "community": default_community, "token_valor_centavos": 4},
        {"id": "impressora14", "ip": "10.10.20.7", "community": default_community, "token_valor_centavos": 4},
        {"id": "impressora15", "ip": "10.10.20.8", "community": default_community, "token_valor_centavos": 4},
        {"id": "impressora16", "ip": "10.10.20.9", "community": default_community, "token_valor_centavos": 4},
    ]


def _load_printers_config(default_community):
    default_printers = _build_default_printers(default_community)
    raw_value = os.getenv("IMPRESSORAS_CONFIG_JSON", "").strip()
    if not raw_value:
        return default_printers

    try:
        printers = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise ValueError("A variavel IMPRESSORAS_CONFIG_JSON precisa conter um JSON valido.") from exc

    if not isinstance(printers, list):
        raise ValueError("A variavel IMPRESSORAS_CONFIG_JSON precisa conter uma lista de impressoras.")

    normalized_printers = []
    for index, printer in enumerate(printers, start=1):
        if not isinstance(printer, dict):
            raise ValueError(
                f"A impressora na posicao {index} de IMPRESSORAS_CONFIG_JSON precisa ser um objeto."
            )

        normalized_printer = {
            "id": str(printer.get("id") or "").strip(),
            "ip": str(printer.get("ip") or "").strip(),
            "community": str(printer.get("community") or default_community).strip(),
            "token_valor_centavos": _normalizar_token_valor_centavos(
                printer.get("token_valor_centavos"), default=4
            ),
        }

        if not normalized_printer["id"] or not normalized_printer["ip"]:
            raise ValueError(
                f"A impressora na posicao {index} de IMPRESSORAS_CONFIG_JSON precisa ter id e ip."
            )

        normalized_printers.append(normalized_printer)

    return normalized_printers


def _load_switches_config(default_community):
    raw_value = os.getenv("SWITCHES_CONFIG_JSON", "").strip()
    if not raw_value:
        return []

    try:
        switches = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise ValueError("A variavel SWITCHES_CONFIG_JSON precisa conter um JSON valido.") from exc

    if not isinstance(switches, list):
        raise ValueError("A variavel SWITCHES_CONFIG_JSON precisa conter uma lista de switches.")

    normalized_switches = []
    for index, switch in enumerate(switches, start=1):
        if not isinstance(switch, dict):
            raise ValueError(
                f"O switch na posicao {index} de SWITCHES_CONFIG_JSON precisa ser um objeto."
            )

        normalized_switch = {
            "id": str(switch.get("id") or "").strip(),
            "ip": str(switch.get("ip") or "").strip(),
            "community": str(switch.get("community") or default_community).strip(),
        }

        if not normalized_switch["id"] or not normalized_switch["ip"]:
            raise ValueError(
                f"O switch na posicao {index} de SWITCHES_CONFIG_JSON precisa ter id e ip."
            )

        normalized_switches.append(normalized_switch)

    return normalized_switches


_load_local_env()

FLASK_DEBUG = _get_bool_env("FLASK_DEBUG", True)
FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1").strip() or "127.0.0.1"
FLASK_PORT = _get_int_env("FLASK_PORT", 5000)

HISTORICO_DB_FILE = _get_path_env("HISTORICO_DB_FILE", BASE_DIR / "historico_impressoes.db")
HISTORICO_FECHAMENTO_DIARIO = os.getenv("HISTORICO_FECHAMENTO_DIARIO", "00:00").strip() or "00:00"

MONITOR_INTERVAL_SECONDS = _get_int_env("MONITOR_INTERVAL_SECONDS", 5)
STATE_PERSIST_INTERVAL_SECONDS = _get_int_env("STATE_PERSIST_INTERVAL_SECONDS", 60)
PRINTER_CACHE_PERSIST_INTERVAL_SECONDS = _get_int_env(
    "PRINTER_CACHE_PERSIST_INTERVAL_SECONDS", 300
)
SNMP_STABLE_REFRESH_INTERVAL_SECONDS = _get_int_env(
    "SNMP_STABLE_REFRESH_INTERVAL_SECONDS", 300
)

SNMP_DEFAULT_COMMUNITY = os.getenv("SNMP_DEFAULT_COMMUNITY", "oabce").strip() or "oabce"
IMPRESSORAS_CONFIG = _load_printers_config(SNMP_DEFAULT_COMMUNITY)
SWITCHES_CONFIG = _load_switches_config(SNMP_DEFAULT_COMMUNITY)

SNMP_OIDS = {
    "location": "1.3.6.1.2.1.1.6.0",
    "uptime": "1.3.6.1.2.1.1.3.0",
    "nome": "1.3.6.1.2.1.1.5.0",
    "descricao_sistema": "1.3.6.1.2.1.1.1.0",
    "contato": "1.3.6.1.2.1.1.4.0",
    "serial": "1.3.6.1.2.1.43.5.1.1.17.1",
    "modelo": "1.3.6.1.2.1.25.3.2.1.3.1",
    "asset_number": "1.3.6.1.4.1.2001.1.1.1.1.11.1.10.40.2.0",
    "total_impressoes": "1.3.6.1.2.1.43.10.2.1.4.1.1",
    "impressoes": "1.3.6.1.4.1.2001.1.1.1.1.11.1.10.170.1.21.3",
    "copias": "1.3.6.1.4.1.2001.1.1.1.1.11.1.10.170.1.17.1",
    "toner": "1.3.6.1.2.1.43.11.1.1.9.1.1",
    "status": "1.3.6.1.2.1.43.16.5.1.2.1.1",
    "scanner": "1.3.6.1.4.1.2001.1.1.4.2.1.3.11.0",
    "mac": "1.3.6.1.2.1.2.2.1.6.1",
    "interfaces_total": "1.3.6.1.2.1.2.1.0",
    "status_porta_principal": "1.3.6.1.2.1.2.2.1.8.1",
}
