import os
import sys

import PyQt5
from cx_Freeze import setup, Executable

# Detecta plataforma
is_windows = sys.platform == "win32"

# Base: Win32GUI no Windows para não abrir terminal. No Linux, não é necessário.
base = "Win32GUI" if is_windows else None

# Caminho da pasta de plugins do Qt
qt_plugins_path = os.path.join(os.path.dirname(PyQt5.__file__), "Qt5", "plugins", "platforms")

# Pasta de build final
build_dir = "build/DockerMonitor"

# Dependências adicionais (se necessário, adicione mais aqui)
packages = ["os", "sys", "PyQt5"]
includes = [
    "PyQt5.QtCore",
    "PyQt5.QtGui",
    "PyQt5.QtWidgets",
    "PyQt5.QtSvg",
    "PyQt5.QtPrintSupport",
    "PyQt5.QtNetwork",
    "PyQt5.Qt",
]

# Arquivos adicionais para incluir no build
include_files = [
    ("reminder_popup_app.py", "reminder_popup_app.py"),
    (qt_plugins_path, "platforms")
]

# Executável
executables = [
    Executable(
        script="main.py",
        base=base,
        target_name="DockerMonitor"
    )
]

setup(
    name="DockerMonitor",
    version="1.0",
    description="Monitor de containers Docker",
    options={
        "build_exe": {
            "includes": includes,
            "include_files": include_files,
            "excludes": [],
            "optimize": 2,
            "build_exe": "build/DockerMonitor",  # saída customizada
        }
    },
    executables=executables
)
