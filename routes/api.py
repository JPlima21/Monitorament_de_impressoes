from flask import Blueprint, jsonify


def create_api_blueprint(monitor_service):
    api_bp = Blueprint("api", __name__)

    @api_bp.route("/api")
    def api():
        return jsonify(monitor_service.get_resultado())

    @api_bp.route("/api/historico")
    def api_historico():
        return jsonify(monitor_service.get_historico())

    return api_bp
