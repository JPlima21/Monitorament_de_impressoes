import threading
import time
import traceback
from datetime import datetime

from config import (
    PRINTER_CACHE_PERSIST_INTERVAL_SECONDS,
    SNMP_OIDS,
    SNMP_STABLE_REFRESH_INTERVAL_SECONDS,
)
from services.historico_service import carregar_cache_switches, salvar_cache_switch
from services.snmp_service import formatar_mac, snmp_get


class SwitchMonitorService:
    def __init__(
        self,
        switch_configs,
        historico_db_file,
        monitor_interval=5,
        cache_persist_interval=PRINTER_CACHE_PERSIST_INTERVAL_SECONDS,
        snmp_stable_refresh_interval=SNMP_STABLE_REFRESH_INTERVAL_SECONDS,
    ):
        self.switch_configs = switch_configs
        self.historico_db_file = historico_db_file
        self.monitor_interval = monitor_interval
        self.cache_persist_interval = max(int(cache_persist_interval), 1)
        self.snmp_stable_refresh_interval = max(int(snmp_stable_refresh_interval), 1)

        self._lock = threading.Lock()
        self._threads_started = False
        self._threads_por_switch = {}
        self.resultado_global = {"switches": {}}
        self.cache_switches = carregar_cache_switches(self.historico_db_file)
        self._ultimo_payload_cache = {}
        self._ultima_persistencia_cache = {}
        self._ultima_atualizacao_snmp_estavel = {}

        self._inicializar_estado()

    def _inicializar_estado(self):
        for config in self.switch_configs:
            switch_id = config["id"]
            self.resultado_global["switches"][switch_id] = {"online": False, "ip": config["ip"]}

    def _deve_persistir(self, switch_id, payload, force=False):
        if force:
            return True

        ultimo_payload = self._ultimo_payload_cache.get(switch_id)
        if ultimo_payload is None:
            return True

        if payload == ultimo_payload:
            return False

        ultimo_instante = self._ultima_persistencia_cache.get(switch_id, 0.0)
        return (time.monotonic() - ultimo_instante) >= self.cache_persist_interval

    def _registrar_persistencia(self, switch_id, payload):
        self._ultimo_payload_cache[switch_id] = payload
        self._ultima_persistencia_cache[switch_id] = time.monotonic()

    def _deve_atualizar_dados_estaveis_snmp(self, switch_id):
        ultimo_instante = self._ultima_atualizacao_snmp_estavel.get(switch_id)
        if ultimo_instante is None:
            return True

        return (time.monotonic() - ultimo_instante) >= self.snmp_stable_refresh_interval

    def _formatar_uptime(self, uptime_ticks):
        seconds = int(uptime_ticks // 100)
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        return f"{days} Dias / {hours} Horas / {minutes} Minutos"

    def _normalizar_status_porta(self, valor):
        mapa = {
            1: "Up",
            2: "Down",
            3: "Testing",
            4: "Unknown",
            5: "Dormant",
            6: "Not Present",
            7: "Lower Layer Down",
        }

        try:
            return mapa.get(int(valor), str(valor))
        except (TypeError, ValueError):
            return "N/A"

    def _normalizar_texto_snmp(self, valor, fallback=None):
        if valor is None:
            return fallback

        texto = str(valor).strip()
        if not texto or texto.lower() == "none":
            return fallback

        return texto

    def _obter_dados_estaveis_switch(self, ip, community, switch_id):
        cache_atual = dict(self.cache_switches.get(switch_id, {}))

        if self._deve_atualizar_dados_estaveis_snmp(switch_id):
            cache_atual.update(
                {
                    "nome": self._normalizar_texto_snmp(
                        snmp_get(ip, community, SNMP_OIDS["nome"])
                    ),
                    "descricao": self._normalizar_texto_snmp(
                        snmp_get(ip, community, SNMP_OIDS["descricao_sistema"])
                    ),
                    "location": self._normalizar_texto_snmp(
                        snmp_get(ip, community, SNMP_OIDS["location"])
                    ),
                    "contato": self._normalizar_texto_snmp(
                        snmp_get(ip, community, SNMP_OIDS["contato"])
                    ),
                    "mac": formatar_mac(snmp_get(ip, community, SNMP_OIDS["mac"])),
                }
            )
            self._ultima_atualizacao_snmp_estavel[switch_id] = time.monotonic()

        return {
            "nome": cache_atual.get("nome") or switch_id,
            "descricao": cache_atual.get("descricao") or "N/A",
            "location": cache_atual.get("location") or "N/A",
            "contato": cache_atual.get("contato") or "N/A",
            "mac": cache_atual.get("mac") or "N/A",
        }

    def _persistir_cache_switch(self, switch_id, dados_cache, force=False):
        self.cache_switches[switch_id] = dados_cache
        payload = (
            dados_cache.get("ip"),
            dados_cache.get("nome"),
            dados_cache.get("descricao"),
            dados_cache.get("location"),
            dados_cache.get("contato"),
            dados_cache.get("uptime"),
            dados_cache.get("mac"),
            dados_cache.get("interfaces_total"),
            dados_cache.get("status_porta_principal"),
        )

        if not self._deve_persistir(switch_id, payload, force=force):
            return

        salvar_cache_switch(self.historico_db_file, switch_id, dados_cache)
        self._registrar_persistencia(switch_id, payload)

    def start(self):
        with self._lock:
            if self._threads_started:
                return

            for config in self.switch_configs:
                thread = threading.Thread(
                    target=self._monitor_loop,
                    args=(config["ip"], config["community"], config["id"]),
                    daemon=True,
                    name=f"SwitchMonitor-{config['id']}",
                )
                thread.start()
                self._threads_por_switch[config["id"]] = thread
                print(f"Thread de switch iniciada para: {config['id']} ({config['ip']})")

            self._threads_started = True

    def add_switch(self, config):
        with self._lock:
            switch_id = str(config.get("id") or "").strip()
            ip = str(config.get("ip") or "").strip()
            community = str(config.get("community") or "").strip()

            if not switch_id:
                raise ValueError("O novo switch precisa de um identificador.")
            if not ip:
                raise ValueError("O novo switch precisa de um IP.")
            if not community:
                raise ValueError("O novo switch precisa de uma community SNMP.")

            if any(str(switch.get("id") or "").lower() == switch_id.lower() for switch in self.switch_configs):
                raise RuntimeError(f"O switch '{switch_id}' ja esta cadastrado.")

            if any(str(switch.get("ip") or "").strip() == ip for switch in self.switch_configs):
                raise RuntimeError(f"Ja existe um switch cadastrado com o IP {ip}.")

            self.switch_configs.append(
                {
                    "id": switch_id,
                    "ip": ip,
                    "community": community,
                }
            )
            self.resultado_global["switches"][switch_id] = {
                "online": False,
                "ip": ip,
                "nome": switch_id,
            }

            if self._threads_started:
                thread = threading.Thread(
                    target=self._monitor_loop,
                    args=(ip, community, switch_id),
                    daemon=True,
                    name=f"SwitchMonitor-{switch_id}",
                )
                thread.start()
                self._threads_por_switch[switch_id] = thread
                print(f"Thread de switch iniciada para: {switch_id} ({ip})")

    def get_resultado(self):
        with self._lock:
            return {
                "switches": {
                    nome: dados.copy()
                    for nome, dados in self.resultado_global["switches"].items()
                }
            }

    def get_switches_resumo(self):
        with self._lock:
            linhas = []

            for config in self.switch_configs:
                switch_id = config["id"]
                dados_atuais = self.resultado_global["switches"].get(switch_id, {})
                dados_cache = self.cache_switches.get(switch_id, {})

                linhas.append(
                    {
                        "id": switch_id,
                        "nome": dados_atuais.get("nome") or dados_cache.get("nome") or switch_id,
                        "online": bool(dados_atuais.get("online")),
                        "ip": dados_atuais.get("ip") or dados_cache.get("ip") or config.get("ip"),
                        "community": config.get("community"),
                        "descricao": dados_atuais.get("descricao") or dados_cache.get("descricao"),
                        "location": dados_atuais.get("location") or dados_cache.get("location"),
                        "contato": dados_atuais.get("contato") or dados_cache.get("contato"),
                        "uptime": dados_atuais.get("uptime") or dados_cache.get("uptime"),
                        "mac": dados_atuais.get("mac") or dados_cache.get("mac"),
                        "interfaces_total": int(
                            dados_atuais.get("interfaces_total")
                            or dados_cache.get("interfaces_total")
                            or 0
                        ),
                        "status_porta_principal": (
                            dados_atuais.get("status_porta_principal")
                            or dados_cache.get("status_porta_principal")
                        ),
                    }
                )

            return linhas

    def _montar_status_offline(self, switch_id, ip):
        dados_cache = self.cache_switches.get(switch_id, {})

        return {
            "online": False,
            "ip": dados_cache.get("ip") or ip,
            "nome": dados_cache.get("nome") or switch_id,
            "descricao": dados_cache.get("descricao") or "N/A",
            "location": dados_cache.get("location") or "N/A",
            "contato": dados_cache.get("contato") or "N/A",
            "uptime": dados_cache.get("uptime") or "N/A",
            "mac": dados_cache.get("mac") or "N/A",
            "interfaces_total": int(dados_cache.get("interfaces_total") or 0),
            "status_porta_principal": dados_cache.get("status_porta_principal") or "N/A",
            "erro": "Sem resposta SNMP",
        }

    def _monitorar_switch(self, ip, community, switch_id):
        uptime = snmp_get(ip, community, SNMP_OIDS["uptime"])

        if uptime is None:
            return self._montar_status_offline(switch_id, ip)

        dados_estaveis = self._obter_dados_estaveis_switch(ip, community, switch_id)
        interfaces_total = snmp_get(ip, community, SNMP_OIDS["interfaces_total"])
        status_porta_principal = snmp_get(ip, community, SNMP_OIDS["status_porta_principal"])

        interfaces_total = int(interfaces_total) if interfaces_total is not None else 0
        uptime_formatado = self._formatar_uptime(int(uptime))
        status_porta_principal = self._normalizar_status_porta(status_porta_principal)

        with self._lock:
            self._persistir_cache_switch(
                switch_id,
                {
                    "ip": ip,
                    "nome": dados_estaveis["nome"],
                    "descricao": dados_estaveis["descricao"],
                    "location": dados_estaveis["location"],
                    "contato": dados_estaveis["contato"],
                    "uptime": uptime_formatado,
                    "mac": dados_estaveis["mac"],
                    "interfaces_total": interfaces_total,
                    "status_porta_principal": status_porta_principal,
                    "atualizado_em": str(datetime.now()),
                },
            )

        return {
            "online": True,
            "ip": ip,
            "nome": dados_estaveis["nome"],
            "descricao": dados_estaveis["descricao"],
            "location": dados_estaveis["location"],
            "contato": dados_estaveis["contato"],
            "uptime": uptime_formatado,
            "mac": dados_estaveis["mac"],
            "interfaces_total": interfaces_total,
            "status_porta_principal": status_porta_principal,
        }

    def _monitor_loop(self, ip, community, switch_id):
        while True:
            try:
                dados = self._monitorar_switch(ip, community, switch_id)
            except Exception as exc:
                print(f"Erro no monitoramento do switch {switch_id}: {exc}")
                print(traceback.format_exc())
                dados = {
                    **self._montar_status_offline(switch_id, ip),
                    "erro": f"Falha interna: {exc}",
                }

            with self._lock:
                self.resultado_global["switches"][switch_id] = dados

            time.sleep(self.monitor_interval)
