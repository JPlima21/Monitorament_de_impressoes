import threading
import time
from datetime import date, datetime, time as time_type

from config import SNMP_OIDS
from services.historico_service import (
    carregar_cache_impressoras,
    carregar_cache_rastreamento_diario_atual,
    carregar_historico,
    carregar_rastreamento_mensal,
    salvar_cache_impressora,
    salvar_cache_rastreamento_diario,
    salvar_registro_historico,
    salvar_rastreamento_mensal,
)
from services.snmp_service import formatar_mac, snmp_get

''' serviço principal de monitoramento das impressoras, 
responsável por coletar os dados via SNMP, 
calcular as impressões diárias e manter o histórico atualizado'''
class PrinterMonitorService:
    def __init__(
        self,
        printer_configs,
        historico_db_file,
        monitor_interval=5,
    ):
        self.printer_configs = printer_configs # lista de dicionários com id, ip e community
        self.historico_db_file = historico_db_file # caminho para o banco de dados SQLite onde o histórico é armazenado
        self.monitor_interval = monitor_interval # intervalo em segundos entre cada coleta de dados

        self._lock = threading.Lock()
        self._threads_started = False
        self.resultado_global = {"impressoras": {}}
        self.cache_rastreamento_dia = {}
        self.rastreamento_mes = {}
        self.data_cache_diario = datetime.now().date()
        self.cache_impressoras = carregar_cache_impressoras(self.historico_db_file)
        self.historico_impressoes = carregar_historico(self.historico_db_file)
        self.cache_rastreamento_dia_persistido = carregar_cache_rastreamento_diario_atual(
            self.historico_db_file,
            self.data_cache_diario,
        )
        self.rastreamento_mes_persistido = carregar_rastreamento_mensal(self.historico_db_file)

        self._inicializar_estado()

    # inicializa o estado para cada impressora, garantindo que a estrutura de rastreamento diário esteja pronta
    def _inicializar_estado(self):
        for config in self.printer_configs:
            impressora_id = config["id"]
            self.resultado_global["impressoras"][impressora_id] = {"online": False}
            cache_rastreamento = self._criar_cache_rastreamento_dia_inicial()
            cache_rastreamento_persistido = self.cache_rastreamento_dia_persistido.get(impressora_id)
            rastreamento_mensal = self._criar_rastreamento_mensal_inicial()
            rastreamento_mensal_persistido = self.rastreamento_mes_persistido.get(impressora_id)

            if cache_rastreamento_persistido:
                cache_rastreamento.update(
                    self._normalizar_cache_rastreamento_dia_persistido(cache_rastreamento_persistido)
                )
            if rastreamento_mensal_persistido:
                rastreamento_mensal.update(
                    self._normalizar_rastreamento_mensal_persistido(rastreamento_mensal_persistido)
                )

            self.cache_rastreamento_dia[impressora_id] = cache_rastreamento
            self.rastreamento_mes[impressora_id] = rastreamento_mensal
 
    # cria o estado inicial para o cache do rastreamento diário
    def _criar_cache_rastreamento_dia_inicial(self):
        return {
            "data_lista": None,
            "hora_primeiro_registro": None,
            "impressoes_inicio": None,
            "impressoes_acumuladas": 0,
            "impressoes_dia": 0,
            "registrado_hoje": False,
        }

    def _criar_rastreamento_mensal_inicial(self):
        return {
            "mes_referencia": None,
            "impressoes_inicio": None,
            "impressoes_acumuladas": 0,
            "impressoes_mes": 0,
            "registrado_mes": False,
        }

    def _normalizar_cache_rastreamento_dia_persistido(self, rastreamento):
        return {
            "data_lista": self._parse_data(rastreamento.get("data_lista")),
            "hora_primeiro_registro": self._parse_hora(rastreamento.get("hora_primeiro_registro")),
            "impressoes_inicio": rastreamento.get("impressoes_inicio"),
            "impressoes_acumuladas": int(rastreamento.get("impressoes_acumuladas", 0) or 0),
            "impressoes_dia": int(rastreamento.get("impressoes_dia", 0) or 0),
            "registrado_hoje": bool(rastreamento.get("registrado_hoje")),
        }

    def _normalizar_rastreamento_mensal_persistido(self, rastreamento):
        return {
            "mes_referencia": rastreamento.get("mes_referencia"),
            "impressoes_inicio": rastreamento.get("impressoes_inicio"),
            "impressoes_acumuladas": int(rastreamento.get("impressoes_acumuladas", 0) or 0),
            "impressoes_mes": int(rastreamento.get("impressoes_mes", 0) or 0),
            "registrado_mes": bool(rastreamento.get("registrado_mes")),
        }

    def _parse_data(self, valor):
        if not valor:
            return None

        try:
            return date.fromisoformat(str(valor))
        except ValueError:
            return None

    def _parse_hora(self, valor):
        if not valor:
            return None

        try:
            return time_type.fromisoformat(str(valor))
        except ValueError:
            return None

    def _salvar_cache_rastreamento_dia(self, nome_impressora):
        rastreamento = self.cache_rastreamento_dia[nome_impressora]
        salvar_cache_rastreamento_diario(
            self.historico_db_file,
            nome_impressora,
            {
                "data_lista": (
                    rastreamento["data_lista"].isoformat()
                    if rastreamento["data_lista"]
                    else None
                ),
                "hora_primeiro_registro": (
                    rastreamento["hora_primeiro_registro"].isoformat()
                    if rastreamento["hora_primeiro_registro"]
                    else None
                ),
                "impressoes_inicio": rastreamento["impressoes_inicio"],
                "impressoes_acumuladas": rastreamento["impressoes_acumuladas"],
                "impressoes_dia": rastreamento["impressoes_dia"],
                "registrado_hoje": rastreamento["registrado_hoje"],
            },
        )

    def _persistir_rastreamento_mes(self, nome_impressora):
        rastreamento = self.rastreamento_mes[nome_impressora]
        salvar_rastreamento_mensal(
            self.historico_db_file,
            nome_impressora,
            {
                "mes_referencia": rastreamento["mes_referencia"],
                "impressoes_inicio": rastreamento["impressoes_inicio"],
                "impressoes_acumuladas": rastreamento["impressoes_acumuladas"],
                "impressoes_mes": rastreamento["impressoes_mes"],
                "registrado_mes": rastreamento["registrado_mes"],
            },
        )

    def _persistir_cache_impressora(self, nome_impressora, dados_cache):
        self.cache_impressoras[nome_impressora] = dados_cache
        salvar_cache_impressora(self.historico_db_file, nome_impressora, dados_cache)

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
            self.historico_impressoes = carregar_historico(self.historico_db_file)
            return dict(self.historico_impressoes)

    def _obter_total_cache_rastreamento_dia(self, rastreamento):
        acumuladas = int(rastreamento.get("impressoes_acumuladas", 0) or 0)
        atual = int(rastreamento.get("impressoes_dia", 0) or 0)
        return acumuladas + atual

    def _obter_total_rastreamento_mensal(self, rastreamento):
        acumuladas = int(rastreamento.get("impressoes_acumuladas", 0) or 0)
        atual = int(rastreamento.get("impressoes_mes", 0) or 0)
        return acumuladas + atual
    
    # método atualizado, que considera o caso de impressões diárias acumuladas
    def _salvar_impressoes_dia(self, nome_impressora, rastreamento, motivo="fechamento_dia"):
        if not rastreamento["data_lista"] or rastreamento["impressoes_dia"] is None:
            return

        data_str = str(rastreamento["data_lista"])
        timestamp = datetime.now().strftime("%H%M%S")
        chave = f"{nome_impressora}_{data_str}_{motivo}_{timestamp}"
        total_consolidado = self._obter_total_cache_rastreamento_dia(rastreamento)

        registro = {
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
        self.historico_impressoes[chave] = registro

        salvar_registro_historico(self.historico_db_file, chave, registro)

    # calcula impressões do dia, considerando reinício do contador e acumulados
    def _calcular_impressoes_dia(self, nome_impressora, impressoes_atuais):
        if impressoes_atuais is None:
            return 0

        rastreamento = self.cache_rastreamento_dia[nome_impressora]
        agora = datetime.now()
        data_hoje = agora.date()

        if rastreamento["data_lista"] is None:
            rastreamento["data_lista"] = data_hoje
            rastreamento["hora_primeiro_registro"] = agora.time()
            rastreamento["impressoes_inicio"] = impressoes_atuais
            rastreamento["registrado_hoje"] = True
            self._salvar_cache_rastreamento_dia(nome_impressora)
            return 0

        if rastreamento["data_lista"] != data_hoje:
            self._salvar_impressoes_dia(nome_impressora, rastreamento)
            rastreamento["data_lista"] = data_hoje
            rastreamento["hora_primeiro_registro"] = agora.time()
            rastreamento["impressoes_inicio"] = impressoes_atuais
            rastreamento["impressoes_acumuladas"] = 0
            rastreamento["impressoes_dia"] = 0
            rastreamento["registrado_hoje"] = True
            self._salvar_cache_rastreamento_dia(nome_impressora)
            return 0

        if rastreamento["impressoes_inicio"] is None:
            rastreamento["impressoes_inicio"] = impressoes_atuais
            rastreamento["hora_primeiro_registro"] = (
                rastreamento["hora_primeiro_registro"] or agora.time()
            )
            rastreamento["registrado_hoje"] = True
            self._salvar_cache_rastreamento_dia(nome_impressora)
            return self._obter_total_cache_rastreamento_dia(rastreamento)

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
            rastreamento["registrado_hoje"] = True

        self._salvar_cache_rastreamento_dia(nome_impressora)

        return self._obter_total_cache_rastreamento_dia(rastreamento)

    def _calcular_impressoes_mes(self, nome_impressora, impressoes_atuais):
        if impressoes_atuais is None:
            return 0

        rastreamento = self.rastreamento_mes[nome_impressora]
        mes_atual = datetime.now().strftime("%Y-%m")

        if rastreamento["mes_referencia"] is None:
            rastreamento["mes_referencia"] = mes_atual
            rastreamento["impressoes_inicio"] = impressoes_atuais
            rastreamento["registrado_mes"] = True
            self._persistir_rastreamento_mes(nome_impressora)
            return 0

        if rastreamento["mes_referencia"] != mes_atual:
            rastreamento["mes_referencia"] = mes_atual
            rastreamento["impressoes_inicio"] = impressoes_atuais
            rastreamento["impressoes_acumuladas"] = 0
            rastreamento["impressoes_mes"] = 0
            rastreamento["registrado_mes"] = True
            self._persistir_rastreamento_mes(nome_impressora)
            return 0

        if rastreamento["impressoes_inicio"] is None:
            rastreamento["impressoes_inicio"] = impressoes_atuais
            rastreamento["registrado_mes"] = True
            self._persistir_rastreamento_mes(nome_impressora)
            return self._obter_total_rastreamento_mensal(rastreamento)

        total = impressoes_atuais - rastreamento["impressoes_inicio"]

        if total < 0:
            total_anterior = int(rastreamento.get("impressoes_mes", 0) or 0)

            if total_anterior > 0:
                rastreamento["impressoes_acumuladas"] += total_anterior

            rastreamento["impressoes_inicio"] = impressoes_atuais
            rastreamento["impressoes_mes"] = 0
            total = impressoes_atuais

        rastreamento["impressoes_mes"] = total
        rastreamento["registrado_mes"] = True
        self._persistir_rastreamento_mes(nome_impressora)

        return self._obter_total_rastreamento_mensal(rastreamento)

    # método que monta o status offline, para evitar repetição de código
    def _montar_status_offline(self, nome_impressora, ip):
        dados_cache = self.cache_impressoras.get(nome_impressora, {})

        return {
            "online": False,
            "ip": dados_cache.get("ip") or ip,
            "nome": dados_cache.get("nome") or nome_impressora,
            "num_serie": dados_cache.get("num_serie") or "N/A",
            "modelo": dados_cache.get("modelo") or "N/A",
            "asset_number": dados_cache.get("asset_number") or "N/A",
            "location": dados_cache.get("location") or "N/A",
            "uptime": dados_cache.get("uptime") or "N/A",
            "mac": dados_cache.get("mac") or "N/A",
            "erro": "Sem resposta SNMP",
        }

    # método que monitora a impressora e coleta os dados via SNMP
    def _monitorar_impressora(self, ip, community, nome_impressora):
        uptime = snmp_get(ip, community, SNMP_OIDS["uptime"])

        if uptime is None:
            return self._montar_status_offline(nome_impressora, ip)

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
            impressoes_mes = self._calcular_impressoes_mes(nome_impressora, impressoes)

            self._persistir_cache_impressora(
                nome_impressora,
                {
                    "ip": ip,
                    "nome": str(nome),
                    "num_serie": str(num_serial),
                    "modelo": str(modelo),
                    "asset_number": str(asset_number),
                    "location": str(location),
                    "uptime": f"{days} Dias / {hours} Horas / {minutes} Minutos",
                    "mac": formatar_mac(mac_raw),
                    "atualizado_em": str(datetime.now()),
                },
            )

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
            "impressoes_mes": impressoes_mes,
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
