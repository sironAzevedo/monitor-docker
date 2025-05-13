from src.services.config_utils import resource_path, exist_file

folder_dev = 'assets'
folder_prod = '/opt/DockerMonitor/assets'

ICON_PATH = f'{folder_prod}/app-icon.png' if exist_file(folder_prod) else resource_path(f"{folder_dev}/app-icon.png")
ICON_HOME_PATH = f'{folder_prod}/home.png' if exist_file(folder_prod) else resource_path(f"{folder_dev}/home.png")
ICON_REPORT_PATH = f'{folder_prod}/report.png' if exist_file(folder_prod) else resource_path(f"{folder_dev}/report.png")
ICON_SETTINGS_PATH = f'{folder_prod}/settings.png' if exist_file(folder_prod) else resource_path(f"{folder_dev}/settings.png")
