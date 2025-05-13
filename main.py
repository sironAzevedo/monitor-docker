import os
import subprocess
import sys

from PyQt5.QtWidgets import QApplication

from src.services.config_utils import load_config, resource_path, log_and_notify
from src.services.docker_utils import DockerUtils
from src.ui.docker_monitor import DockerMonitor


def iniciar_reminder_popup():
    script_path = resource_path("reminder_popup_app.py")
    subprocess.Popen([sys.executable, script_path])


if __name__ == "__main__":

    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(base_path, "platforms")

    docker_utils = DockerUtils()
    app = QApplication(sys.argv)

    log_and_notify("Aplicação iniciada...")
    settings = load_config()
    monitoring_enabled = settings.get("monitoring_enabled", False)

    if monitoring_enabled:
        iniciar_reminder_popup()

    monitor = DockerMonitor(docker_utils)
    monitor.show()
    sys.exit(app.exec_())