import os

from flask import Flask

from config import (
    HISTORICO_DB_FILE,
    IMPRESSORAS_CONFIG,
    MONITOR_INTERVAL_SECONDS,
)
from routes.api import create_api_blueprint
from routes.web import create_web_blueprint
from services.monitor_service import PrinterMonitorService


def create_app():
    app = Flask(__name__)

    monitor_service = PrinterMonitorService(
        printer_configs=IMPRESSORAS_CONFIG,
        historico_db_file=HISTORICO_DB_FILE,
        monitor_interval=MONITOR_INTERVAL_SECONDS,
    )
    monitor_service.start()

    app.register_blueprint(create_api_blueprint(monitor_service))
    app.register_blueprint(create_web_blueprint())

    return app


app = create_app()


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(debug=debug_mode)
