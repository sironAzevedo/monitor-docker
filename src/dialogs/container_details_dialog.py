from PyQt5.QtWidgets import (
    QDialog, QTabWidget, QVBoxLayout, QWidget, QFormLayout,
    QLineEdit, QMessageBox, QPushButton, QHBoxLayout, QTextEdit, QSpinBox, QFileDialog
)
from PyQt5.QtCore import Qt
import json

from src.services.docker_utils import DockerUtils
from src.services.log_updater_thread import LogUpdaterThread


class ContainerDetailsDialog(QDialog):
    def __init__(self, dockerUtlis: DockerUtils, container_id, parent=None):
        super().__init__(parent)

        self.dockerUtlis = dockerUtlis
        self.setWindowTitle("Detalhes do Container")
        self.resize(800, 600)

        self.container_id = container_id
        self.log_thread = None

        self.tabs = QTabWidget()

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tabs)

        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("padding: 6px 12px;")
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.populate_tabs(container_id)

    def closeEvent(self, event):
        if self.log_thread:
            self.log_thread.stop()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def populate_tabs(self, container_id):
        details_json = self.dockerUtlis.get_container_details(container_id)

        try:
            details = json.loads(details_json)
            if isinstance(details, list):
                details = details[0]
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Erro", "Não foi possível decodificar os detalhes do container.")
            return

        # Aba: Informações
        info_tab = QWidget()
        info_layout = QFormLayout()

        info_fields = {
            "Created": details.get("Created"),
            "Image": details.get("Config", {}).get("Image"),
            "Name": details.get("Name", "").strip("/"),
            "Platform": details.get("Platform", "Desconhecido"),
            "NetworkMode": details.get("HostConfig", {}).get("NetworkMode"),
            "NetworkSettings": json.dumps(details.get("NetworkSettings", {}), indent=2),
            "Porta": str(details.get("NetworkSettings", {}).get("Ports", {}))
        }

        for key, value in info_fields.items():
            label = QLineEdit(str(value))
            label.setReadOnly(True)
            label.setStyleSheet("color: #f8f8f2; background-color: #3b3d48;")
            info_layout.addRow(f"{key}:", label)

        info_tab.setLayout(info_layout)
        self.tabs.addTab(info_tab, "Informações")

        # Aba: Configurações (Env)
        config_tab = QWidget()
        config_layout = QFormLayout()
        envs = details.get("Config", {}).get("Env", [])

        if envs:
            for env in envs:
                if '=' in env:
                    key, val = env.split("=", 1)
                    line = QLineEdit(val)
                    line.setReadOnly(True)
                    line.setStyleSheet("color: #f8f8f2; background-color: #3b3d48;")
                    config_layout.addRow(f"{key}:", line)

        config_tab.setLayout(config_layout)
        self.tabs.addTab(config_tab, "Configurações")

        # Aba: Logs
        log_tab = self.create_log_tab()
        self.tabs.addTab(log_tab, "Logs")

        self.start_log_thread()

    def create_log_tab(self):
        log_tab = QWidget()
        log_layout = QVBoxLayout()

        # Campo para definir quantidade de linhas
        self.line_count_spin = QSpinBox()
        self.line_count_spin.setRange(10, 10000)
        self.line_count_spin.setValue(100)
        self.line_count_spin.setSuffix(" linhas")
        self.line_count_spin.setStyleSheet("color: #f8f8f2; background-color: #3b3d48; padding: 4px;")
        self.line_count_spin.valueChanged.connect(self.restart_log_thread)

        # Botão para exportar logs
        export_button = QPushButton("Exportar Logs")
        export_button.setStyleSheet("padding: 4px;")
        export_button.clicked.connect(self.export_logs)

        config_layout = QHBoxLayout()
        config_layout.addWidget(self.line_count_spin)
        config_layout.addStretch()
        config_layout.addWidget(export_button)

        # Área de texto para logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("color: #f8f8f2; background-color: #282a36; font-family: 'Courier New';")

        log_layout.addLayout(config_layout)
        log_layout.addWidget(self.log_text)
        log_tab.setLayout(log_layout)

        return log_tab

    def start_log_thread(self):
        if self.log_thread:
            self.log_thread.stop()

        self.log_thread = LogUpdaterThread(self.container_id, self.line_count_spin.value())
        self.log_thread.new_logs.connect(self.update_logs)
        self.log_thread.start()

    def restart_log_thread(self):
        self.start_log_thread()

    def update_logs(self, logs):
        self.log_text.setPlainText(logs)
        self.log_text.moveCursor(self.log_text.textCursor().End)

    def export_logs(self):
        log_text = self.log_text.toPlainText()
        if not log_text.strip():
            QMessageBox.information(self, "Exportação", "Nenhum log para exportar.")
            return

        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Logs",
            f"{self.container_id}_logs.log",
            "Arquivos de Log (*.log);;Todos os Arquivos (*)",
            options=options
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(log_text)
                QMessageBox.information(self, "Sucesso", f"Logs exportados para:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar o arquivo:\n{str(e)}")