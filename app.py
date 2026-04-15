from pysnmp.hlapi import *

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


def monitorar_impressora(ip, community):
    # OIDs
    OID_UPTIME = '1.3.6.1.2.1.1.3.0'
    OID_NOME = '1.3.6.1.2.1.1.5.0'
    OID_DESC = '1.3.6.1.2.1.1.1.0'
    OID_PAGINAS = '1.3.6.1.2.1.43.10.2.1.4.1.1'
    OID_TONER = '1.3.6.1.2.1.43.11.1.1.9.1.1'
    OID_STATUS = '1.3.6.1.2.1.43.16.5.1.2.1.1'

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
    paginas = snmp_get(ip, community, OID_PAGINAS)
    toner = snmp_get(ip, community, OID_TONER)
    status = snmp_get(ip, community, OID_STATUS)

    # 🔹 Tratamento
    toner = int(toner) if toner and int(toner) >= 0 else None
    paginas = int(paginas) if paginas else None

    return {
        "online": True,
        "nome": str(nome),
        "descricao": str(desc),
        "paginas": paginas,
        "toner": toner,
        "status": str(status),
        "uptime": f"{days} Dias / {hours} Horas / {minutes} Minutos",
    }

resultado = monitorar_impressora("192.168.0.39", "oabce")

if not resultado["online"]:
    print("❌ Impressora OFFLINE")
else:
    print("=" * 40)
    print("STATUS DA IMPRESSORA")
    print("=" * 40)

    print(f"Nome        : {resultado['nome']}")
    print(f"Descrição   : {resultado['descricao']}")
    print(f"Status      : {resultado['status']}")

    print("-" * 40)

    print(f"Uptime      : {resultado['uptime']} dias")
    
    if resultado["paginas"] is not None:
        print(f"Páginas     : {resultado['paginas']}")
    else:
        print("Páginas     : N/A")

    if resultado["toner"] is not None:
        print(f"Toner       : {resultado['toner']}%")
    else:
        print("Toner       : Vazio ou não detectado")

    print("=" * 40)