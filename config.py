import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
HISTORICO_DB_FILE = Path(
    os.getenv("HISTORICO_DB_FILE", str(BASE_DIR / "historico_impressoes.db"))
)

MONITOR_INTERVAL_SECONDS = 5

IMPRESSORAS_CONFIG = [
    {
        "id": "impressora1",
        "ip": "192.168.0.31",
        "community": "oabce",
    },
    {
        "id": "impressora2",
        "ip": "192.168.0.32",
        "community": "oabce",
    },
    {
        "id": "impressora3",
        "ip": "192.168.0.33",
        "community": "oabce",
    },
    {
        "id": "impressora4",
        "ip": "192.168.0.34",
        "community": "oabce",
    },
    {
        "id": "impressora5",
        "ip": "192.168.0.35",
        "community": "oabce",
    },
    {
        "id": "impressora6",
        "ip": "192.168.0.36",
        "community": "oabce",
    },
    {
        "id": "impressora7",
        "ip": "192.168.0.37",
        "community": "oabce",
    },
    {
        "id": "impressora8",
        "ip": "192.168.0.38",
        "community": "oabce",
    },
    {
        "id": "impressora9",
        "ip": "192.168.0.39",
        "community": "oabce",
    },
    {
        "id": "impressora10",
        "ip": "192.168.0.40",
        "community": "oabce",
    },
    {
        "id": "impressora11",
        "ip": "192.168.0.41",
        "community": "oabce",
    },
    {
        "id": "impressora12",
        "ip": "10.10.20.5",
        "community": "oabce",
    },
    {
        "id": "impressora13",
        "ip": "10.10.20.6",
        "community": "oabce",
    },
    {
        "id": "impressora14",
        "ip": "10.10.20.7",
        "community": "oabce",
    },
    {
        "id": "impressora15",
        "ip": "10.10.20.8",
        "community": "oabce",
    },
    {
        "id": "impressora16",
        "ip": "10.10.20.9",
        "community": "oabce",
    },
]

SNMP_OIDS = {
    "location": "1.3.6.1.2.1.1.6.0",
    "uptime": "1.3.6.1.2.1.1.3.0",
    "nome": "1.3.6.1.2.1.1.5.0",
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
}
