from services.historico_service import (
    carregar_configs_impressoras,
    garantir_configs_impressoras_iniciais,
    salvar_config_impressora,
)


class PrinterConfigService:
    TOKEN_VALORES_PERMITIDOS = {4, 50}

    def __init__(self, caminho_banco, default_configs):
        self.caminho_banco = caminho_banco
        self.default_configs = [self._normalizar_config(config) for config in default_configs]
        garantir_configs_impressoras_iniciais(self.caminho_banco, self.default_configs)

    def _normalizar_token_valor_centavos(self, valor):
        if valor is None or str(valor).strip() == "":
            return 4

        texto = str(valor).strip().replace("R$", "").replace(" ", "")
        texto = texto.replace(",", ".")

        try:
            if "." in texto:
                valor_decimal = round(float(texto) * 100)
            else:
                valor_decimal = int(texto)
        except ValueError as exc:
            raise ValueError("Informe um token valido para a impressora.") from exc

        if valor_decimal not in self.TOKEN_VALORES_PERMITIDOS:
            raise ValueError("Escolha um token valido: R$ 0,04 ou R$ 0,50.")

        return valor_decimal

    def _normalizar_config(self, config):
        return {
            "id": str(config.get("id") or "").strip(),
            "ip": str(config.get("ip") or "").strip(),
            "community": str(config.get("community") or "").strip(),
            "token_valor_centavos": self._normalizar_token_valor_centavos(
                config.get("token_valor_centavos")
            ),
        }

    def _validar_config(self, config, configs_existentes=None):
        if not config["id"]:
            raise ValueError("Informe um identificador para a impressora.")
        if not config["ip"]:
            raise ValueError("Informe o IP da impressora.")
        if not config["community"]:
            raise ValueError("Informe a community SNMP da impressora.")
        if config["token_valor_centavos"] not in self.TOKEN_VALORES_PERMITIDOS:
            raise ValueError("Escolha um token valido: R$ 0,04 ou R$ 0,50.")

        existentes = configs_existentes or []
        for existente in existentes:
            if existente["id"].lower() == config["id"].lower():
                raise ValueError(f"Ja existe uma impressora com o identificador '{config['id']}'.")
            if existente["ip"] == config["ip"]:
                raise ValueError(f"Ja existe uma impressora cadastrada com o IP {config['ip']}.")

    def _gerar_proximo_id(self, configs):
        indice = 1
        ids_existentes = {str(config.get("id") or "").lower() for config in configs}

        while f"impressora{indice}" in ids_existentes:
            indice += 1

        return f"impressora{indice}"

    def list_configs(self):
        return carregar_configs_impressoras(self.caminho_banco)

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
        salvar_config_impressora(self.caminho_banco, config_normalizada)
        return dict(config_normalizada)
