import os
import subprocess
import sys

from src.services.config_utils import resource_path, exist_file

folder_dev = 'assets'
folder_prod = '/opt/DockerMonitor/assets'
file_folder_monitor_prod = '/opt/DockerMonitor'
file_monitor = 'monitoramento_container_app.py'

ICON_PATH = f'{folder_prod}/app-icon.png' if exist_file(folder_prod) else resource_path(f"{folder_dev}/app-icon.png")
ICON_HOME_PATH = f'{folder_prod}/home.png' if exist_file(folder_prod) else resource_path(f"{folder_dev}/home.png")
ICON_REPORT_PATH = f'{folder_prod}/report.png' if exist_file(folder_prod) else resource_path(f"{folder_dev}/report.png")
ICON_SETTINGS_PATH = f'{folder_prod}/settings.png' if exist_file(folder_prod) else resource_path(f"{folder_dev}/settings.png")

def iniciar_popup_monitoramento():
    global script_path
    if getattr(sys, 'frozen', False):
        # Caminho do binário MonitoramentoContainer dentro da pasta do app empacotado
        base_path = os.path.dirname(sys.executable)
        popup_executable = os.path.join(base_path, "MonitoramentoContainer")
    else:
        print('Monitormamento no modo desenvolvimento')
        popup_executable = sys.executable
        script_path = resource_path("monitoramento_container_app.py")

    if getattr(sys, 'frozen', False):
        subprocess.Popen([popup_executable])
    else:
        subprocess.Popen([popup_executable, script_path])