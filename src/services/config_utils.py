import json
import os
from os import path
import sys
import platform
from pathlib import Path

from PyQt5.QtCore import QDateTime


def get_path(levels_up: int = 1) -> Path:
    return Path(__file__).resolve().parents[levels_up]

def resource_path(relative_path):
    # Pega o caminho absoluto, funciona tanto no PyInstaller quanto fora
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

DEFAULT_TIMEOUT = 1800  # 30 minutos
LOG_FILE = "docker_monitor/docker-monitor.log"
CONFIG_FILE = "docker_monitor/docker_monitor_config.json"

def log_and_notify(message):
    timestamp = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
    log_path = get_log_path()

    path = Path(log_path)
    if not path.exists():
        log_path = criate_folder(path)

    with open(log_path, "a") as log_file:
        log_file.write(f"{timestamp} - {message}\n")

def get_log_path():
    """Define o caminho do arquivo de log."""
    default_path = Path(LOG_FILE)
    if default_path.exists():
        return default_path

    # Alternativa para Linux: salvar no diretório home
    if get_operating_system() == 'Linux':
        return get_folder_home(LOG_FILE)

    return default_path  # fallback

def get_config_path():
    """Define o caminho do arquivo de configuração."""
    default_path = Path(CONFIG_FILE)
    if default_path.exists():
        return default_path

    # Alternativa para Linux: salvar no diretório home
    if get_operating_system() == 'Linux':
        return get_folder_home(CONFIG_FILE)

    return default_path  # fallback

def get_folder_home(path_file):
    home_path = Path(os.path.expanduser("~")) / path_file
    return home_path

def ensure_config_file(path, timeout=DEFAULT_TIMEOUT, monitoring=False):
    """Cria diretório e arquivo de configuração se não existirem."""
    try:
        path = criate_folder(path)
        save_config(timeout, monitoring, path)
    except Exception as e:
        print(f"[ERRO] Não foi possível criar o arquivo de configuração: {e}")

def load_config():
    path_config = get_config_path()

    path = Path(path_config)
    if not path.exists():
        ensure_config_file(path_config)

    try:
        with open(path_config, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERRO] Falha ao ler informações do arquivo {path_config}: {e}")

    return {
        "timeout": DEFAULT_TIMEOUT,
        "monitoring_enabled": False
    }

def get_operating_system():
    return platform.system()

def save_config(timeout_value, monitoring=False, path_file=CONFIG_FILE):
    try:
        path_file = Path(path_file)
        with open(path_file, "w") as f:
            json.dump({
                "timeout": timeout_value,
                "monitoring_enabled": monitoring
            }, f, indent=4)
    except Exception as e:
        print(f"[ERRO] Falha ao salvar configurações em {path_file}: {e}")

def exist_file(pathFile: str):
    return path.exists(pathFile)

def criate_folder(path):
    default_path = Path(path)
    if default_path.exists():
        return default_path

    default_path.parent.mkdir(parents=True, exist_ok=True)
    return default_path