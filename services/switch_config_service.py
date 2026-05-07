from services.historico_service import (
    carregar_configs_switches,
    garantir_configs_switches_iniciais,
    salvar_config_switch,
)


class SwitchConfigService:
    def __init__(self, caminho_banco, default_configs):
        self.caminho_banco = caminho_banco
        self.default_configs = [self._normalizar_config(config) for config in default_configs]
        garantir_configs_switches_iniciais(self.caminho_banco, self.default_configs)

    def _normalizar_config(self, config):
        return {
            "id": str(config.get("id") or "").strip(),
            "ip": str(config.get("ip") or "").strip(),
            "community": str(config.get("community") or "").strip(),
        }

    def _validar_config(self, config, configs_existentes=None):
        if not config["id"]:
            raise ValueError("Informe um identificador para o switch.")
        if not config["ip"]:
            raise ValueError("Informe o IP do switch.")
        if not config["community"]:
            raise ValueError("Informe a community SNMP do switch.")

        existentes = configs_existentes or []
        for existente in existentes:
            if existente["id"].lower() == config["id"].lower():
                raise ValueError(f"Ja existe um switch com o identificador '{config['id']}'.")
            if existente["ip"] == config["ip"]:
                raise ValueError(f"Ja existe um switch cadastrado com o IP {config['ip']}.")

    def _gerar_proximo_id(self, configs):
        indice = 1
        ids_existentes = {str(config.get("id") or "").lower() for config in configs}

        while f"switch{indice}" in ids_existentes:
            indice += 1

        return f"switch{indice}"

    def list_configs(self):
        return carregar_configs_switches(self.caminho_banco)

    def preparar_nova_config(self, dados):
        configs = self.list_configs()
        config = self._normalizar_config(dados)

        if not config["id"]:
            config["id"] = self._gerar_proximo_id(configs)

        self._validar_config(config, configs_existentes=configs)
        return config

    def add_config(self, dados):
        config = self.preparar_nova_config(dados)
        return self.save_config(config)

    def save_config(self, config):
        configs = self.list_configs()
        config_normalizada = self._normalizar_config(config)
        self._validar_config(config_normalizada, configs_existentes=configs)
        salvar_config_switch(self.caminho_banco, config_normalizada)
        return dict(config_normalizada)
