import os
import sys

from PyQt5.QtWidgets import QApplication

from src.services.config_utils import load_config, log_and_notify
from src.services.docker_utils import DockerUtils
from src.ui.docker_monitor import DockerMonitor
from src.utils.constantes_utils import iniciar_popup_monitoramento

if __name__ == "__main__":

    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(base_path, "platforms")

    settings = load_config()
    monitoring_enabled = settings.get("monitoring_enabled", False)

    # Verifica se o argumento "monitoramento" foi passado
    if len(sys.argv) > 1 and sys.argv[1] == "monitoramento":
        if monitoring_enabled:
            iniciar_popup_monitoramento()
        sys.exit(0)

    docker_utils = DockerUtils()
    app = QApplication(sys.argv)

    if monitoring_enabled:
        iniciar_popup_monitoramento()

    log_and_notify("Aplicação iniciada...")
    monitor = DockerMonitor(docker_utils)
    monitor.show()
    sys.exit(app.exec_())