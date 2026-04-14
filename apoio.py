from pysnmp.hlapi import *
import time

ip = '192.168.0.39'
community = 'oabce'

for i in range(1, 20):
    oid = f'1.3.6.1.2.1.43.11.1.1.9.1.{i}'

    iterator = getCmd(
        SnmpEngine(),
        CommunityData(community, mpModel=1),
        UdpTransportTarget((ip, 161), timeout=2, retries=1),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )

    errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

    if errorIndication:
        print(f"[{i}] Erro:", errorIndication)
    elif errorStatus:
        print(f"[{i}] Erro SNMP:", errorStatus.prettyPrint())
    else:
        for varBind in varBinds:
            print(f"[{i}]", varBind)

    time.sleep(0.5)  # 👈 ESSENCIAL (evita bloqueio)