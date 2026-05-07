from flask import Flask

from config import (
    FLASK_DEBUG,
    FLASK_HOST,
    FLASK_PORT,
    HISTORICO_DB_FILE,
    HISTORICO_FECHAMENTO_DIARIO,
    IMPRESSORAS_CONFIG,
    MONITOR_INTERVAL_SECONDS,
    SWITCHES_CONFIG,
)
from routes.api_routes import create_api_blueprint
from routes.web_routes import create_web_blueprint
from services.historico_service import inicializar_banco
from services.printer_monitor_service import PrinterMonitorService
from services.printer_config_service import PrinterConfigService
from services.switch_config_service import SwitchConfigService
from services.switch_monitor_service import SwitchMonitorService


def create_app():
    app = Flask(__name__)
    inicializar_banco(HISTORICO_DB_FILE)
    printer_config_service = PrinterConfigService(
        HISTORICO_DB_FILE,
        IMPRESSORAS_CONFIG,
    )
    switch_config_service = SwitchConfigService(
        HISTORICO_DB_FILE,
        SWITCHES_CONFIG,
    )
    printer_configs = printer_config_service.list_configs()
    switch_configs = switch_config_service.list_configs()

    monitor_service = PrinterMonitorService(
        printer_configs=printer_configs,
        historico_db_file=HISTORICO_DB_FILE,
        monitor_interval=MONITOR_INTERVAL_SECONDS,
        daily_close_time=HISTORICO_FECHAMENTO_DIARIO,
    )
    switch_monitor_service = SwitchMonitorService(
        switch_configs=switch_configs,
        historico_db_file=HISTORICO_DB_FILE,
        monitor_interval=MONITOR_INTERVAL_SECONDS,
    )
    monitor_service.start()
    switch_monitor_service.start()

    app.register_blueprint(
        create_api_blueprint(
            monitor_service,
            printer_config_service,
            switch_monitor_service=switch_monitor_service,
            switch_config_service=switch_config_service,
        )
    )
    app.register_blueprint(create_web_blueprint())

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
