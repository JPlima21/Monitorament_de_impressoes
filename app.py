from pysnmp.hlapi import SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, getCmd

def snmp_get(ip, community, oid): # IP do dispositivo, comunidade SNMP, OID a ser consultado
    iterator = getCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),  # SNMP v1 = 0, v2c = 1
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

def snmp_get_page(ip, community, oid): # IP do dispositivo, comunidade SNMP, OID a ser consultado
    iterator = getCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),  # SNMP v1 = 0, v2c = 1
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
            print(f'{varBind[0]} = {varBind[1]} páginas')

def snmp_get_toner_level(ip, community, oid):
    iterator = getCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),  # SNMP v1 = 0, v2c = 1
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
            toner_level = int(varBind[1])
            if toner_level < 0:
                print(f'{varBind[0]} = Toner vazio ou não detectado')
            else:
                print(f'{varBind[0]} = {toner_level}% nível do toner')

# Exemplo
print("Consultando nome do dispositivo:")
snmp_get("192.168.0.39", "oabce", "1.3.6.1.2.1.1.5.0") # OID para nome do dispositivo (sysName)
print('=' * 50)

print("Consultando uptime do sistema:")
get_uptime_days('192.168.0.39', 'oabce', '1.3.6.1.2.1.1.3.0') # OID para uptime do sistema (sysUpTimeInstance)
print('=' * 50)

print("Consultando descrição do sistema:")
snmp_get('192.168.0.39', 'oabce', '1.3.6.1.2.1.1.1.0') # OID para descrição do sistema (sysDescr)
print('=' * 50)

print("Consultando quantidade de páginas impressas:")
snmp_get_page('192.168.0.39', 'oabce', '1.3.6.1.2.1.43.10.2.1.4.1.1') # OID para quantidade de páginas impressas (prtMarkerLifeCount)
print('=' * 50)

print("Consultando status do toner:")
snmp_get_toner_level('192.168.0.39', 'oabce', '1.3.6.1.2.1.43.11.1.1.9.1.1') # OID para status do toner (prtMarkerSuppliesLevel) - pode retornar o nível do toner ou um valor negativo indicando que o toner está vazio ou não detectado.