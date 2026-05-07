from flask import Blueprint, jsonify, request


def create_api_blueprint(
    monitor_service,
    printer_config_service,
    switch_monitor_service=None,
    switch_config_service=None,
):
    api_bp = Blueprint("api", __name__)

    def formatar_moeda_centavos(valor_centavos):
        return f"R$ {int(valor_centavos or 0) / 100:.2f}".replace(".", ",")

    def montar_lista_impressoras():
        resumo_por_id = {
            impressora["id"]: impressora
            for impressora in monitor_service.get_impressoras_resumo()
        }
        linhas = []

        for config in printer_config_service.list_configs():
            resumo = resumo_por_id.get(config["id"], {})
            linhas.append(
                {
                    "id": config["id"],
                    "ip": config["ip"],
                    "community": config["community"],
                    "token_valor_centavos": int(config.get("token_valor_centavos", 4) or 4),
                    "token_valor_formatado": formatar_moeda_centavos(
                        config.get("token_valor_centavos", 4)
                    ),
                    "nome": resumo.get("nome") or config["id"],
                    "online": bool(resumo.get("online")),
                    "modelo": resumo.get("modelo"),
                    "location": resumo.get("location"),
                    "custo_estimado_dia_centavos": int(resumo.get("custo_estimado_dia_centavos") or 0),
                    "custo_estimado_dia_formatado": formatar_moeda_centavos(
                        resumo.get("custo_estimado_dia_centavos") or 0
                    ),
                    "custo_estimado_mes_centavos": int(resumo.get("custo_estimado_mes_centavos") or 0),
                    "custo_estimado_mes_formatado": formatar_moeda_centavos(
                        resumo.get("custo_estimado_mes_centavos") or 0
                    ),
                }
            )

        return linhas

    def montar_lista_switches():
        if not switch_config_service or not switch_monitor_service:
            return []

        resumo_por_id = {
            switch["id"]: switch
            for switch in switch_monitor_service.get_switches_resumo()
        }
        linhas = []

        for config in switch_config_service.list_configs():
            resumo = resumo_por_id.get(config["id"], {})
            linhas.append(
                {
                    "id": config["id"],
                    "ip": config["ip"],
                    "community": config["community"],
                    "nome": resumo.get("nome") or config["id"],
                    "online": bool(resumo.get("online")),
                    "descricao": resumo.get("descricao"),
                    "location": resumo.get("location"),
                    "contato": resumo.get("contato"),
                    "uptime": resumo.get("uptime"),
                    "mac": resumo.get("mac"),
                    "interfaces_total": int(resumo.get("interfaces_total") or 0),
                    "status_porta_principal": resumo.get("status_porta_principal"),
                }
            )

        return linhas

    @api_bp.route("/api")
    def api():
        payload = monitor_service.get_resultado()

        if switch_monitor_service:
            payload.update(switch_monitor_service.get_resultado())

        return jsonify(payload)

    @api_bp.route("/api/impressoras")
    def api_impressoras():
        return jsonify(montar_lista_impressoras())

    @api_bp.route("/api/impressoras", methods=["POST"])
    def api_adicionar_impressora():
        dados = request.get_json(silent=True) or {}

        try:
            nova_config = printer_config_service.preparar_nova_config(dados)
            monitor_service.add_printer(nova_config)
            printer_config_service.save_config(nova_config)
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 400
        except RuntimeError as exc:
            return jsonify({"erro": str(exc)}), 409

        return (
            jsonify(
                {
                    "mensagem": "Impressora adicionada com sucesso.",
                    "impressora": {
                        **nova_config,
                        "nome": nova_config["id"],
                        "online": False,
                        "token_valor_formatado": formatar_moeda_centavos(
                            nova_config.get("token_valor_centavos", 4)
                        ),
                    },
                }
            ),
            201,
        )

    @api_bp.route("/api/switches")
    def api_switches():
        return jsonify(montar_lista_switches())

    @api_bp.route("/api/switches", methods=["POST"])
    def api_adicionar_switch():
        if not switch_config_service or not switch_monitor_service:
            return jsonify({"erro": "Monitoramento de switches nao esta habilitado."}), 503

        dados = request.get_json(silent=True) or {}

        try:
            nova_config = switch_config_service.preparar_nova_config(dados)
            switch_monitor_service.add_switch(nova_config)
            switch_config_service.save_config(nova_config)
        except ValueError as exc:
            return jsonify({"erro": str(exc)}), 400
        except RuntimeError as exc:
            return jsonify({"erro": str(exc)}), 409

        return (
            jsonify(
                {
                    "mensagem": "Switch adicionado com sucesso.",
                    "switch": {
                        **nova_config,
                        "nome": nova_config["id"],
                        "online": False,
                    },
                }
            ),
            201,
        )

    @api_bp.route("/api/historico")
    def api_historico():
        return jsonify(monitor_service.get_historico())

    @api_bp.route("/api/debug/historico")
    def api_debug_historico():
        return jsonify(monitor_service.get_debug_info())

    @api_bp.route("/api/debug/forcar-historico")
    def api_debug_forcar_historico():
        salvos = monitor_service.forcar_salvamento_historico()
        return jsonify(
            {
                "salvos": salvos,
                "quantidade": len(salvos),
            }
        )

    @api_bp.route("/api/powerbi/impressoras")
    def api_powerbi_impressoras():
        return jsonify(monitor_service.get_impressoras_resumo())

    @api_bp.route("/api/powerbi/historico")
    def api_powerbi_historico():
        historico = monitor_service.get_historico()
        nomes_impressoras = monitor_service.get_mapa_nomes_impressoras()
        linhas = []

        for chave, registro in historico.items():
            impressora_id = registro.get("impressora")
            linhas.append(
                {
                    "chave": chave,
                    "impressora": impressora_id,
                    "impressora_nome": nomes_impressoras.get(impressora_id, impressora_id),
                    "data": registro.get("data"),
                    "hora_inicio": registro.get("hora_inicio"),
                    "impressoes_total_dia": int(registro.get("impressoes_total_dia") or 0),
                    "motivo": registro.get("motivo"),
                    "timestamp_salvo": registro.get("timestamp_salvo"),
                }
            )

        return jsonify(linhas)

    return api_bp
