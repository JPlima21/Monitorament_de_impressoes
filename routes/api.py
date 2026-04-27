from flask import Blueprint, jsonify


def create_api_blueprint(monitor_service):
    api_bp = Blueprint("api", __name__)

    @api_bp.route("/api")
    def api():
        return jsonify(monitor_service.get_resultado())

    @api_bp.route("/api/historico")
    def api_historico():
        return jsonify(monitor_service.get_historico())

    @api_bp.route("/api/powerbi/impressoras")
    def api_powerbi_impressoras():
        resultado = monitor_service.get_resultado()
        linhas = []

        for impressora_id, dados in resultado.get("impressoras", {}).items():
            linhas.append(
                {
                    "id": impressora_id,
                    "nome": dados.get("nome") or impressora_id,
                    "online": bool(dados.get("online")),
                    "ip": dados.get("ip"),
                    "modelo": dados.get("modelo"),
                    "total_impressoes": int(dados.get("total_impressoes") or 0),
                    "impressoes_dia": int(dados.get("impressoes_dia") or 0),
                    "impressoes_mes": int(dados.get("impressoes_mes") or 0),
                    "copias": int(dados.get("copias") or 0),
                    "scanner": dados.get("scanner"),
                    "toner": dados.get("toner"),
                    "location": dados.get("location"),
                }
            )

        return jsonify(linhas)

    @api_bp.route("/api/powerbi/historico")
    def api_powerbi_historico():
        historico = monitor_service.get_historico()
        linhas = []

        for chave, registro in historico.items():
            linhas.append(
                {
                    "chave": chave,
                    "impressora": registro.get("impressora"),
                    "data": registro.get("data"),
                    "hora_inicio": registro.get("hora_inicio"),
                    "impressoes_total_dia": int(registro.get("impressoes_total_dia") or 0),
                    "motivo": registro.get("motivo"),
                    "timestamp_salvo": registro.get("timestamp_salvo"),
                }
            )

        return jsonify(linhas)

    return api_bp
