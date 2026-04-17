from flask import Flask, jsonify, render_template
from pysnmp.hlapi import *
import threading
import time
import os
import subprocess
from datetime import datetime

# ⚙️ CONFIGURAÇÃO DE IMPRESSORAS
# Para adicionar uma nova impressora, basta adicionar um dicionário nesta lista!
IMPRESSORAS_CONFIG = [
    {
        'id': 'impressora1',
        'ip': '192.168.0.39',
        'community': 'oabce'
    },
    {
        'id': 'impressora2',
        'ip': '192.168.0.32',
        'community': 'oabce'
    },
    {
        'id': 'impressora3',
        'ip': '192.168.0.33',
        'community': 'oabce'
    },
    {
        'id': 'impressora4',
        'ip': '192.168.0.34',
        'community': 'oabce'
    },
    {
        'id': 'impressora5',
        'ip': '192.168.0.35',
        'community': 'oabce'
    },
]

# Dicionário global para armazenar dados de TODAS as impressoras
resultado_global = {
    'impressoras': {}
}

# Dicionário para rastrear impressões do dia
rastreamento_dia = {}

# Inicializar com todas as impressoras da configuração
for config in IMPRESSORAS_CONFIG:
    resultado_global['impressoras'][config['id']] = {'online': False}
    rastreamento_dia[config['id']] = {
        'data_lista': None,  # Data do último registro
        'hora_primeiro_registro': None,  # Hora do primeiro registro
        'impressoes_inicio': None,  # Valor inicial de impressões
        'impressoes_dia': 0,  # Contador de impressões do dia
        'registrado_hoje': False  # Flag para saber se já foi registrado hoje
    }

app = Flask(__name__)

# ============================================================================
# FUNÇÕES DE SNMP E COLETA DE DADOS
# ============================================================================

def snmp_get(ip, community, oid, version=0, timeout=2):
    """
    Realiza uma requisição SNMP a uma impressora
    
    Argumentos:
        ip (str): Endereço IP da impressora (ex: 192.168.0.39)
        community (str): String SNMP da comunidade (ex: 'oabce')
        oid (str): Object Identifier SNMP (ex: '1.3.6.1.2.1.1.5.0')
        version (int): Versão SNMP (0=v1, default=0)
        timeout (int): Timeout em segundos (default=2)
    
    Retorna:
        O valor do OID consultado ou None se houver erro
    """
    try:
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
    except:
        return None


def formatar_mac(mac_raw):
    """
    Converte o endereço MAC bruto para o formato padrão (XX:XX:XX:XX:XX:XX)
    
    Argumentos:
        mac_raw: Bytes brutos do MAC recebido via SNMP
    
    Retorna:
        str: MAC formatado em hexadecimal (ex: '00:25:36:E1:50:3B')
        None: Se o valor de entrada é None
    """
    if mac_raw is None:
        return None

    try:
        mac_bytes = bytes(mac_raw)
        return ':'.join(f'{b:02X}' for b in mac_bytes)
    except:
        return str(mac_raw)

def calcular_impressoes_dia(nome_impressora, impressoes_atuais):
    """
    Calcula as impressões do dia com base nas regras:
    - Primeiro registro às 8:00 da manhã
    - Se offline às 8:00, registra quando fica online
    - Atualiza continuamente durante o dia
    - Reseta à meia-noite
    """
    global rastreamento_dia
    
    if impressoes_atuais is None:
        return 0
    
    rastreamento = rastreamento_dia[nome_impressora]
    agora = datetime.now()
    data_hoje = agora.date()
    
    # Verificar se mudou de dia
    if rastreamento['data_lista'] != data_hoje:
        # É um novo dia, resetar o rastreamento
        rastreamento['data_lista'] = data_hoje
        rastreamento['hora_primeiro_registro'] = None
        rastreamento['impressoes_inicio'] = None
        rastreamento['impressoes_dia'] = 0
        rastreamento['registrado_hoje'] = False
    
    # Verificar se precisa fazer o primeiro registro do dia
    if not rastreamento['registrado_hoje']:
        # Verificar se já passou das 8:00 da manhã
        if agora.hour >= 5:
            # É hora de registrar
            rastreamento['hora_primeiro_registro'] = agora.time()
            rastreamento['impressoes_inicio'] = impressoes_atuais
            rastreamento['impressoes_dia'] = 0
            rastreamento['registrado_hoje'] = True
    else:
        # Já foi registrado, calcular a diferença
        rastreamento['impressoes_dia'] = impressoes_atuais - rastreamento['impressoes_inicio']
        # Se for negativo, significa que o contador foi resetado
        if rastreamento['impressoes_dia'] < 0:
            rastreamento['impressoes_dia'] = impressoes_atuais
    
    return rastreamento['impressoes_dia']

def monitorar_impressora(ip, community, nome_impressora):
    """
    Coleta todas as informações de uma impressora via SNMP
    
    Argumentos:
        ip (str): Endereço IP da impressora
        community (str): String SNMP da comunidade
        nome_impressora (str): ID da impressora para rastrear impressões
    
    Retorna:
        dict: Dicionário com dados da impressora (online, nome, série, etc)
              ou dict com online=False se desconectada
    """
    global rastreamento_dia
    
    # OIDs
    OID_UPTIME = '1.3.6.1.2.1.1.3.0'
    OID_NOME = '1.3.6.1.2.1.1.5.0'
    OID_NUM_SERIAL = '1.3.6.1.2.1.43.5.1.1.17.1'
    OID_MODELO = '1.3.6.1.2.1.25.3.2.1.3.1'
    OID_ASSET_NUMBER = '1.3.6.1.4.1.2001.1.1.1.1.11.1.10.40.2.0'
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
    modelo = snmp_get(ip, community, OID_MODELO)
    num_serial = snmp_get(ip, community, OID_NUM_SERIAL)
    asset_number = snmp_get(ip, community, OID_ASSET_NUMBER)
    impressoes = snmp_get(ip, community, OID_IMPRESSOES)
    toner = snmp_get(ip, community, OID_TONER)
    status = snmp_get(ip, community, OID_STATUS)
    scanner = snmp_get(ip, community, OID_SCANNER)
    mac_raw = snmp_get(ip, community, OID_MAC)

    # 🔹 Tratamento
    toner = int(toner) if toner and int(toner) >= 0 else None
    impressoes = int(impressoes) if impressoes else None
    
    # 🔹 Calcular impressões do dia com as regras específicas
    impressoes_dia = calcular_impressoes_dia(nome_impressora, impressoes)

    mac = formatar_mac(mac_raw)

    return {
        "online": True,
        "ip": ip,
        "nome": str(nome),
        "num_serie": str(num_serial),
        "modelo": str(modelo),
        "asset_number": str(asset_number),
        "impressoes": impressoes,
        "impressoes_dia": impressoes_dia,
        "toner": f'{toner}%',
        "status": str(status),
        "uptime": f"{days} Dias / {hours} Horas / {minutes} Minutos",
        "scanner": str(scanner), 
        "mac": mac

    }

def monitor_loop(ip, community, nome_impressora):
    global resultado_global
    while True:
        dados = monitorar_impressora(ip, community, nome_impressora)
        resultado_global['impressoras'][nome_impressora] = dados
        
        # Limpar terminal (Windows: cls, Linux/Mac: clear)
        try:
            if os.name == 'nt':
                subprocess.run('cls', shell=True)
            else:
                subprocess.run('clear', shell=True)
        except:
            pass
        
        # Exibir resumo limpo
        print("\n" + "="*80)
        print("🖨️  MONITOR DE IMPRESSORAS - OAB CE")
        print("="*80 + "\n")
        
        # Exibir status de todas as impressoras
        for nome, dados_impressora in resultado_global['impressoras'].items():
            status_icon = "✅ ONLINE" if dados_impressora.get('online') else "❌ OFFLINE"
            nome_imp = dados_impressora.get('nome', 'Desconhecida')
            toner = dados_impressora.get('toner', 'N/A')
            impressoes = dados_impressora.get('impressoes', 'N/A')
            impressoes_dia = dados_impressora.get('impressoes_dia', 0)
            mac = dados_impressora.get('mac', 'N/A')
            
            print(f"{status_icon} | {nome_imp}")
            print(f"   📊 Impressões Total: {impressoes:,}  |  📈 Hoje: {impressoes_dia:,}  |  🎨 Toner: {toner}  |  🔗 MAC: {mac}")
            if dados_impressora.get('online'):
                uptime = dados_impressora.get('uptime', 'N/A')
                print(f"   ⏱️  Uptime: {uptime}")
            else:
                print(f"   ⚠️  Erro: {dados_impressora.get('erro', 'Desconhecido')}")
            print()
        
        print("="*80)
        print(f"⏰ Última atualização: {time.strftime('%H:%M:%S')}")
        print("="*80 + "\n")
        
        time.sleep(5)

# inicia thread
for config in IMPRESSORAS_CONFIG:
    thread = threading.Thread(
        target=monitor_loop,
        args=(config['ip'], config['community'], config['id']),
        daemon=True,
        name=f"Monitor-{config['id']}"
    )
    thread.start()
    print(f"✅ Thread iniciada para: {config['id']} ({config['ip']})")

# 🌐 API
@app.route("/api")
def api():
    return jsonify(resultado_global)


# 🖥️ Interface Web
@app.route("/")
def home():
    return render_template('index.html')

# 🖥️ Loop principal: só exibe
if __name__ == "__main__":
    app.run(debug=True)