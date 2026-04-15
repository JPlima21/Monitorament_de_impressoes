from pysnmp.hlapi import *
import threading
import time
import os

resultado_global = {}

def snmp_get(ip, community, oid, version=0, timeout=2):
    iterator = getCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=version),
        UdpTransportTarget((ip, 161), timeout=timeout, retries=3),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )

    errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

    if errorIndication or errorStatus:
        return None

    for varBind in varBinds:
        return varBind[1]

# 🔹 FUNÇÃO PARA CONVERTER MAC
def formatar_mac(mac_raw):
    if mac_raw is None:
        return None

    try:
        mac_bytes = bytes(mac_raw)
        return ':'.join(f'{b:02X}' for b in mac_bytes)
    except:
        return str(mac_raw)

def monitorar_impressora(ip, community):
    # OIDs
    OID_UPTIME = '1.3.6.1.2.1.1.3.0'
    OID_NOME = '1.3.6.1.2.1.1.5.0'
    OID_DESC = '1.3.6.1.2.1.1.1.0'
    OID_IMPRESSOES = '1.3.6.1.2.1.43.10.2.1.4.1.1'
    OID_TONER = '1.3.6.1.2.1.43.11.1.1.9.1.1'
    OID_STATUS = '1.3.6.1.2.1.43.16.5.1.2.1.1'
    OID_SCANNER = '1.3.6.1.4.1.2001.1.1.4.2.1.3.11.0'  # Exemplo de OID para scanner (pode variar conforme modelo)
    OID_MAC = '1.3.6.1.2.1.2.2.1.6.1'  # OID para MAC Address (pode variar conforme modelo)

    # 🔹 Verifica se está online
    uptime = snmp_get(ip, community, OID_UPTIME)

    if uptime is None:
        return {
            "online": False,
            "erro": "Sem resposta SNMP"
        }

    # 🔹 Converte uptime
    uptime_ticks = int(uptime)
    seconds = int(uptime_ticks // 100)

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60

    # 🔹 Coleta dados
    nome = snmp_get(ip, community, OID_NOME)
    desc = snmp_get(ip, community, OID_DESC)
    impressoes = snmp_get(ip, community, OID_IMPRESSOES)
    toner = snmp_get(ip, community, OID_TONER)
    status = snmp_get(ip, community, OID_STATUS)
    scanner = snmp_get(ip, community, OID_SCANNER)
    mac_raw = snmp_get(ip, community, OID_MAC)

    # 🔹 Tratamento
    toner = int(toner) if toner and int(toner) >= 0 else None
    impressoes = int(impressoes) if impressoes else None

    mac = formatar_mac(mac_raw)

    return {
        "online": True,
        "nome": str(nome),
        "descricao": str(desc),
        "impressoes": impressoes,
        "toner": f'{toner}%',
        "status": str(status),
        "uptime": f"{days} Dias / {hours} Horas / {minutes} Minutos",
        "scanner": str(scanner), 
        "mac": mac

    }

# 🔁 Thread: só coleta
def monitor_loop():
    global resultado_global
    while True:
        resultado_global = monitorar_impressora("192.168.0.39", "oabce")
        time.sleep(5)


# inicia thread
threading.Thread(target=monitor_loop, daemon=True).start()

# 🖥️ Loop principal: só exibe
while True:
    os.system('cls')  # limpa terminal

    if not resultado_global:
        print("⏳ Carregando dados...")
        time.sleep(1)
        continue

    if not resultado_global["online"]:
        print("❌ Impressora OFFLINE")
    else:
        print("=" * 40)
        print("🖨️ STATUS DA IMPRESSORA")
        print("=" * 40)

        print(f"Nome        : {resultado_global['nome']}")
        print(f"MAC         : {resultado_global['mac']}")
        print(f"Descrição   : {resultado_global['descricao']}")
        print(f"Status      : {resultado_global['status']}")

        print("-" * 40)

        print(f"Uptime      : {resultado_global['uptime']}")
        print(f"Impressões  : {resultado_global['impressoes'] or 'N/A'}")
        print(f"Toner       : {resultado_global['toner'] if resultado_global['toner'] is not None else 'Vazio'}")
        print(f"Scanner     : {resultado_global['scanner']}")

        print("=" * 40)

    time.sleep(5)