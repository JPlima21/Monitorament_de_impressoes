import threading
import time
from datetime import datetime

from config import SNMP_OIDS
from services.historico_service import carregar_historico, salvar_historico
from services.snmp_service import formatar_mac, snmp_get


class PrinterMonitorService:
    def __init__(self, printer_configs, historico_file, monitor_interval=5):
        self.printer_configs = printer_configs
        self.historico_file = historico_file
        self.monitor_interval = monitor_interval

        self._lock = threading.Lock()
        self._threads_started = False
        self.resultado_global = {"impressoras": {}}
        self.rastreamento_dia = {}
        self.historico_impressoes = carregar_historico(self.historico_file)

        salvar_historico(self.historico_file, self.historico_impressoes)
        self._inicializar_estado()

    def _inicializar_estado(self):
        for config in self.printer_configs:
            impressora_id = config["id"]
            self.resultado_global["impressoras"][impressora_id] = {"online": False}
            self.rastreamento_dia[impressora_id] = self._criar_rastreamento_inicial()

    def _criar_rastreamento_inicial(self):
        return {
            "data_lista": None,
            "hora_primeiro_registro": None,
            "impressoes_inicio": None,
            "impressoes_acumuladas": 0,
            "impressoes_dia": 0,
            "registrado_hoje": False,
        }

    # inicia as threads de monitoramento
    def start(self):
        with self._lock:
            if self._threads_started:
                return

            for config in self.printer_configs:
                thread = threading.Thread(
                    target=self._monitor_loop,
                    args=(config["ip"], config["community"], config["id"]),
                    daemon=True,
                    name=f"Monitor-{config['id']}",
                )
                thread.start()
                print(f"Thread iniciada para: {config['id']} ({config['ip']})")

            self._threads_started = True
    
    # devolve os dados atuais para /api
    def get_resultado(self):
        with self._lock:
            return {
                "impressoras": {
                    nome: dados.copy()
                    for nome, dados in self.resultado_global["impressoras"].items()
                }
            }
    
    # devolve histórico de impressões para /api/historico
    def get_historico(self):
        with self._lock:
            return dict(self.historico_impressoes)

    # método antigo, mantido para referência
    def _obter_total_rastreamento(self, rastreamento):
        acumuladas = int(rastreamento.get("impressoes_acumuladas", 0) or 0)
        atual = int(rastreamento.get("impressoes_dia", 0) or 0)
        return acumuladas + atual
    
    # método atualizado, que considera o caso de impressões diárias acumuladas
    def _salvar_impressoes_dia(self, nome_impressora, rastreamento, motivo="fechamento_dia"):
        if not rastreamento["data_lista"] or rastreamento["impressoes_dia"] is None:
            return

        data_str = str(rastreamento["data_lista"])
        timestamp = datetime.now().strftime("%H%M%S")
        chave = f"{nome_impressora}_{data_str}_{motivo}_{timestamp}"
        total_consolidado = self._obter_total_rastreamento(rastreamento)

        self.historico_impressoes[chave] = {
            "impressora": nome_impressora,
            "data": data_str,
            "hora_inicio": (
                str(rastreamento["hora_primeiro_registro"])
                if rastreamento["hora_primeiro_registro"]
                else "N/A"
            ),
            "impressoes_total": total_consolidado,
            "motivo": motivo,
            "timestamp_salvo": str(datetime.now()),
        }

        salvar_historico(self.historico_file, self.historico_impressoes)

    # calcula impressões do dia, considerando reinício do contador e acumulados
    def _calcular_impressoes_dia(self, nome_impressora, impressoes_atuais):
        if impressoes_atuais is None:
            return 0

        rastreamento = self.rastreamento_dia[nome_impressora]
        agora = datetime.now()
        data_hoje = agora.date()

        if rastreamento["data_lista"] is None:
            rastreamento["data_lista"] = data_hoje
            rastreamento["hora_primeiro_registro"] = agora.time()
            rastreamento["impressoes_inicio"] = impressoes_atuais
            rastreamento["registrado_hoje"] = True
            return 0

        if rastreamento["data_lista"] != data_hoje:
            self._salvar_impressoes_dia(nome_impressora, rastreamento)
            rastreamento["data_lista"] = data_hoje
            rastreamento["hora_primeiro_registro"] = agora.time()
            rastreamento["impressoes_inicio"] = impressoes_atuais
            rastreamento["impressoes_acumuladas"] = 0
            rastreamento["impressoes_dia"] = 0
            rastreamento["registrado_hoje"] = True
            return 0

        if rastreamento["impressoes_inicio"] is not None:
            total = impressoes_atuais - rastreamento["impressoes_inicio"]

            if total < 0:
                total_anterior = int(rastreamento.get("impressoes_dia", 0) or 0)

                if total_anterior > 0:
                    rastreamento["impressoes_acumuladas"] += total_anterior
                    self._salvar_impressoes_dia(
                        nome_impressora,
                        rastreamento,
                        motivo="reset_contador",
                    )

                rastreamento["impressoes_inicio"] = impressoes_atuais
                rastreamento["impressoes_dia"] = 0
                total = impressoes_atuais

            rastreamento["impressoes_dia"] = total

        return self._obter_total_rastreamento(rastreamento)

    # método que monta o status offline, para evitar repetição de código
    def _montar_status_offline(self):
        return {
            "online": False,
            "erro": "Sem resposta SNMP",
        }

    # método que monitora a impressora e coleta os dados via SNMP
    def _monitorar_impressora(self, ip, community, nome_impressora):
        uptime = snmp_get(ip, community, SNMP_OIDS["uptime"])

        if uptime is None:
            return self._montar_status_offline()

        uptime_ticks = int(uptime)
        seconds = int(uptime_ticks // 100)
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60

        nome = snmp_get(ip, community, SNMP_OIDS["nome"])
        modelo = snmp_get(ip, community, SNMP_OIDS["modelo"])
        num_serial = snmp_get(ip, community, SNMP_OIDS["serial"])
        asset_number = snmp_get(ip, community, SNMP_OIDS["asset_number"])
        location = snmp_get(ip, community, SNMP_OIDS["location"])
        impressoes = snmp_get(ip, community, SNMP_OIDS["impressoes"])
        toner = snmp_get(ip, community, SNMP_OIDS["toner"])
        status = snmp_get(ip, community, SNMP_OIDS["status"])
        scanner = snmp_get(ip, community, SNMP_OIDS["scanner"])
        mac_raw = snmp_get(ip, community, SNMP_OIDS["mac"])

        toner = int(toner) if toner and int(toner) >= 0 else None
        impressoes = int(impressoes) if impressoes else None

        with self._lock:
            impressoes_dia = self._calcular_impressoes_dia(nome_impressora, impressoes)

        return {
            "online": True,
            "ip": ip,
            "nome": str(nome),
            "num_serie": str(num_serial),
            "modelo": str(modelo),
            "asset_number": str(asset_number),
            "location": str(location),
            "impressoes": impressoes,
            "impressoes_dia": impressoes_dia,
            "toner": f"{toner}%" if toner is not None else "N/A",
            "status": str(status),
            "uptime": f"{days} Dias / {hours} Horas / {minutes} Minutos",
            "scanner": str(scanner),
            "mac": formatar_mac(mac_raw),
        }

    # loop principal de monitoramento, que chama o método de coleta e atualiza o resultado global
    def _monitor_loop(self, ip, community, nome_impressora):
        while True:
            dados = self._monitorar_impressora(ip, community, nome_impressora)

            with self._lock:
                self.resultado_global["impressoras"][nome_impressora] = dados

            time.sleep(self.monitor_interval)
