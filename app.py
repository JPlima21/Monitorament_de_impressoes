from pysnmp.hlapi import SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, getCmd

def snmp_get(ip, community, oid): # IP do dispositivo, comunidade SNMP, OID a ser consultado
    iterator = getCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=1),  # SNMP v1 = 0, v2c = 1
        UdpTransportTarget((ip, 161)), # 161 = porta padrão SNMP
        ContextData(),
        ObjectType(ObjectIdentity(oid)) # ObjectIdentity o OID a ser consultado, ObjectType é usado para criar uma instância do tipo de objeto SNMP a ser consultado
    )

    errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

    if errorIndication:
        print(errorIndication)
    elif errorStatus:
        print('%s at %s' % (
            errorStatus.prettyPrint(),
            errorIndex and varBinds[int(errorIndex) - 1][0] or '?'
        ))
    else:
        for varBind in varBinds:
            print(f'{varBind[0]} = {varBind[1]}')

def get_uptime_days(ip, community, oid):
    iterator = getCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=1),
        UdpTransportTarget((ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )

    errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

    if errorIndication:
        print("Erro:", errorIndication)
        return
    elif errorStatus:
        print("Erro SNMP:", errorStatus.prettyPrint())
        return

    for varBind in varBinds:
        uptime_ticks = int(varBind[1])  # pega valor

        # Convertendo
        seconds = uptime_ticks / 100  # 1 tick = 0.01 segundos
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60

        print(f"Uptime: {days:.2f} dias", f"{hours:.2f} horas", f"{minutes:.2f} minutos")

# Exemplo
snmp_get("192.168.0.1", "public", "1.3.6.1.2.1.1.5.0")
get_uptime_days('192.168.0.1', 'public', '1.3.6.1.2.1.1.3.0')
# snmp_get('192.168.0.1', 'public', '1.3.6.1.2.1.1.1.0')
